# 1-5. 타입 가독성

> 카테고리: **허용되는 변경** (읽는 사람의 인지 부하를 줄이는 변경만 수행한다)

- **`instanceof` 체크를 타입 가드 메서드로** (`payment is TossPayment` 반환으로 캐스팅도 제거)

  ```ts
  // before
  if (payment instanceof TossPayment) { ...payment as TossPayment... }
  // after
  if (this.isTossPayment(payment)) { ...payment... }
  ```

- 인라인 객체 타입 → 명명된 타입 import (`param: { tid: string; ... }` → `param: NicePayCancelParam`)
- 함수 반환 모양을 type alias로 명명 (의미 있는 키가 많을 때 호출처 추정 부담↓)
- 관련 파라미터 묶기 (Parameter Object) — 의미 단위가 분명할 때만. 시그니처 변경 조건은 `rules/01`의 "매직 boolean 파라미터"와 같다
