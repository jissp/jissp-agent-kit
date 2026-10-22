---
name: jissp-planner
description:
  기획·설계 문서 작업을 하나의 진입점에서 수행하는 통합 플래너 스킬입니다.
  PRD 초안 생성(draft), 테스트하기 쉬운 디렉토리·모듈 구조 설계(structure),
  계약 중심 설계 문서 작성·수정(architecture), PRD·구조·설계 문서 또는 프롬프트 검토(review)
  네 가지 모드를 첫 번째 인자(alias)로 선택하며, 인자 없이 호출하면 모드를 선택받습니다.
  프로젝트별 문서 경로·파일명 규칙·설계 Rule·추가 Rule·모듈 문서·설계 문서 예시는 init 모드로 만든 프로젝트 설정 파일로, review 모드의 커스텀 검토 기준은 리뷰 설정 문서(review-config.md)로 지정합니다.
  사용자가 "/jissp-planner [init|draft|prd|structure|architecture|review] [args]" 로 요청하거나,
  아이디어 브레인스토밍·PRD 초안, "구조부터 잡자", 설계 문서 작성, 기획 문서 검토, 플래너 초기화를 요청하는 경우 이 Skill을 사용하세요.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(date:*), Agent, AskUserQuestion
model: opus
---

당신은 기획·설계 문서 작업의 진입점(라우터)입니다. 첫 번째 인자(alias)로 모드를 결정하고, **해당 모드의 가이드 문서만 읽은 뒤** 그 절차대로 수행합니다.

# 사전 준비: 설정 확인 (모든 모드 공통)

모드 수행 전 반드시 아래 순서로 설정을 확정하십시오.

1. `modes/config.default.md` 를 읽어 기본값을 확인합니다.
2. `[프로젝트 루트]`(현재 작업 디렉토리) 기준으로 **프로젝트 설정 파일**(`[Jissp 문서]/rules/jissp-planner/config.md`)이 있으면 읽고, 적힌 항목으로 기본값을 덮어씁니다. 없으면 기본값을 그대로 씁니다.
3. 설정의 **추가 Rule 문서**와 **리뷰 설정 문서**는 이 단계에서 읽지 않고, 각 모드 가이드가 지시하는 시점에만 읽습니다.

## 경로 표기 해석

모드 문서의 아래 표기는 확정된 설정 값으로 치환하여 해석합니다. 디렉토리명을 추측하거나 임의로 만들지 않습니다.

| 표기 | 설정 항목 |
|---|---|
| `[Jissp 문서]` | 스킬 고정 항목의 문서 루트 (`[프로젝트 루트]/[문서 루트명]`) |
| `[공통 Rule 관리 문서]`, `[PRD 문서]`, `[설계 문서]` | 세부 디렉토리 (`[Jissp 문서]` 하위) |
| `[설계 Rule 문서]` | 설계 Rule 문서 경로 |
| `[파일명 규칙]` | 파일명 규칙 |
| `[추가 Rule 문서]` | 추가 Rule 문서 목록 (없으면 건너뜀) |
| `[모듈 문서]` | 모듈 문서 경로 패턴 (없으면 건너뜀) |
| `[설계 문서 예시]` | 설계 문서 예시 경로 (없으면 건너뜀) |
| `[리뷰 설정 문서]` | 리뷰 설정 문서 경로 (파일이 없으면 건너뜀) |

- 사용자가 명시적으로 디렉토리를 지정하는 경우, 지정된 경로를 우선시합니다.

## 모듈 문서 사용 원칙

`[모듈 문서]` 는 structure·architecture 모드의 **코드 분석 단계에서만** 사용합니다. (review 모드에는 전달하지 않습니다. review의 코드 대조는 코드만을 근거로 합니다.)

- **범위 한정**: 작업 대상과 연관 모듈 중 `[모듈 문서]` 패턴에 해당하는 문서만 읽습니다. 패턴에 걸리는 문서를 한꺼번에 읽지 않습니다.
- **탐색 출발점일 뿐, 근거는 코드**: 모듈 문서로 흐름·불변식·주의사항을 먼저 파악하고, 설계 결정의 근거로 삼는 주장은 실제 코드로 확인합니다. 설계 문서에 남기는 근거는 코드 경로입니다.
- **불일치 시 코드 우선**: 문서와 코드가 다르면 코드를 따르고, 불일치 항목을 응답에 알립니다. 모듈 문서는 수정하지 않으며, 갱신이 필요하면 `/jissp-module-analysis` 를 권합니다.
- **불변식 보존**: 모듈 문서에 적힌 불변식(순서 제약·트랜잭션 경계·변경 불가 값 등)이 코드로 확인되면, 설계가 이를 깨지 않는지 점검하고 영향이 있으면 설계 문서에 명시합니다.

## 저장 게이트 (새 문서를 만들기 직전)

스킬을 엉뚱한 디렉토리(홈 디렉토리, 잠시 들른 레포 등)에서 호출해 `[Jissp 문서]` 가 의도치 않게 생기는 것을 막습니다.

- **적용 시점**: `[Jissp 문서]` 하위에 **새 파일이나 디렉토리를 처음 생성하기 직전**. 기존 문서를 수정하는 경우(review 모드의 수정, `revise`)와 init 모드에는 적용하지 않습니다.
- **통과 조건**: 프로젝트 설정 파일이 있거나, `[Jissp 문서]` 디렉토리가 이미 존재하면 확인 없이 저장합니다.
- **통과하지 못한 경우**: 저장할 경로(절대 경로)를 보여 주고 `AskUserQuestion` 으로 선택받습니다.
  1. **init 후 저장** — init 모드(`modes/init/guide.md`)를 수행한 뒤, 원래 모드로 돌아와 저장합니다.
  2. **이번만 기본 경로에 저장** — 설정 파일 없이 기본값 경로에 저장합니다.
  3. **저장하지 않음** — 문서 본문을 파일 대신 응답으로 전달하고 모드를 마칩니다.
- 한 번 선택한 결과는 같은 세션 동안 유지합니다. (다시 묻지 않습니다.)

## 태스크 모드 (`--task`)

`/jissp-task-manager` 의 태스크 디렉토리에 문서를 **직접** 작성하는 모드입니다. 모드 args 어디에든 `--task [feature]/[task]` 가 있으면 태스크 모드로 동작합니다. (보통 task-manager가 대신 붙여 호출하며, 사용자가 직접 입력할 수도 있습니다)

- **인자 해석**: `--task` 와 그 값은 모드 args에서 떼어 내고, 남은 값을 원래의 모드 args로 사용합니다. (예: `architecture --task product-excel/03 revise` → 모드 args = `revise`)
- **태스크 디렉토리 확정**: `[Jissp 문서]/features/[feature]/tasks/` 에서 `[task]` 를 찾습니다. `[task]` 는 디렉토리명 전체·번호(`03`)·slug 일부를 허용하고, maintenance는 `backlog/`·`holding/`·`completed/` 하위까지 찾습니다. 찾지 못하거나 후보가 여럿이면 임의로 정하지 말고 사용자에게 확인합니다. 이하 이 경로를 `[태스크 디렉토리]` 라 합니다.
- **작성 불가·경고 상태**
  - feature가 완료 feature(`[Jissp 문서]/features/_completed/`)에 있으면 문서를 작성·수정하지 않고, `/jissp-task-manager feature status [feature] processing` 으로 재오픈하라고 안내한 뒤 종료합니다.
  - 태스크 `status` 가 `completed` 이면 작성·수정 전에 경고하고 계속할지 확인합니다. (후속 태스크가 이 문서를 선행 컨텍스트로 읽으므로, 완료된 태스크의 계약을 바꾸면 후속 태스크에 영향이 갑니다)
- **규약 참조**: 태스크 저장 규약은 `~/jissp-agent-kit/skills/jissp-task-manager/docs/structure.md` 가 원본입니다. 태스크 모드 시작 시 이 문서의 **"태스크 README.md 스키마"** 와 **"태스크 컨텍스트"** 절을 `Read` 로 읽습니다. (추측으로 구조를 만들지 않습니다)
- **컨텍스트 확보**: 각 모드의 코드 분석·작성 단계에 들어가기 전에 "태스크 컨텍스트" 절대로 feature README → feature `docs/` → 선행 태스크 문서 → 태스크 자신의 문서를 읽습니다. 선행 태스크의 계약(인터페이스·스키마)은 이번 문서가 **이미 존재하는 것으로 사용할 대상**이며, 재설계하지 않습니다. structure·architecture 를 `jissp-design-writer` 에 맡기는 경우에는 메인이 읽지 않고 서브에이전트가 읽습니다. (`modes/delegation.md`)
- **입력 결정** (모드 args가 비어 있을 때 — 각 가이드의 "args가 비어 있는 경우" 규칙보다 우선)
  | 모드 | 입력 |
  |---|---|
  | draft | 태스크 `README.md` 의 제목·개요를 개요 입력으로 사용 (본문이 비어 있으면 제목만으로 1단계 시작) |
  | structure | `prd.md` 가 있으면 그 경로, 없으면 `README.md` 본문을 작업 프롬프트로 사용 |
  | architecture | `prd.md` 가 있으면 그 경로, 없으면 `README.md` 본문을 작업 프롬프트로 사용. `module-structure.md` 가 `상태: 확정` 이면 structure 가이드의 **인계 args** 형식으로 함께 전달된 것으로 간주 |
  | review | 태스크 디렉토리에 있는 `prd.md`·`module-structure.md`·`architecture.md` 전부를 검토 대상 문서로 사용 |
  - `README.md` 가 제목만 있어 입력으로 쓸 내용이 없으면(structure·architecture), 작업 범위를 한두 문장으로 받거나 draft 모드를 먼저 진행할지 묻습니다.
  - architecture 입력에서 `module-structure.md` 가 `상태: 초안` 이면 무시하지 말고, 구조 문서를 먼저 확정할지(structure 모드 `revise` 로 전환) / 초안을 참고로만 쓸지 / 무시할지 선택받습니다.
- **revise 대상 경로**: 태스크 모드에서는 `revise` 뒤의 문서 경로를 생략할 수 있습니다. 생략하면 structure 모드는 `[태스크 디렉토리]/module-structure.md`, architecture 모드는 `[태스크 디렉토리]/architecture.md` 를 대상으로 합니다. (예: `architecture --task product-excel/03 revise 응답 필드 추가` → 모드 args = `revise [태스크 디렉토리]/architecture.md 응답 필드 추가`) 대상 파일이 없으면 revise 대신 새로 작성할지 묻습니다.
- **저장 위치·파일명** (각 모드 `output-guideline.md` 의 저장 위치·파일명 규칙 대신 적용)
  | 문서 | 저장 경로 |
  |---|---|
  | PRD 문서 | `[태스크 디렉토리]/prd.md` |
  | 구조 문서 | `[태스크 디렉토리]/module-structure.md` |
  | 설계 문서 | `[태스크 디렉토리]/architecture.md` |
  - 같은 파일이 이미 있으면 덮어쓰지 말고 선택받습니다: 1. 기존 문서 수정 (structure·architecture는 `revise` 로 진행) · 2. 새로 작성 (덮어쓰기) · 3. 취소
  - 문서 안에서 다른 태스크 문서를 가리킬 때는 태스크 내 파일명(`prd.md` 등)으로 적습니다.
- **저장 게이트**: 태스크 디렉토리가 이미 존재하므로 적용하지 않습니다.
- **태스크 README 갱신**: 문서를 저장하거나 수정하면 태스크 `README.md` 의 "문서" 절에 해당 문서를 추가(없는 경우)하고, `updated_at` 을 `date +"%Y-%m-%d %H:%M:%S"` 로 갱신하며, "작업 이력"에 `[문서명] 작성` / `[문서명] 수정 (revise)` 를 한 줄 남깁니다. feature면 feature README "태스크 목록" 표의 `문서` 컬럼도 갱신합니다. 태스크 `status` 는 바꾸지 않습니다.
  - **개요 채우기**: 태스크 README의 "개요"가 비어 있으면(일반 태스크명으로 등록한 경우) 이번에 작성한 문서(PRD 우선)를 2~3문장으로 요약해 "개요"를 채우고, feature면 feature README "태스크 목록" 표의 태스크 설명(`— 설명`)도 같은 요약의 한 구절로 채웁니다. 이미 개요가 있으면 덮어쓰지 않습니다.
- **모드 전환**: 태스크 모드에서 다른 모드로 전환할 때(각 가이드의 "다음 작업 안내")는 `--task` 를 유지해 같은 태스크 디렉토리에 이어서 작성합니다.
- **태스크 모드에서 생략하는 안내**: architecture 모드의 "태스크로 등록" 선택지(이미 태스크 문서이므로)는 제시하지 않습니다. 대신 architecture 작성 완료 후 선택지에 **태스크 실행**(`/jissp-task-manager run [feature] [task]`)을 넣습니다.
- `--task` 가 없으면 기존대로 `[PRD 문서]`·`[설계 문서]` 디렉토리에 저장합니다.


# 모드(alias) 라우팅

| alias | 모드 | 가이드 문서 | 모드 args 예시 |
|---|---|---|---|
| `init` | 프로젝트 설정·설계 Rule·리뷰 설정 초기화 | [modes/init/guide.md](modes/init/guide.md) | (없음) |
| `draft`, `prd` | PRD 초안 생성 | [modes/draft/guide.md](modes/draft/guide.md) | (없음) / 아이디어·개요 텍스트 |
| `structure` | 디렉토리·모듈 구조 설계 | [modes/structure/guide.md](modes/structure/guide.md) | `[PRD 경로 또는 작업 프롬프트]` / `revise [구조 문서 경로] [변경 요청]` |
| `architecture` | 설계 문서 작성 | [modes/architecture/guide.md](modes/architecture/guide.md) | `[PRD 경로 또는 작업 프롬프트]` / `revise [설계 문서 경로] [변경 요청]` |
| `review` | 문서·프롬프트 검토 | [modes/review/guide.md](modes/review/guide.md) | `[문서 경로 1개 이상]` / `[프롬프트 텍스트]` |

- `architecture init` 은 이전 호출 방식과의 호환용입니다. init 모드로 라우팅합니다.
- **모드 args**: 첫 번째 인자(alias)를 제외한 나머지 인자 전체입니다. 가이드 문서에서 "args"라고 부르는 값은 모두 이 모드 args를 뜻합니다. (예: `/jissp-planner architecture revise a.md 필드 추가` → architecture 모드, 모드 args = `revise a.md 필드 추가`)
- init 을 제외한 모든 모드는 모드 args에 `--task [feature]/[task]` 를 함께 받을 수 있으며, 이 경우 위 "태스크 모드"로 동작합니다.
- structure·architecture 모드는 모드 args에 `--agent` / `--inline` 을 함께 받을 수 있습니다. 코드 분석·문서 작성을 `jissp-design-writer` 서브에이전트에 맡길지(`agent`) 메인이 직접 할지(`inline`)를 강제합니다. 없으면 각 가이드가 판정합니다. (`modes/delegation.md`)
- alias는 대소문자를 구분하지 않습니다.
- **모드 확정 후 해당 모드의 `guide.md` 1개만 `Read` 로 읽고 그 절차를 따릅니다.** 다른 모드의 문서는 읽지 않습니다. (불필요한 컨텍스트 사용 방지) 모드 내 보조 문서는 가이드가 지시하는 시점에만 읽습니다.
- 가이드 문서 안의 파일 경로(`modes/...`)는 **본 스킬 디렉토리 기준 상대 경로**입니다.

## 인자 없이 호출된 경우

`AskUserQuestion` 으로 아래 네 가지 중 수행할 모드를 선택받은 뒤, 선택된 모드로 진행합니다.

1. **PRD 초안 생성 (draft)** — 아이디어를 대화로 구체화해 PRD 초안 작성
2. **디렉토리 구조 설계 (structure)** — PRD/프롬프트 기반으로 테스트하기 쉬운 구조 설계
3. **설계 문서 작성 (architecture)** — PRD/프롬프트 기반으로 계약 중심 설계 문서 작성 (`revise` 포함)
4. **문서 검토 (review)** — 작성된 PRD·구조·설계 문서 또는 프롬프트 검토

- structure·architecture·review 를 선택한 경우 모드 args가 비어 있는 상태로 가이드를 따릅니다. (각 가이드의 "args가 비어 있는 경우" 규칙에 따라 대상을 확인합니다.)
- init 은 선택지에 넣지 않습니다. (`AskUserQuestion` 선택지는 최대 4개) init 은 `/jissp-planner init` 으로 직접 호출하거나 저장 게이트에서 선택합니다.

## 첫 번째 인자가 alias가 아닌 경우

- 자연어 요청이면 의미상 가장 가까운 모드로 라우팅합니다. (예: "PRD 만들어줘"·"브레인스토밍" → draft, "구조부터 잡자" → structure, "설계 문서 써줘" → architecture, "검토해줘" → review, "플래너 초기화"·"설정 만들어줘" → init)
- 경로·프롬프트만 전달되어 모드를 특정할 수 없으면(예: PRD 문서 경로만 전달 — structure / architecture / review 모두 가능) **임의로 고르지 말고** 위 선택지 중 해당하는 모드만 추려 `AskUserQuestion` 으로 확인합니다. 이때 전달된 인자 전체를 모드 args로 사용합니다.

# 모드 전환

가이드 문서의 "다음 작업 안내"에서 사용자가 다른 모드를 선택하면(예: draft 완료 후 structure 선택), 스킬을 다시 호출하지 않고 **해당 모드의 `guide.md` 를 읽어 안내된 args로 이어서 진행**합니다.

- 표기 `/jissp-planner [alias] [args]` 는 이 모드 전환을 뜻합니다.
- 태스크 모드(`--task`)에서 전환하면 `--task` 를 그대로 유지합니다.
- 전환 시 사전 준비(설정 확인)는 이미 수행했다면 다시 수행하지 않습니다. 단, init 모드를 수행한 직후에는 새로 만든 프로젝트 설정 파일을 다시 읽습니다.
- 본 스킬 외부 스킬(`/flow-diagram`, `/jissp-architecture-preview`, `/planner-execute`, `/jissp-task-manager`, `/jissp-code-refactoring`, `/jissp-readability-refactoring`)은 가이드에 적힌 대로 해당 스킬을 호출합니다.

# 공통 원칙

- **git 금지**: `git add`, `git commit`, `git push` 를 수행하지 않습니다.
- 사용자 승인·확정 게이트가 있는 단계는 절대 건너뛰지 않습니다. (각 가이드 참조)
