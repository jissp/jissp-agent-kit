# 태스크 실행 절차 (run)

> 선행: [structure.md](structure.md)의 저장 구조·태스크 컨텍스트를 따릅니다.
> 상태 전이(frontmatter 갱신·위치 처리·feature README 갱신)의 세부 처리는 [status.md](status.md)를 따릅니다.

사용법: `/jissp-task-manager run [feature] [task] [--impl agent|skill|inline]`

## 1. task 작업 대상 선정

### feature와 task를 지정한 경우

- `tm.sh find [task] [feature]` 로 찾습니다. (structure.md의 탐색 순서, `[task]` 는 디렉토리명·번호·slug 일부 허용) 여러 줄이 나오면 후보로 제시합니다.

### feature만 지정한 경우 (feature)

- `tm.sh tasks [feature]` 결과에서 **번호가 가장 작은 `wait` 태스크**를 다음 태스크로 제안하고 확인받습니다.
- `processing` 태스크가 이미 있으면 그 태스크를 먼저 이어서 할지 함께 묻습니다.
- `wait` 태스크가 없으면 새 태스크 등록(`add [feature] ...`)을 안내하고 종료합니다.

### 아무것도 지정하지 않은 경우

- `tm.sh tasks` (활성) 결과를 feature별로 보여 주고 선택받습니다.

### 실행 전 확인

- **완료 feature**: 대상 태스크가 완료 feature(`_completed/`)에 있으면 실행하지 않고 재오픈(`feature status [slug] processing`)을 안내합니다.
- **feature 보류**: 대상 feature가 `holding` 이면 보류 중임을 알리고 feature 재개(`processing`) 여부를 먼저 확인합니다.
- **순서 확인** (feature): 번호가 더 작은 태스크 중 `completed` 가 아닌 것이 있으면 목록을 보여 주고 그대로 진행할지 확인합니다. (막지는 않습니다)
- **작업 문서 가드**: 대상 태스크가 structure.md의 **작업 문서가 없는 상태**(개요·요구사항 본문도, `prd.md`·`module-structure.md`·`architecture.md` 도 없음)면 실행하지 않습니다.
  - 상태는 그대로 유지합니다. (`processing` 전이 금지)
  - `AskUserQuestion` 으로 작업 문서 작성을 제안합니다: 1. PRD 작성 (draft) · 2. 구조 설계 (structure) · 3. 설계 문서 작성 (architecture) · 4. 종료
  - 선택한 모드는 `/jissp-planner [mode] --task [feature]/[태스크 디렉토리명]` 으로 이 스킬이 대신 호출합니다. 문서 작성이 끝나면 다시 실행할지 묻습니다.
- **세션 확인**: 이 세션에서 run 전에 다른 작업(PRD·구조·설계 문서 작성, 리뷰, 다른 태스크 run 등)을 진행했다면 새 세션에서 시작할 것을 권고합니다. run 은 태스크 컨텍스트를 문서에서 다시 읽으므로 앞선 대화가 필요 없고, 이어서 진행하면 그 대화가 이후 모든 호출에 실려 비용만 커집니다.
  - `AskUserQuestion` 으로 묻습니다: 1. 새 세션에서 시작 (권장) — `/clear` 후 `/jissp-task-manager run [feature] [task]` 를 안내하고 종료 · 2. 이 세션에서 이어서 진행
  - 대화에서 합의했지만 태스크 문서에 반영되지 않은 결정이 있으면, 1번을 고르기 전에 문서에 반영할 수 있도록 그 항목을 함께 알립니다.
  - run 이 이 세션의 첫 작업이거나, 직전 안내(planner 다음 작업 안내 등)에서 사용자가 이미 이어서 진행을 고른 경우에는 묻지 않습니다.

## 2. task 실행

1. **작업 착수 직전**에 `tm.sh set-status [태스크 경로] processing` 으로 상태를 바꿉니다. (status.md 절차 — maintenance의 상태 디렉토리에 있던 태스크는 스크립트가 `maintenance/tasks/` 로 옮기므로, 출력된 **새 경로**를 이후 작업에 사용합니다)
   - 착수 전에 전이해 두어야 작업이 중단되더라도 상태가 실제 진행 상황을 반영합니다.
2. structure.md의 **태스크 컨텍스트**를 확보합니다. (feature README → feature `docs/` → 선행 태스크 문서 → 태스크 자신의 문서)
3. task의 지시문서(`README.md`)를 **준수**하여 작업을 진행합니다.
   - 태스크 문서끼리 내용이 어긋나면 `architecture.md`(계약) > `module-structure.md`(구조) > `prd.md`(요구사항) 순으로 따르되, 어긋난 지점을 사용자에게 알립니다. (하위 단계 문서가 상위 문서를 근거로 확정된 결정이기 때문)
   - 선행 태스크 결과물(공통 모듈 등)은 **수정하지 않고 사용하는 것이 원칙**입니다. 수정이 필요하면 임의로 고치지 말고 사용자에게 확인합니다. (선행 태스크의 완료 범위를 흔들지 않기 위함)
   - 지시문서와 실제 상황이 어긋나는 부분을 발견하면 임의로 진행하지 말고 사용자에게 확인합니다.
   - `architecture.md` 가 있으면 [implement.md](implement.md)를 읽고, 지정된 구현 방식(`--impl agent|skill|inline`, 생략 시 [config.md](../config.md)의 `default_impl`)으로 구현합니다.
     - `inline` 은 `~/jissp-agent-kit/skills/planner-execute/guideline.md` 를 `Read` 로 읽고, 그 「설계 문서 해석」·「구현 단위 규약」·「구현 순서 규약」·「테스트 코드 작성 정책」·「주석 원칙」 을 따라 메인 세션에서 직접 구현합니다.
     - 어느 방식이든 설계 문서 갱신은 guideline의 「설계 문서 갱신 정책」 대신 아래 "완료 전·후 안내" 절차를 따릅니다.
   - `architecture.md` 가 없으면 [implement.md](implement.md) 4장 「설계 없는 태스크 위임」 을 따릅니다. `agent` 방식이면 `jissp-implementer` 에 위임하고, run 메인 세션은 코드를 직접 고치지 않습니다. (Bash 로 파일을 고치는 것도 포함)
   - 진행 내역·결정 사항은 README.md의 "작업 이력"에 기록합니다.
4. 구현이 끝나면 아래 「변경 파일 스테이징」 을 따라 바뀐 파일을 스테이징합니다.
5. 작업이 완료되면 task를 완료처리합니다. (아래 절차)

### 변경 파일 스테이징

코드를 고치는 작업이 끝날 때마다 run 메인 세션이 바뀐 파일을 스테이징합니다. 사용자가 매번 "스테이지 처리해줘" 를 요청하지 않아도 되도록, 그리고 커밋 대상을 이번 태스크 작업분으로 좁혀 두기 위함입니다.

- **시점**: 구현의 모든 단계가 끝난 뒤(병렬 그룹은 합류·검증 후) 1회, 그리고 3장 검토 루프에서 코드를 고친 작업(보완·가독성 리팩토링·추가 명령)이 끝날 때마다 1회. 단계가 `중단` 으로 끝났으면 사용자 결정 후 재개해 완료될 때까지 스테이징하지 않습니다.
- **대상**: 「리뷰 대상 파일 목록」 과 같은 방식으로 모은, 이번 작업에서 바뀐 파일만. `git add` 에 **개별 파일 경로**를 지정하고, `git add .`·`-A` 는 쓰지 않습니다. 삭제된 파일도 경로를 지정해 스테이징합니다.
- **제외**: Jissp 문서(`0-jissp-docs` 하위), 이번 작업과 무관한 로컬 변경. 스테이징 전에 `0-jissp-docs` 하위 파일이 이미 스테이지에 있으면 스테이징하지 않고 사용자에게 알립니다.
- 스테이징한 파일 목록을 결과 보고에 함께 적습니다. 커밋은 하지 않습니다.

## 3. task의 완료 처리

task의 처리가 완료된 경우 **사용자에게 검토를 받고**, 문제가 없다면 `completed` 로 변경합니다. (status.md 절차 — feature는 이동 없이 status와 feature README 표 갱신, maintenance는 `tasks/completed/` 이동)

### 사용자의 검토 (필수)

작업이 완료된 task는 작업 결과를 요약 보고한 뒤, 완료처리할 것인지 보완작업을 진행할 것인지 아래 선택지로 검토·승인을 받습니다.

1. **`jissp-gap-validator` 에이전트**: 기준 문서(task의 README.md·prd.md·module-structure.md·architecture.md)와 작업 산출물 간의 정합성을 교차 검증하여 누락·미비 항목을 갭 리포트 파일로 받습니다.
   - Gemini(agy) 환경에서는 `invoke_subagent` 로 `TypeName: "jissp-gap-validator"` 를 띄웁니다.
   - 호출 시 다음을 전달합니다: `review_target`(이번 작업의 산출물 경로), `reference_docs`(task의 README.md와 존재하는 태스크 문서 prd.md·module-structure.md·architecture.md), `focus`("지시문서의 요구사항이 산출물에 모두 반영되었는지"), `report_path`(`[태스크 디렉토리]/validation-[N]차.md`), `iteration`(회차). 2회차 이상이면 `previous_report_path` 도 함께 전달합니다.
   - 이 에이전트는 **리포트 파일과 경로·요약 수치만** 반환합니다. 산출물과 지시문서는 수정하지 않으므로, 보완 작업은 이 선택지로 돌아온 뒤 사용자 승인을 받아 진행합니다.
2. **`/jissp-reviewer`**: 작업 결과를 대상으로 코드 리뷰를 진행합니다.
   - 아래 「리뷰 대상 파일 목록」을 대상으로 넘겨 **호출 측 대상 목록 모드(C)** 로 호출합니다. 스테이지 여부와 무관하게 로컬 변경분을 리뷰하므로 사전 `git add` 가 필요 없습니다.
3. **`/jissp-readability-refactoring`**: 작업 결과를 가독성 위주로 리팩토링을 진행합니다.
   - 아래 「리뷰 대상 파일 목록」을 **명시된 파일(모드 B)** 로 넘겨 호출합니다.
4. **추가 명령(프롬프트)**: 선택 시 사용자에게 작업 요청 프롬프트를 입력받고 추가 작업을 진행합니다.
5. **완료처리**: `completed` 전이 후 종료합니다.

- 1~4를 수행한 경우, 해당 작업이 끝나면 다시 이 검토 선택지로 돌아와 재검토를 받습니다. (5를 선택할 때까지 반복)
- 1·2·4에서 승인된 코드 보완은 [implement.md](implement.md) "보완 위임" 을 따라 구현 방식(`--impl` 또는 `config.md` 의 `default_impl`)대로 진행합니다.
- 1~4에서 코드가 바뀌었으면 검토 선택지로 돌아오기 전에 「변경 파일 스테이징」 을 따릅니다.
- 검토 중 진행한 보완 내역도 README.md의 "작업 이력"에 기록합니다.

#### 리뷰 대상 파일 목록 (선택지 2·3)

- 이번 run에서 구현·보완으로 바뀐 파일을 모읍니다. `agent`·`skill` 방식은 각 반환의 「변경 파일」을, `inline` 방식은 메인 세션이 직접 수정한 파일을 합칩니다.
- 새 세션에서 검토를 이어가는 등 위 정보가 없으면 `git status --short` 의 로컬 변경 파일로 후보를 만들고, 목록을 보여준 뒤 이번 태스크 범위가 맞는지 사용자에게 확인받습니다.
- Jissp 문서(`0-jissp-docs` 하위)는 목록에서 제외합니다.
- 리뷰를 위해 따로 `git add` 하지 않습니다. 스테이징은 구현이 끝날 때 「변경 파일 스테이징」 에서 이미 처리합니다.

### 완료 전·후 안내 (feature)

- 구현 중 계약(인터페이스·스키마)이 `architecture.md` 와 달라졌다면, 후속 태스크가 이 문서를 선행 컨텍스트로 읽으므로 `architecture.md` 를 실제 결과에 맞게 갱신할지 묻습니다.
  - 갱신을 선택하면 달라진 계약을 변경 요청으로 정리해 `/jissp-planner architecture --task [feature]/[task] revise [변경 요청]` 을 이 스킬이 대신 호출합니다. (**완료처리 전에** 진행합니다. 완료 후에는 planner가 문서 수정 시 경고하기 때문)
- 다음 단계를 안내합니다.
  - 다음 `wait` 태스크가 있으면: 새 세션(`/clear` 후)에서 `/jissp-task-manager run [feature]`
  - 없으면: 다음 태스크 등록(`add [feature] ...`) 또는 모든 태스크가 완료된 경우 feature 완료(`feature status [feature] completed`)
