# 1-3. 표현식 명료화

> 카테고리: **허용되는 변경** (읽는 사람의 인지 부하를 줄이는 변경만 수행한다)

- 긴 boolean 조건·계산식을 의미 있는 임시 변수로 추출 (변수명이 진짜 정보를 추가할 때만)
- **계산을 단계별 임시 변수로 분해**

  ```ts
  // before
  vatAmount: (total - taxFree) - VatUtil.getSupplyAmount(total - taxFree)
  // after
  const taxableAmount = total - taxFree
  const supplyAmount = VatUtil.getSupplyAmount(taxableAmount)
  // ... vatAmount: taxableAmount - supplyAmount
  ```

- **구조 분해로 깊은 접근·반복 접근 정리 (조기 구조 분해)** — 객체 경로를 매번 따라 읽는 시각적 노이즈를 걷어내, 이 메서드가 "무엇을 입력으로 쓰는지"를 첫 줄에서 드러낸다.

  ```ts
  // before
  const counts = await this.countResults(job.data.uploadId)
  await this.complete(job.data.uploadId, counts)
  this.logger.log(`업로드 ${job.data.uploadId} 완료 — 성공 ${counts.successCount}건 / 실패 ${counts.failCount}건`)
  // after
  const { uploadId } = job.data

  const counts = await this.countResults(uploadId)
  await this.complete(uploadId, counts)

  const { successCount, failCount } = counts
  this.logger.log(`업로드 ${uploadId} 완료 — 성공 ${successCount}건 / 실패 ${failCount}건`)
  ```

  - **대상** (하나라도 해당)
    - 같은 객체 경로를 2회 이상 접근한다
    - 2단계 이상 깊은 경로(`job.data.uploadId`)가 템플릿 문자열·조건식·인자 목록 안에서 읽기를 방해한다
  - **위치**
    - 메서드 입력(파라미터, job 페이로드, DTO)은 **메서드 시작 지점**에서 분해한다. 입력은 시작 지점이 곧 도입 지점이므로 `rules/06`의 "최초 사용 지점 근처로"와 충돌하지 않는다
    - 중간 산출물(호출 결과)은 **그 값이 만들어진 직후 또는 사용 직전**에 분해한다
  - **하지 않는다**
    - 1회만 접근하는 얕은 경로(`dto.id`) — 추적할 심볼만 늘어난다(`rules/11`)
    - 분해하면 이름이 정보를 잃거나 충돌하는 경우(`order.id`, `member.id` → `id`) — 경로를 그대로 둔다
    - 원본 객체 자체를 다른 호출에 넘겨야 하는 경우, 그 객체까지 억지로 해체하지 않는다(위 예시의 `counts`)
  - 접근 시점을 앞당기므로 `rules/10`의 "접근 시점 이동" 조건을 반드시 함께 확인한다

- 이상한 삼항 단순화 (`x === y ? false : true` → `x !== y`)

- **조건부 spread는 피하고 변수로 풀어 쓴다** — `...(cond ? { key: val } : {})`는 짧지만 객체 리터럴 안에서 다시 해체해야 의미가 잡힌다. 키가 한두 개면 변수로 분리해 평탄하게 포함시킨다. 같은 패턴이 여러 곳에서 반복될 때만 헬퍼 함수로 추출한다(`09-extraction-condition.md`의 조건을 통과한 경우).

  ```ts
  // before
  return {
    ep_code: easyPayMethod,
    ep_bill_type: this.determineBillType(order),
    ...(easyPayMethod === 'SSG' ? { ep_no: phone.replaceAll('-', '') } : {}),
  }
  // after
  const ep_no = easyPayMethod === 'SSG' ? phone.replaceAll('-', '') : undefined

  return {
    ep_code: easyPayMethod,
    ep_bill_type: this.determineBillType(order),
    ep_no,
  }
  ```
