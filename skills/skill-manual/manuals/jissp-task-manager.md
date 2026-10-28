---
skill: jissp-task-manager
source: ~/jissp-agent-kit/skills/jissp-task-manager
generated_at: 2026-10-27 07:19:27
---

### feature

| 용도 | 명령어 |
|---|---|
| feature 추가 | `/jissp-task-manager feature add [slug] [설명]` |
| feature 목록 | `/jissp-task-manager feature list [all]` — `all`: 완료 feature 포함 |
| feature 상태 변경 | `/jissp-task-manager feature status [slug] [processing\|holding\|completed]` |
| feature 삭제 | `/jissp-task-manager feature rm [slug]` |

### 태스크

| 용도 | 명령어 |
|---|---|
| 태스크 추가 | `/jissp-task-manager add [feature] [요청]` — feature 생략 시 maintenance |
| 태스크 목록 | `/jissp-task-manager list [feature] [범위]` — 범위: `backlog` / `holding` / `completed` / `all` |
| 태스크 실행 | `/jissp-task-manager run [feature] [task] [--impl agent\|skill\|inline]` — task 생략 시 다음 wait 태스크, `--impl` 생략 시 `config.md` 의 `default_impl` |
| 태스크 상태 변경 | `/jissp-task-manager status [feature] [task] [backlog\|wait\|processing\|completed\|holding]` |
| 태스크 삭제 | `/jissp-task-manager rm [feature] [task]` |

- **작업 요청 (등록 + 실행)**: "[feature]에 [작업] 태스크 작업해줘", "[feature] 에서 ~ 작업 진행해줘" 처럼 자연어로 요청하면 기존 태스크를 찾거나 `add` 로 등록한 뒤 "바로 실행"(`run`)을 권장안으로 이어갑니다.
- **수정**: 태스크·feature 내용 수정, 다른 feature로 옮기기는 별도 명령 없이 자연어로 요청합니다. ("이 태스크 요구사항 수정해줘", "다른 feature로 옮겨줘")
- 인자 없이 호출하면 사용법과 전체 현황(feature·태스크 목록)을 보여줍니다.

### 인자 참고

- `[feature]`: 진행 중인 feature slug 또는 `maintenance`. 일치하지 않으면 인자 전체를 요청으로 보고 maintenance에 등록합니다.
- `[요청]`: 태스크명(kebab-case) · 프롬프트 · 슬랙 스레드 링크 · 기획/설계 문서 경로
- `[task]`: 디렉토리명 전체 · 번호(`01`) · slug 일부. `[feature]/[task]` 형태(예: `product-excel/01`)도 가능합니다.
- 태스크 문서 작성: `/jissp-planner [mode] --task [feature]/[task]` (등록·실행 시 스킬이 대신 호출)
- `--impl`: `agent`(서브에이전트 위임) · `skill`(run 세션에서 모델만 전환) · `inline`(메인 세션 직접 구현)
- 설계 문서 없이 실행: 개요·요구사항(또는 PRD)만 있고 `architecture.md` 가 없어도 `run` 할 수 있습니다. (`agent` 방식이면 `jissp-implementer` 에 위임) 작업 문서가 전혀 없으면 planner 문서 작성을 먼저 제안합니다.
- 구현 범위: run 중 "1~3단계", "2그룹만" 처럼 §12 단계·병렬 그룹 범위를 지정할 수 있습니다. 설계 문서 §12에 병렬 그룹(`2-A`, `2-B`)이 있으면 `agent` 방식은 그룹 단계를 동시에 착수하고, `skill`·`inline` 은 순차로 진행합니다.
- run 은 태스크 문서에서 컨텍스트를 다시 읽으므로, 다른 작업을 한 세션이라면 `/clear` 후 새 세션에서 실행하는 것을 권장합니다.

### 설정 참고

- `~/jissp-agent-kit/skills/jissp-task-manager/config.md` — `default_impl` (`run` 의 기본 구현 방식, 없으면 `agent`)

### 예시

```
/jissp-task-manager feature add collection-in-collection 컬렉션 안의 컬렉션
/jissp-task-manager add collection-in-collection collection-tree-query
/jissp-task-manager list collection-in-collection
/jissp-task-manager run collection-in-collection 01
/jissp-task-manager run collection-in-collection 01 --impl skill
collection-in-collection 에 트리 조회 API 태스크 작업해줘
```
