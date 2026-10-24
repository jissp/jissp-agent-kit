---
skill: planner-execute
source: ~/jissp-agent-kit/skills/planner-execute
generated_at: 2026-10-21 16:58:23
---

### 명령어

| 용도 | 명령어 |
|---|---|
| 설계 문서 기반 구현 | `/planner-execute [설계 문서 경로]` — 설계 문서의 계약(§4·§5)을 지키며 실제 코드베이스에 구현 |
| 범위·요청 덧붙여 구현 | `/planner-execute [설계 문서 경로] [추가 요청]` — 예: 진행할 §12 단계, 테스트 작성 요청 |

- 실행 모델은 Sonnet 입니다. 설계 문서 §12 에 `Opus (opus-required)` 로 지정된 단계는 구현하지 않고 멈추며 Opus 전환 여부를 묻습니다. (명시적으로 Sonnet 진행을 지시하면 진행)
- 구현이 끝나면 빌드·기존 테스트를 실행하고 결과를 보고한 뒤 종료합니다.
- 신규 테스트 코드는 기본적으로 작성하지 않습니다. 필요하면 착수할 때 함께 요청하세요. (신규 개발건이면 보고에 "테스트 작성이 후속 작업" 이라고 한 줄 고지)
- 설계 문서 Part B(§11 파일 목록·§12 작업 순서)는 고치지 않습니다. Part A 계약을 바꿔야 하면 보고 후 승인을 받고 `/jissp-planner architecture revise` 로 갱신합니다.

### 권장 흐름

- `/jissp-planner architecture` 로 설계 문서 작성 → (선택) `/jissp-architecture-preview [설계 문서]` → `/planner-execute [설계 문서]`
- 태스크 단위로 진행 중이면 `/jissp-task-manager` 의 run 을 사용합니다. (이 스킬은 직접 구현 요청용)

### 인자 참고

- `[설계 문서 경로]`: `/jissp-planner architecture` 로 작성한 설계 문서(architecture.md). 계약·작업 순서를 이 문서에서 읽습니다.
- `[추가 요청]`: 생략 가능. 테스트 작성을 원하면 여기서 명시합니다. (예외적으로 프로젝트 규약·CI 가 테스트를 요구하면 요청 없이도 작성)

### 예시

```
/planner-execute 0-jissp-docs/plans/20261021_101500_order-csv-export.md
/planner-execute 0-jissp-docs/plans/20261021_101500_order-csv-export.md §12 1~3단계만 진행
/planner-execute 0-jissp-docs/plans/20261021_101500_order-csv-export.md 테스트 코드도 같이 작성해줘
```
