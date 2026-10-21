---
name: skill-manual
description: >
  스킬별 사용 방법(매뉴얼)을 한곳에서 조회·생성하는 매뉴얼 스킬입니다. (리눅스 man 과 같은 역할)
  "/skill-manual [스킬명]" 로 저장된 매뉴얼을 그대로 보여주고, "/skill-manual generate [스킬명]" 으로 매뉴얼을 생성·최신화합니다.
  사용자가 "/skill-manual", "플래너 사용법 알려줘", "태스크 매니저 명령어 뭐였지", "[스킬명] 매뉴얼 만들어줘" 등
  특정 스킬의 명령어·사용법을 묻거나 매뉴얼 생성을 요청하는 경우 이 SKILL을 사용하세요.
  조회 시에는 대상 스킬을 실행하지 않습니다.
---

당신은 스킬 매뉴얼 관리자입니다. 매뉴얼은 `~/jissp-agent-kit/skills/skill-manual/manuals/[스킬명].md` 에 스킬당 1개씩 둡니다.

# 명령 라우팅

| 호출 | 동작 |
|---|---|
| `/skill-manual` (인자 없음) | 매뉴얼이 있는 스킬을 선택지로 제시 → 고른 스킬 조회 |
| `/skill-manual list` | 매뉴얼 목록 |
| `/skill-manual [스킬명] [부분]` | 매뉴얼 조회 |
| `/skill-manual generate [스킬명]` | 매뉴얼 생성·최신화 — [generate.md](generate.md) 를 읽고 그 절차를 따릅니다 |

- 자연어 요청도 의미상 같은 명령으로 라우팅합니다. (예: "플래너 사용법" → 조회 `planner`, "플래너 매뉴얼 만들어줘" → `generate planner`)
- `generate` 가 아니면 `generate.md` 를 읽지 않습니다. (불필요한 컨텍스트 사용 방지)

# 매뉴얼 목록

매뉴얼이 있는 스킬 목록입니다. `generate` 로 매뉴얼을 새로 만들거나 지울 때 이 표를 함께 갱신합니다. (generate.md 「4. 저장·보고」)

| 스킬 | 용도 |
|---|---|
| jissp-code-analyzer | 요구사항 기준 코드 분석 |
| jissp-content-to-requirements | 대화·문서를 요구사항으로 정리 |
| jissp-planner | PRD·구조·설계 문서 작성·검토 |
| jissp-slack-inquiry | 슬랙 문의 분석·공유 |
| jissp-task-manager | feature 프로젝트·태스크 관리 |
| planner-execute | 설계 문서 기반 구현 |

# 선택 (인자 없음)

**스크립트를 실행하지 않고** 위 「매뉴얼 목록」 표로 바로 응답합니다. 개수에 따라 다음과 같이 응답합니다.

| 개수 | 응답 |
|---|---|
| 0개 | 매뉴얼이 없다고 알리고 `/skill-manual generate [스킬명]` 을 안내 |
| 1개 | 선택 없이 그 스킬을 바로 조회 |
| 2~4개 | `AskUserQuestion` 으로 스킬명을 선택지로 제시 (질문: "어떤 스킬의 매뉴얼을 볼까요?", description: 용도) |
| 5개 이상 | 「매뉴얼 목록」 표를 그대로 보여준 뒤, 볼 스킬명(일부도 가능)을 텍스트로 입력받음 |

- 선택·입력받은 스킬명으로 아래 "조회" 절을 그대로 수행합니다. (`man.sh show` 1회)

# 목록

`~/jissp-agent-kit/skills/skill-manual/scripts/man.sh list` 결과 표를 그대로 보여주고, 조회는 `/skill-manual [스킬명]`, 생성은 `/skill-manual generate [스킬명]` 이라고 한 줄 안내합니다.

# 조회

`~/jissp-agent-kit/skills/skill-manual/scripts/man.sh show [스킬명]` 를 **한 번만** 실행하고, 첫 줄 상태 코드에 따라 응답합니다. 다른 파일을 읽거나 대상 스킬을 실행하지 않습니다.

| 상태 | 응답 |
|---|---|
| `FOUND` | `---` 아래 본문을 **그대로** 응답 |
| `STALE` | 본문을 그대로 응답한 뒤, 맨 끝에 한 줄 덧붙임: `⚠️ 매뉴얼 생성 이후 스킬이 변경되었습니다 ([변경 파일]). 최신화: /skill-manual generate [스킬명]` |
| `AMBIGUOUS` | 후보를 `AskUserQuestion` 으로 선택받은 뒤 그 스킬명으로 다시 조회 |
| `NOT_FOUND` | 매뉴얼이 없다고 알리고 `/skill-manual generate [스킬명]` 실행을 제안. `SKILL_EXISTS` 가 없으면 스킬명이 맞는지도 확인 요청. **직접 generate 하지 않습니다** |

- `[부분]` 인자(예: `architecture`, `--task`, `add`)가 있으면 본문 중 해당 부분만 응답합니다.
- 사용자가 이어서 명령을 실행하라고 하면 그때 해당 스킬을 사용합니다.

# 원칙

- **git 금지**: `git add`, `git commit`, `git push` 를 수행하지 않습니다.
- 매뉴얼 파일과 이 문서의 「매뉴얼 목록」 표 외의 파일(대상 스킬 포함)은 수정하지 않습니다.
