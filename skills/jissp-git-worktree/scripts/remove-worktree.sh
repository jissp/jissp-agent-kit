#!/usr/bin/env bash
#
# remove-worktree.sh
#
# create-worktree.sh 로 만든 worktree를 안전하게 제거한다.
#
# 공유용 심볼릭 링크(메인 repo를 가리키는 링크)를 먼저 걷어낸 뒤 `git worktree remove` 를
# --force 없이 실행한다. 링크로 교체한 추적 파일은 skip-worktree 처리되어 있으므로,
# 제거가 거부되면 그것은 커밋하지 않은 "실제 작업 내용"이 남아 있다는 뜻이다.
# 이 경우 걷어낸 링크를 원래대로 복구하고 실패로 종료한다.
#
# 사용법:
#   remove-worktree.sh <branch|worktree-path> [--delete-branch] [--force]
#
#   <branch|worktree-path>  제거할 worktree의 브랜치명 또는 경로 (필수)
#   --delete-branch         제거 후 브랜치도 삭제 (git branch -d — 병합되지 않은 브랜치는 삭제하지 않음)
#   --force                 커밋하지 않은 변경이 있어도 강제로 제거 (변경 내용이 사라짐)
#
set -euo pipefail

USAGE="사용법: remove-worktree.sh <branch|worktree-path> [--delete-branch] [--force]"

die() {
  echo "❌ $1" >&2
  exit 1
}

# ---- 인자 파싱 -------------------------------------------------------------
TARGET=""
DELETE_BRANCH=false
FORCE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --delete-branch) DELETE_BRANCH=true; shift ;;
    --force)         FORCE=true; shift ;;
    -h|--help)       echo "$USAGE"; exit 0 ;;
    -*)              die "알 수 없는 옵션입니다: $1
   $USAGE" ;;
    *)
      [[ -z "$TARGET" ]] || die "인자가 너무 많습니다: $1
   $USAGE"
      TARGET="$1"
      shift
      ;;
  esac
done

[[ -n "$TARGET" ]] || die "제거할 worktree의 브랜치명 또는 경로가 필요합니다.
   $USAGE"

# ---- 메인 repo / 대상 worktree 확인 ----------------------------------------
COMMON_GIT_DIR="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)" \
  || die "git 저장소 안에서 실행해야 합니다."
[[ "$(basename "$COMMON_GIT_DIR")" == ".git" ]] \
  || die "메인 repo를 찾을 수 없습니다 (bare 저장소는 지원하지 않습니다): $COMMON_GIT_DIR"
MAIN_REPO="$(dirname "$COMMON_GIT_DIR")"

# worktree list 에서 "<경로>\t<브랜치>" 목록을 만든다. (detached HEAD 는 브랜치가 빈 값)
worktree_entries() {
  git -C "$MAIN_REPO" worktree list --porcelain | awk '
    /^worktree / { if (path != "") print path "\t" branch; path = substr($0, 10); branch = "" }
    /^branch /   { branch = substr($0, 8); sub(/^refs\/heads\//, "", branch) }
    END          { if (path != "") print path "\t" branch }
  '
}

WT_PATH=""
WT_BRANCH=""
if [[ -d "$TARGET" ]]; then
  TARGET_REAL="$(cd "$TARGET" && pwd -P)"
  while IFS=$'\t' read -r path branch; do
    if [[ "$path" == "$TARGET_REAL" ]]; then WT_PATH="$path"; WT_BRANCH="$branch"; fi
  done < <(worktree_entries)
else
  while IFS=$'\t' read -r path branch; do
    if [[ "$branch" == "$TARGET" ]]; then WT_PATH="$path"; WT_BRANCH="$branch"; fi
  done < <(worktree_entries)
fi

[[ -n "$WT_PATH" ]] || die "'$TARGET' 에 해당하는 worktree를 찾을 수 없습니다. ('git worktree list' 로 확인하세요)"
[[ "$WT_PATH" != "$MAIN_REPO" ]] || die "메인 repo는 제거할 수 없습니다: $WT_PATH"

case "$PWD/" in
  "$WT_PATH"/*) die "제거할 worktree 안에서 실행 중입니다. 메인 repo 등 다른 위치에서 실행하세요." ;;
esac

echo "📁 메인 repo : $MAIN_REPO"
echo "📂 worktree  : $WT_PATH"
echo "🌿 브랜치    : ${WT_BRANCH:-(detached HEAD)}"
echo ""

# ---- 공유 링크 걷어내기 ----------------------------------------------------
# 메인 repo를 가리키는 절대 경로 링크만 대상으로 한다. (node_modules 내부는 탐색하지 않음)
link_paths=()
link_targets=()
while IFS= read -r -d '' link; do
  target="$(readlink "$link")"
  case "$target" in
    "$MAIN_REPO"/*)
      link_paths+=("$link")
      link_targets+=("$target")
      ;;
  esac
done < <(find "$WT_PATH" -name node_modules -prune -o -name .git -prune -o -type l -print0)

for link in ${link_paths[@]+"${link_paths[@]}"}; do rm "$link"; done

restore_links() {
  local i
  for i in "${!link_paths[@]}"; do
    [[ -e "${link_paths[$i]}" || -L "${link_paths[$i]}" ]] || ln -s "${link_targets[$i]}" "${link_paths[$i]}"
  done
}

# ---- worktree 제거 ---------------------------------------------------------
remove_args=()
[[ "$FORCE" == true ]] && remove_args+=(--force)

if ! git -C "$MAIN_REPO" worktree remove ${remove_args[@]+"${remove_args[@]}"} "$WT_PATH"; then
  restore_links
  echo "" >&2
  echo "❌ worktree에 커밋하지 않은 변경이 남아 있어 제거하지 않았습니다. (공유 링크는 복구함)" >&2
  echo "   변경 내용 확인: git -C \"$WT_PATH\" status" >&2
  echo "   변경을 버리고 강제로 제거하려면 --force 를 붙여 다시 실행하세요." >&2
  exit 1
fi

echo "✅ worktree 제거 완료 (공유 링크 ${#link_paths[@]}개 해제 — 메인 repo 원본은 그대로입니다)"

# ---- 브랜치 삭제 (선택) ----------------------------------------------------
if [[ "$DELETE_BRANCH" == true ]]; then
  if [[ -z "$WT_BRANCH" ]]; then
    echo "ℹ️  detached HEAD 상태의 worktree라 삭제할 브랜치가 없습니다."
  elif git -C "$MAIN_REPO" branch -d "$WT_BRANCH"; then
    echo "✅ 브랜치 삭제 완료: $WT_BRANCH"
  else
    echo "⚠️  '$WT_BRANCH' 브랜치는 병합되지 않아 삭제하지 않았습니다." >&2
    echo "   정말 삭제하려면 직접 실행하세요: git branch -D \"$WT_BRANCH\"" >&2
  fi
fi
