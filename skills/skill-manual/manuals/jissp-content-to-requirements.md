---
skill: jissp-content-to-requirements
source: ~/jissp-agent-kit/skills/jissp-content-to-requirements
generated_at: 2026-10-21 16:57:35
---

### 명령어

| 용도 | 명령어 |
|---|---|
| 원문을 요구사항으로 정리 | `/jissp-content-to-requirements [원문 붙여넣기]` — 슬랙 대화·메모·아이디어·회의 내용 |
| 파일로 정리 | `/jissp-content-to-requirements [파일 경로]` — Thread Dump·메모·회의록 파일 |

- 내용을 버그/이슈 제보 / 업무 요청 / 일정 관리 / 잡담·기타로 분류해 요구사항 문서로 정리합니다.
- 코드는 보지 않고 원문 내용만으로 정리합니다. 어느 디렉토리에서 호출해도 똑같이 동작합니다.
- 결과는 채팅에 출력만 하고 파일로 저장하지 않습니다. 저장이 필요하면 따로 요청하세요. (저장 위치를 확인한 뒤 저장)
- 진행 중 멈추는 곳: 버그/이슈의 요구사항 승인(추가 요청이 없을 때까지 반복) · 잡담·기타의 요약 방향 합의 (문서화 불필요를 고르면 종료)

### 인자 참고

- `[원문]` / `[파일 경로]`: 이미 확보한 내용이어야 합니다.
- 슬랙 링크·노션 URL만 주면 직접 수집하지 않고 안내 후 종료합니다. → `/jissp-slack-inquiry [링크]` 또는 `/jissp-slack-thread-reader [링크]` 먼저 사용
- 인자 없이 호출하면 필요한 입력을 안내하고 종료합니다.
- 원문 안의 참조 문서 링크(Figma·Notion·GitHub)는 읽어서 반영합니다.

### 이어지는 작업

- 코드 분석: `/jissp-code-analyzer` (정리한 요구사항을 넘김)
- PRD 작성: `/jissp-planner draft`

### 예시

```
/jissp-content-to-requirements (슬랙 대화 원문 붙여넣기)
/jissp-content-to-requirements /tmp/slack-messages/20261021_163534_slack-thread-general.md
/jissp-content-to-requirements 오늘 회의: 다음 주 금요일까지 정산 리포트 CSV 내보내기 추가 ...
```
