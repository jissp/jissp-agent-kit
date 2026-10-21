---
name: jissp-git-worktree
description:
  Git worktree를 통해 브랜치와 작업 디렉토리를 분리할 때 프로젝트 설정, 환경변수, skills 등을 심볼릭 링크로 같이 공유하며 worktree를 생성하고, 다 쓴 worktree를 안전하게 제거합니다.
  사용자가 "워크트리 만들어줘", "이 브랜치 worktree로 열어줘", "브랜치 분리해서 동시에 작업하고 싶어", "워크트리 지워줘", "/jissp-git-worktree [브랜치명]", "/jissp-git-worktree remove [브랜치명]" 등으로 요청하는 경우 이 SKILL을 사용합니다.
---

# jissp-git-worktree

## 역할

이 스킬은 git worktree로 브랜치와 작업 디렉토리를 **물리적으로 분리**해, 하나의 메인 repo에서 여러 브랜치를 동시에 작업할 수 있게 합니다. 이때 환경변수·`.claude` 설정·프로젝트 문서 등 git에 추적되지 않거나 매번 다시 만들기 번거로운 자산을, **복사가 아니라 `ln -s` 심볼릭 링크로 메인 repo와 공유**합니다. 다 쓴 worktree는 공유 링크를 정리한 뒤 안전하게 제거합니다.

## 호출 방식

| 호출 | 동작 |
|------|------|
| `/jissp-git-worktree` | 사용자에게 **새로 만들 브랜치명을 요청**한 뒤, 그 브랜치를 `dev`에서 분기해 worktree를 생성합니다. |
| `/jissp-git-worktree [브랜치명]` | 인자로 받은 이름의 새 브랜치를 `dev`에서 분기해 worktree를 생성합니다. (예: `/jissp-git-worktree refact/pg`) |
| `/jissp-git-worktree remove [브랜치명\|경로]` | 해당 worktree를 제거합니다. ([제거 워크플로우](#제거-워크플로우) 참고) |

## 스크립트 위치

스크립트와 기본 목록 파일은 **이 스킬 디렉토리(`<SKILL_DIR>`)** 기준으로 위치합니다. 대상 프로젝트 안이 아니므로, 실행할 때는 아래 절대 경로를 사용합니다.

| 에이전트 | `<SKILL_DIR>` |
|------|------|
| Claude Code | `~/.claude/skills/jissp-git-worktree` |
| Gemini(안티그라비티) | `~/.gemini/antigravity-cli/skills/jissp-git-worktree` |

- 생성: `<SKILL_DIR>/scripts/create-worktree.sh`
- 제거: `<SKILL_DIR>/scripts/remove-worktree.sh`
- 기본 링크 목록: `<SKILL_DIR>/worktree-links.default`

스크립트는 **대상 프로젝트(메인 repo 또는 그 repo의 worktree) 안을 현재 디렉토리로 두고** 실행합니다. 어느 worktree 안에서 실행하든 항상 메인 repo를 기준으로 동작합니다.

## worktree 관리 디렉토리

worktree는 **워크스페이스(메인 repo의 부모 디렉토리) 내 `worktrees/` 디렉토리**에서 일괄 관리합니다. 메인 repo와 형제 위치에 흩어지지 않고 한곳에 모이므로 정리가 쉽습니다.

- **관리 디렉토리**: 메인 repo의 부모 디렉토리 아래 `worktrees/`
- **worktree 디렉토리명**: `<origin 디렉토리명>-<브랜치 slug>` (브랜치명의 `/`는 `-`로 치환)

예) `~/WebstormProjects/my-org/my-api`에서 `/jissp-git-worktree refact/pg` 호출 시
→ `~/WebstormProjects/my-org/worktrees/my-api-refact-pg` 에 worktree가 생성됩니다.

`worktrees/` 디렉토리가 없으면 스크립트가 자동으로 생성합니다.

심볼릭 링크를 쓰는 이유는 두 가지입니다.

- **단일 원본 유지**: 메인 repo의 `.env`나 `.claude/skills`를 수정하면 모든 worktree에 즉시 반영됩니다.
- **저장 공간 절약 + 즉시 실행**: worktree마다 설정을 복제하지 않고도 곧바로 작업을 시작할 수 있습니다.

특정 항목을 worktree별로 **독립적으로 관리하고 싶을 때**는, 사용자가 직접 링크를 끊고 실제 파일/디렉토리를 생성합니다. (아래 [수동 분리 절차](#수동-분리-절차) 참고)

## 링크 대상은 목록 파일로 관리

링크할 대상은 스크립트에 하드코딩하지 않고 **`.gitignore` 스타일의 목록 파일**에서 읽습니다. 한 줄에 하나씩 메인 repo 루트 기준 상대 경로를 적으며, `#` 주석과 빈 줄은 무시됩니다. 절대 경로나 `..`이 포함된 경로는 거부되고, 메인 repo에 없는 항목은 건너뜁니다.

**목록 파일 우선순위:**

1. `<main-repo>/.worktree-links` — **로컬 전용**. 있으면 이 파일이 우선합니다. 나만 쓰는 로컬 스킬·설정을 자유롭게 관리할 때 사용하세요.
2. `<SKILL_DIR>/worktree-links.default` — 스킬 **기본값**. 루트 파일이 없을 때 사용됩니다.

> 기본값으로 어떤 대상이 링크되는지는 `worktree-links.default` 파일을 직접 확인하세요. 목록을 이 문서에 중복 기재하면 동기화가 어긋나므로, **단일 출처는 항상 `worktree-links.default`** 입니다.

목록에는 **추적/비추적 구분 없이 경로만** 적으면 됩니다. `git worktree add`는 추적되는 파일만 새 디렉토리에 생성하므로 처리 방식이 다르지만, 스크립트가 `git ls-files`로 추적 여부를 자동 판별합니다.

- **비추적 항목** (`.env`, `0-jissp-docs` 등): worktree에 없으므로 바로 `ln -s`.
- **추적 항목** (`.claude`): worktree에 이미 생성되어 있으므로 제거 후 `ln -s` 하고, 해당 파일에 `skip-worktree`를 적용합니다. (⚠️ 아래 주의사항)
- `.claude/skills/my-skill`처럼 **하위 경로만** 콕 집어 링크할 수도 있습니다 (로컬 전용 스킬 공유에 유용). 단, 상위 경로(`.claude`)가 목록에 함께 있으면 상위 링크로 이미 공유되므로 하위 경로는 건너뜁니다.

> `node_modules`, `dist` 등 의존성·빌드 산출물은 브랜치별 차이가 생길 수 있어 **기본 목록에서 제외**했습니다. 필요하면 worktree에서 의존성 설치·빌드를 실행하거나 목록 파일에 경로를 추가하세요.

### 로컬 목록 파일 만들기

```bash
# 스킬 기본값을 복사해 와서 내 입맛대로 편집 (메인 repo 루트에서 실행)
cp ~/.claude/skills/jissp-git-worktree/worktree-links.default .worktree-links
# 이후 .worktree-links 를 편집하면 그 목록이 우선 적용됨
```

`.worktree-links`는 개인 설정이므로 커밋되지 않게 직접 제외 등록합니다. 팀과 공유하는 `.gitignore`를 건드리기 싫다면 로컬 전용인 `.git/info/exclude`에 추가하세요.

```bash
echo ".worktree-links" >> .git/info/exclude
```

## 생성 워크플로우

### 1. 입력 확인

- **브랜치명** (필수) — **새로 만들 브랜치명**입니다. `/jissp-git-worktree [브랜치명]`처럼 인자로 받았으면 그대로 사용하고, `/jissp-git-worktree`만 호출되어 브랜치명이 없으면 **사용자에게 새로 만들 브랜치명을 질문**합니다.
  - 이 스킬은 **항상 새 브랜치를 만듭니다.** 이미 존재하는 브랜치명(로컬 또는 origin)이면 스크립트가 에러로 중단하므로, 사용자에게 다른 이름을 받습니다.
- **분기 기준(base)** (선택) — 기본은 **`dev`** 입니다. 스크립트가 아래 순서로 자동 결정하며, 새 브랜치는 base를 upstream으로 추적하지 않습니다(`--no-track`).
  1. `origin/dev` (fetch 후 최신 상태)
  2. 로컬 `dev` (origin에 dev가 없을 때)
  3. origin 기본 브랜치(`origin/HEAD`, 보통 `origin/main`) — `dev` 자체가 없는 레포
  4. 위 모두 없으면 에러로 중단 → 사용자에게 분기 기준을 묻고 `--base`로 지정
  - 사용자가 다른 기준(예: hotfix를 main에서)을 명시한 경우에만 `--base <ref>`로 지정합니다. (예: `--base origin/main`)
- **worktree 경로** (선택) — 미지정 시 `<workspace>/worktrees/<repo>-<branch-slug>`로 자동 계산
- **링크 목록** (선택) — 별도 지정이 없으면 위 [목록 파일 우선순위](#링크-대상은-목록-파일로-관리)를 따름

### 2. 생성 + 링크 실행

`<SKILL_DIR>/scripts/create-worktree.sh`를 실행하면 worktree 생성과 심볼릭 링크 설정이 한 번에 처리됩니다. (아래 예시는 Claude Code 경로 기준)

```bash
# 새 브랜치를 dev 에서 분기 (→ <workspace>/worktrees/<repo>-feature-login)
bash ~/.claude/skills/jissp-git-worktree/scripts/create-worktree.sh feature/login

# 분기 기준 직접 지정 (예: hotfix 를 main 에서)
bash ~/.claude/skills/jissp-git-worktree/scripts/create-worktree.sh hotfix/pay --base origin/main

# 경로 직접 지정 (자동 계산 무시)
bash ~/.claude/skills/jissp-git-worktree/scripts/create-worktree.sh feature/login /tmp/my-login

# 링크 목록 파일 직접 지정 (우선순위 무시)
bash ~/.claude/skills/jissp-git-worktree/scripts/create-worktree.sh feature/login --links ./my-links.txt
```

스크립트는 멱등성을 가집니다. 이미 등록된 worktree 경로에 다시 실행하면 브랜치는 건드리지 않고 **누락된 링크만 추가**하며, 이미 링크된 항목과 worktree에 실제 파일/디렉토리로 존재하는 항목(수동 분리한 항목)은 건드리지 않습니다.

경로가 이미 존재하지만 이 repo의 worktree가 아니거나, 알 수 없는 옵션·누락된 옵션 값이 있으면 아무것도 변경하지 않고 에러로 종료합니다.

### 3. 결과 안내

실행 결과를 사용자에게 요약합니다.

- 생성된 worktree 경로와 브랜치(분기 기준 포함)
- 첫 push는 `git push -u origin <브랜치>`로 해야 자기 이름의 원격 브랜치를 추적한다는 점
- 링크된 항목 / 건너뛴 항목(사유 포함)
- 추적 항목을 링크한 경우의 git 주의사항
- 의존성·빌드 산출물 비공유 안내 (필요 시 의존성 설치)
- IDE에서 여는 경로, 제거 방법(`/jissp-git-worktree remove [브랜치명]`)

## 제거 워크플로우

### 1. 대상 확인

- 제거할 worktree의 **브랜치명 또는 경로**를 받습니다. 없으면 `git worktree list` 결과를 보여주고 사용자에게 선택받습니다.
- **브랜치도 함께 삭제할지** 사용자에게 확인합니다. 명시적으로 원한 경우에만 `--delete-branch`를 붙입니다.

### 2. 제거 실행

```bash
# worktree만 제거
bash ~/.claude/skills/jissp-git-worktree/scripts/remove-worktree.sh refact/pg

# worktree 제거 + 브랜치 삭제 (병합되지 않은 브랜치는 삭제하지 않음)
bash ~/.claude/skills/jissp-git-worktree/scripts/remove-worktree.sh refact/pg --delete-branch
```

스크립트는 메인 repo를 가리키는 공유 링크를 먼저 걷어낸 뒤 `git worktree remove`를 `--force` 없이 실행합니다. 메인 repo의 원본 자산은 그대로 보존됩니다.

### 3. 실패 시 처리

- 커밋하지 않은 변경이 남아 있으면 제거가 거부되고, 걷어낸 링크는 **원래대로 복구**됩니다. `git -C <worktree> status`로 남은 변경을 사용자에게 보여줍니다.
- `--force`는 변경 내용을 **버리고** 강제로 제거하므로, 사용자가 남은 변경을 확인하고 명시적으로 승인한 경우에만 사용합니다.
- 병합되지 않은 브랜치는 `--delete-branch`를 줘도 삭제되지 않습니다. 강제 삭제(`git branch -D`)는 사용자가 직접 요청한 경우에만 수행합니다.

## 수동 분리 절차

특정 항목을 worktree 전용으로 분리하려면 **링크를 끊고 실제 파일/디렉토리를 직접 생성**합니다.

```bash
# 예: 이 worktree만 다른 .env 를 쓰고 싶을 때
rm <worktree>/.env                    # 심볼릭 링크 제거
cp <main-repo>/.env <worktree>/.env   # 실제 복사본 생성 후 자유롭게 수정

# 디렉토리(.claude 등)를 분리할 때
rm <worktree>/.claude                 # 링크 제거
cp -R <main-repo>/.claude <worktree>/.claude   # 독립 복사본 생성
```

분리한 항목은 더 이상 메인 repo와 동기화되지 않으므로, 이후에는 worktree 내부에서 직접 관리합니다. 생성 스크립트를 다시 실행해도 분리한 항목은 덮어쓰지 않습니다.

## 주의사항

- **목록 중 git 추적 대상**(예: `.claude`, `CLAUDE.md`)은 심볼릭 링크로 교체한 뒤 `skip-worktree`를 적용하므로 파일 변경은 worktree의 `git status`에 잡히지 않습니다. 다만 디렉토리 링크 자체는 `?? .claude`처럼 보일 수 있습니다. **그 항목은 이 worktree에서 add/커밋하지 마세요.** 링크를 통해 수정한 내용은 메인 repo 원본에 반영됩니다.
- **의존성·빌드 산출물(`node_modules`, `dist` 등)은 공유되지 않습니다.** worktree에서 빌드/실행이 필요하면 의존성 설치를 먼저 수행하세요.
- **worktree 제거**는 `remove-worktree.sh`(또는 `/jissp-git-worktree remove`)를 사용합니다. 공유 링크가 남은 상태에서 `git worktree remove`를 직접 실행하면 변경 사항이 있는 것으로 판단되어 `--force` 없이는 거부됩니다.
- 심볼릭 링크는 **절대 경로**로 생성되어, worktree를 어디서 열든 깨지지 않습니다.
