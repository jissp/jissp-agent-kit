#!/usr/bin/env bash
# skill-manual 조회 스크립트
#   man.sh list                 매뉴얼 목록 (스킬명 | 생성 일시)
#   man.sh show <스킬명>         매뉴얼 해석 → 최신 여부 확인 → 본문 출력
#
# show 출력의 첫 줄은 상태 코드입니다.
#   FOUND <스킬명>                      매뉴얼 있음 (이어서 본문)
#   STALE <스킬명>                      매뉴얼 있음 + 원본 스킬이 더 최근에 수정됨 (변경 파일 목록, 이어서 본문)
#   AMBIGUOUS <후보...>                 후보가 여럿
#   NOT_FOUND <query> [SKILL_EXISTS <스킬명>]  매뉴얼 없음 (원본 스킬이 있으면 함께 표시)

set -euo pipefail

BASE="$HOME/jissp-agent-kit/skills/skill-manual"
MANUALS="$BASE/manuals"
SKILL_ROOTS=("$HOME/jissp-agent-kit/skills" "$HOME/.claude/skills" "$HOME/.gemini/antigravity-cli/skills")

lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

# frontmatter 값 읽기: fm <파일> <키>
fm() { awk -v k="$2" 'NR==1&&/^---$/{f=1;next} f&&/^---$/{exit} f&&index($0,k": ")==1{sub("^"k": ","");print;exit}' "$1"; }

manual_files() { find "$MANUALS" -maxdepth 1 -name '*.md' -type f | sort; }

cmd_list() {
  local f
  printf '| 스킬 | 생성 일시 |\n|---|---|\n'
  for f in $(manual_files); do
    printf '| %s | %s |\n' "$(basename "$f" .md)" "$(fm "$f" generated_at)"
  done
}

resolve() {
  local q f name
  q="$(lower "$1")"

  # 1) 스킬명 정확히 일치
  [ -f "$MANUALS/$q.md" ] && { echo "$q"; return; }

  # 2) 스킬명 부분 일치
  for f in $(manual_files); do
    name="$(basename "$f" .md)"
    case "$name" in *"$q"*) echo "$name" ;; esac
  done
}

cmd_show() {
  local q="$1" hits count name manual src changed root
  hits="$(resolve "$q")"
  count="$(printf '%s' "$hits" | grep -c . || true)"

  if [ "$count" -eq 0 ]; then
    for root in "${SKILL_ROOTS[@]}"; do
      [ -d "$root/$q" ] && { echo "NOT_FOUND $q SKILL_EXISTS $q"; return; }
    done
    echo "NOT_FOUND $q"
    return
  fi
  if [ "$count" -gt 1 ]; then
    echo "AMBIGUOUS $(printf '%s' "$hits" | tr '\n' ' ')"
    return
  fi

  name="$hits"
  manual="$MANUALS/$name.md"
  src="$(fm "$manual" source)"
  src="${src/#\~/$HOME}"
  changed=""
  [ -n "$src" ] && [ -d "$src" ] && changed="$(find -L "$src" -type f -name '*.md' -newer "$manual" 2>/dev/null | head -5)"

  if [ -n "$changed" ]; then
    echo "STALE $name"
    printf '%s\n' "$changed" | sed "s#^$src/#  - #"
  else
    echo "FOUND $name"
  fi
  echo "---"
  # frontmatter 제외한 본문만 출력
  awk 'NR==1&&/^---$/{f=1;next} f&&/^---$/{f=0;next} !f' "$manual"
}

case "${1:-list}" in
  list) cmd_list ;;
  show) [ -n "${2:-}" ] || { echo "usage: man.sh show <스킬명>" >&2; exit 1; }; cmd_show "$2" ;;
  *) echo "usage: man.sh [list|show <스킬명>]" >&2; exit 1 ;;
esac
