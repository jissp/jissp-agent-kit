# 상태 관리 절차 (상태 변경 · 목록 조회)

> 선행: [structure.md](structure.md)의 태스크 상태 모델·위치 규칙·저장 구조를 따릅니다.
> 프로젝트 자체의 상태 변경은 [project.md](project.md)를 따릅니다.

## 상태 전이 규칙

```
 [등록]
   │ 기본                       백로그로 등록
   ▼                                ▼
 ┌──────┐      착수 결정       ┌─────────┐
 │ wait │ ◀─────────────────── │ backlog │
 └──┬───┘                      └─────────┘
    │ 실행 시작
    ▼
 ┌────────────┐    완료     ┌───────────┐
 │ processing │ ──────────▶ │ completed │
 └──────┬─────┘             └───────────┘
        │ 보류
        ▼
 ┌─────────┐    재개
 │ holding │ ──────────▶ wait
 └─────────┘
```

- 위 흐름이 일반적인 전이이며, 사용자가 명시적으로 요청하면 그 외 전이(예: `wait` → `holding`, `completed` → `wait` 재오픈)도 허용합니다.

## 상태 변경 절차

사용법: `/jissp-task-manager status [project] [task] [status]` (프로젝트 생략 가능 — structure.md의 탐색 순서)

1. **대상 특정**: structure.md의 탐색 방법으로 태스크를 찾습니다. 모호하면 후보를 제시하고 선택받습니다.
   - 대상이 완료 프로젝트(`_completed/`)의 태스크면 변경하지 않고 재오픈을 안내합니다. (structure.md "프로젝트 상태 모델")
2. **상태 변경 실행**: `tm.sh set-status [태스크 경로] [새 상태] "[사유]"` 를 실행합니다. 스크립트가 아래를 한 번에 처리하고 새 경로를 출력합니다.
   - frontmatter `status`·`updated_at` 갱신, `completed` 전이 시 `completed_at` 기록(되돌리면 비움)
   - "작업 이력"에 `이전 상태 → 새 상태 (사유)` 한 줄 추가
   - 완료 프로젝트의 태스크는 거부
3. **위치 처리 규칙** (스크립트가 수행 — 참고용)
   - **feature 프로젝트**: 디렉토리를 **이동하지 않습니다.**
   - **maintenance**: 새 상태의 위치가 현재 위치와 다르면 이동합니다. (이동 실패 시 status 원복)
     | 새 상태 | 이동 위치 |
     |---|---|
     | `wait`, `processing` | `maintenance/tasks/` |
     | `backlog` | `maintenance/tasks/backlog/` |
     | `completed` | `maintenance/tasks/completed/` |
     | `holding` | `maintenance/tasks/holding/` |
4. **프로젝트 README 갱신** (feature 프로젝트만, 스킬이 수행): "태스크 목록" 표의 해당 행 `상태`(완료 시 `완료일` = `completed_at` 날짜)를 갱신하고, `completed`·`holding` 전이는 "이력"에도 한 줄 남깁니다.
5. **결과 보고**: 전이 결과(상태, 경로)를 사용자에게 보고합니다.
   - feature 프로젝트에서 이번 전이로 **모든 태스크가 `completed`** 가 되었다면, 다음 태스크를 추가할지 / 프로젝트를 완료 처리할지(`project status [slug] completed`) 안내합니다. (태스크를 순차로 추가하는 방식이므로 자동 완료하지 않습니다)

## 목록 조회

사용법: `/jissp-task-manager list [project] [범위]`

| 입력 | 보여 주는 것 |
|---|---|
| (생략) | **전체 현황**: 진행 중 프로젝트별 요약 + 활성(`wait`/`processing`) 태스크 |
| `[project]` | 그 프로젝트의 태스크. feature 프로젝트는 **모든 상태를 번호 순**으로, maintenance는 활성만 |
| `[project] [범위]` | 그 프로젝트에서 범위에 해당하는 태스크 |
| `[범위]` | 모든 진행 중 프로젝트에서 범위에 해당하는 태스크 |

- `[범위]`: `backlog` / `holding` / `completed` / `all` (`all` = 모든 상태)
- 자연어 요청(예: "상품 엑셀 태스크 보여줘", "완료된 태스크", "전체 목록")도 동일하게 해석합니다.
- 완료 프로젝트(`_completed/`)는 기본 조회에서 제외합니다. 완료 프로젝트 이름을 직접 지정하면 조회합니다.
- 조회는 `tm.sh` 로 하고, 결과를 **그대로 목록으로** 보여 줍니다. (표로 재가공하지 않습니다. frontmatter가 SSOT)
  | 입력 | 실행 |
  |---|---|
  | (생략) | `tm.sh projects` + `tm.sh tasks` (활성) — "[프로젝트]", "[활성 태스크]" 두 묶음으로 나열 |
  | `[project]` | `tm.sh tasks [project]` |
  | `[project] [범위]` | `tm.sh tasks [project] [범위]` |
  | `[범위]` | `tm.sh tasks [범위]` |
- 태스크 한 줄: `경로  status  name  updated_at`
- 조회 후 다른 범위·프로젝트 조회가 가능함을 한 줄로 안내합니다.
