# 태스크 등록 절차 (add)

> 선행: [structure.md](structure.md)의 저장 구조·이름 규칙·README 스키마를 따릅니다.

사용법: `/jissp-task-manager add [feature] [요청]`

- `[feature]`: 등록할 feature slug. **생략하면 `maintenance`** 에 등록합니다.
- `[요청]`: 일반 태스크명, 슬랙 스레드 링크, 프롬프트, 기획·설계 문서 경로 등

## 0. feature 판별

1. 첫 번째 인자가 `features/` 아래 **진행 중인 feature slug**(또는 `maintenance`)와 일치하면 그 feature로 정하고, 나머지 인자를 `[요청]` 으로 봅니다.
2. 일치하지 않으면 인자 전체를 `[요청]` 으로 보고 `maintenance` 에 등록합니다.
   - 단, 첫 인자가 slug 모양(kebab-case 한 단어)이고 뒤에 인자가 더 있어 **feature를 의도한 것으로 보이면**, 임의로 정하지 말고 다음 중 선택받습니다.
     1. `[첫 인자]` feature를 새로 만들고 거기에 등록 ([feature.md](feature.md) 생성 절차 후 이어서 등록)
     2. maintenance에 인자 전체를 태스크로 등록
3. 대상 feature가 `holding` 이면 보류 중임을 알리고 계속할지 확인합니다. `_completed/` 에 있는 feature면 등록하지 않고 재오픈(`feature status [slug] processing`)을 안내합니다.

## 1. 태스크 디렉토리명과 초기 상태

| feature | 디렉토리명 | 위치 |
|---|---|---|
| feature | `[NN]_[task-slug]` — `NN` = `tasks/` 안 가장 큰 번호 + 1 | `features/[slug]/tasks/` (상태 무관) |
| maintenance | `[YYYYMMDD_HHmmss]_[task-slug]` — `date +%Y%m%d_%H%M%S` 로 실제 시각 확인 | `wait` = `tasks/`, `backlog` = `tasks/backlog/` |

- 초기 상태: 기본 `wait`. 사용자가 백로그 등록을 요청하면 `backlog`.
- **생성은 `tm.sh new-task [feature] [slug] [wait|backlog]` 로 합니다.** 번호·타임스탬프 계산, 디렉토리 생성, README frontmatter(`feature` 포함)·제목·"작업 이력" 첫 줄, feature README "이력"의 `태스크 등록:` 기록까지 스크립트가 처리하고 생성 경로를 출력합니다.
  - `slug` 는 입력 유형별 처리(2)로 태스크명을 확정한 뒤에 넘깁니다. 스크립트가 만든 README에 제목·본문·`source_type`·`source` 를 채우는 것은 이 스킬의 몫입니다. (본문은 "작업 이력" 절 **위**에 작성해 "작업 이력"이 마지막 절로 남게 합니다)

## 2. 입력 유형별 처리

입력 `[요청]` 의 유형을 판별하고 아래 절차대로 처리합니다.

### 2-1. 일반 태스크명인 경우 (예: `s3-upload-module`)

- 태스크명: 입력받은 값을 그대로 사용합니다.
- `README.md`: **기본 frontmatter + 제목만** 가진 빈 README로 생성합니다. (`source_type: name`)

### 2-2. 슬랙 스레드 링크인 경우

1. `/jissp-slack-thread-reader` 스킬로 슬랙 메세지를 읽어옵니다.
2. `/jissp-content-to-requirements` 스킬에 **1번에서 수집한 Thread Dump를 전달하여** 요구사항으로 정리합니다. (슬랙 링크만 전달하지 않습니다. 요구사항 스킬은 수집을 수행하지 않습니다)
3. 요구사항 스킬이 반환한 **문서 본문**을 `README.md` 로 저장합니다.
4. 태스크명: 요구사항 스킬이 반환한 **핵심 키워드**를 사용합니다.

- frontmatter: `source_type: slack-thread`, `source` 에 슬랙 링크 기록

### 2-3. 프롬프트인 경우 (예: "상품 엑셀 sheet를 관리하는 공통 모듈을 만든다")

1. `/jissp-content-to-requirements` 스킬에 프롬프트를 전달하여 요구사항으로 정리합니다.
2. 요구사항 스킬이 반환한 **문서 본문**을 `README.md` 로 저장합니다.
3. 태스크명: 요구사항 스킬이 반환한 **핵심 키워드**를 사용합니다.

- frontmatter: `source_type: prompt`
- feature에서 프롬프트가 한두 문장으로 **태스크 범위만 정의**하는 경우(예: 위 예시), 요구사항 스킬을 거치지 않고 그 문장을 README "개요"에 그대로 적는 것을 우선 제안합니다. (범위 정의만 있는 짧은 입력을 PRD로 부풀리지 않기 위함)

> `/jissp-content-to-requirements` 는 **변환 전용** 스킬입니다. 파일을 저장하지 않고 문서 본문을 반환하므로, 태스크 디렉토리에 `README.md` 로 저장하는 것은 이 스킬의 몫입니다.

### 2-4. 기존 기획·설계 문서인 경우 (PRD·구조 문서·설계 문서 경로, `/jissp-planner` 인계 args)

`/jissp-planner` 를 태스크 없이 단독으로 사용해 `prds/`·`plans/` 에 만든 문서를 태스크로 가져오는 경우입니다. (태스크 모드 `--task` 로 작성한 문서는 이미 태스크 디렉토리에 있으므로 이 절차가 필요 없습니다)

#### 2-4-1. 주 문서 판별

전달된 문서 중 기획 흐름(PRD → 구조 문서 → 설계 문서)에서 **가장 뒤 단계의 문서**를 주 문서로 삼습니다. (우선순위: 설계 문서 > 구조 문서 > PRD 문서)

| 주 문서 | `source_type` | 판별 기준 |
|---|---|---|
| 설계 문서 | `architecture` | 파일명 `*-architecture.md` 또는 인계 args의 `설계 문서:` |
| 구조 문서 | `structure` | 파일명 `*-structure.md` 또는 인계 args의 `구조 문서:` |
| PRD 문서 | `prd` | 파일명 `*-prd.md` 또는 인계 args의 `PRD 문서:` |

- 파일명으로 판별되지 않으면 문서 내용을 읽고 유형을 사용자에게 확인합니다.

#### 2-4-2. 관련 문서 수집

1. **인계 args에 경로가 명시된 문서**는 그대로 사용합니다. (가장 우선)
2. 명시되지 않은 상위 문서는 주 문서 본문에서 찾습니다.
   - 설계 문서: §1 개요의 참조 PRD 문서 경로·구조 문서 경로
   - 구조 문서: 참조 PRD 문서 경로
3. 본문에도 없으면 **추측으로 채우지 않고** 해당 문서 없이 진행합니다.
   - 단, PRD·설계 문서 디렉토리에 파일명의 `[feature]` 가 같은 문서가 있으면 후보로 제시하고, 사용자가 고른 경우에만 묶음에 넣습니다.
   - 디렉토리는 `[Jissp 문서]/rules/jissp-planner/config.md`(jissp-planner 프로젝트 설정)가 있으면 그 파일의 `PRD 문서`·`설계 문서` 세부 디렉토리를, 없으면 기본값 `prds`·`plans` 를 사용합니다.
4. 수집한 각 경로가 실제로 존재하는지 확인합니다. 없는 경로는 목록에서 빼고 2-4-3 확인 시 함께 알립니다.

#### 2-4-3. 등록 전 확인

아래 내용을 한 번에 제시하고 사용자 확인을 받은 뒤 생성합니다.

- 대상 feature, 태스크 디렉토리명, 초기 상태 (`wait` 기본 / `backlog` 선택 가능)
- **이동할** 문서 묶음 (원본 경로 → 태스크 내 파일명)
  - 문서는 복사하지 않고 **이동(`mv`)** 합니다. 이동 후에는 태스크 디렉토리의 문서가 유일한 원본이 되며, `prds/`·`plans/` 에는 남지 않습니다. (사본을 두면 원본과 어긋나는 문제가 다시 생기므로 복사는 하지 않습니다)
- 찾지 못해 제외된 문서 (있는 경우)
- **중복 등록 확인**: `features/**/README.md` 중 frontmatter `source` 가 이번 주 문서와 같은 파일(파일명 기준)인 태스크가 있으면 함께 보여 주고, 새로 등록할지 / 취소할지 선택받습니다.

#### 2-4-4. 이동 및 README 작성

- 관련 문서를 아래 고정 파일명으로 이동합니다.

  | 문서 | 태스크 내 파일명 |
  |---|---|
  | PRD 문서 | `prd.md` |
  | 구조 문서 | `module-structure.md` |
  | 설계 문서 | `architecture.md` |

- 이동한 문서 본문 안에서 서로를 가리키는 경로(예: 설계 문서 §1의 PRD·구조 문서 경로)는 **태스크 내 파일명으로 고칩니다.** (이동 후 끊어진 참조를 남기지 않기 위함)
- 태스크명: 주 문서 파일명의 `[feature]` 부분(`[YYYYMMDD_HHmmss]_` 프리픽스와 `-[문서 유형]` 접미사를 뗀 값)을 사용합니다.
- frontmatter: `source_type` 은 2-4-1의 값, `source` 에는 **이동 전 주 문서 경로**를 기록합니다. (이력 추적용)
- `README.md` 본문은 주 문서를 기반으로 README 스키마에 맞춰 작성합니다.
  - 개요·요구사항은 요약만 적고 상세는 태스크 문서에 위임합니다. (계약·구조를 README에 다시 옮겨 적지 않습니다)
  - 인계 args에 `작업 프롬프트:` 가 있으면(PRD 없이 프롬프트로 설계한 경우) 그 내용을 요구사항의 출처로 개요에 요약해 적습니다.
  - "작업 이력"에 이동한 문서와 이동 전 경로를 적습니다.

## 3. feature README 갱신

- feature면 feature README "태스크 목록" 표에 새 행을 추가합니다. ("이력"의 `태스크 등록:` 줄은 `tm.sh new-task` 가 이미 남깁니다. maintenance는 표가 없으므로 생략)

## 4. 등록 후 다음 단계 (필수)

등록이 완료되면 생성된 태스크(feature·경로·상태·태스크명)를 보고하고, `AskUserQuestion` 으로 다음 단계를 선택받습니다. 선택한 planner 모드는 **이 스킬이 `--task` 인자를 붙여 대신 호출**합니다. (사용자가 `--task` 를 직접 입력하지 않게 하기 위함)

| 태스크 상태 | 선택지 |
|---|---|
| `architecture.md` 가 있음 | 1. 태스크 실행 (`run`) · 2. 나중에 |
| 개요·요구사항 본문은 있으나 `architecture.md` 없음 | 1. 바로 실행 (`run`, 설계 없이 구현) · 2. PRD 작성 (draft) · 3. 구조 설계 (structure) · 4. 설계 문서 작성 (architecture) · 5. 나중에 |
| 그 외 (작업 문서가 없는 상태) | 1. PRD 작성 (draft, 권장) · 2. 구조 설계 (structure) · 3. 설계 문서 작성 (architecture) · 4. 나중에 |

- 권장안: [SKILL](../SKILL.claude.md) 「작업 요청 (등록 + 실행)」 으로 들어온 경우는 "바로 실행", 그 밖에는 "PRD 작성" 입니다. 단 요구사항이 여러 모듈에 걸치는 큰 작업이면 "바로 실행" 대신 설계 문서 작성을 권장합니다.

- planner 호출 형식: `/jissp-planner [draft|structure|architecture] --task [feature]/[태스크 디렉토리명]`
  - 모드 args는 비워 둡니다. planner가 태스크 모드에서 입력(README·prd.md 등)을 스스로 정합니다.
  - PRD 작성(draft)에서 요구사항은 planner가 텍스트로 묻고 사용자가 직접 입력합니다. 이 스킬이 요구사항을 선택지로 미리 만들어 넘기지 않습니다.
- "나중에"를 고르면 아래 명령을 안내하고 종료합니다.
  - 문서 작성: `/jissp-planner [mode] --task [feature]/[NN]` (번호만 적어도 됨)
  - 실행: `/jissp-task-manager run [feature] [NN]`
- feature이고 번호가 작은 태스크 중 이번 태스크와 관련 있어 보이는 것이 있으면, README "선행 태스크" 절에 적을지 함께 물어봅니다. (planner·run이 컨텍스트로 읽는 근거가 됩니다)
