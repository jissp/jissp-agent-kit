# feature 관리 절차 (feature)

> 선행: [structure.md](structure.md)의 저장 구조·feature 상태 모델·feature README 스키마를 따릅니다.

사용법: `/jissp-task-manager feature [add|list|status|rm] [args]`

| 하위 명령 | 사용법 | 역할 |
|---|---|---|
| `add` | `feature add [slug] [설명]` | feature 생성 |
| `list` | `feature list [all]` | feature 목록 조회 (`all`: 완료 feature 포함) |
| `status` | `feature status [slug] [processing\|holding\|completed]` | feature 상태 변경 |
| `rm` | `feature rm [slug]` | feature 삭제 → [delete.md](delete.md)의 feature 삭제 절차 |

- 자연어 요청도 동일하게 라우팅합니다. (예: "상품 엑셀 기능 feature 만들어줘" → `add`, "feature 목록" → `list`, "이 feature 끝났어" → `status completed`)

## 1. feature 생성 (add)

1. **slug 확정**
   - 사용자가 slug를 주면 kebab-case로 정규화해 사용합니다.
   - 설명만 주면(예: "상품 엑셀 업로드/다운로드 기능") 설명에서 slug를 제안하고 확인받습니다.
   - 예약어(structure.md "이름 규칙")이거나 `features/` 또는 `features/_completed/` 에 같은 slug가 있으면 생성하지 않고 다른 이름을 받습니다. (`tm.sh new-feature` 가 거부하면 그 메시지를 근거로 다시 받습니다) (완료 feature와 겹치면 재오픈(`status processing`)을 대안으로 안내)
2. **개요 확보**
   - 설명(텍스트·슬랙 링크·문서 경로)이 함께 오면 그것으로 README "개요"를 작성합니다.
     - 슬랙 링크: `/jissp-slack-thread-reader` 로 수집 → `/jissp-content-to-requirements` 로 정리한 요구사항 문서를 요약해 개요로 씁니다. 요구사항 문서 전체는 `docs/definition.md` 로 저장하고 "참고 문서"에 등록합니다.
     - 문서 경로: 내용을 요약해 개요로 쓰고, 원본을 `docs/` 로 복사할지 확인받습니다.
   - 설명이 없으면 "이 feature의 목표를 한두 문장으로 알려주세요"라고 **텍스트로** 한 번 묻고 자유 입력을 기다립니다. (`AskUserQuestion` 선택지로 묻지 않습니다) 답이 없으면 개요를 `(미정)` 으로 둡니다.
   - 요구사항은 여기서 받지 않습니다. feature 단위 PRD는 만들지 않으며, 요구사항은 태스크를 등록한 뒤 **태스크별 PRD**(`/jissp-planner prd --task`)에서 입력받습니다. (feature를 태스크 단위로 빌드업하는 방식이므로 전체 범위를 먼저 확정하지 않습니다)
3. **생성**
   - `tm.sh new-feature [slug] "[제목]"` 으로 `README.md`(frontmatter·빈 표·이력), `docs/`, `tasks/` 를 만듭니다. (예약어·중복 검사 포함)
   - 이어서 README "개요"(와 "참고 문서")를 2에서 확보한 내용으로 채웁니다. slug 확정(1)과 개요 확보(2)는 생성 전에 끝냅니다.
4. **결과 보고 및 다음 단계 안내**
   - 생성된 경로를 보고하고, 이어서 **첫 태스크 등록**으로 넘어갑니다. 첫 태스크의 범위(태스크명 또는 설명)를 **텍스트로** 묻고 자유 입력을 받아 `add [slug] [입력]` 절차([register.md](register.md))로 진행합니다. (범위를 선택지로 만들어 고르게 하지 않습니다)
   - 등록이 끝나면 register.md "등록 후 다음 단계"에 따라 태스크 PRD 작성(`/jissp-planner prd --task [slug]/[NN]`)으로 이어집니다.
   - 사용자가 지금 등록하지 않겠다고 하면 `/jissp-task-manager add [slug] [태스크 태스크명 또는 설명]` 을 안내하고 종료합니다.
