---
skill: jissp-task-auto-register
source: ~/jissp-agent-kit/skills/jissp-task-auto-register
generated_at: 2026-10-23 07:28:29
---

### 명령어

| 용도 | 명령어 |
|---|---|
| feature·태스크 자동 분류 등록 | `/jissp-task-auto-register feature [개요]` — 개요를 feature 1개 이상으로 나누고, feature마다 태스크를 나눠 등록 |
| 태스크 자동 분류 등록 | `/jissp-task-auto-register task [feature] [개요]` — 지정한 feature 안에 태스크를 나눠 등록 |
| 모드 선택 | `/jissp-task-auto-register [개요]` — 모드 없이 호출하면 `feature` / `task` 를 선택받음 |

- **직접 호출 전용**입니다. AI가 요청을 보고 자동으로 호출하지 않습니다.
- 분류 결과를 먼저 제안하고, 승인 / 수정 요청 / 취소 중 **승인한 경우에만** 등록합니다.
- 등록 후 첫 태스크의 PRD 작성(`/jissp-planner draft --task`) 또는 바로 실행(`/jissp-task-manager run`)으로 이어갈 수 있습니다. 이후 관리는 `jissp-task-manager` 로 합니다.

### 인자 참고

- `[개요]`: 텍스트 · 슬랙 스레드 링크 · PRD·기획 문서 경로. 생략하면 텍스트로 묻습니다.
- `[feature]`: 기존 feature slug 또는 `maintenance`. 일치하지 않으면 인자 전체를 개요로 봅니다.
  - 생략 시: 개요가 maintenance에 맞아 보이면 maintenance에 넣을지 묻고, 아니면 feature 모드로 전환합니다.
  - 개요가 여러 feature로 나눌 만큼 크면 feature 모드 전환을 제안합니다. (거절하면 지정한 feature에 모두 등록)
  - 완료된 feature를 지정하면 등록하지 않고 재오픈을 안내합니다.
- 원문은 feature의 `docs/definition.md` 에 저장됩니다. (maintenance는 태스크마다 저장)

### 예시

```
/jissp-task-auto-register feature 상품 옵션 기능 추가 — 단독형·조합형·추가 옵션 지원
/jissp-task-auto-register feature 0-jissp-docs/prds/20261023_product-option-prd.md
/jissp-task-auto-register task refactor-pg PG사 연동 모듈 리팩토링 개요...
/jissp-task-auto-register task https://xxx.slack.com/archives/C000/p000
/jissp-task-auto-register task maintenance 관리자 화면 자잘한 개선 묶음...
```
