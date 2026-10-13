from pathlib import Path
from types import SimpleNamespace
import json

import jinja2
import numpy as np
import pytest

from dfm14.native_reasoning import (parse_answer, repair_row, native_template,
                                  THOUGHT, END_THOUGHT, END_TURN)


class Characters:
    def encode(self,text,**kwargs):return SimpleNamespace(ids=list(map(ord,text)))
    def decode(self,ids,**kwargs):return ''.join(map(chr,ids))
    @classmethod
    def from_file(cls,path):return cls()


PROMPT='<bos><|turn>user\nQ<turn|>\n<|turn>model\n'


@pytest.mark.parametrize('body,action', [
    ('<think>Reason.</think><answer>4</answer>','converted'),
    ('<thinking>Reason.</thinking>4','converted'),
    ('Reason.</think><answer>4</answer>','repaired'),
    ('<think><think>Reason.</think>4','repaired'),
    ('<think>broken</think>more</think><answer>4</answer>','stripped'),
    ('<answer>4</answer>','repaired'),
])
def test_explicit_boundaries(body,action):
    a=parse_answer(body)
    assert a.final=='4' and a.action==action


@pytest.mark.parametrize('body',[
    '<think>Never finished', '<think>Reason.</think>',
    '<think>Reason.</think><answer>truncated',
    'Answer first<think>Reason</think>',
    'Explain `</think>` to me', '<think>Nested<think>bad</think>A',
    '<think>Reason.</think><answer><think>Bad</answer>',
])
def test_ambiguous_quarantine(body):
    with pytest.raises(ValueError):parse_answer(body)


def test_modes_and_mask_boundary():
    fixed=repair_row(PROMPT,'<think>Reason.</think>4'+END_TURN,Characters())
    assert '<|think|>' in fixed['prompt']
    assert fixed['response']==THOUGHT+'Reason.\n'+END_THOUGHT+'4'+END_TURN
    assert fixed['prompt'].endswith('<|turn>model\n')
    assert '<|channel>' not in fixed['prompt']
    assert fixed['reasoning']=='Reason.' and fixed['final']=='4'
    plain=repair_row(PROMPT,'Visible explanation. 4'+END_TURN,Characters())
    assert plain['prompt']==PROMPT and not plain['enable_thinking']
    assert plain['response']=='Visible explanation. 4'+END_TURN


def test_history_hides_thought_but_preserves_final():
    p=PROMPT+'<think>Old secret</think>Old answer'+END_TURN+'<|turn>user\nNext'+END_TURN+'<|turn>model\n'
    fixed=repair_row(p,'<think>New thought</think>New answer'+END_TURN,Characters())
    assert 'Old secret' not in fixed['prompt'] and 'Old answer' in fixed['prompt']
    assert 'New thought' in fixed['response']


def test_no_truncated_native_targets():
    fixed=repair_row(PROMPT,'<think>'+'R'*500+'</think>4'+END_TURN,Characters(),max_length=150)
    assert fixed['action']=='stripped_length'
    assert fixed['prompt']==PROMPT and fixed['response']=='4'+END_TURN
    with pytest.raises(ValueError,match='does not fit'):
        repair_row(PROMPT,'<think>R</think>'+'A'*500+END_TURN,Characters(),max_length=150)


def test_native_template_parity():
    template=jinja2.Environment().from_string(native_template())
    messages=[dict(role='user',content='Q'),dict(role='assistant',content='4',reasoning_content='Reason.')]
    for enabled in (False,True):
        prompt=template.render(messages=messages[:1],enable_thinking=enabled,add_generation_prompt=True,bos_token='<bos>')
        full=template.render(messages=messages,enable_thinking=enabled,add_generation_prompt=False,bos_token='<bos>')
        fixed=repair_row(PROMPT,('<think>Reason.</think>' if enabled else '')+'4'+END_TURN,Characters())
        assert prompt==fixed['prompt']
        assert full==fixed['prompt']+fixed['response']
    old=jinja2.Environment().from_string(Path('data_io/chat_templates/gemma4_native_chat.jinja').read_text())
    assert template.render(messages=messages,enable_thinking=False)==old.render(messages=messages,enable_thinking=False)


def test_tool_structure_and_user_literals():
    p=PROMPT.replace('Q','What is <think>?')
    call='<|tool_call>call:search{q:<|"|>abc<|"|>}<tool_call|>'
    fixed=repair_row(p,'<think>Need search</think>'+call+END_TURN,Characters())
    assert 'What is <think>?' in fixed['prompt']
    assert fixed['final']==call


def test_terminal_json_recovered_only_for_terminal_source():
    answer=json.dumps(dict(analysis='Ready',plan='Run',commands=[dict(keystrokes='ls\n',duration=1)],task_complete=False))
    body='<think>Need to inspect.\n'+answer+'</think>'
    with pytest.raises(ValueError):parse_answer(body)
    fixed=parse_answer(body,terminal=True)
    assert fixed.final==answer and fixed.reasoning=='Need to inspect.'
    with pytest.raises(ValueError):parse_answer('<think>Reason\n{"answer":4}</think>',terminal=True)


def test_answer_block_with_solution_prose():
    fixed=parse_answer('Calculate the inverse.\n\n<answer>17</answer>\nThis satisfies the equation.')
    assert fixed.final=='17' and fixed.action=='repaired_answer_block'
    assert 'Calculate' in fixed.reasoning and 'satisfies' in fixed.reasoning
    with pytest.raises(ValueError):parse_answer('Use the tag `<answer>42</answer>` here.')


def test_terminal_missing_json_analysis_prefix():
    body='<think>Need files.\nCheck first.", "plan":"list", "commands":[{"keystrokes":"ls\\n","duration":1}], "task_complete":false}</think>'
    fixed=parse_answer(body,terminal=True)
    assert fixed.action=='repaired_terminal_json_prefix' and not fixed.reasoning
    assert json.loads(fixed.final)['analysis']=='Need files.\nCheck first.'


def test_quarantine_sampling_preserves_order_and_repeats(tmp_path):
    from dfm14.repair_reasoning import build_sample
    base=tmp_path/'base';root=tmp_path/'repair';source=tmp_path/'source';fixed=root/'tokenized/test'
    for p in (base/'epoch_0',source,fixed):p.mkdir(parents=True)
    def save(p,values):
        for k,v in values.items():np.save(p/(k+'.npy'),np.array(v,dtype=np.uint64))
    save(base,dict(tokens=list(range(9))))
    save(source,dict(inst_start=[0,3],inst_len=[1,1],resp_start=[1,4],resp_len=[2,2]))
    save(fixed,dict(tokens=[20,21,22],inst_start=[0,3],inst_len=[1,0],resp_start=[1,3],resp_len=[2,0],valid=[2,0]))
    save(base/'epoch_0',dict(inst_start=[3,6,0,0],inst_len=[1]*4,resp_start=[4,7,1,1],resp_len=[2]*4))
    (base/'metadata.json').write_text(json.dumps(dict(total_length=12,max_seq_len=4097)))
    build_sample(root,base,[dict(name='test',path=str(source),offset=0,tokens=6,new_tokens=3)],native=True)
    out=root/'sampled_dfm14/epoch_0'
    assert np.load(out/'inst_start.npy').tolist()==[6,9,9]
    report=json.loads((out/'repair.json').read_text())
    assert report['quarantined_occurrences']==1 and report['native_thinking_occurrences']==2
    assert report['tokens']==9


def test_part_quarantines_without_preserving_bad_target(tmp_path,monkeypatch):
    from dfm14 import build_native_reasoning as mod
    monkeypatch.setattr(mod,'Tokenizer',Characters)
    source=tmp_path/'source';base=tmp_path/'base';root=tmp_path/'root'
    source.mkdir();base.mkdir()
    data=[]; indices={k:[] for k in mod.FIELDS}
    for response in ['<think>R</think>A'+END_TURN,'<think>Truncated'+END_TURN]:
        for field,text in [('inst',PROMPT),('resp',response)]:
            indices[field+'_start'].append(len(data));indices[field+'_len'].append(len(text));data.extend(map(ord,text))
    for k,v in dict(tokens=data,**indices).items():np.save(source/(k+'.npy'),np.asarray(v,dtype=np.uint32))
    np.save(base/'tokens.npy',np.asarray(data,dtype=np.uint32))
    entry=dict(name='test',path=str(source),offset=0,tokens=len(data),norwegian=False)
    result=mod.repair_part((str(root),str(base),entry,'unused'))
    assert result['counts']['thinking']==1 and result['counts']['quarantined']==1
    assert np.load(root/'tokenized/test/valid.npy').tolist()==[2,0]
