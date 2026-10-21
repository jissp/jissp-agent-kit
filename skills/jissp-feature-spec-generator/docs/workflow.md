# jissp-feature-spec-generator 실행 워크플로우

본 문서는 `jissp-feature-spec-generator` 스킬이 실행될 때의 상세 오케스트레이션 단계 및 예외 처리 정책을 정의합니다.

---

## 1. 사전 검증 및 준비 (Discovery)

1. **feature 유효성 검증**:
   - 대상 feature 경로: `[Git Root]/0-jissp-docs/features/[feature]`
   - 해당 디렉토리가 존재하고, 상위 `README.md`가 존재하는지 확인합니다.
2. **완료 태스크 목록 수집**:
   - `README.md`의 `## 태스크 목록` 표를 파싱합니다.
   - 상태가 `completed` 인 태스크들을 번호 오름차순(01, 02, ..., NN)으로 수집합니다.
   - (`backlog`, `holding` 등 미완료 태스크는 최종 스펙 대상에서 제외합니다.)
3. **스펙 디렉토리 및 캐시 확인**:
   - 대상 디렉토리: `0-jissp-docs/features/[feature]/specs/` 및 하위 `.tmp/` 생성
   - 이미 `.tmp/[NN]_[task-slug].spec.md` 가 존재하는 경우:
     - 태스크의 수정 시각이 캐시 파일보다 최신이 아니라면 **재분석을 건너뛰고(Skip) 기존 캐시를 재사용**합니다.

---

## 2. 1단계: 청크 단위 병렬 서브에이전트 실행 (Map Phase)

1. **청크 분할**:
   - 분석해야 할 태스크들을 `config.md`에 정의된 `batch_size`(기본 4개) 단위의 청크(배치)로 나눕니다.
   - 예: 태스크 14개인 경우 -> `[01, 02, 03, 04]`, `[05, 07, 08, 09]`, `[10, 12, 13, 14]`, `[15, 16]`
2. **배치별 병렬 실행**:
   - 각 배치 내 태스크들에 대해 `jissp-task-spec-extractor` 서브에이전트를 병렬로 호출합니다.
   - 전달 인자:
     - `task_dir`: `[feature]/tasks/[NN]_[task-slug]`
     - `output_path`: `[feature]/specs/.tmp/[NN]_[task-slug].spec.md`
   - 각 서브에이전트는 태스크 내 문서들을 분석하여 `output_path`에 직접 1차 스펙을 작성하고 메타데이터만 회신합니다.
3. **진행 상황 안내**:
   - 한 배치가 완료될 때마다 사용자에게 진행률을 출력합니다:
     > `[진행률] 4/14 태스크 분석 완료 (28%) - 01~04 태스크 1차 Spec 저장 완료`

---

## 3. 2단계: 타임라인 순차 병합 및 Conflict 해소 (Reduce Phase)

모든 태스크의 1차 스펙(`.tmp/*.spec.md`)이 준비되면, 메인 에이전트가 순차 병합을 수행합니다:

1. **타임라인 순회 (01 → NN)**:
   - 태스크 번호 순서대로 각 스펙 파일을 읽습니다.
   - 특히 `## 4. 선행 태스크에 대한 수정/폐기 사항 (Overrides & Deprecations)` 섹션을 집중 분석하여, 이전 태스크의 규칙/모델/인터페이스 중 뒤집힌 내용을 최신 결정으로 갱신합니다.
2. **feature 전역 문서(`docs/`) 최종 교차 검증**:
   - `0-jissp-docs/features/[feature]/docs/` 내에 최신 API 명세서, Figma 요구사항 정리본, ERD 흐름도 등이 존재하는 경우, 최종 병합 결과와 대조하여 누락된 디테일이나 최신 네이밍을 보정합니다.
3. **SDD 관점의 언어 중립화 정제**:
   - NestJS 데코레이터(`@Controller`, `@Injectable`), TypeORM 엔티티 문법(`@Column`), 특정 라이브러리 함수 호출 등을 제거하고, 순수 도메인 규칙, 상태 머신 전이표, DTO 필드 검증 규칙으로 정제합니다.

---

## 4. 3단계: 최종 Spec 산출물 작성 및 보고

1. **파일 작성**:
   - `0-jissp-docs/features/[feature]/specs/functional-spec.md` (기능 사양서)
   - `0-jissp-docs/features/[feature]/specs/technical-spec.md` (기술 사양서)
2. **임시 파일 정리 여부**:
   - `config.md`의 `keep_tmp_specs`가 `true`이면 `.tmp/` 디렉토리를 보존하여 사용자가 태스크별 변경 내역을 추적할 수 있도록 합니다.
   - 사용자가 `--clean` 플래그를 전달한 경우에만 `.tmp/`를 삭제합니다.
3. **완료 리포트 출력**:
   - 생성된 스펙 파일 경로와 핵심 도메인 요약, 분석에 반영된 완료 태스크 수(예: 32개 완료)를 사용자에게 보고합니다.
