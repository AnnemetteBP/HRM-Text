import pytest

from dfm14.repair_reasoning import repair_rendered


def test_reasoning_preserved_without_wrappers():
    assert repair_rendered('<think>Compute 2+2.</think><answer>4</answer><turn|>\n', response=True) == 'Compute 2+2.\n\n4<turn|>\n'


def test_missing_opening_tag():
    assert repair_rendered('Compute.\n</think><answer>4</answer><turn|>\n', response=True) == 'Compute.\n\n4<turn|>\n'


def test_answer_precedes_reasoning():
    assert repair_rendered('Alice wins.\n<think>Proof.</think>',response=True) == 'Alice wins.\n\nProof.'


def test_nested_legacy_wrappers():
    text='<think>\n<think>\nReason.\n</think>\n<answer>\n<think>\nReason.</answer><turn|>\n'
    assert repair_rendered(text,response=True) == 'Reason.\n\nReason.<turn|>\n'


def test_repeated_orphan_closing_tags():
    assert repair_rendered('Reason.</think>More.</think>Answer.',response=True) == 'Reason.\n\nMore.\n\nAnswer.'


def test_reasoning_meta_reference_keeps_solution():
    text='I omit the full `<think>` trace.\n\nThe answer is 4.<turn|>\n'
    assert repair_rendered(text,response=True) == 'I omit the full reasoning trace.\n\nThe answer is 4.<turn|>\n'


def test_quoted_pair_and_markdown_headers():
    assert repair_rendered('I omit the private "<think>...</think>" reasoning.',response=True) == 'I omit the private reasoning.'
    assert repair_rendered('# <think>\nProof\n# </think>\n# <answer>\n4\n# </answer><turn|>\n',response=True) == 'Proof\n\n4<turn|>\n'


def test_empty_reasoning():
    assert repair_rendered('<think>\n</think><answer>4</answer><turn|>\n', response=True) == '4<turn|>\n'


def test_truncated_reasoning():
    assert repair_rendered('<think>Still computing', response=True) == 'Still computing'


def test_native_template_and_tools_unchanged():
    text='<bos><|turn>system\n<|tool>schema<tool|><turn|>\n<|turn>user\nHi<turn|>\n<|turn>model\n'
    assert repair_rendered(text) == text
    text='<|channel>thought\nreason\n<channel|><|tool_call>call:search{q:1}<|tool_response>'
    assert repair_rendered(text,response=True) == text


def test_multi_turn_repair():
    text='<bos><|turn>user\nQ<turn|>\n<|turn>model\n<think>R</think>A<turn|>\n<|turn>user\nNext<turn|>\n<|turn>model\n'
    assert repair_rendered(text) == text.replace('<think>R</think>A','R\n\nA')


def test_norwegian_stray_user_close():
    text='<bos><|turn>user\nSporsmal?\n</think><turn|>\n<|turn>model\n'
    assert repair_rendered(text,norwegian=True) == text.replace('\n</think>','')
    with pytest.raises(ValueError):repair_rendered(text)


def test_quoted_markup_not_silently_deleted():
    with pytest.raises(ValueError):repair_rendered('The tag `<think>` means something.',response=True)


def test_plain_text_identity():
    text='  Step one.\n\nThen give \\boxed{42}.<turn|>\n'
    assert repair_rendered(text,response=True) == text


def test_sample_redirect_preserves_order_repeats_and_unaffected_tokens(tmp_path):
    import json
    import numpy as np
    from dfm14.repair_reasoning import build_sample

    base=tmp_path/'base'; root=tmp_path/'repair'; original=tmp_path/'original'
    fixed=root/'tokenized'/'affected'
    for path in (base/'epoch_0',original,fixed):path.mkdir(parents=True)
    def save(path, data):
        for key,value in data.items():np.save(path/(key+'.npy'),np.asarray(value,dtype=np.uint64))
    save(base,dict(tokens=list(range(9))))
    save(original,dict(inst_start=[0,3],inst_len=[1,1],resp_start=[1,4],resp_len=[2,2]))
    save(fixed,dict(tokens=[0,2,3,4,5],inst_start=[0,2],inst_len=[1,1],resp_start=[1,3],resp_len=[1,2]))
    save(base/'epoch_0',dict(inst_start=[3,6,0,0],inst_len=[1]*4,resp_start=[4,7,1,1],resp_len=[2]*4))
    (base/'metadata.json').write_text(json.dumps(dict(total_length=12,max_seq_len=4097)))
    build_sample(root,base,[dict(name='affected',path=str(original),offset=0,tokens=6,new_tokens=5)])
    output=root/'sampled_dfm14'
    assert np.load(output/'epoch_0/inst_start.npy').tolist()==[11,6,9,9]
    assert np.load(output/'epoch_0/resp_start.npy').tolist()==[12,7,10,10]
    assert np.load(output/'epoch_0/resp_len.npy').tolist()==[2,2,1,1]
    assert np.load(output/'tokens.npy')[6:9].tolist()==[6,7,8]
    assert json.loads((output/'metadata.json').read_text())['total_length']==10
    assert json.loads((output/'ready.json').read_text())['status']=='validated_staged_not_promoted'


def test_repair_part_matches_frozen_backing_and_preserves_original(tmp_path,monkeypatch):
    import numpy as np
    from types import SimpleNamespace
    from dfm14 import repair_reasoning as mod

    class FakeTokenizer:
        @classmethod
        def from_file(cls,path):return cls()
        def decode(self,ids,**kwargs):return ''.join(map(chr,ids))
        def encode(self,text,**kwargs):return SimpleNamespace(ids=list(map(ord,text)))
    monkeypatch.setattr(mod,'Tokenizer',FakeTokenizer)
    source=tmp_path/'source';base=tmp_path/'base';root=tmp_path/'repair'
    source.mkdir();base.mkdir()
    prompt='<bos><|turn>user\nQ<turn|>\n<|turn>model\n'
    response='<think>R</think><answer>A</answer><turn|>\n'
    tokens=np.array(list(map(ord,prompt+response)),dtype=np.uint32)
    np.save(source/'tokens.npy',tokens)
    for k,v in dict(inst_start=[0],inst_len=[len(prompt)],resp_start=[len(prompt)],resp_len=[len(response)]).items():
        np.save(source/(k+'.npy'),np.asarray(v,dtype=np.uint64))
    np.save(base/'tokens.npy',np.concatenate(([99],tokens,[99])))
    entry=dict(path=str(source),name='test',offset=1,tokens=len(tokens),norwegian=False)
    result=mod.repair_part((str(root),str(base),entry,'unused'))
    assert result['changed']==1 and result['unresolved']==0
    fixed=''.join(map(chr,np.load(root/'tokenized/test/tokens.npy')))
    assert fixed == prompt+'R\n\nA<turn|>\n'
    assert np.array_equal(np.load(source/'tokens.npy'),tokens)
