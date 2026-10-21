#!/usr/bin/env bash
#
# create-worktree.sh
#
# git worktree를 워크스페이스의 worktrees 디렉토리에 생성하고, 메인 repo의 자산을
# 심볼릭 링크(ln -s)로 공유한다. 링크 대상은 스크립트에 하드코딩하지 않고
# "목록 파일"에서 읽는다.
#
# 목록 파일 우선순위:
#   1) <main-repo>/.worktree-links            (로컬 전용, 있으면 우선)
#   2) <skill-dir>/worktree-links.default     (스킬 기본값)
#
# 목록 파일 형식 (.gitignore 스타일):
#   - 한 줄에 하나씩, 메인 repo 루트 기준 상대 경로
#   - '#'로 시작하는 줄과 빈 줄은 무시
#   - git 추적 항목/비추적 항목 구분 없이 적어도 스크립트가 자동 판별
#   - 절대 경로나 '..' 이 포함된 경로는 거부
#
# 항상 "새 브랜치"를 만든다. 이미 존재하는 브랜치명(로컬 또는 origin)이면 에러로 중단한다.
#
# 분기 기준(base) 결정 순서 (--base 미지정 시):
#   1) origin/dev  (fetch 후 최신 상태)
#   2) 로컬 dev
#   3) origin 의 기본 브랜치 (origin/HEAD, 보통 origin/main)
#   어느 것도 없으면 에러로 중단하고 --base 지정을 안내한다.
#
# 사용법:
#   create-worktree.sh <branch> [worktree-path] [--base <ref>] [--links <file>]
#
#   <branch>          새로 만들 브랜치명 (필수)
#   [worktree-path]   worktree 경로 (생략 시 <workspace>/worktrees/<repo>-<branch> 자동 계산)
#   --base <ref>      분기 기준 직접 지정 (예: main, origin/release/1.2)
#   --links <file>    링크 목록 파일을 직접 지정 (우선순위 무시)
#
# 예시:
#   create-worktree.sh feature/login
#   create-worktree.sh hotfix/pay --base origin/main
#   create-worktree.sh feature/login /tmp/my-login
#   create-worktree.sh feature/login --links ./my-links.txt
#
# 이미 등록된 worktree 경로에 다시 실행하면 브랜치는 건드리지 않고 누락된 링크만 추가한다.
#
# 메인 repo 안이든, 이미 만든 worktree 안이든 어디서 실행해도 메인 repo를 기준으로 동작한다.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"   # worktree-links.default 가 위치한 스킬 루트

USAGE="사용법: create-worktree.sh <branch> [worktree-path] [--base <ref>] [--links <file>]"
DEFAULT_BASE_BRANCH="dev"

die() {
  echo "❌ $1" >&2
  exit 1
}

# ---- 인자 파싱 -------------------------------------------------------------
BRANCH=""
WT_PATH=""
BASE_REF=""
LINKS_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base|--links)
      [[ $# -ge 2 && -n "$2" && "$2" != --* ]] || die "$1 옵션에 값이 필요합니다.
   $USAGE"
      [[ "$1" == --base ]] && BASE_REF="$2" || LINKS_OVERRIDE="$2"
      shift 2
      ;;
    -h|--help)
      echo "$USAGE"
      exit 0
      ;;
    -*)
      die "알 수 없는 옵션입니다: $1
   $USAGE"
      ;;
    *)
      if [[ -z "$BRANCH" ]]; then
        BRANCH="$1"
      elif [[ -z "$WT_PATH" ]]; then
        WT_PATH="$1"
      else
        die "인자가 너무 많습니다: $1
   $USAGE"
      fi
      shift
      ;;
  esac
done

[[ -n "$BRANCH" ]] || die "브랜치명이 필요합니다.
   $USAGE"

# ---- 메인 repo 루트 / worktree 경로 계산 ----------------------------------
# --show-toplevel 은 worktree 안에서 실행하면 그 worktree를 가리키므로,
# 모든 worktree가 공유하는 common git dir(<main-repo>/.git)에서 메인 repo를 구한다.
COMMON_GIT_DIR="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)" \
  || die "git 저장소 안에서 실행해야 합니다."
[[ "$(basename "$COMMON_GIT_DIR")" == ".git" ]] \
  || die "메인 repo를 찾을 수 없습니다 (bare 저장소는 지원하지 않습니다): $COMMON_GIT_DIR"
MAIN_REPO="$(dirname "$COMMON_GIT_DIR")"
REPO_NAME="$(basename "$MAIN_REPO")"
PARENT_DIR="$(dirname "$MAIN_REPO")"

# 브랜치명의 슬래시(/)는 디렉토리명에서 하이픈(-)으로 치환한다.
BRANCH_SLUG="${BRANCH//\//-}"

# 경로 미지정 시 워크스페이스(메인 repo의 부모)의 worktrees 디렉토리 아래에
# "<repo>-<branch-slug>" 형태로 생성한다.
#   예) /…/workspace/my-api 에서 refact/pg → /…/workspace/worktrees/my-api-refact-pg
if [[ -z "$WT_PATH" ]]; then
  WT_PATH="${PARENT_DIR}/worktrees/${REPO_NAME}-${BRANCH_SLUG}"
fi

# 절대 경로로 정규화 (심볼릭 링크가 어디서든 깨지지 않도록)
mkdir -p "$(dirname "$WT_PATH")"
WT_PATH="$(cd "$(dirname "$WT_PATH")" && pwd -P)/$(basename "$WT_PATH")"

# ---- 기존 경로 검증 --------------------------------------------------------
is_registered_worktree() {
  git -C "$MAIN_REPO" worktree list --porcelain | grep -Fxq "worktree $1"
}

WT_EXISTS=false
if [[ -e "$WT_PATH" || -L "$WT_PATH" ]]; then
  [[ -d "$WT_PATH" && ! -L "$WT_PATH" ]] || die "worktree 경로에 디렉토리가 아닌 파일이 있습니다: $WT_PATH"
  [[ "$WT_PATH" != "$MAIN_REPO" ]] || die "worktree 경로가 메인 repo와 같습니다: $WT_PATH"
  is_registered_worktree "$WT_PATH" \
    || die "경로가 이미 존재하지만 이 repo의 worktree가 아닙니다: $WT_PATH
   다른 경로를 지정하거나 해당 디렉토리를 정리한 뒤 다시 실행하세요."
  WT_EXISTS=true
fi

# ---- 브랜치 / 분기 기준 결정 ---------------------------------------------
has_origin() {
  git -C "$MAIN_REPO" remote get-url origin >/dev/null 2>&1
}
ref_exists() {
  git -C "$MAIN_REPO" show-ref --verify --quiet "$1"
}
fetch_remote_branch() {
  # origin 의 브랜치 하나를 최신화한다. 실패(네트워크·미존재)는 호출 측에서 ref 존재로 판단한다.
  has_origin || return 1
  GIT_TERMINAL_PROMPT=0 git -C "$MAIN_REPO" fetch --quiet origin \
    "refs/heads/$1:refs/remotes/origin/$1" 2>/dev/null
}
remote_default_branch() {
  # origin/HEAD 가 가리키는 기본 브랜치명을 출력한다. 로컬에 설정이 없으면 원격에 물어 설정한다.
  local head
  head="$(git -C "$MAIN_REPO" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)" \
    || { GIT_TERMINAL_PROMPT=0 git -C "$MAIN_REPO" remote set-head origin --auto >/dev/null 2>&1 \
         && head="$(git -C "$MAIN_REPO" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)"; } \
    || return 1
  echo "${head#origin/}"
}

if [[ "$WT_EXISTS" == true ]]; then
  [[ -z "$BASE_REF" ]] || die "--base 는 새 worktree를 만들 때만 사용할 수 있습니다. 이미 존재하는 worktree입니다: $WT_PATH"
else
  # 기존 브랜치 보호: 원격에만 있는 브랜치도 놓치지 않도록 fetch 후 확인한다.
  fetch_remote_branch "$BRANCH" || true
  if ref_exists "refs/heads/${BRANCH}" || ref_exists "refs/remotes/origin/${BRANCH}"; then
    die "'${BRANCH}' 브랜치가 이미 존재합니다 (로컬 또는 origin). 새 브랜치명을 지정하세요."
  fi

  if [[ -n "$BASE_REF" ]]; then
    [[ "$BASE_REF" == origin/* ]] && { fetch_remote_branch "${BASE_REF#origin/}" || true; }
    git -C "$MAIN_REPO" rev-parse --verify --quiet "${BASE_REF}^{commit}" >/dev/null \
      || die "--base 로 지정한 ref를 찾을 수 없습니다: ${BASE_REF}"
  else
    fetch_remote_branch "$DEFAULT_BASE_BRANCH" || true
    if ref_exists "refs/remotes/origin/${DEFAULT_BASE_BRANCH}"; then
      BASE_REF="origin/${DEFAULT_BASE_BRANCH}"
    elif ref_exists "refs/heads/${DEFAULT_BASE_BRANCH}"; then
      BASE_REF="${DEFAULT_BASE_BRANCH}"
    elif default_branch="$(remote_default_branch)"; then
      fetch_remote_branch "$default_branch" || true
      ref_exists "refs/remotes/origin/${default_branch}" \
        || die "origin 기본 브랜치(${default_branch})를 찾을 수 없습니다. --base 로 분기 기준을 지정하세요."
      BASE_REF="origin/${default_branch}"
      echo "ℹ️  '${DEFAULT_BASE_BRANCH}' 브랜치가 없어 origin 기본 브랜치(${default_branch})에서 분기합니다."
    else
      die "'${DEFAULT_BASE_BRANCH}' 브랜치와 origin 기본 브랜치를 모두 찾을 수 없습니다. --base 로 분기 기준을 지정하세요."
    fi
  fi
fi

# ---- 링크 목록 파일 결정 ---------------------------------------------------
if [[ -n "$LINKS_OVERRIDE" ]]; then
  LINKS_FILE="$LINKS_OVERRIDE"
elif [[ -f "${MAIN_REPO}/.worktree-links" ]]; then
  LINKS_FILE="${MAIN_REPO}/.worktree-links"
else
  LINKS_FILE="${SKILL_DIR}/worktree-links.default"
fi

[[ -f "$LINKS_FILE" ]] || die "링크 목록 파일을 찾을 수 없습니다: $LINKS_FILE"

# 목록 파일에서 대상 경로를 파싱한다.
ITEMS=()
while IFS= read -r raw || [[ -n "$raw" ]]; do
  raw="${raw%$'\r'}"                         # CRLF 대비
  raw="${raw#"${raw%%[![:space:]]*}"}"       # 앞 공백 제거
  raw="${raw%"${raw##*[![:space:]]}"}"       # 뒤 공백 제거
  [[ -z "$raw" || "$raw" == \#* ]] && continue
  raw="${raw%/}"                             # 끝 슬래시 제거 (.claude/ → .claude)
  ITEMS+=("$raw")
done < "$LINKS_FILE"

echo "📁 메인 repo : $MAIN_REPO"
if [[ "$WT_EXISTS" == true ]]; then
  echo "🌿 브랜치    : $BRANCH (기존 worktree)"
else
  echo "🌿 브랜치    : $BRANCH (신규, 분기 기준: $BASE_REF)"
fi
echo "📂 worktree  : $WT_PATH"
echo "📋 링크 목록 : $LINKS_FILE (${#ITEMS[@]}개 항목)"
echo ""

# ---- worktree 생성 ---------------------------------------------------------
if [[ "$WT_EXISTS" == true ]]; then
  echo "ℹ️  이미 등록된 worktree입니다. 누락된 링크만 추가합니다."
else
  # --no-track: 원격 브랜치(origin/dev 등)에서 분기하면 새 브랜치가 그 브랜치를 upstream 으로
  # 추적해 pull/push 대상이 base 로 엉키므로, 추적 설정 없이 분기만 한다.
  # (첫 push 때 'git push -u origin <branch>' 로 자기 이름의 원격 브랜치를 추적하게 된다)
  git -C "$MAIN_REPO" worktree add --no-track -b "$BRANCH" "$WT_PATH" "$BASE_REF"
fi
echo ""

# ---- 심볼릭 링크 설정 ------------------------------------------------------
linked=()
skipped=()
tracked_linked=()

is_tracked() {
  # 경로(파일/디렉토리)가 git 추적 대상이면 0을 반환한다.
  git -C "$MAIN_REPO" ls-files --error-unmatch -- "$1" >/dev/null 2>&1
}

is_safe_item() {
  # 절대 경로, '.', '..' 구성요소가 포함된 경로는 worktree 밖을 건드릴 수 있으므로 거부한다.
  local item="$1" part
  local -a parts
  [[ "$item" != /* ]] || return 1
  IFS='/' read -r -a parts <<< "$item"
  for part in "${parts[@]}"; do
    [[ -n "$part" && "$part" != "." && "$part" != ".." ]] || return 1
  done
}

linked_ancestor() {
  # 상위 경로 중 이미 심볼릭 링크인 것이 있으면 그 경로를 출력한다.
  # (예: .claude 가 링크된 상태에서 .claude/skills/foo 를 처리하면 실제로는
  #  메인 repo 안을 건드리게 되므로, 이런 항목은 반드시 건너뛰어야 한다.)
  local item="$1" prefix=""
  local -a parts
  IFS='/' read -r -a parts <<< "$item"
  local last=$(( ${#parts[@]} - 1 )) i
  for (( i = 0; i < last; i++ )); do
    prefix="${prefix:+$prefix/}${parts[$i]}"
    if [[ -L "${WT_PATH}/${prefix}" ]]; then
      echo "$prefix"
      return 0
    fi
  done
  return 1
}

hide_tracked_changes() {
  # 링크로 교체한 추적 파일에 skip-worktree 를 걸어 git status 에 삭제/변경으로 잡히지 않게 한다.
  # (worktree 별 index 에만 적용되며 메인 repo 에는 영향이 없다.)
  local item="$1" f
  local files=()
  while IFS= read -r -d '' f; do files+=("$f"); done \
    < <(git -C "$WT_PATH" ls-files -z -- "$item")
  [[ ${#files[@]} -gt 0 ]] && git -C "$WT_PATH" update-index --skip-worktree -- "${files[@]}"
  return 0
}

for item in "${ITEMS[@]}"; do
  if ! is_safe_item "$item"; then
    skipped+=("$item (허용되지 않는 경로 — 절대 경로나 '..' 사용 불가)")
    continue
  fi

  src="${MAIN_REPO}/${item}"
  dst="${WT_PATH}/${item}"

  # 원본이 없으면 건너뛴다.
  if [[ ! -e "$src" && ! -L "$src" ]]; then
    skipped+=("$item (메인 repo에 없음)")
    continue
  fi

  if ancestor="$(linked_ancestor "$item")"; then
    skipped+=("$item (상위 경로 '${ancestor}' 가 이미 링크되어 함께 공유됨)")
    continue
  fi

  # 이미 올바른 심볼릭 링크면 멱등 처리로 건너뛴다.
  if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then
    skipped+=("$item (이미 링크됨)")
    continue
  fi

  if [[ -e "$dst" || -L "$dst" ]]; then
    # 이번 실행에서 막 생성한 worktree 의 추적 항목만 교체한다. 그 외에 실제 파일/디렉토리가
    # 있다면 사용자가 수동 분리한 것으로 보고 절대 지우지 않는다.
    if [[ "$WT_EXISTS" == true || -L "$dst" ]] || ! is_tracked "$item"; then
      skipped+=("$item (worktree에 실제 파일/다른 링크가 있음 — 수동 분리로 보고 유지)")
      continue
    fi
    rm -rf "$dst"
  fi

  mkdir -p "$(dirname "$dst")"
  ln -s "$src" "$dst"
  linked+=("$item")

  if is_tracked "$item"; then
    hide_tracked_changes "$item"
    tracked_linked+=("$item")
  fi
done

# ---- 결과 요약 -------------------------------------------------------------
echo "✅ worktree 준비 완료"
echo ""
echo "🔗 링크된 항목:"
if [[ ${#linked[@]} -eq 0 ]]; then
  echo "   (없음)"
else
  for i in "${linked[@]}"; do echo "   - $i"; done
fi

if [[ ${#skipped[@]} -gt 0 ]]; then
  echo ""
  echo "⏭️  건너뛴 항목:"
  for i in "${skipped[@]}"; do echo "   - $i"; done
fi

if [[ ${#tracked_linked[@]} -gt 0 ]]; then
  echo ""
  echo "⚠️  아래 항목은 git 추적 대상이라 링크로 교체하고 skip-worktree 를 적용했습니다."
  echo "    파일 변경은 git status 에 잡히지 않지만, 링크 자체가 '??' 로 보일 수 있습니다."
  echo "    → 이 항목들은 이 worktree에서 add/커밋하지 마세요. (수정은 메인 repo 원본에 반영됩니다)"
  for i in "${tracked_linked[@]}"; do echo "    - $i"; done
fi

echo ""
echo "📦 의존성 디렉토리·빌드 산출물(node_modules, dist 등)은 목록에 없으면 공유되지 않습니다."
if [[ -f "${WT_PATH}/package.json" ]]; then
  echo "    → 필요 시 'cd \"$WT_PATH\" && npm install' 로 의존성을 설치하세요."
else
  echo "    → 필요 시 worktree에서 의존성 설치·빌드를 진행하세요."
fi
echo ""
echo "🚀 IDE에서 열기:  $WT_PATH"
echo "🧹 제거하려면:    bash \"${SCRIPT_DIR}/remove-worktree.sh\" \"$BRANCH\""
