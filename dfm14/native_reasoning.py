"""Conservative CPU conversion of legacy traces to Gemma thought channels.

Operates on immutable rendered originals so tool syntax and masking boundaries
are retained. Ambiguous rows are quarantined, never guessed or flattened.
"""
from dataclasses import dataclass
import json
from pathlib import Path
import re

THOUGHT = '<|channel>thought\n'
END_THOUGHT = '<channel|>'
END_TURN = '<turn|>\n'
LEGACY = re.compile(r'</?(?:think|thinking|answer)>', re.I)
TURN = re.compile(r'(<\|turn>(?:system|user|model|tool)\n)')


def native_template():
    """Opt-in staged template; leave the shared/live template unchanged."""
    text = Path('data_io/chat_templates/gemma4_native_chat.jinja').read_text()
    old = "thinking_text and loop.index0 > ns_turn.last_user_idx and message.get('tool_calls')"
    new = "thinking_text and loop.index0 > ns_turn.last_user_idx and (message.get('tool_calls') or (enable_thinking is defined and enable_thinking))"
    if text.count(old) != 1:
        raise ValueError('Shared template changed; revalidate native reasoning adapter')
    return text.replace(old, new)


@dataclass(frozen=True)
class Answer:
    final: str
    reasoning: str = ''
    action: str = 'unchanged'

    def render(self):
        return (THOUGHT + self.reasoning + '\n' + END_THOUGHT if self.reasoning else '') + self.final


def terminal_answer(thought):
    """Recover a terminal action JSON wrongly enclosed inside a thought block."""
    decoder = json.JSONDecoder()
    candidates=[]
    for match in re.finditer(r'(?m)^\s*(?=\{)', thought):
        start=match.end()
        try:
            value,end=decoder.raw_decode(thought[start:])
        except ValueError:
            continue
        if thought[start+end:].strip():continue
        if not isinstance(value,dict) or not {'analysis','plan','commands','task_complete'} <= value.keys():continue
        if not isinstance(value['analysis'],str) or not isinstance(value['plan'],str) or not isinstance(value['task_complete'],bool):continue
        if not isinstance(value['commands'],list) or any(not isinstance(c,dict) or not isinstance(c.get('keystrokes'),str) or not isinstance(c.get('duration'),(int,float)) for c in value['commands']):continue
        reasoning=thought[:start].strip()
        if not LEGACY.search(reasoning+thought[start:]):
            candidates.append(Answer(thought[start:].strip(),reasoning,'repaired_terminal_json'))
    if len(candidates)==1:return candidates[0]
    # This source also loses the opening {"analysis": " while enclosing the
    # remaining JSON in <think>. Recover only if the entire strict schema parses;
    # this is user-requested visible JSON analysis, not a separate hidden trace.
    try:
        value=json.loads('{"analysis": "'+thought,strict=False)
    except ValueError:
        value=None
    if (isinstance(value,dict) and set(value)=={'analysis','plan','commands','task_complete'}
            and isinstance(value['analysis'],str) and isinstance(value['plan'],str)
            and isinstance(value['task_complete'],bool) and isinstance(value['commands'],list)
            and all(isinstance(c,dict) and isinstance(c.get('keystrokes'),str)
                    and isinstance(c.get('duration'),(int,float)) for c in value['commands'])
            and not LEGACY.search(json.dumps(value))):
        return Answer(json.dumps(value,ensure_ascii=False),action='repaired_terminal_json_prefix')
    raise ValueError('No unique terminal action JSON after reasoning')


def parse_answer(text, *, terminal=False):
    """Only repair explicit structural boundaries; never infer from prose."""
    if not LEGACY.search(text):
        if '<|channel>' in text:
            match = re.fullmatch(re.escape(THOUGHT) + r'(.*?)\n?' + re.escape(END_THOUGHT) + r'(.+)', text, re.S)
            if not match or not match[2].strip() or '<|channel>' in match[1] or END_THOUGHT in match[2]:
                raise ValueError('Malformed native reasoning')
            return Answer(match[2], match[1].rstrip('\n'), 'native_existing')
        return Answer(text)
    body = re.sub(r'(?m)^\s*#{1,6}[ \t]+(?=</?(?:think|thinking|answer)>)', '', text).strip()
    # A single closing thought boundary is recoverable even if its opening
    # was omitted. Leading duplicate openings are structural, not nested prose.
    closes = list(re.finditer(r'</(?:think|thinking)>', body, re.I))
    if len(closes) == 1:
        before, final = body[:closes[0].start()], body[closes[0].end():].strip()
        thought = re.sub(r'^(?:\s*<(?:think|thinking)>\s*)+', '', before, flags=re.I).strip()
        if terminal and not final and re.match(r'^\s*<(?:think|thinking)>',before,re.I):
            return terminal_answer(thought)
        final_match = re.fullmatch(r'<answer>\s*(.*?)\s*</answer>', final, re.S | re.I)
        if not re.match(r'^\s*<(?:think|thinking)>', before, re.I) and not final_match:
            raise ValueError('Missing opening tag without explicit final-answer boundary')
        final = final_match[1] if final_match else final
        if final.strip() and not LEGACY.search(thought) and not LEGACY.search(final):
            if any(marker in thought + final for marker in ('<|channel>', END_THOUGHT)):
                raise ValueError('Mixed native and legacy boundaries')
            well_formed = bool(re.match(r'^<(?:think|thinking)>', body, re.I)) and len(re.findall(r'<(?:think|thinking)>', before, re.I)) == 1
            return Answer(final, thought, 'converted' if well_formed else 'repaired')
    # An explicit, terminal answer block can survive corrupt/truncated thoughts.
    final_match = re.search(r'<answer>\s*(.*?)\s*</answer>\s*$', body, re.S | re.I)
    if final_match and final_match[1].strip() and not LEGACY.search(final_match[1]):
        prefix = body[:final_match.start()].strip()
        if not prefix or re.match(r'^<(?:think|thinking)>', prefix, re.I):
            return Answer(final_match[1], action='stripped' if prefix else 'repaired')
    # These reasoning sources also use a standalone answer block without any
    # thought tags. Its explicit boundary permits moving surrounding solution
    # prose into the thought channel, without guessing a final answer from prose.
    blocks=list(re.finditer(r'(?m)^<answer>\s*(.*?)\s*</answer>',body,re.S|re.I))
    if len(blocks)==1:
        match=blocks[0];reasoning=(body[:match.start()]+'\n'+body[match.end():]).strip()
        if match[1].strip() and not LEGACY.search(reasoning+match[1]) and '```' not in reasoning:
            return Answer(match[1],reasoning,'repaired_answer_block')
    raise ValueError('No unambiguous complete final answer / quoted or embedded legacy markup')


def repair_prompt(prompt, norwegian=False, terminal=False):
    """Previous assistant thoughts are hidden, as in Gemma's history guard."""
    parts = TURN.split(prompt)
    if parts[0] not in ('', '<bos>'):
        raise ValueError('Unexpected rendered prompt prefix')
    for i in range(1, len(parts), 2):
        role, body = parts[i][len('<|turn>'):-1], parts[i+1]
        if role == 'model' and body:
            if not body.endswith(END_TURN):
                raise ValueError('Unfinished assistant history')
            parsed = parse_answer(body[:-len(END_TURN)],terminal=terminal)
            parts[i+1] = parsed.final + END_TURN
        elif role == 'user' and norwegian:
            parts[i+1] = re.sub(r'\s*</think>(?=<turn\|>\n$)', '', body, flags=re.I)
    return ''.join(parts)


def set_thinking(prompt, enabled):
    prefix = '<bos>' if prompt.startswith('<bos>') else ''
    text = prompt[len(prefix):]
    header = '<|turn>system\n'
    if text.startswith(header):
        end = text.index(END_TURN)
        system = text[len(header):end]
        if system.startswith('<|think|>\n'):
            system = system[len('<|think|>\n'):]
        system = ('<|think|>\n' if enabled else '') + system
        text = (header + system + END_TURN if system else '') + text[end+len(END_TURN):]
    elif enabled:
        text = header + '<|think|>\n' + END_TURN + text
    return prefix + text


def repair_row(prompt, response, tokenizer, *, norwegian=False, terminal=False, max_length=4097):
    if not response.endswith(END_TURN):
        raise ValueError('Truncated/unsupported response ending')
    parsed = parse_answer(response[:-len(END_TURN)],terminal=terminal)
    if not parsed.final.strip():
        raise ValueError('Empty final answer')
    prompt = repair_prompt(prompt, norwegian,terminal)
    def encode(answer):
        p = set_thinking(prompt, bool(answer.reasoning))
        r = answer.render() + END_TURN
        return p, r, tokenizer.encode(p, add_special_tokens=False).ids, tokenizer.encode(r, add_special_tokens=False).ids
    p, r, pi, ri = encode(parsed)
    action = parsed.action
    if len(pi) + len(ri) > max_length and parsed.reasoning:
        parsed = Answer(parsed.final, action='stripped_length')
        action = parsed.action
        p, r, pi, ri = encode(parsed)
    if len(pi) + len(ri) > max_length:
        raise ValueError('Complete final answer does not fit context; no truncation permitted')
    return dict(prompt=p, response=r, inst=pi, resp=ri, action=action,
                reasoning=parsed.reasoning, final=parsed.final, enable_thinking=bool(parsed.reasoning))
