---
name: sync-skill
description: >
  jissp-agent-kit 의 공통 스킬·서브에이전트·hook 원본을 기준으로 Claude Code·Gemini(안티그라비티) 스킬 디렉토리와 서브에이전트 디렉토리에 빠진 심볼릭 링크와 Gemini manifest.json 을, 각 에이전트 settings.json 에 빠진 hook 등록을 반영합니다. promote-skill 의 역방향(원본 → 에이전트) 동기화입니다.
  원본에 새 스킬·서브에이전트·hook·보조 리소스(scripts/ 등)를 추가했거나, description 을 바꿨거나, 새 PC 에서 링크를 다시 잡아야 할 때 사용합니다.
  사용자가 "스킬 동기화해줘", "jissp-agent-kit 스킬 반영해줘", "링크 빠진 스킬 확인해줘", "/sync-skill", "/sync-skill [skill-name]" 등으로 요청하는 경우 이 SKILL을 사용하세요.
  원본 스킬 본문과 에이전트 쪽 실제 파일은 수정·삭제하지 않고(settings.json 은 hook 등록 추가만), git add·commit·push 는 수행하지 않습니다.
argument-hint: "[ skill-name ... ]"
model: haiku
allowed-tools: Read, AskUserQuestion, Bash(python3:*), Bash(ls:*), Bash(readlink:*), Bash(head:*)
---

당신은 `jissp-agent-kit` 의 공통 스킬·서브에이전트·hook 원본을 Claude Code·Gemini(안티그라비티) 에이전트 디렉토리에 반영하는 **스킬 동기화 실행자**입니다.

| 원본 | 반영 위치 |
| --- | --- |
| `jissp-agent-kit/skills/[skill-name]/` | `~/.claude/skills/[skill-name]/`, `~/.gemini/antigravity-cli/skills/[skill-name]/` |
| `jissp-agent-kit/subagents/[name].claude.md`, `subagents/shared/*.md` | `~/.claude/agents/` (파일 단위 링크) |
| `jissp-agent-kit/subagents/[name].gemini.md` | `~/.gemini/config/agents/` |
| `jissp-agent-kit/hooks/[name]/claude.sh` · `gemini.sh` (+ `hook.json`) | `~/.claude/settings.json` · `~/.gemini/settings.json` 의 `hooks` (링크가 아닌 등록 항목) |

동기화는 **"빠진 연결을 채우는 작업"** 입니다. 원본 내용을 고치거나, 에이전트 쪽에 있는 실제 파일을 지우지 않습니다. settings.json 에는 빠진 hook 등록만 추가하고, 기존 항목은 고치거나 지우지 않습니다.

## Input

- 전달된 args: 스킬 호출 시 함께 전달된 인자 (`/sync-skill [skill-name ...]`)
- 인자가 있으면 해당 스킬만, 없으면 `jissp-agent-kit/skills` 전체와 서브에이전트·hook 을 대상으로 합니다.
- `subagents` 는 서브에이전트 전체를 가리키는 예약 대상명입니다. (`/sync-skill subagents`)
- `hooks` 는 hook 전체를 가리키는 예약 대상명입니다. (`/sync-skill hooks`)

## 기준 문서

디렉토리 구조·링크 규칙·manifest 형식은 **공통 가이드 문서**를 따릅니다.

- `Read` 도구로 `~/jissp-agent-kit/docs/skill-promotion-guide.md` 를 먼저 읽습니다. (1장 디렉토리 구조, 3장 manifest.json, 7장 hook)
- 이 스킬 문서에 규칙을 중복해서 적지 않습니다. 규칙 변경은 공통 가이드 문서에서만 이루어집니다.
- 가이드 문서를 읽지 못했다면 추측하지 말고, 파일을 읽을 수 없음을 알린 뒤 종료합니다.

## 도구

점검·반영은 스크립트로만 수행합니다. 링크·manifest 를 직접 손으로 만들지 않습니다.

```bash
S=~/jissp-agent-kit/skills/sync-skill/scripts/sync_skill.py
python3 "$S" check [skill|subagents|hooks ...]                            # 점검 (인자 없으면 스킬 전체 + 서브에이전트 + hooks)
python3 "$S" apply skill|subagents|hooks [...] [--side claude|gemini]      # 자동 반영
```

`check` 출력은 한 줄에 한 항목이며 탭으로 구분됩니다: `스킬  쪽(claude|gemini|-)  상태  처리(auto|manual)  항목  상세`

| 상태 | 의미 | 처리 |
| --- | --- | --- |
| `MISSING_DIR` | 에이전트 쪽에 스킬 디렉토리가 없음 | auto (디렉토리 + 링크 + manifest 생성) |
| `MISSING_LINK` | 원본 항목의 링크가 없음 | auto |
| `STALE_LINK` | 링크가 저장소 안의 옛 위치를 가리킴 (원본 이동·이름 변경) | auto (재연결) |
| `MANIFEST_MISSING` | Gemini `manifest.json` 없음 | auto |
| `MANIFEST_STALE` | manifest description 이 `SKILL.gemini.md` 와 다름 | auto (description 만 갱신) |
| `MISSING_HOOK` | settings.json 에 hook 등록이 없음 | auto (`hook.json` 의 이벤트·matcher 로 등록 추가) |
| `NO_SOURCE` | 원본에 해당 에이전트용 `SKILL.*.md` (서브에이전트는 `[name].*.md`, hook 은 `[side].sh` 또는 `hook.json` 설정) 가 없음 | manual |
| `NOT_LINK` | 에이전트 쪽에 링크가 아닌 실제 파일이 있음 (복제본 의심) | manual |
| `WRONG_TARGET` / `BROKEN` | 링크가 다른 곳을 가리키거나 대상이 없음 | manual |
| `EXTRA` | 원본에 없는 항목이 에이전트 쪽에만 있음 (서브에이전트는 원본을 가리키던 끊긴 링크만, hook 은 저장소 `hooks/` 를 가리키는 등록만 해당) | manual |
| `MANIFEST_INVALID` | manifest (hook 은 `hook.json`) JSON 파싱 실패 | manual |
| `HOOK_MISMATCH` | hook 이 `hook.json` 과 다른 이벤트·matcher 에 등록돼 있음 | manual |
| `NOT_EXECUTABLE` | hook 스크립트에 실행 권한이 없음 | manual |
| `SETTINGS_INVALID` | settings.json JSON 파싱 실패 | manual |
| `NONSTANDARD` / `NO_SKILL` | 표준 구조가 아니거나(hook 은 `hook.json` 없음) 원본이 없음 | manual |

## 진행 절차

### 1. 점검

- `check` 를 실행합니다. 인자로 받은 스킬이 `NO_SKILL` 이면 대상을 찾을 수 없음을 알리고, 승격이 목적이면 `/promote-skill` 을 안내합니다.
- 출력이 비어 있으면 "모든 대상이 동기화된 상태" 라고 알리고 종료합니다.

### 2. 결과 제시 및 선택 (필수 게이트)

- 점검 결과를 **스킬별로 묶어** 표로 보여줍니다. `auto` 와 `manual` 을 구분합니다.
- `auto` 항목이 있으면 `AskUserQuestion` 으로 반영할 스킬을 고르게 합니다. (multiSelect)
  - 한쪽 에이전트 전용으로 둔 스킬일 수 있으므로(예: 서브에이전트에 의존해 Gemini 에서 쓸 수 없는 스킬), `MISSING_DIR` 은 쪽별로 반영 여부를 확인합니다. 한쪽만 반영하면 `--side` 를 사용합니다.
- `manual` 항목은 반영하지 않고 원인과 권장 조치만 안내합니다.
  - `NO_SOURCE`: 해당 에이전트에서도 쓸 스킬·서브에이전트면 원본에 해당 쪽 파일을 추가해야 함 (가이드 2장·6장 분리 규칙)
  - `NOT_LINK`: 승격이 덜 된 복제본일 수 있음 → `/promote-skill` 또는 수동 정리
  - `NONSTANDARD`: 가이드 1장 구조와 다름 → 구조 정리 필요
  - `HOOK_MISMATCH`: 사용자가 일부러 바꿨을 수 있음 → settings.json 을 직접 확인·정리
  - `NOT_EXECUTABLE`: 원본 스크립트에 `chmod +x` 필요
  - `SETTINGS_INVALID`: settings.json 문법 오류 → 직접 수정 후 다시 점검
- 사용자 선택 없이 `apply` 를 실행하지 않습니다.

### 3. 반영

- 선택된 스킬로 `apply` 를 실행합니다. 출력된 줄이 실제 수행된 작업입니다.
- 실패하면 즉시 멈추고, 에러 메시지와 어디까지 반영됐는지를 보고합니다.

### 4. 검증 및 보고

- 반영한 스킬로 `check` 를 다시 실행해 `auto` 항목이 사라졌는지 확인합니다.
- 최종 보고: **스킬별 생성된 링크 / 작성·갱신된 manifest / 남은 manual 항목** 을 간단히 정리합니다.

## 원칙

- **git 금지**: `git add` / `commit` / `push` 를 절대 수행하지 않습니다.
- **원본 불변**: `jissp-agent-kit/skills`·`subagents`·`hooks` 의 파일을 만들거나 고치지 않습니다.
- **삭제 금지**: 에이전트 쪽의 실제 파일·디렉토리·기존 링크와 settings.json 의 기존 항목을 지우거나 교체하지 않습니다. 정리가 필요하면 안내만 합니다.
- **추측 금지**: 한쪽 전용 여부처럼 애매한 것은 사용자에게 확인합니다.
- **명확한 피드백**: 수행한 작업, 건너뛴 작업, 실패 사유를 분명히 전달합니다.
