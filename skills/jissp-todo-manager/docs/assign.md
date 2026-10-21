# 프로젝트 할당 절차 (assign)

> 선행: [structure.md](structure.md)의 저장 구조·상태 모델을 따릅니다.

사용법: `/jissp-todo-manager assign [todo명] [프로젝트]`

TODO를 **대상 프로젝트의 태스크로 등록**하고, TODO 목록에서 제외하는 역할입니다.
`[프로젝트]`는 생략할 수 있으며, 생략하면 STEP 2에서 사용자에게 질문합니다.

## 흐름

```
STEP 1. 대상 TODO 특정
   │
STEP 2. 대상 프로젝트 확인 [게이트]  ← 인자로 주어졌으면 질문 없이 통과
   │
STEP 3. 프로젝트 경로 해석 (project-mapping-table.md)
   │
STEP 4. 태스크 생성 (대상 프로젝트의 maintenance)
   │
STEP 5. TODO를 assigned로 전환
   │
STEP 6. 결과 보고
```

## STEP 1. 대상 TODO 특정

- [structure.md](structure.md)의 탐색 순서(활성 → assigned)로 TODO를 찾습니다.
- 모호하면 후보 목록을 제시하고 선택받습니다.
- 이미 `assigned` 상태인 TODO면 **진행하지 말고** 기존 할당 정보(`assigned_project` / `assigned_task`)를 알린 뒤, 다시 할당할지 확인받습니다.
- `[todo명]`이 생략되었으면 활성 TODO 목록을 보여주고 어떤 것을 할당할지 선택받습니다.

## STEP 2. 대상 프로젝트 확인 [게이트]

인자로 프로젝트가 주어지지 않았으면 `AskUserQuestion` 도구로 질문합니다. **임의로 추측해 정하지 않습니다.**

- 질문: "이 TODO를 어느 프로젝트의 태스크로 등록할까요?"
- 선택지: TODO 내용(제목·본문·출처)으로 미루어 **가능성이 높은 프로젝트 2~3개**를 별칭과 함께 제시합니다. 판단 근거가 없으면 자주 쓰는 프로젝트를 제시하고, 그 외는 Other로 입력받습니다.
  - 선택지 `description`에는 해석될 절대 경로를 함께 적어 사용자가 확인할 수 있게 합니다.
- 사용자가 백로그로 넣기를 원하는지 알 수 있는 언급(예: "당장은 아니고")이 있으면 초기 상태를 `backlog`로 합니다. 기본은 `wait`입니다.

## STEP 3. 프로젝트 경로 해석

- **`~/jissp-agent-kit/project-mapping-table.md`를 Read로 읽어** 그 문서의 해석 절차대로 별칭 → 절대 경로를 산정합니다. 경로를 기억이나 추측으로 만들지 않습니다.
- 매핑 실패 / 경로 없음이면 해당 문서의 규칙대로 사유를 안내하고 **재입력을 받습니다.** 이 상태로 STEP 4를 진행하지 않습니다.
- 확정된 절대 경로와 프로젝트명(경로의 마지막 디렉토리명)을 이후 STEP에서 사용합니다.

## STEP 4. 태스크 생성

태스크 저장 규약은 `/jissp-task-manager` 스킬의 것을 그대로 따릅니다. **아래 문서를 Read로 읽어** 최신 규약을 확인한 뒤 생성합니다. (규약이 바뀌어도 어긋나지 않게 하기 위함이며, 추측으로 구조를 만들지 않습니다.)

- `~/jissp-agent-kit/skills/jissp-task-manager/docs/structure.md` — "태스크 README.md 스키마"·"스크립트 (`tm.sh`)" 절

TODO는 프로젝트(feature) 단위로 묶이지 않은 단발성 업무이므로 대상 프로젝트의 **`maintenance`** 에 등록합니다.

생성 절차:

1. 태스크 디렉토리를 `tm.sh` 로 생성합니다. 직접 `mkdir` 하지 않습니다. (`maintenance` 가 없으면 스크립트가 만듭니다)
   ```bash
   TM_DOCS="[프로젝트 경로]/0-jissp-docs" ~/jissp-agent-kit/skills/jissp-task-manager/scripts/tm.sh new-task maintenance [TODO name] [wait|backlog]
   ```
   - 출력된 경로(`[프로젝트 경로]/0-jissp-docs` 기준 상대 경로)가 생성된 태스크 디렉토리입니다. 실패(`error: ...`)하면 그대로 보고하고 중단합니다.
   - 스크립트가 frontmatter(`name`·`project`·`status`·`created_at`·`updated_at`)·제목·"작업 이력" 첫 줄을 채웁니다.
2. 생성된 태스크 `README.md` 를 아래와 같이 채웁니다.

   | 태스크 README 항목 | 값 |
   |---|---|
   | `source_type` | TODO의 `source_type` 승계 (`manual`은 `feature`로 기록) |
   | `source` | TODO의 `source` (없으면 TODO 디렉토리 절대 경로). 스크립트가 만들지 않는 필드이므로 `source_type` 아래에 추가합니다 |
   | 제목 | TODO의 제목 |
   | 본문 | TODO README의 본문을 **내용 그대로 이관** (`## 이력` 섹션은 제외). README 스키마의 "개요"·"요구사항" 절에 나눠 담을 수 있으면 나눠 담되 문장을 바꾸지 않습니다. "작업 이력" 절 **위**에 작성해 "작업 이력"이 마지막 절로 남게 합니다 |
   | 작업 이력 | 스크립트가 남긴 첫 줄 아래에 `- [시각] TODO에서 할당: [TODO 디렉토리명]` 추가 |

   - TODO 본문이 비어 있는(작업명만 등록된) 경우, 태스크 README에 본문을 추가하지 않습니다. 없는 요구사항을 지어내지 않습니다.
3. TODO에 `prd.md` 등 부속 문서가 있으면 태스크 디렉토리로 **복사**합니다. (원본은 STEP 5에서 `assigned/`로 함께 이동) 태스크 README의 "문서" 절에 복사한 문서를 적습니다.

## STEP 5. TODO를 assigned로 전환

frontmatter 갱신과 디렉토리 이동을 **함께** 처리합니다.

1. TODO `README.md` frontmatter를 갱신합니다.
   - `status: assigned`
   - `updated_at`: `date +"%Y-%m-%d %H:%M:%S"` 실제 시각
   - `assigned_project`: 프로젝트명 (예: `my-project`)
   - `assigned_task`: 생성된 태스크 디렉토리 **절대 경로** (`[프로젝트 경로]/0-jissp-docs/` + STEP 4에서 `tm.sh` 가 출력한 상대 경로)
2. `## 이력`에 `- [시각] [프로젝트명] 태스크로 할당 (todo → assigned)` 한 줄을 추가합니다.
3. TODO 디렉토리를 `todos/assigned/` 로 `mv` 합니다. (`assigned/`가 없으면 먼저 생성)
4. 이동에 실패하면 frontmatter를 원복하고 사용자에게 보고합니다. 태스크는 이미 생성되었으므로 그 경로도 함께 알립니다.

## STEP 6. 결과 보고

아래를 보고합니다.

- 생성된 태스크: 프로젝트명, 태스크 디렉토리 절대 경로, 초기 상태
- TODO 처리 결과: `assigned`로 전환되어 활성 목록에서 제외됨
- 다음 단계 안내:
  1. **`/jissp-planner [draft|structure|architecture] --task maintenance/[태스크 디렉토리명]`**: 태스크 문서(PRD·구조·설계) 작성
  2. **`/jissp-task-manager run maintenance [태스크 디렉토리명]`**: 해당 프로젝트에서 태스크 실행
  - feature 프로젝트로 옮기려면 `/jissp-task-manager` 에 "다른 프로젝트로 옮겨줘" 로 요청하도록 안내합니다.
  - 태스크 실행은 **대상 프로젝트 디렉토리 안에서** 해야 함을 함께 알립니다. (필요 시 `/add-project [별칭]`으로 디렉토리 추가)

## 주의

- 태스크 생성(STEP 4)과 TODO 전환(STEP 5)은 **한 흐름으로 끝까지** 수행합니다. 태스크만 만들고 TODO를 그대로 두면 같은 업무가 두 곳에 남습니다.
- 프로젝트 경로가 확정되기 전에는 어떤 파일도 생성하지 않습니다.
