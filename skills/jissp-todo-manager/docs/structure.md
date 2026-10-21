# 저장 구조 및 상태 모델 (공통 정의)

모든 역할(등록·조회·할당·삭제)이 공통으로 따르는 정의입니다.

## TODO 루트

- 경로: `~/jissp-agent-kit/databases/todos`
- **현재 작업 디렉토리와 무관하게 항상 이 경로**를 사용합니다. 어떤 프로젝트에서 호출하든 TODO는 이 저장소 한 곳에만 기록됩니다.
- 루트(및 하위 `assigned/`)가 없으면 사용 시점에 생성합니다.

## 디렉토리 구조

```
todos/
├── [YYYYMMDD_HHmmss]_[slug]/     # 활성 TODO (status: todo)
│   ├── README.md                 # TODO 메타데이터 + 본문 (필수)
│   └── prd.md                    # 분석 산출물이 길어 분리한 경우 (선택)
└── assigned/
    └── [YYYYMMDD_HHmmss]_[slug]/ # 프로젝트로 할당 완료된 TODO (status: assigned)
```

- TODO 디렉토리명: `[YYYYMMDD_HHmmss]_[slug]`
  - 시각은 반드시 `date +%Y%m%d_%H%M%S` 명령으로 실제 시각을 확인해 사용합니다. (임의 생성 금지)
  - `slug`: TODO 내용을 요약한 kebab-case 식별자
  - 예) `20260814_143205_admin-order-export-csv`

## 상태 모델 (2종)

| 상태 | 의미 | 디렉토리 위치 |
|---|---|---|
| `todo` | 처리해야 할 업무. 등록 시 기본 상태 | `todos/` 루트 |
| `assigned` | 프로젝트 태스크로 할당 완료 (TODO 목록에서 제외) | `todos/assigned/` |

- **SSOT**: 상태의 유일한 원본은 `README.md` frontmatter의 `status` 필드입니다. 디렉토리 위치는 상태의 파생 정보입니다.
- 상태 변경 시 `status` 갱신과 디렉토리 이동을 **함께** 처리해야 합니다.
- 할당된 TODO를 물리적으로 삭제하지 않고 `assigned/`에 남기는 이유는 **어떤 업무가 어느 프로젝트로 갔는지 추적**하기 위함입니다.

## README.md 스키마

```markdown
---
name: admin-order-export-csv
status: todo                 # todo | assigned
source_type: manual          # manual | slack-thread | notion
source: [원본 참조]           # 슬랙 링크, 노션 링크 등. 수동 등록이면 생략
doc_type: 업무 요청           # 요구사항 스킬이 반환한 문서 유형. 수동(작업명만) 등록이면 생략
created_at: 2026-08-14 14:32:05
updated_at: 2026-08-14 14:32:05
assigned_project:            # 할당 시 기록 (프로젝트명, 예: my-project)
assigned_task:               # 할당 시 기록 (생성된 태스크 디렉토리 절대 경로)
---

# [TODO 제목]

[요구사항 스킬이 반환한 문서 본문 — 개요·요구사항·작업 범위 등]
[수동 등록(작업명만)인 경우 본문 없이 제목만 둡니다.]

## 이력

- 2026-08-14 14:32:05 등록 (todo)
```

- `assigned_project` / `assigned_task`는 할당 전까지 **키 자체를 생략**합니다. 빈 값으로 남기지 않습니다.
- 본문은 `/jissp-content-to-requirements`가 반환한 문서 본문을 **그대로** 사용합니다. 이 스킬이 임의로 재요약하지 않습니다.

## TODO 탐색 방법 (공통)

특정 TODO를 찾거나 목록을 조회할 때는 아래 패턴으로 `README.md`의 frontmatter를 스캔합니다.

- 활성: `todos/*/README.md` (`assigned/` 는 깊이가 달라 자연히 제외됨)
- 할당됨: `todos/assigned/*/README.md`

### 특정 TODO 탐색 순서

`[todo명]`(디렉토리명 전체 또는 slug 일부)으로 특정 TODO를 찾을 때는 **활성 → assigned** 순으로 스캔합니다. 모든 역할이 이 순서를 따릅니다.

- 일치 후보가 여러 개면 후보 목록(디렉토리명 + `name` + `status`)을 제시하고 사용자에게 선택받습니다.
- 어디에서도 찾지 못하면 작업을 수행하지 않고 사용자에게 알립니다.
