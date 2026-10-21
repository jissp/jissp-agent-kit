# TODO 목록 조회 절차 (list)

> 선행: [structure.md](structure.md)의 저장 구조·상태 모델을 따릅니다.

사용법: `/jissp-todo-manager list [범위]`

## 범위

| 범위 | 대상 | 스캔 패턴 |
|---|---|---|
| (생략) | **현재 처리해야 할 TODO** (`status: todo`) — 기본값 | `todos/*/README.md` |
| `assigned` | 프로젝트로 할당 완료된 TODO | `todos/assigned/*/README.md` |
| `all` | 전체 (활성 + assigned) | 위 패턴 전부 |

- 자연어 요청(예: "지금 뭐 해야 하지" → 기본, "넘긴 거 보여줘" → `assigned`, "전체 목록" → `all`)도 동일 범위로 해석합니다.

## 절차

1. 해당 범위의 `README.md` frontmatter를 스캔합니다.
2. **`created_at` 오름차순**(오래된 것부터)으로 정렬해 표로 보여줍니다. 오래 방치된 업무가 위에 오도록 하기 위함입니다.
3. 표 컬럼

   | 범위 | 컬럼 |
   |---|---|
   | 활성 | `#`(순번), `name`, `doc_type`, `source_type`, `created_at`, 제목(README 본문의 H1) |
   | assigned | `#`, `name`, `assigned_project`, `created_at`, `updated_at` |
   | all | 위 두 표를 **활성 → assigned** 순으로 나누어 출력 |

4. 표 아래에 총 건수를 한 줄로 덧붙입니다. (예: `활성 TODO 7건`)
5. 범위 지정이 없으면 활성 TODO를 기본으로 보여주고, `assigned` / `all` 조회가 가능함을 안내합니다.

## 결과가 없는 경우

- 활성 TODO가 0건이면 "현재 처리해야 할 TODO가 없습니다"라고 알리고, 등록 방법(`/jissp-todo-manager add [입력]`)을 한 줄로 안내합니다.
- TODO 루트 디렉토리 자체가 없으면 아직 등록된 TODO가 없는 상태이므로, 동일하게 안내합니다. (조회만으로 디렉토리를 만들지는 않습니다)

## 개별 TODO 상세 보기

사용자가 특정 TODO의 내용을 보고 싶어 하면([structure.md](structure.md)의 탐색 순서로 대상 특정), 해당 `README.md`를 읽어 제목·출처·본문 요약을 보여줍니다. 원본 링크(`source`)가 있으면 함께 제시합니다.
