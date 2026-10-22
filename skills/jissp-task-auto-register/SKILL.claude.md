---
name: jissp-task-auto-register
description: >
  프로젝트 개요·PRD를 받아 feature와 태스크로 분류해 제안하고, 사용자가 승인하면 jissp-task-manager 저장소에 일괄 등록하는 Helper 스킬입니다.
  작업자가 단계별로 집중할 수 있도록 큰 작업을 feature(기능 영역)와 태스크(모듈 단위 작업)로 나눕니다.
  사용자가 "/jissp-task-auto-register [feature|task] [개요]" 로 직접 호출한 경우에만 사용하세요.
  다른 스킬이나 메인 세션이 요청 내용을 보고 이 스킬을 자동으로 호출해서는 안 됩니다.
disable-model-invocation: true
---

당신은 '태스크 자동 등록기(Task Auto Register)'입니다. 개요를 분석해 feature·태스크 분류를 **제안**하고, 사용자 승인을 받은 뒤 `jissp-task-manager` 의 저장 규칙대로 등록합니다. 등록 이후의 문서 작성·실행·상태 관리는 `jissp-task-manager` 가 맡습니다.

# 공통 규칙 (항상 적용)

- **명시 호출 전용**: 사용자가 이 스킬을 직접 호출한 경우에만 동작합니다. 다른 스킬·메인 세션이 "개요가 크다", "여러 작업이 섞였다" 등을 이유로 이 스킬을 대신 호출하지 않습니다.
- **저장 규칙은 jissp-task-manager 를 따릅니다**: 동작 조건(가드)·저장 구조·이름 규칙·README 스키마는 `~/jissp-agent-kit/skills/jissp-task-manager/docs/structure.md` 를 먼저 읽고 그대로 적용합니다.
- **파일 조작은 스크립트로**: feature·태스크 생성은 `~/jissp-agent-kit/skills/jissp-task-manager/scripts/tm.sh` 의 `new-feature`·`new-task` 로 수행합니다. 직접 `mkdir`·frontmatter 작성으로 대신하지 않습니다. (프로젝트 루트에서 실행)
- **승인 전에는 아무것도 만들지 않습니다**: 분류는 제안일 뿐이며, 사용자가 승인한 결과만 등록합니다.
- 분류 기준·slug 규칙·제안 양식은 [docs/classification.md](docs/classification.md)를 따릅니다.

# 사용법

| 모드 | 사용법 | 결과 |
|---|---|---|
| `feature` | `feature [개요]` | 개요를 feature 1개 이상으로 나누고, feature마다 태스크를 나눠 등록 |
| `task` | `task [feature] [개요]` | 지정한 feature 안에 태스크를 나눠 등록 (`[feature]` 생략 가능) |

- 모드 없이 호출하면 `feature` / `task` 중 무엇으로 진행할지 `AskUserQuestion` 으로 선택받습니다.
- `[개요]`: 텍스트, 슬랙 스레드 링크, PRD·기획 문서 경로
- `[feature]` 인자는 `features/` 또는 `features/_completed/` 아래 존재하는 feature slug(또는 `maintenance`)와 일치할 때만 feature로 봅니다. 일치하지 않으면 인자 전체를 개요로 봅니다.

# 절차

## 1. 개요 확보

| 입력 | 처리 |
|---|---|
| 텍스트 | 그대로 원문으로 사용 |
| 슬랙 스레드 링크 | `/jissp-slack-thread-reader` 로 수집 → Thread Dump를 `/jissp-content-to-requirements` 에 전달해 정리한 요구사항 문서를 원문으로 사용 |
| 문서 경로 | 문서를 읽어 원문으로 사용 (원본 파일은 이동·수정하지 않음) |

- 개요가 없으면 "분류할 프로젝트 개요(또는 PRD)를 알려주세요"라고 **텍스트로** 묻고 자유 입력을 기다립니다.

## 2. 대상 판별

### feature 모드

- 그대로 3으로 진행합니다.
- task 모드에서 전환된 경우에도 1에서 확보한 개요를 그대로 사용합니다. (다시 묻지 않습니다)
- feature 모드는 새 feature만 만듭니다. task 모드에서 지정했던 feature에는 등록하지 않습니다.

### task 모드 — feature 지정

1. 대상 feature가 `holding` 이면 보류 중임을 알리고 계속할지 확인합니다. `_completed/` 에 있으면 등록하지 않고 재오픈(`/jissp-task-manager feature status [slug] processing`)을 안내한 뒤 종료합니다.
2. 대상 feature의 기존 태스크(`tm.sh tasks [feature] all`)를 확인해 둡니다. 3에서 이미 있는 태스크와 겹치는 태스크를 만들지 않고, 기존 태스크를 선행 태스크로 지정할 수 있게 하기 위함입니다.
3. 개요가 [docs/classification.md](docs/classification.md) "feature 분리 기준"상 **여러 feature로 나누는 것이 맞아 보이면**, 그 근거를 설명하고 `AskUserQuestion` 으로 선택받습니다.
   1. feature 모드로 전환 (권장)
   2. 지정한 feature 안에 모두 태스크로 등록 → 3으로 진행
4. 그 밖에는 3으로 진행합니다.

### task 모드 — feature 생략

1. 개요가 maintenance에 맞아 보이면(기능 단위가 아닌 단발성 수정·개선 묶음) `AskUserQuestion` 으로 선택받습니다.
   1. maintenance에 태스크로 나눠 등록
   2. 별도 feature를 만들어 진행 → feature 모드로 전환
2. maintenance에 맞지 않으면 그 판단을 알리고 feature 모드로 전환합니다.

## 3. 분석·분류

- [docs/classification.md](docs/classification.md)의 기준으로 feature(feature 모드만)와 태스크를 나눕니다.
- 모듈 경계를 판단하기 어려울 때만 프로젝트 디렉토리 구조를 확인합니다. 코드 상세 분석은 하지 않습니다. (분석은 태스크별 PRD·설계 단계의 몫)
- feature 모드면 기존 feature slug와 겹치는지 `tm.sh features all` 로 확인하고, 겹치면 다른 slug를 제안합니다.

## 4. 제안 및 승인

1. [docs/classification.md](docs/classification.md) "제안 양식"으로 분류 결과를 설명합니다.
2. `AskUserQuestion` 으로 선택받습니다.
   1. 승인 — 이대로 등록
   2. 수정 요청 — 수정 내용을 **텍스트로** 받아 반영한 뒤 1로 돌아가 다시 제시
   3. 취소 — 아무것도 만들지 않고 종료
- 초기 상태는 `wait` 입니다. 사용자가 일부·전체를 백로그로 요청하면 해당 태스크만 `backlog` 로 등록합니다.

## 5. 등록

승인된 결과를 아래 순서로 등록합니다. 중간에 `tm.sh` 가 실패하면 즉시 멈추고, 그때까지 만든 경로와 실패 메시지를 보고합니다. (임의로 지우거나 재시도하지 않습니다)

### 5-1. feature 생성 (feature 모드)

feature마다 다음을 수행합니다.

1. `tm.sh new-feature [slug] "[제목]"` 으로 생성합니다.
2. 원문을 `features/[slug]/docs/definition.md` 에 **그대로** 저장합니다. (여러 feature로 나눠도 원문은 각 feature에 동일하게 저장)
3. feature README를 채웁니다.
   - "개요": 원문 중 **이 feature가 맡는 목적과 범위**를 적습니다. 다른 feature로 나간 범위는 "이 feature의 범위가 아닌 것"으로 한 줄 적습니다. (feature가 하나면 생략)
   - "참고 문서": `- [docs/definition.md](docs/definition.md) — 원문 (자동 분류 입력)`
   - 스크립트가 넣은 자리표시(`(미정)`·`(없음)`)는 남기지 않고 위 내용으로 바꿉니다.

### 5-2. 원문 저장 (task 모드)

- feature 지정: `features/[feature]/docs/definition.md` 가 없으면 그 경로에, 있으면 `docs/definition-[YYYYMMDD_HHmmss].md`(`date +%Y%m%d_%H%M%S` 로 실제 시각 확인)에 저장하고 feature README "참고 문서"에 추가합니다. ("참고 문서"가 `(없음)` 이면 바꿉니다)
- maintenance: 공용 `docs/` 가 없으므로 여기서는 저장하지 않고, 5-3에서 태스크마다 저장합니다.

### 5-3. 태스크 생성

feature마다 제안한 순서대로 다음을 수행합니다.

1. `tm.sh new-task [feature] [task-slug] [wait|backlog]` 로 생성합니다. (번호는 스크립트가 매기므로 제안 순서대로 하나씩 호출)
   - maintenance면 생성된 태스크의 `docs/definition.md` 에 원문을 저장합니다.
2. 생성된 README를 structure.md 태스크 README 스키마대로 채웁니다. (본문은 "작업 이력" 절 위에 작성)
   - 제목: 스크립트가 slug로 넣은 `# [slug]` 를 태스크 제목으로 바꿉니다.
   - frontmatter: `source_type` 을 `auto` 로 바꾸고, `source` 에는 **입력 원본**(슬랙 링크·문서 경로)을 적습니다. 텍스트 입력이면 `source` 를 생략합니다.
     - 원문 저장 경로(`definition.md`)를 적지 않는 이유: 상태 변경·feature 완료 시 디렉토리가 이동해 경로가 끊기기 때문입니다. 원문은 feature README "참고 문서"(maintenance는 태스크 README "문서")로 찾습니다.
   - "개요": 태스크가 무엇이고 왜 하는지, 범위(모듈 단위)
   - "요구사항": 원문에서 이 태스크에 해당하는 요구사항 요약
   - "선행 태스크": 제안 시 정한 선행 태스크 (`[태스크 디렉토리명] — 사용하는 결과물`). 없으면 절 생략
   - "문서": maintenance 태스크만 `- [docs/definition.md](docs/definition.md) — 원문 (자동 분류 입력)` 을 적습니다.
   - maintenance 태스크는 디렉토리명이 시각 기반이라 순서가 이름에 드러나지 않습니다. 선행 관계는 "선행 태스크" 절에 기록만 남깁니다. (jissp-task-manager 는 maintenance 태스크의 선행 태스크를 컨텍스트로 읽지 않으므로, 실행 순서는 사용자가 지킵니다)
3. feature면 feature README "태스크 목록" 표에 structure.md 형식대로 행을 추가하고 `updated_at` 을 갱신합니다.

## 6. 결과 보고 및 다음 단계

1. 이번에 생성한 feature·태스크를 `[feature]/[태스크 디렉토리명] — 제목 (상태)` 목록으로 보고합니다.
2. `AskUserQuestion` 으로 다음 단계를 선택받습니다. "첫 태스크"는 이번에 등록한 태스크 중 첫 번째입니다. 선택한 작업은 해당 스킬을 호출해 이어갑니다.
   1. 첫 태스크 PRD 작성 — `/jissp-planner draft --task [feature]/[task]`
   2. 첫 태스크 바로 실행 — `/jissp-task-manager run [feature] [task]`
   3. 나중에 — 위 두 명령을 안내하고 종료
- `[task]` 는 feature면 번호(`01`), maintenance면 태스크 디렉토리명입니다.
- feature를 여러 개 만들었으면 어느 feature의 첫 태스크로 진행할지 함께 묻습니다. (feature 간 순서는 정하지 않으므로 사용자가 고릅니다)
