# 스킬 승격(Promotion) 가이드

Claude Code 또는 Gemini(안티그라비티)에서 **한쪽 전용으로 만든 스킬**을, 두 에이전트가 **공통으로 사용하는 스킬**로 전환하는 절차를 정의합니다.

승격의 핵심은 **원본을 `jissp-agent-kit/skills` 한 곳에 두고, 각 에이전트의 스킬 디렉토리는 심볼릭 링크로 그 원본을 바라보게 만드는 것**입니다. 이렇게 하면 스킬 본문을 한 번만 수정해도 양쪽에 동시에 반영됩니다.

## 1. 디렉토리 구조

| 역할 | 경로 |
| --- | --- |
| **원본(공통 관리)** | `~/jissp-agent-kit/skills/[skill-name]/` |
| Claude Code 스킬 | `~/.claude/skills/[skill-name]/` |
| Gemini(안티그라비티) 스킬 | `~/.gemini/antigravity-cli/skills/[skill-name]/` |

승격이 완료된 상태의 구조는 다음과 같습니다.

```
jissp-agent-kit/skills/[skill-name]/          ← 실제 파일이 존재하는 유일한 위치
├── SKILL.claude.md                          ← Claude 전용 본문
├── SKILL.gemini.md                          ← Gemini 전용 본문
└── [보조 리소스]/                            ← references/ · docs/ 등 (있는 경우)
    └── *.md

.claude/skills/[skill-name]/
├── SKILL.md      → jissp-agent-kit/skills/[skill-name]/SKILL.claude.md   (symlink)
└── [보조 리소스]  → jissp-agent-kit/skills/[skill-name]/[보조 리소스]      (symlink)

.gemini/antigravity-cli/skills/[skill-name]/
├── SKILL.md      → jissp-agent-kit/skills/[skill-name]/SKILL.gemini.md   (symlink)
├── [보조 리소스]  → jissp-agent-kit/skills/[skill-name]/[보조 리소스]      (symlink)
└── manifest.json                             ← Gemini 전용, 실제 파일(링크 아님)
```

- **파일 실체는 원본에만 존재합니다.** 에이전트 쪽에 복제본을 두지 않습니다.
- **보조 리소스(`references/`, `docs/` 등)는 디렉토리 단위로 링크**합니다. 파일 하나씩 링크하지 않습니다.
- `manifest.json`은 Gemini 런타임 전용 메타파일이므로 원본에 두지 않고 Gemini 스킬 디렉토리에 직접 생성합니다.

## 2. SKILL.claude.md / SKILL.gemini.md 분리 규칙

두 파일의 **본문은 동일**하며, 차이는 원칙적으로 frontmatter뿐입니다.

### frontmatter

| 필드 | SKILL.claude.md | SKILL.gemini.md |
| --- | --- | --- |
| `name` | O | O |
| `description` | O | O |
| `tools` | O (있으면 유지) | **제거** |
| `model` | O (있으면 유지) | **제거** |
| `color` | O (있으면 유지) | **제거** |

- Gemini는 `tools` / `model` / `color`를 해석하지 않으므로 반드시 제거합니다.
- 원본 스킬에 `tools` / `model` / `color`가 없었다면 **임의로 추가하지 않습니다.** 이 경우 두 파일의 내용은 완전히 동일해지지만, 파일은 그대로 둘로 유지합니다(이후 모델별 분화를 위한 자리).

### 본문 (선택) — Gemini 전용 보강

Gemini 모델이 특정 단계를 건너뛰거나 추상적으로 답하는 경향이 있는 스킬은, `SKILL.gemini.md`에만 아래와 같은 섹션을 추가할 수 있습니다. (예: `jissp-architecture-preview`)

```markdown
# AI 모델별 특별 주의사항

## Gemini 모델 전용

- **[단계 번호] 단계를 절대 생략하지 말 것.** ...
- **추상적 요약 금지.** ...
- **정량 표현 우선.** "많이 줄어듭니다"(X) / "138줄 → 약 60줄"(O)
```

필수는 아닙니다. 기본은 frontmatter만 다른 동일 본문이며, **승격 작업 중에 임의로 본문을 손대지 않습니다.**

## 3. manifest.json (Gemini 전용)

Gemini 스킬 디렉토리에 아래 형식으로 생성합니다.

```json
{
  "name": "[skill-name]",
  "description": "[SKILL.gemini.md의 description을 그대로 옮김]",
  "instructions": "SKILL.md 파일에 명시된 규칙, 포맷, 제약 사항을 완벽하게 숙지하고, 사용자의 요청을 처리할 때 그 지침을 엄격하게 적용하여 답변을 생성하십시오.",
  "agent_settings": {
    "thinking_level": "high"
  }
}
```

- `instructions` / `agent_settings`는 **모든 스킬이 동일한 값**을 사용합니다.
- `description`은 SKILL 파일의 description을 그대로 옮기되, JSON 문자열로 안전하도록 아래 두 가지를 반드시 적용합니다.
  - **큰따옴표는 작은따옴표로 치환**합니다.
  - **여러 줄 description은 한 줄로 합칩니다.** SKILL 파일의 frontmatter는 YAML이라 description을 여러 줄로 쓸 수 있지만, JSON 문자열 안에는 실제 개행이 들어갈 수 없습니다. 줄바꿈과 이어지는 들여쓰기 공백을 **공백 하나로 바꿔** 한 줄로 만듭니다.

> 이 규칙을 놓쳐 `planner-review` · `jissp-task-manager` · `flow-diagram` 의 `manifest.json` 이 파싱 불가 상태로 생성된 적이 있습니다. 작성 후 **반드시 JSON 파싱이 되는지 검증**하십시오. (예: `python3 -c "import json; json.load(open('manifest.json'))"`)

## 4. 승격 절차

`[skill-name]`을 승격시킬 때 아래 순서로 진행합니다. `[SRC]`는 원본 스킬이 현재 존재하는 에이전트 쪽 경로입니다.

### 1) 사전 확인

- `jissp-agent-kit/skills/[skill-name]`이 이미 존재하는지 확인합니다. 존재하면 **이미 승격된 스킬**이므로 덮어쓰기 전에 사용자에게 확인합니다.
- 승격 대상의 파일 구성(`SKILL.md` + 보조 리소스 디렉토리)을 파악합니다.
- 기존 승격 스킬(`jissp-planner`, `jissp-reviewer` 등)의 구조를 참고 기준으로 삼습니다.

### 2) 원본 생성

```bash
BASE=~/jissp-agent-kit/skills/[skill-name]
mkdir -p "$BASE"
cp "[SRC]/SKILL.md" "$BASE/SKILL.claude.md"
cp "[SRC]/SKILL.md" "$BASE/SKILL.gemini.md"
cp -R "[SRC]/[보조 리소스]" "$BASE/[보조 리소스]"   # 있는 경우만
```

이후 `SKILL.gemini.md`의 frontmatter에서 `tools` / `model` / `color` 라인을 제거합니다.

### 3) Claude 쪽 링크 전환

```bash
SRC=~/.claude/skills/[skill-name]
rm -rf "$SRC"/*                 # 복제본 제거 (원본 복사 완료 확인 후)
mkdir -p "$SRC"
ln -s "$BASE/SKILL.claude.md" "$SRC/SKILL.md"
ln -s "$BASE/[보조 리소스]"    "$SRC/[보조 리소스]"
```

### 4) Gemini 쪽 링크 생성

```bash
G=~/.gemini/antigravity-cli/skills/[skill-name]
mkdir -p "$G"
ln -s "$BASE/SKILL.gemini.md" "$G/SKILL.md"
ln -s "$BASE/[보조 리소스]"   "$G/[보조 리소스]"
# manifest.json 작성 (3장 형식)
```

### 5) 검증

- `ls -la` 로 양쪽 `SKILL.md`가 **각각 `.claude.md` / `.gemini.md`를 가리키는 심볼릭 링크**인지 확인합니다.
- 링크를 통해 실제 내용이 읽히는지 확인합니다. (`head`, `ls [링크된 디렉토리]/`)
- `diff SKILL.claude.md SKILL.gemini.md` 결과가 **frontmatter 차이만**인지 확인합니다.

## 5. 원칙과 주의사항

- **`git add` / `commit` / `push`는 절대 수행하지 않습니다.** `.claude/skills`와 `jissp-agent-kit`는 각각 git 저장소이므로, 승격 후 파일 삭제·심볼릭 링크 생성이 `git status`에 나타나는 것은 정상입니다. 커밋 여부는 사용자가 결정합니다.
- **본문을 임의로 수정하지 않습니다.** 승격은 "위치와 연결 구조의 변경"이며 내용 개선 작업이 아닙니다. frontmatter의 `tools`/`model`/`color` 제거만이 허용된 변경입니다.
- **복제본을 남기지 않습니다.** 에이전트 쪽에 실제 파일이 남으면 원본과 갈라져 유지보수 지점이 두 곳이 됩니다.
- **삭제 전에 복사 성공을 확인합니다.** 원본 생성이 완료된 것을 확인한 뒤에만 에이전트 쪽 복제본을 제거합니다.
- 스킬명(디렉토리명)은 세 위치에서 **완전히 동일**해야 합니다.

## 6. 서브에이전트

서브에이전트도 스킬과 같은 방식으로 원본을 `jissp-agent-kit/subagents/` 한 곳에 두고, 각 에이전트 쪽은 심볼릭 링크로 원본을 바라봅니다.

### 디렉토리 구조

```
jissp-agent-kit/subagents/
├── [name].claude.md         ← Claude 전용 (tools·model·color 포함)
├── [name].gemini.md         ← Gemini 전용 (tools·model·color 제거)
└── shared/                  ← 여러 서브에이전트가 함께 읽는 공용 문서 (frontmatter 없음)
    └── *.md

~/.claude/agents/
├── [name].md       → jissp-agent-kit/subagents/[name].claude.md   (symlink)
└── shared/*.md     → jissp-agent-kit/subagents/shared/*.md        (symlink, 파일 단위)

~/.gemini/config/agents/
└── [name].md       → jissp-agent-kit/subagents/[name].gemini.md   (symlink)
```

- Gemini(agy)는 `~/.gemini/config/agents/` 의 Markdown 파일을 커스텀 에이전트로 읽습니다. `agy agents` 로 인식 여부를 확인할 수 있습니다.
- **`.gemini.md` 에서 `tools` / `model` / `color` 를 반드시 제거합니다.** Claude 원본을 그대로 두면 agy 가 에이전트로 인식하지 않습니다.
- 본문은 두 파일이 동일합니다. 공용 문서는 에이전트 쪽 링크가 아니라 **저장소 경로**(`~/jissp-agent-kit/subagents/shared/...`)로 참조해, 한쪽 에이전트만 설치된 환경에서도 읽히게 합니다.
- 한쪽 에이전트에서만 쓰는 서브에이전트는 해당 쪽 파일만 둡니다. 다른 쪽은 `sync-skill` 점검에서 `NO_SOURCE` 로 표시됩니다.

### 연결

링크는 직접 만들지 않고 `/sync-skill subagents` (또는 `sync_skill.py apply subagents`) 로 반영합니다. 원본 파일명이 바뀌어 저장소 안의 옛 위치를 가리키는 링크도 함께 다시 연결됩니다.
