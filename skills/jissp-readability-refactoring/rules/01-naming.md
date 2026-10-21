# 1-1. 네이밍 명료화

> 카테고리: **허용되는 변경** (읽는 사람의 인지 부하를 줄이는 변경만 수행한다)

- 의도를 숨기는 이름(`data`, `tmp`, `flag`, `result2`) → 의도가 드러나는 이름
- 메서드명을 실제 동작에 맞게 (`toApproveReturn` → `approveReturn`, `validateApprove` → `isAutoApprove`)
- **매직 boolean 파라미터 → 명명된 옵션 키**

  ```ts
  // before
  await this.approve(siteId, dto, requestId, true)
  // after
  await this.approve({ siteId, dto, requestId, isExecutionByCustomer: true })
  ```

  시그니처가 바뀌므로 호출처가 모두 작업 대상 파일 안에 있을 때만 적용한다. 아니면 "범위 외 관찰"로 보고한다.

- 도메인 개념을 함수명으로 캡슐화 (단, `09-extraction-condition.md`의 "함수/메서드 추출 조건"을 통과한 경우에만)

## 이름을 바꾸지 않는 대상

아래 이름은 가독성이 다소 떨어져 보여도 바꾸지 않는다. 바꾸면 동작이 깨지거나, 코드베이스의 공통 언어가 흔들린다.

- **프레임워크 규약에 묶인 이름** — 오버라이드·훅 메서드(`WorkerHost.process`, `onModuleInit`, `canActivate`), 데코레이터 인자, DI 토큰, 큐·이벤트·잡 이름
- **외부 계약에 노출된 이름** — DTO·요청·응답 필드, DB 컬럼 매핑 필드, 직렬화되는 키
- **코드베이스에서 일관되게 쓰는 도메인 용어** — 더 일반적인 단어로 바꾸지 않는다 (`complete` → `finalize`, `upload` → `import` 등). 같은 개념에 서로 다른 용어가 섞여 있을 때만, 이미 우세한 쪽으로 맞춘다
- **이미 의도가 드러나는 이름** — 취향 차이에 불과한 rename은 하지 않는다(`rules/11`)
