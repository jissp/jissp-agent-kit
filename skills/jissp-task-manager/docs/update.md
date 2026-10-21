# 태스크·프로젝트 수정 절차

> 선행: [structure.md](structure.md)의 저장 구조·README 스키마를 따릅니다.

## 1. 대상 특정

- 태스크: structure.md의 **특정 태스크 탐색 순서**로 찾습니다.
- 프로젝트: `projects/[slug]/` 에서 찾습니다. (README 개요·참고 문서 수정 등)

## 2. 수정 수행

### 태스크

- **README.md 본문**: 개요·요구사항·선행 태스크·문서 목록 등 갱신
- **태스크 문서**: `prd.md`, `module-structure.md`, `architecture.md` 는 태스크 디렉토리에 있는 문서가 유일한 원본이므로 **직접 수정**합니다. (원본 동기화 절차 없음)
  - 내용을 크게 고치거나 새로 쓰는 경우에는 `/jissp-planner [mode] --task [project]/[task]` (설계 문서는 `architecture revise`)를 권합니다. planner가 계약·구조 검증 절차를 함께 수행하기 때문입니다.
  - 신규 문서를 추가하면 README "문서" 목록과 (feature 프로젝트면) 프로젝트 README 표의 `문서` 컬럼에도 반영합니다.
- **참고 문서**: 태스크 `docs/` 에 추가·수정하고 README "문서" 목록에 반영합니다.
- **frontmatter 메타데이터**: `name`, `source` 등 갱신
  - `project` 변경(다른 프로젝트로 옮기기)은 디렉토리명 규칙이 바뀌므로 아래 "태스크를 다른 프로젝트로 옮기기"를 따릅니다.
- **`status` 변경은 이 문서가 아니라 [status.md](status.md)의 절차를 따릅니다.** (위치·프로젝트 README 갱신이 수반되기 때문)

### 프로젝트

- README "개요" 갱신, `docs/` 문서 추가·수정과 "참고 문서" 목록 반영
- 태스크 목록 표가 태스크 frontmatter와 어긋나 있으면 frontmatter 기준으로 표를 다시 맞춥니다. (SSOT는 태스크 frontmatter)
- 프로젝트 `status` 변경은 [project.md](project.md)를 따릅니다.

### 태스크를 다른 프로젝트로 옮기기

1. 옮길 대상 프로젝트와 새 디렉토리명(feature 프로젝트면 다음 번호 `NN_`, maintenance면 `등록 시각_feature`)을 제시하고 승인받습니다.
2. `mv` 로 이동하고 frontmatter `project` 를 갱신합니다. maintenance로 옮기는 경우 상태에 맞는 하위 디렉토리로 이동합니다.
3. 떠난 프로젝트와 들어간 프로젝트의 README 표·"이력"을 모두 갱신합니다. (maintenance는 표가 없으므로 "이력"만)

## 3. 공통 마무리

- 수정한 README의 `updated_at` 을 `date +"%Y-%m-%d %H:%M:%S"` 실제 시각으로 갱신하고, "작업 이력"(프로젝트는 "이력")에 수정 내역을 한 줄 추가합니다. 태스크 문서를 직접 수정한 경우 수정한 문서명을 적습니다.
- 수정된 파일과 변경 요지를 사용자에게 보고합니다.
