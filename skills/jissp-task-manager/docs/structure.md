# 저장 구조 및 상태 모델 (공통 정의)

모든 역할(feature 관리·등록·수정·삭제·실행·상태 관리)이 공통으로 따르는 정의입니다.

## feature 루트

- 경로: 스킬을 호출한 **프로젝트 내** `[Jissp 문서]/features` (`[Jissp 문서]` = `[프로젝트 경로]/0-jissp-docs`, jissp-document.md 정의 준용)
- **동작 조건 (가드)**: 이 스킬은 `~/jissp-agent-kit/project-mapping-table.md`에서 정의한 프로젝트 경로에 해당하는 프로젝트 내에서만 동작합니다. (심볼릭 링크 경로는 같은 문서의 `심볼릭 링크 경로 비교` 규칙대로 `realpath` 해석 후 비교)
  - 현재 작업 디렉토리가 해당 규칙으로 해석되는 프로젝트 내부인지 확인하고, 아니면(예: `~/.claude/skills`) 작업을 수행하지 말고 그 사실을 안내한 뒤 종료합니다.
  - 태스크는 스킬 디렉토리가 아니라 **호출한 프로젝트의 저장소**에 기록됩니다.
- 루트와 `maintenance` 버킷이 없으면 최초 사용 시 생성합니다. (`maintenance/README.md` 는 아래 feature README 스키마로 작성)

## 용어

| 용어 | 의미 |
|---|---|
| **feature** | 하나의 기능 단위. 여러 태스크를 순차로 묶습니다. 예: 상품 엑셀 업로드/다운로드 |
| **maintenance** | feature에 속하지 않는 단발성 작업을 받는 **공용 유지보수 버킷**. `features/` 아래의 예약 slug이며, feature를 지정하지 않으면 여기에 등록됩니다. |
| **태스크** | feature 안에서 사용자가 모듈 단위로 범위를 정한 작업 1건. PRD·설계 문서를 태스크마다 가집니다. |

- **표기 규칙**: maintenance는 기능 단위가 아니지만, 저장 위치·식별자에서는 feature와 **같은 자리**를 씁니다. `features/` 디렉토리, `[feature]` 인자, 태스크 frontmatter `feature` 필드, `tm.sh features` 목록에는 maintenance도 들어갑니다. 둘의 처리가 다른 규칙은 "feature"와 "maintenance"를 나란히 적어 구분합니다. (예: "feature는 번호 순, maintenance는 활성만")

## 디렉토리 구조

```
features/
├── maintenance/                              # 공용 유지보수 버킷
│   ├── README.md                             # README (feature README 스키마, 태스크 목록 표 없음)
│   └── tasks/
│       ├── [YYYYMMDD_HHmmss]_[task-slug]/    # wait / processing
│       ├── backlog/[YYYYMMDD_HHmmss]_[task-slug]/
│       ├── holding/[YYYYMMDD_HHmmss]_[task-slug]/
│       └── completed/[YYYYMMDD_HHmmss]_[task-slug]/
│
├── [feature-slug]/                           # feature
│   ├── README.md                             # feature 설명 · 태스크 목록(자동 갱신) · 이력
│   ├── docs/                                 # 기능 정의, 구조·순서 참고 문서 등 태스크 공통 참고 문서
│   └── tasks/
│       └── [NN]_[task-slug]/                 # 상태와 무관하게 항상 이 위치
│           ├── README.md                     # 작업 정의 (필수)
│           ├── prd.md                        # PRD 문서 (선택)
│           ├── module-structure.md           # 구조 문서 (선택)
│           ├── architecture.md               # 설계 문서 (선택)
│           ├── validation-[N]차.md           # 완료 검토 시 갭 리포트 (선택)
│           └── docs/                         # 이 태스크만의 참고 문서 (선택)
│
└── _completed/
    └── [feature-slug]/                       # 완료된 feature (통째로 이동)
```

### 이름 규칙

| 대상 | 형식 | 예시 |
|---|---|---|
| feature | `[feature-slug]` (kebab-case) | `product-excel` |
| feature의 태스크 | `[NN]_[task-slug]` | `01_s3-upload-module` |
| maintenance 태스크 | `[YYYYMMDD_HHmmss]_[task-slug]` | `20260723_223717_add-board-publish-date` |

- **예약어**: feature slug로 `maintenance`, `_` 로 시작하는 이름(`_completed` 등), 목록 범위 키워드(`backlog`, `holding`, `completed`, `all`)는 쓸 수 없습니다. (`list [범위]` 와 `list [feature]` 가 구분되지 않기 때문)
- **태스크 번호 `[NN]`**: 같은 feature에서 **지금까지 쓴 가장 큰 번호 + 1**을 두 자리(`01`~`99`, 100부터는 세 자리)로 붙입니다. 만든 순서가 곧 번호입니다.
  - "지금까지 쓴 번호"는 `tasks/` 안의 디렉토리 번호와 feature README "이력"의 `태스크 삭제: [NN]_...` 기록을 모두 포함합니다. (마지막 태스크를 지운 뒤 같은 번호가 재사용되지 않게 하기 위함)
  - QA처럼 여러 태스크로 나뉘는 경우도 별도 규칙 없이 다음 번호를 씁니다. (예: `04_upload-qa-validation`, `05_upload-qa-permission`)
  - 삭제로 번호가 비어도 **재번호를 매기지 않습니다.** (문서 간 참조가 깨지지 않게 하기 위함)
- **타임스탬프**: 반드시 `date +%Y%m%d_%H%M%S` 명령으로 실제 시각을 확인해 사용합니다. (임의 생성 금지)
- `task-slug` / `feature`: 태스크 내용을 요약한 kebab-case 식별자

## 태스크 상태 모델 (5종)

| 상태 | 의미 |
|---|---|
| `backlog` | 지금 당장 하지는 않지만 해야 할 태스크 |
| `wait` | 대기. 태스크 최초 등록 시 기본 상태 |
| `processing` | 처리 중. 태스크 처리를 시작하면 전이 |
| `completed` | 처리 완료 |
| `holding` | 처리 보류/홀딩 |

- **SSOT**: 상태의 유일한 원본은 태스크 `README.md` frontmatter의 `status` 필드입니다.
- **위치 규칙** (feature 종류별로 다름)
  | feature | 상태별 위치 |
  |---|---|
  | feature | **이동하지 않습니다.** 모든 상태가 `[feature]/tasks/[NN]_[task]/` 에 머뭅니다. (번호 순서가 흐트러지지 않게 하기 위함) |
  | maintenance | `wait`·`processing` = `tasks/` 루트, `backlog` = `tasks/backlog/`, `holding` = `tasks/holding/`, `completed` = `tasks/completed/` |
- 상태 변경 절차는 [status.md](status.md)를 따릅니다.

## feature 상태 모델 (feature 전용)

| 상태 | 의미 | 위치 |
|---|---|---|
| `processing` | 진행 중. feature 생성 시 기본 상태 | `features/[slug]/` |
| `holding` | feature 전체 보류 | `features/[slug]/` |
| `completed` | feature 완료 | `features/_completed/[slug]/` |

- `maintenance` 는 상태가 없으며 완료·보류·삭제할 수 없습니다.
- **완료 feature의 태스크**(`_completed/` 하위)는 조회만 허용합니다. 태스크 등록·실행·상태 변경·문서 작성(`/jissp-planner --task`) 요청이 오면 수행하지 않고 feature 재오픈(`feature status [slug] processing`)을 안내합니다.
- feature 상태 변경 절차는 [feature.md](feature.md)를 따릅니다.

## feature README.md 스키마

```markdown
---
name: product-excel
type: feature               # feature | maintenance
status: processing          # feature만 (processing | holding | completed)
created_at: 2026-09-29 10:00:00
updated_at: 2026-09-29 10:00:00
---

# [feature 제목] (예: 상품 엑셀 업로드/다운로드)

## 개요

[feature가 무엇이고 왜 만드는지, 최종 목표]

## 참고 문서

<!-- docs/ 하위 문서를 나열. 없으면 "(없음)" -->
- [docs/definition.md](docs/definition.md) — 기능 정의

## 태스크 목록

<!-- feature만. 스킬이 자동 갱신합니다. 수동 수정 시 태스크 README의 status가 우선합니다 -->
| # | 태스크 | 상태 | 문서 | 완료일 |
|---|---|---|---|---|
| 01 | [s3-upload-module](tasks/01_s3-upload-module/README.md) — S3 upload 공통 모듈 | completed | prd · arch | 2026-09-30 |
| 02 | [excel-sheet-module](tasks/02_excel-sheet-module/README.md) — 엑셀 sheet 공통 모듈 | wait | - | - |

## 이력

- 2026-09-29 10:00:00 feature 생성
```

- `maintenance/README.md` 는 `type: maintenance`, `status` 없음, "태스크 목록" 절을 두지 않습니다. (태스크가 계속 쌓이므로 목록은 `list` 로 조회)
- **태스크 목록 표 갱신 시점**: 태스크 등록·상태 변경·삭제·문서 추가 시 해당 행을 갱신하고 `updated_at` 을 갱신합니다.
  - `문서` 컬럼: 태스크에 있는 문서를 `prd` · `structure` · `arch` 로 표기, 없으면 `-`
  - `완료일`: 태스크 frontmatter `completed_at` 의 날짜 (`YYYY-MM-DD`)
- "이력"에는 feature 수준 이벤트(생성, 태스크 등록·완료·삭제, feature 상태 변경)를 한 줄씩 남깁니다.

## 태스크 README.md 스키마

```markdown
---
name: s3-upload-module
feature: product-excel       # 소속 feature slug (maintenance 포함)
status: wait
completed_at:                # completed 전이 시각 (그 외 상태에서는 비움)
source_type: name            # name | slack-thread | prompt | prd | structure | architecture | 기타 (열린 목록)
source: [원본 참조]           # 슬랙 링크, 이동 전 문서 경로 등. 없으면 생략
created_at: 2026-09-29 10:05:00
updated_at: 2026-09-29 10:05:00
---

# [태스크 제목]

## 개요

[태스크가 무엇인지, 왜 하는지, 이 태스크의 범위(모듈 단위)]

## 요구사항

[핵심 요구사항 요약 — 상세는 prd.md 등에 위임]

## 선행 태스크

<!-- 이 태스크가 결과물에 의존하는 같은 feature의 태스크. 없으면 절 생략 -->
- 01_s3-upload-module — S3 upload 공통 모듈 사용

## 문서

<!-- 태스크 디렉토리에 있는 문서만 나열 -->
- [prd.md](prd.md) — PRD 문서
- [module-structure.md](module-structure.md) — 구조 문서
- [architecture.md](architecture.md) — 설계 문서
- [docs/](docs/) — 참고 문서

## 작업 이력

- 2026-09-29 10:05:00 등록 (wait)
```

- 일반 태스크명으로 등록한 직후에는 **frontmatter + 제목만** 있는 빈 README입니다. (본문 없음)
- **경로 우선**: frontmatter `feature` 는 검색 편의를 위한 필드입니다. 실제 디렉토리 위치와 어긋나면 **경로를 기준**으로 삼고 frontmatter를 경로에 맞게 고칩니다.
- **작업 문서가 없는 상태**: 개요·요구사항 본문이 없고 `prd.md`·`module-structure.md`·`architecture.md` 도 없는 태스크를 말합니다. (README에 "문서"·"작업 이력" 절만 있어도 해당) 이 상태의 태스크는 실행하지 않습니다. ([execute.md](execute.md)의 가드)
- 태스크 문서(`prd.md`·`module-structure.md`·`architecture.md`)는 **태스크 디렉토리의 원본**입니다. 다른 곳의 사본이 아니므로 원본 동기화 개념이 없습니다.

## 태스크 컨텍스트 (문서 작성·실행 시 함께 읽는 문서)

feature의 태스크는 앞 태스크의 결과물(공통 모듈 등)을 이어서 사용하므로, 태스크 문서를 **작성**(`/jissp-planner --task`)하거나 태스크를 **실행**(`run`)할 때 아래 순서로 컨텍스트를 확보합니다. (`/jissp-planner` 도 이 절을 읽고 따릅니다)

1. **feature README.md**: feature 목표와 태스크 목록(어떤 태스크가 완료되었는지)을 파악합니다.
2. **feature `docs/`**: "참고 문서" 절에 나열된 문서 중 이번 태스크 범위와 관련된 문서를 읽습니다.
3. **선행 태스크 문서**:
   - 태스크 README의 "선행 태스크" 절에 적힌 태스크의 `architecture.md`(없으면 `README.md`)를 읽습니다. 계약(Part A)을 우선 확인합니다.
   - "선행 태스크" 절이 없으면, feature README 태스크 목록에서 이번 태스크보다 번호가 작고 `completed` 인 태스크 중 **범위가 겹치는 것만** 골라 읽습니다. 전부 읽지 않습니다.
   - 선행 태스크가 `completed` 가 아니면 그 사실을 사용자에게 알립니다. (진행은 막지 않습니다)
4. **태스크 자신의 문서**: `README.md` → `prd.md` → `module-structure.md` → `architecture.md` → `docs/*`

- 문서에 적힌 선행 태스크의 인터페이스는 **실제 코드로 확인**합니다. 구현 중 계약이 바뀌었을 수 있기 때문입니다. 불일치하면 코드를 따르고 사용자에게 알립니다.
- maintenance 태스크는 1~3을 건너뛰고 4만 읽습니다.

## 태스크 탐색 방법 (공통)

특정 태스크를 찾거나 목록을 조회할 때는 아래 Glob 패턴으로 `README.md` frontmatter를 스캔합니다.

| 대상 | 패턴 |
|---|---|
| feature 목록 | `features/*/README.md` (`_completed` 제외) |
| 완료 feature | `features/_completed/*/README.md` |
| feature의 태스크 | `features/[slug]/tasks/*/README.md` |
| maintenance 활성 | `features/maintenance/tasks/*/README.md` |
| maintenance 백로그·보류·완료 | `features/maintenance/tasks/{backlog,holding,completed}/*/README.md` |

### 태스크 지정 방식

`[task명]` 은 아래 형식 중 하나로 받습니다.

- `[feature]/[task]` 또는 `[feature] [task]` — 예: `product-excel/01`, `product-excel 01_s3-upload-module`
- `[task]` 만 — feature를 생략
- `[task]` 부분은 디렉토리명 전체, 번호(`01`, `1`), slug 일부 모두 허용합니다.

### 특정 태스크 탐색 순서

1. feature가 지정되면 그 feature 안에서만 찾습니다. (maintenance면 활성 → backlog → holding → completed 순)
2. feature가 생략되면 **진행 중인 feature 전체 → maintenance(활성 → backlog → holding → completed) → 완료 feature** 순으로 찾습니다. (완료 feature에서 찾은 태스크는 조회만 가능 — 위 "feature 상태 모델" 참고)
3. 일치 후보가 여러 개면 후보 목록(`[feature]/[디렉토리명]` + `name` + `status`)을 제시하고 선택받습니다.
4. 어디에서도 찾지 못하면 작업을 수행하지 않고 사용자에게 알립니다.

## 스크립트 (`tm.sh`)

규칙대로만 하면 되는 파일 조작은 LLM이 직접 하지 않고 **반드시 스크립트로** 수행합니다. (번호·시각·frontmatter·이동의 정합성을 보장하기 위함)

- 경로: `~/jissp-agent-kit/skills/jissp-task-manager/scripts/tm.sh`
- **프로젝트 루트(현재 작업 디렉토리)에서** 실행합니다. 경로 인자·출력은 `[Jissp 문서]`(`0-jissp-docs`) 기준 상대 경로입니다.
- 출력은 한 줄에 한 항목, 필드는 탭으로 구분합니다. 실패 시 `error: ...` 를 stderr로 내고 종료 코드 1을 반환하며, 이 경우 사용자에게 그대로 알립니다.

| 명령 | 역할 | 출력 |
|---|---|---|
| `features [all]` | feature 목록 (`all`: 완료 포함) | `slug  status  완료수/전체  다음wait태스크` (maintenance는 `active N`) |
| `tasks [feature] [active\|backlog\|holding\|completed\|all]` | 태스크 목록 | `경로  status  name  updated_at` |
| `find <query> [feature]` | 태스크 탐색 (디렉토리명·번호·slug 일부, 위 탐색 순서) | 일치 경로 (여러 줄이면 후보) |
| `new-feature <slug> [title]` | feature 생성 (예약어·중복 검사, maintenance 자동 생성) | 경로 |
| `new-task <feature> <slug> [wait\|backlog]` | 태스크 생성 (번호/타임스탬프, frontmatter, 작업 이력, feature 이력) | 경로 |
| `set-status <task_path> <status> [reason]` | `status`·`updated_at`·`completed_at` 갱신, 작업 이력 기록, maintenance 이동 | 새 경로 |
| `feature-status <slug> <status>` | feature 상태 갱신·이력 기록, `_completed/` 이동·복귀 | 새 경로 |

- 스크립트가 **하지 않는 일**(스킬이 수행): 태스크 README 제목·본문 작성, feature README "태스크 목록" 표 갱신, "개요"·"참고 문서" 작성, 태스크·feature 삭제(`rm -rf` + "이력"의 `태스크 삭제:` 기록), 다른 feature로 옮기기.
- 이력 줄은 README의 마지막 절(`## 작업 이력` / `## 이력`) 끝에 추가됩니다. 이 두 절은 항상 README의 **마지막 절**로 유지합니다.
