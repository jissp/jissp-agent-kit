---
name: jissp-task-implement
description: 
  jissp-task-manager run 의 구현 방식 `skill` 에서만 호출하는 태스크 구현 스킬입니다.
  설계 문서(architecture.md)가 있는 태스크를 §12 단계 단위로 구현하거나 승인된 보완 항목을 고치고, 정해진 양식으로 결과를 반환합니다.
  사용자가 직접 설계 문서 기반 구현을 요청한 경우에는 이 스킬이 아니라 planner-execute 를 사용하세요.
model: sonnet
---

# 공통 계약 (필수 선행)

**작업 시작 전 반드시 `~/jissp-agent-kit/skills/jissp-task-manager/docs/implement.md` 를 `Read` 로 읽고, 그 문서의 「2. 구현 측 계약」 을 그대로 적용하십시오.**

호출 측이 인자로 전달한 항목(`task_dir`·`architecture`·`task_docs`·`context_docs`·`stage`·`workdir`·`user_rules`·`notes`)을 입력으로 사용합니다.

아래는 스킬로 실행될 때만 해당하는 **차이점**입니다.

# 스킬 실행 시

- run 세션 안에서 실행되지만, 서브에이전트 방식과 비교하기 위해 **사용자에게 직접 묻지 않습니다.** 결정이 필요하면 계약의 "중단하고 반환할 조건" 에 따라 반환 양식을 출력하고 멈춥니다.
- 반환 양식을 출력하면 이 스킬의 역할은 끝납니다. 이후 처리(보고·작업 이력·다음 단계·완료 처리)는 `implement.md` 「1. 호출 측 절차」 를 따라 run 이 이어갑니다.
