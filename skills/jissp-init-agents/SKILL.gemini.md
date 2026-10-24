---
name: jissp-init-agents
description: >-
  프로젝트에 표준 멀티 AI 에이전트 작업 환경(AGENTS.md 및 .agents/ 구조)을 초기화하거나,
  기존 단일 AI 설정(예: .claude)을 표준 구조로 마이그레이션하는 스킬입니다.
---

# jissp-init-agents: AI 표준 작업 환경 초기화 스킬

이 스킬은 프로젝트에 `AGENTS.md` 단일 진입점 허브와 `.agents/` 체계(공용 지침·핵심 규칙, 개인화, 개발자 연동 가이드)를 스캐폴딩하고 설정합니다.
기본 구조에서 `.agents/README.md` 는 다른 문서를 참조하지 않으며, 상세 문서(`.agents/docs/`·`.agents/rules/`)도 만들지 않습니다. 필요해지면 사용자가 추가하고, 작업별 문서는 해당 스킬 설정에, 공통 문서는 README 참조로 연결합니다. (`INTEGRATION.md` 4장 참고)

---

## 1. 사전 진단 (Diagnostics)

작업 대상 디렉토리의 루트에서 다음 사항을 점검합니다:

1. **기존 AI 설정 감지**:
   - `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`
   - `.agents/`, `.claude/`, `.gemini/`
   - `.claude/CLAUDE.md`, `.claude/docs/`, `.claude/rules/` — 하나라도 내용이 있으면 **마이그레이션 모드**를 권장합니다.
   - 빈 디렉토리(`.agents/skills/`, `.gemini/skills/` 등)는 기존 설정으로 보지 않으며, 건드리지 않습니다.
2. **프로젝트 환경 분석**:
   - `package.json`, `tsconfig.json`, `requirements.txt`, `go.mod` 등을 통해 스택(Node/TS, NestJS, Next.js, Python 등) 파악
   - 모노레포 또는 단일 프로젝트 여부 확인
   - `.gitignore` 존재 여부 확인

---

## 2. 인터뷰 및 확인 (Interview)

대화를 통해 다음 사항을 사용자에게 확인합니다:

1. **초기화 모드**:
   - **신규 초기화**: 깨끗한 상태에서 표준 `.agents/` 및 `AGENTS.md` 생성
   - **기존 환경 마이그레이션**: 기존 설정(예: `.claude/`)을 유지하면서 `.agents/`로 연결 또는 이전
2. **프로젝트 기본 정보 확인**:
   - 프로젝트명 및 한 줄 설명
   - 주요 플랫폼/서브 프로젝트 구조(있을 경우)
3. **사용할 AI 도구 선택**:
   - Antigravity (agy), Claude Code, Cursor/Windsurf 등
   - Gemini CLI 는 Legacy 로 취급합니다. Antigravity 가 `AGENTS.md` 를 네이티브로 읽으므로 별도 진입점 파일을 만들지 않습니다. (4.5 참고)

---

## 3. 디렉토리 구조 스캐폴딩 (Scaffolding)

아래의 디렉토리 구조를 생성합니다:

```text
[프로젝트 루트]/
├── AGENTS.md                  # 🎯 [모든 AI의 최상위 진입점]
├── .claude/
│   └── CLAUDE.md              # 🔗 Claude Code 진입점 (`@../AGENTS.md` 한 줄, 커밋 대상)
└── .agents/
    ├── README.md              # 📌 공용 AI 지침 및 핵심 규칙(Core Rules)
    ├── README.local.md        # 🔒 로컬 개인화 지침 (.gitignore)
    ├── INTEGRATION.md         # 📖 개발자를 위한 AI 도구 연동/관리 가이드
    └── local-docs/            # 🔒 로컬 전용 문서 디렉토리 (.gitignore)
```

- `.agents/docs/`·`.agents/rules/` 는 만들지 않습니다. 일반 프로젝트는 `README.md` 의 Core Rules 와 기존 코드만으로 충분하다는 전제입니다.

- 루트에 `CLAUDE.md` · `GEMINI.md` 를 만들지 않습니다. `AGENTS.md` 를 가리키는 심볼릭 링크도 만들지 않습니다.
- `local-docs/` 에 `.gitkeep` 같은 자리표시 파일을 두지 않습니다. (어차피 git 제외 대상)

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
- **작성 기준**: 작업이 진행돼도 유효하고, 코드를 열기 전에 알아야 하는 **근본 정보**만 적습니다.
  - 적는 것: 기술 스택, 검증 명령, 도메인 용어, 구조 원칙·불변 조건, 금지 패턴
  - 적지 않는 것: 코드를 보면 알 수 있거나 작업하며 바뀌는 현재 상태 (모듈·파일·탭 목록, 모듈 간 import 관계, 구현된 기능 목록 등)
- 핵심 원칙(절대 추론 금지, 컨벤션 준수 등)
- 기술 스택 및 베이스 경로 정의
  - `tsconfig.json` 의 `paths` 등 경로 별칭이 있으면 `- **Path alias**: ...` 줄로 함께 적고, 없으면 `None` 으로 적습니다.
- **Build & verify** 줄: `package.json` scripts 등에서 확인된 검증 명령(typecheck·lint·test·build)을 실행 순서대로 적습니다. 확인된 명령이 없으면 줄을 제거합니다.
- **Agent Rule Protection 섹션**: 템플릿 문구를 그대로 유지합니다. 삭제하거나 완화하지 않습니다.
  - 사용자가 명시적으로 최신화를 요청한 경우가 아니면 AI 가 `AGENTS.md`·`.claude/CLAUDE.md`·`.agents/` 문서를 수정하지 못하게 하는 지침입니다.
- **Core Rules 섹션**: 상세 규칙 문서 대신, 이 프로젝트에서만 통하는 핵심 규칙을 짧은 불릿으로 적습니다.
  - 첫 줄 "Follow the existing code for anything not listed here..." 는 그대로 유지합니다. 나머지 컨벤션은 기존 코드가 기준입니다.
  - 형식: `- **[주제]**: [규칙]` 한 줄씩, 영어로 작성. 대략 5~10개.
  - 대상: 의존 방향·레이어 경계, 엔트리포인트 역할, 상수·메시지·에러 처리 위치, 보안상 금지 패턴, 주석 언어 등 **코드를 조금 읽어서는 알기 어렵거나 어기기 쉬운 것**.
  - 특정 모듈명을 나열하지 말고 원칙으로 적습니다. (예: `ui/ · session/ → shared/` 대신 "`shared/` 는 다른 모듈을 import 하지 않는다")
  - 코드·설정 파일에서 확인된 사실만 적습니다. 추측으로 채우지 않습니다. 코드가 거의 없는 신규 프로젝트라면 사용자에게 확인하거나 섹션을 첫 줄만 남깁니다.
  - 언어·프레임워크의 일반 상식(예: "타입을 잘 쓰세요")은 적지 않습니다.
- **Glossary 섹션 (선택)**: 코드 식별자만으로는 의미를 알기 어려운 도메인 용어를 `- **[용어]**: [뜻]` 한 줄씩 적습니다. 확인된 용어가 없으면 섹션째 제거합니다.
- 모호성 질문 정책 (Clarification & Interview Policy)

### 4.3 `.agents/INTEGRATION.md` (개발자용 연동 가이드)
- AI 에이전트가 읽지 않는 **개발자 전용 문서**
- Antigravity(agy), Claude Code, Cursor, Windsurf 등 각 도구에서 진입점(`AGENTS.md`)을 어떻게 바인딩하는지 안내
- 신규 AI 도구 추가 절차, 상세 문서 추가 방법(선택), 진입점 마이그레이션 히스토리 섹션 포함
- `{{INIT_DATE}}` 는 오늘 날짜(`YYYY-MM-DD`), `{{TARGET_TOOLS}}` 는 2장에서 선택한 도구로 채웁니다. 선택하지 않은 도구의 2장 하위 섹션은 그대로 두어도 됩니다. (연동 안내용)

### 4.4 `.agents/README.local.md` (개인화 로컬 지침)
- 한국어 답변 강제
- Inquiry(분석 단계) 안전 가드
- `.env` 접근 금지 및 Git 제약 사항
- `0-jissp-docs/` git add 제외
- 로컬 전용 문서(`.agents/local-docs/`) 안내

### 4.5 `.claude/CLAUDE.md` (Claude Code 진입점)
- 실제 파일로 생성하며, 내용은 아래 한 줄뿐입니다. 커밋 대상입니다.
  ```markdown
  @../AGENTS.md
  ```
- `.claude/` 의 다른 파일(`settings.json`, `hooks/`, `skills/`, `commands/` 등)은 건드리지 않습니다.
- Gemini CLI 가 꼭 필요하다는 요청이 있을 때만, 루트 `GEMINI.md` 를 **로컬 전용**으로 만들고 `.git/info/exclude` 에 `/GEMINI.md` 로 등록하도록 안내합니다. 스킬이 직접 만들지 않습니다.

---

## 4-M. 마이그레이션 절차 (기존 `.claude/` 설정이 있는 경우)

마이그레이션 모드에서는 4장의 템플릿 생성에 앞서 아래를 수행합니다. 진행 전에 이동·변경 목록을 사용자에게 보여주고 승인을 받습니다.

1. **기존 상세 문서 처리** (`.claude/docs/*`, `.claude/rules/*`, 기존 `.agents/docs/`·`.agents/rules/` 등): 사용자에게 아래 중 하나를 선택받습니다.
   - **Core Rules 로 압축 (권장)**: 핵심 규칙만 추려 `.agents/README.md` 의 Core Rules 로 옮기고, 원본은 `.agents/local-docs/` 로 백업한 뒤 원래 위치에서 제거합니다. 추적 중인 파일이면 제거는 `git rm` 으로 합니다. (커밋은 하지 않습니다)
   - **문서로 유지**: `.agents/docs/` 로 옮기고(`git mv` 로 이력 유지), 문서 안의 `.claude/docs/...`, `.claude/rules/...` 경로 참조를 `.agents/...` 로 고칩니다. README 에는 연결하지 않습니다.
     - 완료 보고에서 문서별 연결 방법을 안내합니다. 작업별 문서는 스킬 설정 등록, 공통 문서는 README 참조 추가입니다. (`INTEGRATION.md` 4장) 스킬 설정과 README 참조는 사용자가 요청한 경우에만 직접 추가합니다.
   - 같은 이름의 파일이 이미 대상 위치에 있으면 덮어쓰지 말고 사용자에게 확인합니다.
2. **기존 `.claude/CLAUDE.md` 정리**:
   - 원본 내용을 `.agents/local-docs/org.claude.md` 로 백업합니다. (git 제외 위치)
   - 원본에 있던 프로젝트 설명은 `AGENTS.md` 상단 설명으로, 지침·규칙은 `.agents/README.md` 의 Core Rules 로 옮깁니다.
   - 문서 참조 목록(`@./docs/...`, `@./rules/...`)은 제거합니다. (1번의 안내로 대체)
   - 정리가 끝나면 `.claude/CLAUDE.md` 내용을 `@../AGENTS.md` 한 줄로 교체합니다.
3. **루트 `CLAUDE.md`·`GEMINI.md` 가 있는 경우**: 삭제하지 말고, 내용과 처리 방법(이전 후 삭제 / 로컬 전용 유지)을 사용자에게 확인합니다.

---

## 5. 사후 작업 및 검증 (Post-Action)

1. **`.gitignore` 설정 점검**:
   - `.agents/README.local.md`
   - `.agents/local-docs/`
   위 두 항목이 `.gitignore`에 등록되어 있는지 확인하고, 없으면 추가하거나 사용자에게 안내합니다.
2. **동작 검증**:
   - 각 파일의 상대 경로 링크가 올바른지 확인합니다.
   - `.claude/CLAUDE.md` 가 실제 파일이고 내용이 `@../AGENTS.md` 인지 확인합니다.
   - 루트에 `CLAUDE.md` · `GEMINI.md` 가 생성되지 않았는지 확인합니다.
   - `.agents/docs/`·`.agents/rules/` 가 새로 생기지 않았는지 확인합니다. (마이그레이션에서 문서로 유지를 고른 경우 제외)
   - `.agents/README.md` 에 다른 문서를 참조하는 섹션이 없는지 확인합니다. (사용자가 참조 추가를 요청한 경우 제외. 그때는 표의 경로가 모두 실제 파일을 가리키는지 확인합니다)
   - 템플릿의 `{{...}}` 자리표시자가 남아 있지 않은지 확인합니다.
   - 불필요한 중복 파일이 없는지 점검합니다.
3. **완료 보고**:
   - 생성된 디렉토리 구조 및 각 파일의 역할을 사용자에게 요약 보고합니다.
