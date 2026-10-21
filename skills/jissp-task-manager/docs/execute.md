# 태스크 실행 절차 (run)

> 선행: [structure.md](structure.md)의 저장 구조·태스크 컨텍스트를 따릅니다.
> 상태 전이(frontmatter 갱신·위치 처리·프로젝트 README 갱신)의 세부 처리는 [status.md](status.md)를 따릅니다.

사용법: `/jissp-task-manager run [project] [task] [--impl agent|skill|inline]`

## 1. task 작업 대상 선정

### project와 task를 지정한 경우

- `tm.sh find [task] [project]` 로 찾습니다. (structure.md의 탐색 순서, `[task]` 는 디렉토리명·번호·slug 일부 허용) 여러 줄이 나오면 후보로 제시합니다.

### project만 지정한 경우 (feature 프로젝트)

- `tm.sh tasks [project]` 결과에서 **번호가 가장 작은 `wait` 태스크**를 다음 태스크로 제안하고 확인받습니다.
- `processing` 태스크가 이미 있으면 그 태스크를 먼저 이어서 할지 함께 묻습니다.
- `wait` 태스크가 없으면 새 태스크 등록(`add [project] ...`)을 안내하고 종료합니다.

### 아무것도 지정하지 않은 경우

- `tm.sh tasks` (활성) 결과를 프로젝트별로 보여 주고 선택받습니다.

### 실행 전 확인

- **완료 프로젝트**: 대상 태스크가 완료 프로젝트(`_completed/`)에 있으면 실행하지 않고 재오픈(`project status [slug] processing`)을 안내합니다.
- **프로젝트 보류**: 대상 프로젝트가 `holding` 이면 보류 중임을 알리고 프로젝트 재개(`processing`) 여부를 먼저 확인합니다.
- **순서 확인** (feature 프로젝트): 번호가 더 작은 태스크 중 `completed` 가 아닌 것이 있으면 목록을 보여 주고 그대로 진행할지 확인합니다. (막지는 않습니다)
- **작업 문서 가드**: 대상 태스크가 structure.md의 **작업 문서가 없는 상태**(개요·요구사항 본문도, `prd.md`·`module-structure.md`·`architecture.md` 도 없음)면 실행하지 않습니다.
  - 상태는 그대로 유지합니다. (`processing` 전이 금지)
  - `AskUserQuestion` 으로 작업 문서 작성을 제안합니다: 1. PRD 작성 (draft) · 2. 구조 설계 (structure) · 3. 설계 문서 작성 (architecture) · 4. 종료
  - 선택한 모드는 `/jissp-planner [mode] --task [project]/[태스크 디렉토리명]` 으로 이 스킬이 대신 호출합니다. 문서 작성이 끝나면 다시 실행할지 묻습니다.

## 2. task 실행

1. **작업 착수 직전**에 `tm.sh set-status [태스크 경로] processing` 으로 상태를 바꿉니다. (status.md 절차 — maintenance의 상태 디렉토리에 있던 태스크는 스크립트가 `maintenance/tasks/` 로 옮기므로, 출력된 **새 경로**를 이후 작업에 사용합니다)
   - 착수 전에 전이해 두어야 작업이 중단되더라도 상태가 실제 진행 상황을 반영합니다.
2. structure.md의 **태스크 컨텍스트**를 확보합니다. (프로젝트 README → 프로젝트 `docs/` → 선행 태스크 문서 → 태스크 자신의 문서)
3. task의 지시문서(`README.md`)를 **준수**하여 작업을 진행합니다.
   - 태스크 문서끼리 내용이 어긋나면 `architecture.md`(계약) > `module-structure.md`(구조) > `prd.md`(요구사항) 순으로 따르되, 어긋난 지점을 사용자에게 알립니다. (하위 단계 문서가 상위 문서를 근거로 확정된 결정이기 때문)
   - 선행 태스크 결과물(공통 모듈 등)은 **수정하지 않고 사용하는 것이 원칙**입니다. 수정이 필요하면 임의로 고치지 말고 사용자에게 확인합니다. (선행 태스크의 완료 범위를 흔들지 않기 위함)
   - 지시문서와 실제 상황이 어긋나는 부분을 발견하면 임의로 진행하지 말고 사용자에게 확인합니다.
   - `architecture.md` 가 있으면 [implement.md](implement.md)를 읽고, 지정된 구현 방식(`--impl agent|skill|inline`, 생략 시 [config.md](../config.md)의 `default_impl`)으로 구현합니다.
     - `inline` 은 `~/jissp-agent-kit/skills/planner-execute/guideline.md` 를 `Read` 로 읽고, 그 「설계 문서 해석」·「구현 단위 규약」·「구현 순서 규약」·「테스트 코드 작성 정책」·「주석 원칙」 을 따라 메인 세션에서 직접 구현합니다.
     - 어느 방식이든 설계 문서 갱신은 guideline의 「설계 문서 갱신 정책」 대신 아래 "완료 전·후 안내" 절차를 따릅니다.
   - 진행 내역·결정 사항은 README.md의 "작업 이력"에 기록합니다.
4. 작업이 완료되면 task를 완료처리합니다. (아래 절차)

## 3. task의 완료 처리

task의 처리가 완료된 경우 **사용자에게 검토를 받고**, 문제가 없다면 `completed` 로 변경합니다. (status.md 절차 — feature 프로젝트는 이동 없이 status와 프로젝트 README 표 갱신, maintenance는 `tasks/completed/` 이동)

### 사용자의 검토 (필수)

작업이 완료된 task는 작업 결과를 요약 보고한 뒤, 완료처리할 것인지 보완작업을 진행할 것인지 아래 선택지로 검토·승인을 받습니다.

1. **`jissp-gap-validator` 에이전트**: 기준 문서(task의 README.md·prd.md·module-structure.md·architecture.md)와 작업 산출물 간의 정합성을 교차 검증하여 누락·미비 항목을 갭 리포트 파일로 받습니다.
   - 호출 시 다음을 전달합니다: `review_target`(이번 작업의 산출물 경로), `reference_docs`(task의 README.md와 존재하는 태스크 문서 prd.md·module-structure.md·architecture.md), `focus`("지시문서의 요구사항이 산출물에 모두 반영되었는지"), `report_path`(`[태스크 디렉토리]/validation-[N]차.md`), `iteration`(회차). 2회차 이상이면 `previous_report_path` 도 함께 전달합니다.
   - 이 에이전트는 **리포트 파일과 경로·요약 수치만** 반환합니다. 산출물과 지시문서는 수정하지 않으므로, 보완 작업은 이 선택지로 돌아온 뒤 사용자 승인을 받아 진행합니다.
2. **`/jissp-reviewer`**: 작업 결과를 대상으로 코드 리뷰를 진행합니다.
3. **`/jissp-readability-refactoring`**: 작업 결과를 가독성 위주로 리팩토링을 진행합니다.
4. **추가 명령(프롬프트)**: 선택 시 사용자에게 작업 요청 프롬프트를 입력받고 추가 작업을 진행합니다.
5. **완료처리**: `completed` 전이 후 종료합니다.

- 1~4를 수행한 경우, 해당 작업이 끝나면 다시 이 검토 선택지로 돌아와 재검토를 받습니다. (5를 선택할 때까지 반복)
- 1·2·4에서 승인된 코드 보완은 [implement.md](implement.md) "보완 위임" 을 따라 구현 방식(`--impl` 또는 `config.md` 의 `default_impl`)대로 진행합니다.
- 검토 중 진행한 보완 내역도 README.md의 "작업 이력"에 기록합니다.

### 완료 전·후 안내 (feature 프로젝트)

- 구현 중 계약(인터페이스·스키마)이 `architecture.md` 와 달라졌다면, 후속 태스크가 이 문서를 선행 컨텍스트로 읽으므로 `architecture.md` 를 실제 결과에 맞게 갱신할지 묻습니다.
  - 갱신을 선택하면 달라진 계약을 변경 요청으로 정리해 `/jissp-planner architecture --task [project]/[task] revise [변경 요청]` 을 이 스킬이 대신 호출합니다. (**완료처리 전에** 진행합니다. 완료 후에는 planner가 문서 수정 시 경고하기 때문)
- 다음 단계를 안내합니다.
  - 다음 `wait` 태스크가 있으면: `/jissp-task-manager run [project]`
  - 없으면: 다음 태스크 등록(`add [project] ...`) 또는 모든 태스크가 완료된 경우 프로젝트 완료(`project status [project] completed`)
