# TODO 등록 절차 (add)

> 선행: [structure.md](structure.md)의 저장 구조·README 스키마를 따릅니다.

사용법: `/jissp-todo-manager add [입력]`

`[입력]`에는 **작업명(수동)**, **슬랙 스레드 링크**, **노션 문서 링크**가 올 수 있습니다.

## 흐름

```
STEP 0. 입력 유형 판별
   │  (무중단)
STEP 1. 수집   → 슬랙: jissp-slack-thread-reader / 노션: Notion MCP / 수동: 없음
   │  (무중단)
STEP 2. 요구사항 정리 → Skill: jissp-content-to-requirements  (작업명만 있는 수동 등록은 생략)
   │  (무중단)
STEP 3. 저장   ← 저장은 이 스킬이 수행한다
   │
STEP 4. 결과 보고 + 다음 단계 안내
```

**STEP 0 → 3은 하나의 연속된 흐름입니다.** 하위 스킬 호출이 끝나는 것은 그 스킬의 종료일 뿐이므로, **사용자에게 턴을 넘기지 말고 즉시 다음 STEP을 이어서 수행합니다.**
(예외: 하위 스킬이 링크 없음·접근 불가·내부 게이트를 보고한 경우에만 멈춥니다.)

## STEP 0. 입력 유형 판별

| 유형 | 판별 기준 | 수집 방법 |
|---|---|---|
| 슬랙 스레드 | `*.slack.com/archives/...` 형태의 URL | `/jissp-slack-thread-reader` |
| 노션 문서 | `notion.so` / `www.notion.so` / `*.notion.site` 도메인의 URL | Notion MCP |
| 수동 | 위에 해당하지 않는 텍스트 | 수집 없음 |

- 입력이 아예 없으면 진행하지 말고 사용법을 안내한 뒤 종료합니다.

```
등록할 내용이 필요합니다.
예) /jissp-todo-manager add 관리자 주문 목록 CSV 내보내기
    /jissp-todo-manager add https://<workspace>.slack.com/archives/C0XXXXXX/p1712345678901234
    /jissp-todo-manager add https://www.notion.so/...
```

## STEP 1~2. 유형별 수집·요구사항 정리

### 1. 수동 등록

수동 입력은 다시 두 가지로 나뉩니다.

| 입력 형태 | 처리 |
|---|---|
| **작업명만** (짧은 제목 한 줄, 예: `주문 목록 CSV 내보내기`) | 요구사항 정리 없이 그대로 사용. 본문 없는 README 생성 |
| **내용이 있는 프롬프트** (요구사항·상황 설명이 포함된 서술) | `/jissp-content-to-requirements`에 전달하여 요구사항으로 정리 |

- 판단이 애매하면 **작업명만**으로 간주해 가볍게 등록합니다. TODO는 상세 문서가 아니라 "잊지 않기 위한 항목"이 우선입니다.
- frontmatter: `source_type: manual`, `source`는 생략
- slug: 작업명을 kebab-case로 변환하여 사용합니다. (요구사항 정리를 수행한 경우 요구사항 스킬이 반환한 **핵심 키워드**를 사용)

### 2. 슬랙 스레드 링크

1. `/jissp-slack-thread-reader` 스킬로 스레드를 수집하여 **Thread Dump**를 확보합니다.
2. `/jissp-content-to-requirements` 스킬에 **1번에서 수집한 Thread Dump를 전달**하여 요구사항으로 정리합니다.
   - 슬랙 링크만 전달하지 않습니다. 요구사항 스킬은 수집을 수행하지 않으므로 링크만 받으면 안내 후 종료합니다.
3. 요구사항 스킬이 반환한 값(**문서 유형 / 핵심 키워드 / 문서 본문 / 요약**)을 STEP 3에 사용합니다.

- **Thread Dump를 채팅에 출력하지 않습니다.** 진행 상황은 한 줄 요약으로만 알립니다. (예: `스레드 수집 완료 — 메시지 12건`)
- frontmatter: `source_type: slack-thread`, `source`에 슬랙 링크 기록
- slug: 요구사항 스킬이 반환한 **핵심 키워드**

### 3. 노션 문서 링크

1. Notion MCP의 `notion-fetch` 도구로 해당 URL의 문서를 읽어옵니다.
   - 문서가 다른 노션 페이지를 참조하고 있고 요구사항 파악에 필요하다고 판단되면 **1단계까지만** 추가로 fetch합니다.
   - 접근 권한이 없거나 URL이 유효하지 않으면 진행하지 말고 사용자에게 알린 뒤 종료합니다.
2. `/jissp-content-to-requirements` 스킬에 **1번에서 읽은 문서 본문을 전달**하여 요구사항으로 정리합니다. (노션 URL만 전달하지 않습니다)
3. 요구사항 스킬이 반환한 값을 STEP 3에 사용합니다.

- **노션 원문을 채팅에 출력하지 않습니다.** 진행 상황은 한 줄 요약으로만 알립니다. (예: `노션 문서 수집 완료 — [문서 제목]`)
- frontmatter: `source_type: notion`, `source`에 노션 링크 기록
- slug: 요구사항 스킬이 반환한 **핵심 키워드**

> `/jissp-content-to-requirements`는 **변환 전용** 스킬입니다. 파일을 저장하지 않고 문서 본문을 반환하므로, TODO 디렉토리에 `README.md`로 저장하는 것은 이 스킬의 몫입니다.
> 반환 항목은 **문서 유형 / 핵심 키워드 / 문서 본문 / 요약** 4가지이며, 이 값들을 STEP 3의 저장에 그대로 사용합니다.

## STEP 3. 저장

1. `date +%Y%m%d_%H%M%S`로 실제 시각을 확인합니다.
2. `~/jissp-agent-kit/databases/todos/[YYYYMMDD_HHmmss]_[slug]/` 디렉토리를 생성합니다.
3. `README.md`를 [structure.md](structure.md)의 스키마대로 작성합니다.
   - `status: todo`, `created_at` / `updated_at`은 `date +"%Y-%m-%d %H:%M:%S"` 결과
   - `doc_type`: 요구사항 스킬이 반환한 **문서 유형** (요구사항 정리를 수행하지 않은 수동 등록은 생략)
   - 본문: 요구사항 스킬이 반환한 **문서 본문을 그대로** 사용합니다. 임의로 재요약하지 않습니다.
   - 본문 하단에 `## 이력` 섹션과 `- [시각] 등록 (todo)` 한 줄을 추가합니다.
4. 요구사항 본문이 매우 길어 README의 가독성을 해치는 경우에만 본문을 `prd.md`로 분리하고, README 본문에는 요약과 `- [prd.md](prd.md)` 링크를 남깁니다.

## STEP 4. 결과 보고 + 다음 단계 안내

등록이 완료되면 생성된 TODO(경로·slug·출처 유형)와 **요구사항 스킬이 반환한 요약**을 보고합니다. 문서 본문 전문을 채팅에 붙여넣지 않습니다.

이어서 다음에 진행할 수 있는 단계를 안내합니다.

1. **`/jissp-todo-manager list`**: 현재 처리해야 할 TODO 목록 확인
2. **`/jissp-todo-manager assign [todo명]`**: 이 TODO를 프로젝트 태스크로 할당
