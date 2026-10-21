---
skill: jissp-slack-inquiry
source: ~/jissp-agent-kit/skills/jissp-slack-inquiry
generated_at: 2026-10-21 16:56:13
---

### 명령어

| 용도 | 명령어 |
|---|---|
| 슬랙 문의 분석 | `/jissp-slack-inquiry [슬랙 메시지 링크]` — 스레드 수집 → 요구사항 정리 → 코드 분석 → 문서 저장 |
| 원문으로 분석 | `/jissp-slack-inquiry [스레드 원문 붙여넣기]` — 링크가 없을 때. 이 경우 슬랙 답글 전송은 불가(초안만 제공) |

- 읽기 전용입니다. 코드를 수정하지 않고, 분석 문서 저장까지만 합니다.
- 진행 중 멈추는 곳: 요구사항 확인(버그/이슈, 추가 요청이 없을 때까지 반복) · 요약 방향 합의(잡담·기타) · 분석 레포 선택(필요 시) · 다음 작업 안내
- 버그/이슈 제보·업무 요청만 코드 분석을 하고, 일정 관리·잡담·기타는 요약만 저장한 뒤 끝냅니다.

### 다음 작업 안내 (분석 완료 후)

| 선택지 | 동작 |
|---|---|
| 작업 착수 / 추가 작업 | 업무 요청: PRD 작성(`/jissp-planner draft`) · 버그/이슈: 바로 수정 — 공통: 태스크 등록(`/jissp-task-manager`) · 추가 분석(같은 문서 갱신) |
| 슬랙으로 공유 | 원본 스레드에 답글 — 미리보기 → 전송 / 수정 / 전송 안 함 (`/jissp-slack-message-sender`) |
| 마무리 | 문서 저장으로 종료 |
| 기타 (직접 입력) | 확인 필요 사항 답변·문서 수정 요청 (코드 수정 요청은 `바로 수정` 으로 안내) |

- 선택한 작업이 끝나면 다시 이 안내로 돌아옵니다. (`마무리` 또는 다른 스킬로 넘어갈 때까지 반복, 끝낸 항목에는 `(완료)` 표기)
- PRD 작성·태스크 등록·바로 수정을 고르면 이 스킬은 종료되고 해당 작업으로 넘어갑니다.

### 인자 참고

- `[슬랙 메시지 링크]`: `https://<workspace>.slack.com/archives/C0XXXXXX/p1712345678901234` 형태. 부모·답글·링크된 스레드(1단계)까지 수집합니다.
- 인자 없이 호출하면 링크(또는 원문)를 요청하고 종료합니다.
- 함께 볼 참조 문서(Figma·Notion·GitHub 링크)를 같이 적어도 됩니다.

### 설정 참고

- 저장 위치: 분석 레포의 `0-jissp-docs` 분석 문서 디렉토리 (`~/jissp-agent-kit/jissp-document.md` 정의)
- 파일명: `[YYYYMMDD_HHmmss]_[cs-issue|request|schedule|summary]-[핵심키워드].md`
- 분석 레포: 현재 디렉토리가 서비스 레포가 아니면 `~/jissp-agent-kit/project-mapping-table.md` 에서 선택받습니다.

### 예시

```
/jissp-slack-inquiry https://myteam.slack.com/archives/C0ABCDEF1/p1712345678901234
/jissp-slack-inquiry https://myteam.slack.com/archives/C0ABCDEF1/p1712345678901234 피그마: https://figma.com/design/xxx
```
