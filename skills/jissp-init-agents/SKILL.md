---
name: jissp-init-agents
description: >-
  프로젝트에 표준 멀티 AI 에이전트 작업 환경(AGENTS.md 및 .agents/ 구조)을 초기화하거나,
  기존 단일 AI 설정(예: .claude)을 표준 구조로 마이그레이션하는 스킬입니다.
---

# jissp-init-agents: AI 표준 작업 환경 초기화 스킬

이 스킬은 프로젝트에 `AGENTS.md` 단일 진입점 허브와 `.agents/` 체계(지침, 문서, 규칙, 개인화, 개발자 연동 가이드)를 스캐폴딩하고 설정합니다.

---

## 1. 사전 진단 (Diagnostics)

작업 대상 디렉토리의 루트에서 다음 사항을 점검합니다:

1. **기존 AI 설정 감지**:
   - `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`
   - `.agents/`, `.claude/`, `.gemini/`
2. **프로젝트 환경 분석**:
   - `package.json`, `tsconfig.json`, `requirements.txt`, `go.mod` 등을 통해 스택(Node/TS, NestJS, Next.js, Python 등) 파악
   - 모노레포 또는 단일 프로젝트 여부 확인
   - `.gitignore` 존재 여부 확인

---

## 2. 인터뷰 및 확인 (Interview)

`ask_question` 또는 대화를 통해 다음 사항을 사용자에게 확인합니다:

1. **초기화 모드**:
   - **신규 초기화**: 깨끗한 상태에서 표준 `.agents/` 및 `AGENTS.md` 생성
   - **기존 환경 마이그레이션**: 기존 설정(예: `.claude/`)을 유지하면서 `.agents/`로 연결 또는 이전
2. **프로젝트 기본 정보 확인**:
   - 프로젝트명 및 한 줄 설명
   - 주요 플랫폼/서브 프로젝트 구조(있을 경우)
3. **사용할 AI 도구 선택**:
   - Antigravity (agy), Claude Code, Cursor/Windsurf, Gemini CLI 등

---

## 3. 디렉토리 구조 스캐폴딩 (Scaffolding)

아래의 디렉토리 구조를 생성합니다:

```text
[프로젝트 루트]/
├── AGENTS.md                  # 🎯 [모든 AI의 최상위 진입점]
└── .agents/
    ├── README.md              # 📌 공용 AI 지침 및 On-demand 문서 인덱스
    ├── README.local.md        # 🔒 로컬 개인화 지침 (.gitignore)
    ├── INTEGRATION.md         # 📖 개발자를 위한 AI 도구 연동/관리 가이드
    ├── docs/                  # 📚 프로젝트 도메인 및 지식
    │   ├── OVERVIEW.md
    │   ├── TECHSTACK.md
    │   └── GLOSSARY.md
    ├── rules/                 # 📏 공통 코딩 및 설계 규칙
    │   ├── ARCHITECTURE.md
    │   ├── CONVENTION.md
    │   └── PROJECT_STRUCTURE.md (필요시)
    └── local-docs/            # 🔒 로컬 전용 문서 디렉토리 (.gitignore)
```

---

## 4. 파일 생성 절차 (Template Generation)

스킬 디렉토리 하위의 `templates/`에 정의된 양식을 기반으로 프로젝트 특성에 맞게 내용을 채워 생성합니다.

### 4.1 `AGENTS.md` (AI 전용 진입점)
- **절대 주의**: 사람이 읽는 안내문(Note, 개발자 가이드 링크 등)은 포함하지 않습니다. 오직 AI 에이전트가 읽는 진입점 및 참조 문법만 작성합니다.
- 예시:
  ```markdown
  # AGENTS.md

  Shared entry point for AI agents in the [Project Name] repository.
  [Project Brief Description]

  ## claude

  @./.agents/README.md
  @./.agents/README.local.md

  ## gemini

  @[Shared AI Guide](./.agents/README.md)
  @[Personalization Guide](./.agents/README.local.md)
  ```

### 4.2 `.agents/README.md` (공용 AI 지침)
- 핵심 원칙(절대 추론 금지, 컨벤션 준수 등)
- 기술 스택 및 베이스 경로 정의
- **On-Demand Loading 테이블**: 작업 시작 시에만 필요에 따라 읽을 상세 규칙/문서 인덱스 명시
- 모호성 질문 정책 (Clarification & Interview Policy)

### 4.3 `.agents/INTEGRATION.md` (개발자용 연동 가이드)
- AI 에이전트가 읽지 않는 **개발자 전용 문서**
- Antigravity(agy), Claude Code, Cursor, Windsurf 등 각 도구에서 진입점(`AGENTS.md`)을 어떻게 바인딩하는지 안내
- 신규 AI 도구 추가 절차 및 진입점 마이그레이션 히스토리 섹션 포함

### 4.4 `.agents/README.local.md` (개인화 로컬 지침)
- 한국어 답변 강제
- Inquiry(분석 단계) 안전 가드
- `.env` 접근 금지 및 Git 제약 사항
- 로컬 전용 가이드 링크

### 4.5 `.agents/docs/` 및 `.agents/rules/`
- `OVERVIEW.md`: 프로젝트 개요, 서브 프로젝트 역할
- `TECHSTACK.md`: 사용 언어, 프레임워크, 라이브러리, 인프라
- `GLOSSARY.md`: 도메인 용어 사전
- `ARCHITECTURE.md`: 계층 구조, 데이터 흐름, 트랜잭션/이벤트 정책
- `CONVENTION.md`: 네이밍 규칙, 포맷팅, 코딩 패턴

---

## 5. 사후 작업 및 검증 (Post-Action)

1. **`.gitignore` 설정 점검**:
   - `.agents/README.local.md`
   - `.agents/local-docs/`
   위 두 항목이 `.gitignore`에 등록되어 있는지 확인하고, 없으면 추가하거나 사용자에게 안내합니다.
2. **동작 검증**:
   - 각 파일의 상대 경로 링크가 올바른지 확인합니다.
   - 불필요한 중복 파일이 없는지 점검합니다.
3. **완료 보고**:
   - 생성된 디렉토리 구조 및 각 파일의 역할을 사용자에게 요약 보고합니다.
