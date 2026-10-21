# 1-2. 제어 흐름 평탄화

> 카테고리: **허용되는 변경** (읽는 사람의 인지 부하를 줄이는 변경만 수행한다)

- 중첩 if/else → early return, guard clause
- 이중 부정 제거 (`if (!isNotReady)` → `if (isReady)`)
- "검증 → 본 작업" 구조로 검증 블록을 본 흐름 앞에 정리 (검증이 앞선 부수효과의 결과에 의존하지 않아 순서를 옮겨도 동작이 같을 때만)
- **처리 단계를 한 문장씩 분리 (명시적 단계별 흐름)** — 부수효과가 있는 호출(`await`, 저장·전송·상태 변경)을 인자 안에 중첩하거나 한 줄로 이어 붙이면, 안쪽부터 거꾸로 읽어야 실행 순서가 잡힌다. 단계마다 한 문장으로 풀어 위에서 아래로 실행 순서대로 읽히게 한다.

  ```ts
  // before
  this.logResult(uploadId, await this.complete(uploadId, await this.countResults(uploadId)))
  // after
  const counts = await this.countResults(uploadId)
  const result = await this.complete(uploadId, counts)
  this.logResult(uploadId, result)
  ```

  - **대상**: 부수효과·`await` 호출이 다른 호출의 인자 안에 중첩된 경우, 한 문장에 처리 단계가 3개 이상 묶인 경우
  - **순서 보존**: 인자는 왼쪽→오른쪽, 안쪽 먼저 평가된다. 분리 후에도 호출 순서가 원본과 같아야 한다 (`f(a(), await b())`라면 `a()`를 먼저 뽑는다)
  - 중간값 이름은 그 단계의 **산출물**을 나타낸다 (`result1`, `temp` 금지)
  - 순수 값 계산식의 분해는 `rules/03`의 "계산을 단계별 임시 변수로 분해"를 따른다
  - **대상이 아니다**: 한 줄에 읽히는 순수 변환 체이닝(`items.filter(isPaid).map(toAmount)`) — 쪼개면 오히려 심볼만 늘어난다. 체이닝을 루프로(또는 반대로) 바꾸는 것은 `rules/08`의 금지 변경이다
- **삼항연산자 return → if문** — 반환값을 결정하는 삼항연산자가 한 줄에 들어오지 않거나(줄바꿈으로 분해된 경우), 각 분기가 `await`/부수효과를 포함해 흐름을 한 호흡에 읽기 어려우면 early return하는 `if`문으로 평탄화한다.

  ```ts
  // before
  return idType === 'site'
    ? await this.mainMemberExternalService.findBySiteId(id)
    : await this.mainMemberExternalService.findById(id)
  // after
  if (idType === 'site') {
    return await this.mainMemberExternalService.findBySiteId(id)
  }

  return await this.mainMemberExternalService.findById(id)
  ```

  단, `x !== y` 처럼 한 줄에 명확히 들어오는 단순 삼항은 그대로 두거나 `03-expression-clarity.md`의 "이상한 삼항 단순화"를 따른다. 무조건 if문으로 바꾸지 않는다.

- **단일 라인 제어문 금지 — 본문이 한 줄이어도 중괄호(`{}`)로 감싼다.** 제어부(조건·반복 헤더)와 본문이 같은 줄에 붙어 있으면 "제어부를 읽는 눈"과 "동작을 읽는 눈"이 분리되지 않아 본문을 놓치기 쉽다. 특히 반복문 헤더는 그 자체로 읽는 비용이 크기 때문에, 뒤에 붙은 본문이 시야에서 밀려난다. 본문을 다음 줄로 내리고 블록으로 감싸 제어부/동작을 시각적으로 분리한다.

  ```ts
  // before
  if (조건) return

  // after
  if (조건) {
    return
  }
  ```

  ```ts
  // before
  for (let i = 0; i < items.length; i += size) chunks.push(items.slice(i, i + size))

  // after
  for (let i = 0; i < items.length; i += size) {
    chunks.push(items.slice(i, i + size))
  }
  ```

  - **적용 대상**: `if` / `else` / `else if` / `for` / `for...of` / `for...in` / `while` / `do...while` 등 **본문 블록을 갖는 모든 제어문**.
  - 본문이 `return` 뿐 아니라 `continue` / `break` / `throw` / 단일 호출문 / 단일 대입문 등 **어떤 단일 문장이어도** 동일하게 적용한다.
  - 중괄호 없이 본문만 다음 줄에 놓인 형태(`if (조건)` 개행 후 `return`)도 동일하게 블록으로 감싼다.
  - 이 변경은 동작에 영향이 없고 기존 흐름을 그대로 보존하므로, 발견 시 예외 없이 적용한다.
  - **범위 제한**: 중괄호 부착만 수행한다. `else if` 체인을 재구성하거나, 조건·반복 헤더 자체를 재배치하거나, `for` 루프를 `map`/`filter`/`reduce` 등으로 바꾸는 것은 이 규칙의 범위가 아니다(후자는 `08-forbidden-changes.md`의 알고리즘·구조 변경에 해당).
  - 화살표 함수의 표현식 본문(`items.map((item) => item.id)`)은 제어문이 아니므로 **대상이 아니다.** 블록 본문으로 바꾸지 않는다.
