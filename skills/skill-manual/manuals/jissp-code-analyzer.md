---
skill: jissp-code-analyzer
source: ~/jissp-agent-kit/skills/jissp-code-analyzer
generated_at: 2026-10-21 16:57:35
---

### 명령어

| 용도 | 명령어 |
|---|---|
| 요구사항 기준 코드 분석 | `/jissp-code-analyzer [요구사항 문서 또는 파일 경로]` — 현재 레포 코드를 읽기 전용으로 분석 |
| 직접 쓴 요구사항으로 분석 | `/jissp-code-analyzer [확인할 질문·요청 내용]` |

- **분석할 레포 안에서 호출하세요.** 현재 작업 디렉토리의 코드를 대상으로 합니다.
- 버그/이슈 제보: 코드 경로를 추적해 재현·원인을 판정합니다.
- 업무 요청: 현행 동작·요청과의 차이·영향 범위·구현 가능성을 정리합니다.
- 일정 관리·잡담·기타는 분석 대상이 아니므로 안내 후 종료합니다.
- 코드를 수정하지 않고, 결과는 채팅에 출력만 합니다. 저장이 필요하면 따로 요청하세요. (저장 위치를 확인한 뒤 저장)

### 인자 참고

- `[요구사항]`: `/jissp-content-to-requirements` 결과, 요구사항 문서 파일 경로, 또는 확인할 질문이 드러나는 직접 작성 텍스트.
- 정리되지 않은 원문(슬랙 링크·Thread Dump·회의록)을 주면 분석하지 않고 안내 후 종료합니다. → `/jissp-slack-inquiry [링크]` 또는 `/jissp-content-to-requirements [원문]` 먼저 사용
- 요구사항이 모호해 분석 목표를 정할 수 없으면 무엇이 필요한지 먼저 묻습니다.

### 권장 흐름

- 원문 → `/jissp-content-to-requirements` → `/jissp-code-analyzer`
- 슬랙 문의는 수집·정리·분석·저장을 한 번에 하는 `/jissp-slack-inquiry` 를 권장합니다.

### 예시

```
/jissp-code-analyzer 0-jissp-docs/analysis/20261021_143205_cs-issue-login-error.md
/jissp-code-analyzer 쿠폰 중복 적용 시 결제 금액이 음수가 되는지 확인해줘
/jissp-code-analyzer 주문 목록에 CSV 내보내기를 추가하려면 어디를 바꿔야 하는지 분석해줘
```
