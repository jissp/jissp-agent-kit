---
skill: jissp-task-manager
source: ~/jissp-agent-kit/skills/jissp-task-manager
generated_at: 2026-10-21 23:57:03
---

### 프로젝트

| 용도 | 명령어 |
|---|---|
| 프로젝트 추가 | `/jissp-task-manager project add [slug] [설명]` |
| 프로젝트 목록 | `/jissp-task-manager project list [all]` — `all`: 완료 프로젝트 포함 |
| 프로젝트 상태 변경 | `/jissp-task-manager project status [slug] [processing\|holding\|completed]` |
| 프로젝트 삭제 | `/jissp-task-manager project rm [slug]` |

### 태스크

| 용도 | 명령어 |
|---|---|
| 태스크 추가 | `/jissp-task-manager add [project] [feature]` — project 생략 시 maintenance |
| 태스크 목록 | `/jissp-task-manager list [project] [범위]` — 범위: `backlog` / `holding` / `completed` / `all` |
| 태스크 실행 | `/jissp-task-manager run [project] [task] [--impl agent\|skill\|inline]` — task 생략 시 다음 wait 태스크, `--impl` 생략 시 `config.md` 의 `default_impl` |
| 태스크 상태 변경 | `/jissp-task-manager status [project] [task] [backlog\|wait\|processing\|completed\|holding]` |
| 태스크 삭제 | `/jissp-task-manager rm [project] [task]` |

### 인자 참고

- `[project]`: 진행 중인 프로젝트 slug 또는 `maintenance`. 일치하지 않으면 인자 전체를 feature로 보고 maintenance에 등록합니다.
- `[feature]`: feature명(kebab-case) · 프롬프트 · 슬랙 스레드 링크 · 기획/설계 문서 경로
- `[task]`: 디렉토리명 전체 · 번호(`01`) · slug 일부. `[project]/[task]` 형태(예: `product-excel/01`)도 가능합니다.
- 태스크 문서 작성: `/jissp-planner [mode] --task [project]/[task]` (등록·실행 시 스킬이 대신 호출)
- `--impl`: `agent`(서브에이전트 위임) · `skill`(run 세션에서 모델만 전환) · `inline`(메인 세션 직접 구현)
- 구현 범위: run 중 "1~3단계", "2그룹만" 처럼 §12 단계·병렬 그룹 범위를 지정할 수 있습니다. 설계 문서 §12에 병렬 그룹(`2-A`, `2-B`)이 있으면 `agent` 방식은 그룹 단계를 동시에 착수하고, `skill`·`inline` 은 순차로 진행합니다.

### 설정 참고

- `~/jissp-agent-kit/skills/jissp-task-manager/config.md` — `default_impl` (`run` 의 기본 구현 방식, 없으면 `agent`)

### 예시

```
/jissp-task-manager project add collection-in-collection 컬렉션 안의 컬렉션
/jissp-task-manager add collection-in-collection collection-tree-query
/jissp-task-manager list collection-in-collection
/jissp-task-manager run collection-in-collection 01
/jissp-task-manager run collection-in-collection 01 --impl skill
```
