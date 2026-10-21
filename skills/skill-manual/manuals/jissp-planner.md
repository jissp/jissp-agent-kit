---
skill: jissp-planner
source: ~/jissp-agent-kit/skills/jissp-planner
generated_at: 2026-10-21 23:57:23
---

### 모드

| 용도 | 명령어 |
|---|---|
| 모드 선택 | `/jissp-planner` — 인자 없이 호출하면 draft / structure / architecture / review 중 선택 |
| 플래너 초기화 | `/jissp-planner init` — 프로젝트 설정·설계 Rule·리뷰 설정 생성 |
| PRD 초안 | `/jissp-planner draft [아이디어·개요]` — alias: `prd` |
| 구조 설계 | `/jissp-planner structure [PRD 경로 \| 작업 프롬프트]` |
| 구조 문서 수정 | `/jissp-planner structure revise [구조 문서 경로] [변경 요청]` |
| 설계 문서 작성 | `/jissp-planner architecture [PRD 경로 \| 작업 프롬프트]` |
| 설계 문서 수정 | `/jissp-planner architecture revise [설계 문서 경로] [변경 요청]` |
| 문서·프롬프트 검토 | `/jissp-planner review [문서 경로 1개 이상 \| 프롬프트 텍스트]` |

- 권장 흐름: `init` (최초 1회) → `draft` → `structure` (신규 모듈·큰 구조 변경 시) → `architecture` → `review`
- 각 모드 완료 후 다음 작업 안내에서 고르면 스킬을 다시 호출하지 않고 이어서 진행합니다.
- `architecture` 는 서로 독립인 모듈이 여럿이면 §12 작업 순서를 병렬 그룹(`2-A`, `2-B`)으로 나눠 작성합니다. 그룹은 `/jissp-task-manager run` 의 `agent` 방식에서 동시에 착수됩니다.

### 태스크 모드 (`--task`)

`jissp-task-manager` 의 태스크 디렉토리에 문서를 직접 작성합니다. init 을 제외한 모든 모드에 붙일 수 있습니다.

| 용도 | 명령어 |
|---|---|
| 태스크 PRD | `/jissp-planner draft --task [feature]/[task]` → `prd.md` |
| 태스크 구조 문서 | `/jissp-planner structure --task [feature]/[task]` → `module-structure.md` |
| 태스크 설계 문서 | `/jissp-planner architecture --task [feature]/[task]` → `architecture.md` |
| 태스크 설계 수정 | `/jissp-planner architecture --task [feature]/[task] revise [변경 요청]` — 문서 경로 생략 가능 |
| 태스크 문서 검토 | `/jissp-planner review --task [feature]/[task]` — 태스크 문서 전부 검토 |

- `[task]`: 디렉토리명 전체 · 번호(`03`) · slug 일부
- 입력을 생략하면 태스크의 `prd.md` 또는 `README.md` 를 입력으로 사용합니다.

### 설정 참고

- 문서 루트: `[프로젝트 루트]/0-jissp-docs` (PRD → `prds/`, 구조·설계 → `plans/`)
- 프로젝트 설정: `0-jissp-docs/rules/jissp-planner/config.md` — 문서 경로·파일명 규칙·추가 Rule·모듈 문서·설계 문서 예시
- 리뷰 설정: `0-jissp-docs/rules/jissp-planner/review-config.md` — review 모드 추가 관점·제외 항목·심각도 조정
- 설정 파일이 없는 곳에서 새 문서를 저장하려 하면 init 여부를 먼저 묻습니다.

### 예시

```
/jissp-planner init
/jissp-planner draft 상품 목록 엑셀 다운로드
/jissp-planner architecture 0-jissp-docs/prds/20260923_143205_export-csv-prd.md
/jissp-planner architecture revise 0-jissp-docs/plans/20260923_150312_export-csv-architecture.md 응답 필드 추가
/jissp-planner review 0-jissp-docs/plans/20260923_150312_export-csv-architecture.md
/jissp-planner architecture --task product-excel/03
```
