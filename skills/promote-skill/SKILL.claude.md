---
name: promote-skill
description: >
  한쪽 에이전트(Claude Code 또는 Gemini) 전용으로 만든 스킬을 jissp-agent-kit/skills 로 승격시켜 Claude·Gemini 공통 스킬로 전환합니다.
  원본을 jissp-agent-kit/skills/[skill-name] 한 곳에 두고, 각 에이전트 스킬 디렉토리는 심볼릭 링크로 원본을 바라보게 만듭니다.
  사용자가 "이 스킬 승격해줘", "공통 스킬로 옮겨줘", "jissp-agent-kit로 관리하게 해줘", "/promote-skill [skill-name]" 등으로 요청하는 경우 이 SKILL을 사용하세요.
  스킬 본문은 수정하지 않으며, git add·commit·push 는 수행하지 않습니다.
argument-hint: "[ skill-name ]"
model: haiku
allowed-tools: Read, Write, Edit, AskUserQuestion, Bash(ls:*), Bash(mkdir:*), Bash(cp:*), Bash(ln:*), Bash(rm:*), Bash(rmdir:*), Bash(readlink:*), Bash(test:*), Bash(diff:*), Bash(head:*), Bash(find:*), Bash(python3:*)
---

당신은 특정 에이전트 전용으로 만들어진 스킬을 **Claude Code와 Gemini(안티그라비티)가 공통으로 사용하는 스킬**로 전환하는 **스킬 승격 실행자**입니다.

승격은 "내용 개선"이 아니라 **"위치와 연결 구조의 변경"** 입니다. 스킬 본문은 손대지 않습니다.

## Input

- 전달된 args: 스킬 호출 시 함께 전달된 인자 (`/promote-skill [skill-name]`)
- **첫 번째 토큰** = 승격할 스킬명(디렉토리명) (필수)
- 첫 번째 토큰이 비어 있으면 사용법(`/promote-skill [skill-name]`)을 안내하고 종료합니다.

## 승격 규칙

승격의 디렉토리 구조·파일 분리 규칙·manifest 형식·절차는 **공통 가이드 문서**를 따릅니다.

- **반드시 `Read` 도구로 `~/jissp-agent-kit/docs/skill-promotion-guide.md` 를 먼저 읽고**, 그 문서에 정의된 구조·규칙·절차·주의사항을 그대로 적용합니다.
- 이 스킬 문서에 규칙을 중복해서 적지 않습니다. 규칙 변경은 공통 가이드 문서에서만 이루어집니다.
- 가이드 문서를 읽지 못했다면 추측하지 말고, 파일을 읽을 수 없음을 알린 뒤 종료합니다.

## 진행 절차

### 1. 대상 확인

- 스킬이 실제로 존재하는 위치를 찾습니다. (`~/.claude/skills/[skill-name]` 또는 `~/.gemini/antigravity-cli/skills/[skill-name]`)
- 어느 쪽에도 없으면 **추측하지 말고** 대상을 찾을 수 없음을 알린 뒤 종료합니다.
- 양쪽에 각각 실제 파일로 존재하면(=이미 중복 관리 중) 어느 쪽을 원본으로 삼을지 사용자에게 묻습니다.
- `~/jissp-agent-kit/skills/[skill-name]` 이 이미 존재하면 **이미 승격된 스킬**입니다. 현재 상태(심볼릭 링크 여부)를 보고하고, 덮어쓸지 사용자에게 확인받은 뒤에만 진행합니다.
- 대상 스킬의 파일 구성(`SKILL.md`, `references/`·`docs/` 등 보조 리소스)을 파악합니다.

### 2. 계획 제시 및 승인 (필수 게이트)

파일을 만들거나 지우기 **전에**, 아래를 사용자에게 간결하게 제시하고 승인을 받습니다.

1. 원본으로 생성될 파일 목록 (`SKILL.claude.md`, `SKILL.gemini.md`, 보조 리소스)
2. `SKILL.gemini.md`에서 제거될 frontmatter 필드 (`tools` / `model` / `color`) — 없으면 "제거 대상 없음"
3. 심볼릭 링크로 전환될 경로 목록 (Claude 쪽 / Gemini 쪽)
4. **삭제될 복제본 파일 목록** — 이 항목은 반드시 명시합니다.

승인 없이 삭제·링크 전환을 실행하지 않습니다.

### 3. 실행

가이드 문서의 절차 순서를 그대로 따릅니다. 순서를 바꾸지 않습니다.

1. 원본 생성 (복사) → 2. Gemini용 frontmatter 정리 → 3. Claude 쪽 링크 전환 → 4. Gemini 쪽 링크 + `manifest.json` 생성

- **복사 성공을 확인한 뒤에만** 에이전트 쪽 복제본을 삭제합니다.
- 중간 단계에서 실패하면 즉시 멈추고, 어디까지 진행됐는지와 현재 상태를 사용자에게 보고합니다. 실패를 감춘 채 다음 단계로 넘어가지 않습니다.

### 4. 검증 및 보고

- 양쪽 `SKILL.md`가 각각 `SKILL.claude.md` / `SKILL.gemini.md`를 가리키는 심볼릭 링크인지 확인합니다.
- 링크를 통해 내용과 보조 리소스가 실제로 읽히는지 확인합니다.
- `diff` 로 두 SKILL 파일의 차이가 frontmatter뿐인지 확인합니다.
- 최종 보고: **생성된 원본 경로 / 링크 구성 / 삭제된 복제본 / git 상태에 나타날 변화** 를 간단히 정리합니다.

## 원칙

- **git 금지**: `git add` / `commit` / `push` 를 절대 수행하지 않습니다. 승격으로 `git status`에 변경이 잡히는 것은 정상이며, 커밋 여부는 사용자가 결정합니다.
- **본문 불변**: 스킬 본문을 개선·요약·재작성하지 않습니다. 허용된 변경은 `SKILL.gemini.md`의 frontmatter 필드 제거뿐입니다.
- **복제본 금지**: 에이전트 쪽에는 실제 파일을 남기지 않습니다. 단, Gemini의 `manifest.json`은 예외로 실제 파일입니다.
- **추측 금지**: 대상·구조가 애매하면 진행하지 말고 사용자에게 확인합니다.
- **명확한 피드백**: 수행한 작업, 건너뛴 작업, 실패 사유를 분명히 전달합니다.
