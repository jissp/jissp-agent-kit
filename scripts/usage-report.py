#!/usr/bin/env python3
"""Claude Code 대화 기록(~/.claude/projects)으로 스킬 실행 1회당 토큰·캐시·비용을 집계한다.

사용법:
  python3 usage-report.py                                  # jissp-task-manager run (기본)
  python3 usage-report.py --since 2026-10-17               # 기간 제한
  python3 usage-report.py --skill planner-execute --args ''
  python3 usage-report.py --detail                         # 실행별 행 출력
  python3 usage-report.py --end human                      # 실행 구간을 다음 사람 입력 직전까지로 제한

실행 1회 = 스킬 호출부터 다음 슬래시 명령 입력(또는 세션 끝) 직전까지.
  --end human 이면 다음 사람 입력 직전까지. (run 이후 이어진 대화 제외, 대신 텍스트 승인 응답 이후도 잘림)
서브에이전트는 meta.json 의 toolUseId 로 해당 실행에서 띄운 것만 합산한다.
비용은 API 단가 환산값이다. (구독 요금제의 실제 청구액이 아님)
"""
import argparse
import collections
import glob
import json
import os
import statistics
from datetime import datetime, timedelta, timezone

ROOT = os.path.expanduser('~/.claude/projects')
KST = timezone(timedelta(hours=9))

# $/MTok (input, output, cache read). 캐시 쓰기는 1시간 TTL 기준 input 의 2배로 계산한다.
PRICES = {
    'claude-fable-5-1': (10, 50, 0.25),
    'claude-opus-5-5': (4, 20, 0.20),
    'claude-opus-5': (5, 25, 0.50),
    'claude-sonnet-5-5': (2, 10, 0.20),
    'claude-sonnet-5': (2, 10, 0.20),
    'claude-haiku-5-5': (0.10, 0.50, 0.01),
}
CACHE_WRITE_MULTIPLIER = 2

IMPL_AGENT = 'jissp-task-implementer'
IMPL_SKILL = 'jissp-task-implement'
GUIDELINE = 'planner-execute/guideline.md'
REVIEW_AGENTS = ('jissp-doc-reviewer', 'jissp-gap-validator', 'jissp-doc-reviewer-report')  # 마지막은 개명 전 이름 (과거 세션 집계용)
SKILL_ALIASES = {
    'jissp-task-manager': ('jissp-task-manager-v2',),
    'jissp-feature-spec-generator': ('jissp-project-spec-generator',),
}  # 개명 전 이름 (과거 세션 집계용)
REVIEW_BUCKETS = ((0, 0, '0'), (1, 1, '1'), (2, 2, '2'), (3, 4, '3-4'), (5, None, '5+'))


def to_kst(timestamp):
    return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone(KST).strftime('%Y-%m-%d %H:%M')


def kst_date_to_utc(date):
    if not date:
        return ''
    start = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=KST)
    return start.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M')


def load_jsonl(path):
    entries = []
    with open(path, errors='ignore') as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except ValueError:
                pass
    return entries


def content_of(entry):
    message = entry.get('message')
    return message.get('content') if isinstance(message, dict) else None


def text_of(entry):
    content = content_of(entry)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ' '.join(block.get('text', '') for block in content if isinstance(block, dict))
    return ''


def tool_uses(entry):
    content = content_of(entry)
    if entry.get('type') != 'assistant' or not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict) and block.get('type') == 'tool_use']


def is_human_input(entry):
    if entry.get('type') != 'user' or entry.get('isMeta') or entry.get('isSidechain'):
        return False
    content = content_of(entry)
    if isinstance(content, list) and any(isinstance(b, dict) and b.get('type') == 'tool_result' for b in content):
        return False
    text = text_of(entry)
    return not (text.startswith('<system-reminder') or '<task-notification' in text or '<local-command' in text)


def is_slash_command(entry):
    return is_human_input(entry) and '<command-name>/' in text_of(entry)


def is_run_start(entry, skills, args_prefix):
    for block in tool_uses(entry):
        payload = block.get('input') or {}
        if block.get('name') == 'Skill' and payload.get('skill') in skills \
                and (payload.get('args') or '').startswith(args_prefix):
            return True
    if is_human_input(entry):
        text = text_of(entry)
        if any(f'<command-name>/{skill}</command-name>' in text for skill in skills) \
                and f'<command-args>{args_prefix}' in text:
            return True
    return False


def add_usage(totals, entries, seen):
    for entry in entries:
        message = entry.get('message')
        if entry.get('type') != 'assistant' or not isinstance(message, dict):
            continue
        usage = message.get('usage')
        model = message.get('model')
        message_id = message.get('id') or entry.get('requestId')
        if not usage or model == '<synthetic>' or message_id in seen:
            continue
        seen.add(message_id)
        bucket = totals[model]
        bucket['calls'] += 1
        bucket['input'] += usage.get('input_tokens', 0)
        bucket['cache_write'] += usage.get('cache_creation_input_tokens', 0)
        bucket['cache_read'] += usage.get('cache_read_input_tokens', 0)
        bucket['output'] += usage.get('output_tokens', 0)


def cost_parts(model, bucket):
    input_price, output_price, read_price = PRICES.get(model, PRICES['claude-opus-5-5'])
    return {
        'input': bucket['input'] * input_price / 1e6,
        'cache_write': bucket['cache_write'] * input_price * CACHE_WRITE_MULTIPLIER / 1e6,
        'cache_read': bucket['cache_read'] * read_price / 1e6,
        'output': bucket['output'] * output_price / 1e6,
    }


def detect_impl_mode(entries):
    modes = set()
    for entry in entries:
        for block in tool_uses(entry):
            payload = block.get('input') or {}
            if block.get('name') in ('Agent', 'Task') and payload.get('subagent_type') == IMPL_AGENT:
                modes.add('agent')
            elif block.get('name') == 'Skill' and payload.get('skill') == IMPL_SKILL:
                modes.add('skill')
            elif block.get('name') == 'Read' and GUIDELINE in payload.get('file_path', ''):
                modes.add('inline')
    return '+'.join(sorted(modes)) or '-'


def load_subagents(session_path):
    subagents = {}
    for meta_path in glob.glob(session_path[:-len('.jsonl')] + '/subagents/*.meta.json'):
        try:
            meta = json.load(open(meta_path))
        except ValueError:
            continue
        transcript = meta_path[:-len('.meta.json')] + '.jsonl'
        if meta.get('toolUseId') and os.path.exists(transcript):
            subagents[meta['toolUseId']] = (meta.get('agentType', '?'), transcript)
    return subagents


def collect_runs(skill, args_prefix, since, end_at):
    skills = (skill,) + SKILL_ALIASES.get(skill, ())
    is_run_end = is_human_input if end_at == 'human' else is_slash_command
    runs = []
    seen_starts = set()  # resume 한 세션은 이전 기록을 복사하므로 같은 실행이 두 파일에 존재한다.
    for session_path in glob.glob(f'{ROOT}/*/*.jsonl'):
        entries = load_jsonl(session_path)
        starts = [i for i, e in enumerate(entries) if is_run_start(e, skills, args_prefix)]
        if not starts:
            continue
        subagents = load_subagents(session_path)
        consumed = set()
        for start in starts:
            start_id = entries[start].get('uuid')
            if start in consumed or start_id in seen_starts or (entries[start].get('timestamp') or '') < since:
                continue
            seen_starts.add(start_id)
            end = start + 1
            while end < len(entries) and not is_run_end(entries[end]):
                end += 1
            consumed.update(s for s in starts if start <= s < end)
            window = entries[start:end]

            main_usage = collections.defaultdict(collections.Counter)
            add_usage(main_usage, window, set())
            sub_usage = collections.defaultdict(collections.Counter)
            sub_types = collections.Counter()
            for entry in window:
                for block in tool_uses(entry):
                    if block.get('id') in subagents:
                        agent_type, transcript = subagents[block['id']]
                        sub_types[agent_type] += 1
                        add_usage(sub_usage, load_jsonl(transcript), set())
            if not main_usage:
                continue
            runs.append({
                'start': entries[start].get('timestamp', ''),
                'session': os.path.basename(os.path.dirname(session_path)),
                'mode': detect_impl_mode(window),
                'main': main_usage,
                'sub': sub_usage,
                'sub_types': sub_types,
            })
    return sorted(runs, key=lambda r: r['start'])


def summarize(usage_by_model):
    total = collections.Counter()
    costs = collections.Counter()
    for model, bucket in usage_by_model.items():
        total.update(bucket)
        costs.update(cost_parts(model, bucket))
    prompt = total['input'] + total['cache_write'] + total['cache_read']
    total['tokens'] = prompt + total['output']
    total['hit_rate'] = total['cache_read'] / prompt if prompt else 0
    total['cost'] = sum(costs.values())
    total['cost_read'] = costs['cache_read']
    total['cost_write'] = costs['cache_write'] + costs['input']
    total['cost_output'] = costs['output']
    return total


def review_count(run):
    return sum(n for name, n in run['sub_types'].items() if name in REVIEW_AGENTS)


def review_bucket(count):
    for low, high, label in REVIEW_BUCKETS:
        if count >= low and (high is None or count <= high):
            return label


def short_models(usage_by_model):
    return ','.join(sorted(m.replace('claude-', '') for m in usage_by_model)) or '-'


def fmt_tokens(value):
    return f'{value / 1e6:.2f}M' if value >= 1e6 else f'{value / 1e3:.0f}K'


def print_detail(runs):
    print(f"{'시작(KST)':<17} {'방식':<12} {'메인 모델':<14} {'호출':>5} {'검토':>4} {'메인 토큰':>9} {'적중률':>6} {'메인$':>7} "
          f"{'읽기$':>6} {'쓰기$':>6} {'출력$':>6} {'서브 토큰':>9} {'서브$':>7} {'합계$':>7}  서브에이전트")
    for run in runs:
        main, sub = summarize(run['main']), summarize(run['sub'])
        agents = ', '.join(f'{name}×{n}' for name, n in run['sub_types'].items())
        print(f"{to_kst(run['start']):<17} {run['mode']:<12} {short_models(run['main']):<14} "
              f"{main['calls']:>5} {review_count(run):>4} {fmt_tokens(main['tokens']):>9} {main['hit_rate']:>6.0%} {main['cost']:>7.2f} "
              f"{main['cost_read']:>6.2f} {main['cost_write']:>6.2f} {main['cost_output']:>6.2f} "
              f"{fmt_tokens(sub['tokens']):>9} {sub['cost']:>7.2f} {main['cost'] + sub['cost']:>7.2f}  {agents}")
    print()


def print_summary(runs):
    by_mode = collections.defaultdict(list)
    for run in runs:
        by_mode[run['mode']].append(run)
    print(f"{'방식':<12} {'실행':>4} {'합계$ 평균':>10} {'중앙':>7} {'메인$ 평균':>10} "
          f"{'읽기$':>6} {'쓰기$':>6} {'출력$':>6} {'서브$ 평균':>10} "
          f"{'메인 호출 평균':>12} {'메인 토큰 평균':>13} {'메인 적중률':>10} {'서브 캐시쓰기 평균':>16}")
    for mode, items in sorted(by_mode.items()):
        mains = [summarize(r['main']) for r in items]
        subs = [summarize(r['sub']) for r in items]
        totals = [m['cost'] + s['cost'] for m, s in zip(mains, subs)]
        prompt_main = sum(m['input'] + m['cache_write'] + m['cache_read'] for m in mains)
        hit_rate = sum(m['cache_read'] for m in mains) / prompt_main if prompt_main else 0
        print(f"{mode:<12} {len(items):>4} {statistics.mean(totals):>10.2f} {statistics.median(totals):>7.2f} "
              f"{statistics.mean(m['cost'] for m in mains):>10.2f} "
              f"{statistics.mean(m['cost_read'] for m in mains):>6.2f} "
              f"{statistics.mean(m['cost_write'] for m in mains):>6.2f} "
              f"{statistics.mean(m['cost_output'] for m in mains):>6.2f} "
              f"{statistics.mean(s['cost'] for s in subs):>10.2f} "
              f"{statistics.mean(m['calls'] for m in mains):>12.0f} {fmt_tokens(statistics.mean(m['tokens'] for m in mains)):>13} {hit_rate:>10.0%} "
              f"{fmt_tokens(statistics.mean(s['cache_write'] for s in subs)):>16}")


def print_review_summary(runs):
    by_bucket = collections.defaultdict(list)
    for run in runs:
        by_bucket[review_bucket(review_count(run))].append(run)
    print(f"\n{'검토 횟수':<10} {'실행':>4} {'합계$ 평균':>10} {'중앙':>7} {'메인$ 평균':>10} {'서브$ 평균':>10} "
          f"{'메인 호출 평균':>12} {'메인 토큰 평균':>13}")
    for _, _, label in REVIEW_BUCKETS:
        items = by_bucket.get(label)
        if not items:
            continue
        mains = [summarize(r['main']) for r in items]
        subs = [summarize(r['sub']) for r in items]
        totals = [m['cost'] + s['cost'] for m, s in zip(mains, subs)]
        print(f"{label:<10} {len(items):>4} {statistics.mean(totals):>10.2f} {statistics.median(totals):>7.2f} "
              f"{statistics.mean(m['cost'] for m in mains):>10.2f} {statistics.mean(s['cost'] for s in subs):>10.2f} "
              f"{statistics.mean(m['calls'] for m in mains):>12.0f} "
              f"{fmt_tokens(statistics.mean(m['tokens'] for m in mains)):>13}")


def main():
    parser = argparse.ArgumentParser(description='스킬 실행 1회당 토큰·캐시·비용 집계')
    parser.add_argument('--skill', default='jissp-task-manager')
    parser.add_argument('--args', dest='args_prefix', default='run', help="스킬 인자 접두어 ('' 이면 전체)")
    parser.add_argument('--since', default='', help='이 날짜(KST, YYYY-MM-DD) 이후 시작한 실행만')
    parser.add_argument('--detail', action='store_true', help='실행별 행 출력')
    parser.add_argument('--end', choices=('slash', 'human'), default='slash',
                        help='실행 구간 끝: slash=다음 슬래시 명령 직전(기본) / human=다음 사람 입력 직전')
    options = parser.parse_args()

    runs = collect_runs(options.skill, options.args_prefix, kst_date_to_utc(options.since), options.end)
    if not runs:
        print('집계할 실행이 없습니다.')
        return
    if options.detail:
        print_detail(runs)
    print_summary(runs)
    print_review_summary(runs)
    print('\n방식: agent=서브에이전트 위임 / skill=구현 스킬 / inline=메인 직접 구현 / -=설계 문서 없는 실행 등')
    print('검토 횟수: 실행 중 jissp-doc-reviewer, jissp-gap-validator 서브에이전트 호출 수 (합산).')
    print('메인$ 분해: 읽기=캐시 읽기 / 쓰기=캐시 쓰기+비캐시 input / 출력=output. 호출=메인 API 호출 수.')
    print('비용은 API 단가 환산값. 캐시 쓰기는 input 단가×2 로 계산.')


if __name__ == '__main__':
    main()
