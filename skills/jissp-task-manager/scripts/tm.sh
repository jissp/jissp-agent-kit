#!/usr/bin/env bash
# jissp-task-manager 결정적 파일 조작 스크립트
# - 규칙대로만 하면 되는 조작(생성·번호·상태 갱신·이동·목록)만 담당합니다. 판단·대화는 스킬이 합니다.
# - 출력은 표 없이 한 줄에 한 항목, 필드는 탭(\t)으로 구분합니다.
# - 프로젝트 루트(현재 작업 디렉토리) 기준으로 동작합니다. TM_DOCS 로 [Jissp 문서] 경로를 바꿀 수 있습니다.
set -euo pipefail

DOCS="${TM_DOCS:-$PWD/0-jissp-docs}"
ROOT="$DOCS/features"
STATUSES="backlog wait processing completed holding"
RESERVED="maintenance backlog holding completed all"

die() { echo "error: $*" >&2; exit 1; }
now() { date +"%Y-%m-%d %H:%M:%S"; }
rel() { echo "${1#$DOCS/}"; }

# ---------- frontmatter ----------

fm_get() { # <file> <key>
  awk -v k="$2" '
    NR==1 && $0=="---" {in_fm=1; next}
    in_fm && $0=="---" {exit}
    in_fm {
      i=index($0,":"); if (i==0) next
      if (substr($0,1,i-1)==k) { v=substr($0,i+1); sub(/^[ \t]+/,"",v); sub(/[ \t]+#.*$/,"",v); sub(/[ \t]+$/,"",v); print v; exit }
    }' "$1"
}

fm_set() { # <file> <key> <value> : 키가 없으면 닫는 --- 앞에 추가
  local tmp; tmp="$(mktemp)"
  awk -v k="$2" -v v="$3" '
    NR==1 && $0=="---" {in_fm=1; print; next}
    BEGIN { line = (v=="") ? k ":" : k ": " v }
    in_fm && $0=="---" { if (!done) print line; in_fm=0; print; next }
    in_fm { i=index($0,":"); if (i>0 && substr($0,1,i-1)==k) { print line; done=1; next } }
    {print}' "$1" > "$tmp"
  mv "$tmp" "$1"
}

append_line() { # <file> <heading> <line> : 이력 절(파일의 마지막 절)에 한 줄 추가. 절이 없으면 파일 끝에 만듦
  [ -n "$(tail -c1 "$1")" ] && echo >> "$1"
  grep -qxF "$2" "$1" || printf '\n%s\n\n' "$2" >> "$1"
  echo "$3" >> "$1"
}
task_log() { append_line "$1" "## 작업 이력" "$2"; }
feature_log() { append_line "$1" "## 이력" "$2"; }

# ---------- 경로 ----------

feature_dir() { # <slug> : 진행 중 → 완료 순으로 찾음
  if [ -d "$ROOT/$1" ]; then echo "$ROOT/$1"
  elif [ -d "$ROOT/_completed/$1" ]; then echo "$ROOT/_completed/$1"
  else return 1; fi
}

task_readmes() { # <feature_dir> <scope> : scope = active|backlog|holding|completed|all
  local d="$1/tasks" scope="$2" slug; slug="$(basename "$1")"
  [ -d "$d" ] || return 0
  if [ "$slug" = "maintenance" ]; then
    case "$scope" in
      active) ls -1d "$d"/*/README.md 2>/dev/null | grep -Ev '/tasks/(backlog|holding|completed)/' || true ;;
      backlog|holding|completed) ls -1d "$d/$scope"/*/README.md 2>/dev/null || true ;;
      all) { ls -1d "$d"/*/README.md "$d"/{backlog,holding,completed}/*/README.md 2>/dev/null || true; } | grep -Ev '/tasks/(backlog|holding|completed)/README.md$' || true ;;
    esac
  else
    local f s
    for f in "$d"/*/README.md; do
      [ -f "$f" ] || continue
      s="$(fm_get "$f" status)"
      case "$scope" in
        all) echo "$f" ;;
        active) [ "$s" = wait ] || [ "$s" = processing ] && echo "$f" || true ;;
        *) [ "$s" = "$scope" ] && echo "$f" || true ;;
      esac
    done
  fi
}

task_line() { # <README> → feature/dir  status  name  updated_at
  local f="$1" dir proj
  dir="$(dirname "$f")"; proj="$(fm_get "$f" feature)"
  [ -n "$proj" ] || proj="$(basename "$(dirname "$(dirname "$dir")")")"
  printf '%s\t%s\t%s\t%s\n' "$(rel "$dir")" "$(fm_get "$f" status)" "$(fm_get "$f" name)" "$(fm_get "$f" updated_at)"
}

max_number() { # <feature_dir> : 디렉토리 번호와 README 이력의 삭제 기록 중 최댓값
  local d="$1" m=0 n
  for n in $( { ls -1 "$d/tasks" 2>/dev/null; grep -oE '태스크 삭제: [0-9]+_' "$d/README.md" 2>/dev/null | grep -oE '[0-9]+'; } | grep -oE '^[0-9]+' ); do
    n=$((10#$n)); [ "$n" -gt "$m" ] && m=$n
  done
  echo "$m"
}

ensure_maintenance() {
  local d="$ROOT/maintenance" t
  [ -f "$d/README.md" ] && return 0
  mkdir -p "$d/tasks"; t="$(now)"
  cat > "$d/README.md" <<EOF
---
name: maintenance
type: maintenance
created_at: $t
updated_at: $t
---

# 유지보수

## 개요

어떤 feature에도 속하지 않는 단발성 작업을 관리하는 공용 버킷입니다.

## 이력

- $t 생성
EOF
}

# ---------- 명령 ----------

cmd_features() { # [all] → slug  status  done/total  next_wait
  [ -d "$ROOT" ] || return 0
  local d slug f total done next s
  for d in "$ROOT"/*/ ${1:+"$ROOT"/_completed/*/}; do
    [ -f "$d/README.md" ] || continue
    slug="$(basename "$d")"; [ "$slug" = "_completed" ] && continue
    if [ "$slug" = "maintenance" ]; then
      printf 'maintenance\t-\tactive %s\t-\n' "$(task_readmes "${d%/}" active | grep -c . || true)"
      continue
    fi
    total=0; done=0; next="-"
    for f in "$d"tasks/*/README.md; do
      [ -f "$f" ] || continue
      total=$((total+1)); s="$(fm_get "$f" status)"
      [ "$s" = completed ] && done=$((done+1))
      [ "$s" = wait ] && [ "$next" = "-" ] && next="$(basename "$(dirname "$f")")"
    done
    printf '%s\t%s\t%s/%s\t%s\n' "$slug" "$(fm_get "$d/README.md" status)" "$done" "$total" "$next"
  done
}

cmd_tasks() { # [feature] [scope]
  local p="${1:-}" scope="${2:-}" d f
  case "$p" in backlog|holding|completed|all) scope="$p"; p="" ;; esac
  if [ -n "$p" ]; then
    d="$(feature_dir "$p")" || die "feature not found: $p"
    if [ -z "$scope" ]; then [ "$p" = maintenance ] && scope=active || scope=all; fi
    task_readmes "$d" "$scope" | while read -r f; do task_line "$f"; done
  else
    [ -d "$ROOT" ] || return 0
    for d in "$ROOT"/*/; do
      [ "$(basename "$d")" = "_completed" ] && continue
      task_readmes "${d%/}" "${scope:-active}" | while read -r f; do task_line "$f"; done
    done
  fi
}

cmd_find() { # <query> [feature] → 일치 태스크 디렉토리 (탐색 순서대로)
  local q="$1" p="${2:-}" d f base num
  num=""; [[ "$q" =~ ^[0-9]+$ ]] && num="$((10#$q))"
  {
    if [ -n "$p" ]; then d="$(feature_dir "$p")" || die "feature not found: $p"; task_readmes "$d" all
    else
      for d in "$ROOT"/*/; do case "$(basename "$d")" in _completed|maintenance) ;; *) task_readmes "${d%/}" all ;; esac; done
      [ -d "$ROOT/maintenance" ] && for s in active backlog holding completed; do task_readmes "$ROOT/maintenance" "$s"; done
      for d in "$ROOT"/_completed/*/; do [ -d "$d" ] && task_readmes "${d%/}" all; done
    fi
  } | while read -r f; do
    base="$(basename "$(dirname "$f")")"
    if [ -n "$num" ]; then [[ "$base" =~ ^0*${num}_ ]] && rel "$(dirname "$f")"
    else case "$base" in *"$q"*) rel "$(dirname "$f")" ;; esac; fi
  done
}

cmd_new_feature() { # <slug> [title]
  local slug="$1" title="${2:-$1}" d t
  [[ "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]] || die "slug must be kebab-case: $slug"
  for r in $RESERVED; do [ "$slug" = "$r" ] && die "reserved slug: $slug"; done
  [ -e "$ROOT/$slug" ] && die "already exists: $(rel "$ROOT/$slug")"
  [ -e "$ROOT/_completed/$slug" ] && die "completed feature exists (reopen instead): $(rel "$ROOT/_completed/$slug")"
  ensure_maintenance
  d="$ROOT/$slug"; mkdir -p "$d/docs" "$d/tasks"; t="$(now)"
  cat > "$d/README.md" <<EOF
---
name: $slug
type: feature
status: processing
created_at: $t
updated_at: $t
---

# $title

## 개요

(미정)

## 참고 문서

(없음)

## 태스크 목록

| # | 태스크 | 상태 | 문서 | 완료일 |
|---|---|---|---|---|

## 이력

- $t feature 생성
EOF
  rel "$d"
}

cmd_new_task() { # <feature> <slug> [wait|backlog]
  local p="$1" slug="$2" st="${3:-wait}" d dir t
  [[ "$slug" =~ ^[a-z0-9][a-z0-9-]*$ ]] || die "slug must be kebab-case: $slug"
  [ "$st" = wait ] || [ "$st" = backlog ] || die "initial status must be wait|backlog"
  ensure_maintenance
  [ -d "$ROOT/$p" ] || die "feature not found (or completed): $p"
  d="$ROOT/$p"; t="$(now)"
  if [ "$p" = maintenance ]; then
    dir="$d/tasks/$( [ "$st" = backlog ] && echo backlog/ )$(date +%Y%m%d_%H%M%S)_$slug"
  else
    dir="$d/tasks/$(printf '%02d' $(( $(max_number "$d") + 1 )))_$slug"
  fi
  [ -e "$dir" ] && die "already exists: $(rel "$dir")"
  mkdir -p "$dir"
  cat > "$dir/README.md" <<EOF
---
name: $slug
feature: $p
status: $st
completed_at:
source_type: name
created_at: $t
updated_at: $t
---

# $slug

## 작업 이력

- $t 등록 ($st)
EOF
  [ "$p" = maintenance ] || feature_log "$d/README.md" "- $t 태스크 등록: $(basename "$dir")"
  rel "$dir"
}

cmd_set_status() { # <task_dir> <status> [reason] → 새 경로
  local dir="${1%/}" new="$2" reason="${3:-}" f old proj dest t
  [[ "$dir" = /* ]] || dir="$DOCS/$dir"
  f="$dir/README.md"; [ -f "$f" ] || die "task not found: $1"
  echo " $STATUSES " | grep -q " $new " || die "invalid status: $new"
  case "$dir" in "$ROOT"/_completed/*) die "task in completed feature (reopen first)";; esac
  old="$(fm_get "$f" status)"; t="$(now)"
  fm_set "$f" status "$new"; fm_set "$f" updated_at "$t"
  if [ "$new" = completed ]; then fm_set "$f" completed_at "$t"; else fm_set "$f" completed_at ""; fi
  task_log "$f" "- $t $old → $new${reason:+ ($reason)}"
  proj="$(dirname "$dir")"                                   # .../tasks 또는 .../tasks/<상태>
  case "$(basename "$proj")" in backlog|holding|completed) proj="$(dirname "$proj")";; esac
  proj="$(basename "$(dirname "$proj")")"
  if [ "$proj" = maintenance ]; then
    case "$new" in
      wait|processing) dest="$ROOT/maintenance/tasks" ;;
      *) dest="$ROOT/maintenance/tasks/$new" ;;
    esac
    if [ "$(dirname "$dir")" != "$dest" ]; then
      mkdir -p "$dest"
      if ! mv "$dir" "$dest/"; then
        fm_set "$f" status "$old"; die "move failed; status restored"
      fi
      dir="$dest/$(basename "$dir")"
    fi
  fi
  rel "$dir"
}

cmd_feature_status() { # <slug> <processing|holding|completed> → 새 경로
  local slug="$1" new="$2" d t
  [ "$slug" = maintenance ] && die "maintenance has no status"
  case "$new" in processing|holding|completed) ;; *) die "invalid feature status: $new";; esac
  d="$(feature_dir "$slug")" || die "feature not found: $slug"
  t="$(now)"
  if [ "$new" = completed ] && [ "$d" = "$ROOT/$slug" ]; then
    mkdir -p "$ROOT/_completed"; mv "$d" "$ROOT/_completed/"; d="$ROOT/_completed/$slug"
  elif [ "$new" != completed ] && [ "$d" = "$ROOT/_completed/$slug" ]; then
    [ -e "$ROOT/$slug" ] && die "active feature with same slug exists"
    mv "$d" "$ROOT/"; d="$ROOT/$slug"
  fi
  local old; old="$(fm_get "$d/README.md" status)"
  fm_set "$d/README.md" status "$new"; fm_set "$d/README.md" updated_at "$t"
  feature_log "$d/README.md" "- $t feature 상태 $old → $new"
  rel "$d"
}

usage() {
  cat <<'EOF'
usage: tm.sh <command> [args]
  features [all]                          slug  status  done/total  next_wait
  tasks [feature] [active|backlog|holding|completed|all]
                                          feature/tasks/dir  status  name  updated_at
  find <query> [feature]                  일치 태스크 경로 (번호·slug 일부)
  new-feature <slug> [title]              feature 생성 → 경로
  new-task <feature> <slug> [wait|backlog]  태스크 생성 → 경로
  set-status <task_path> <status> [reason]  status/updated_at/completed_at/이력 갱신 + maintenance 이동 → 새 경로
  feature-status <slug> <processing|holding|completed>  → 새 경로
경로 인자·출력은 [Jissp 문서](0-jissp-docs) 기준 상대 경로입니다.
EOF
}

cmd="${1:-}"; [ $# -gt 0 ] && shift
case "$cmd" in
  features) cmd_features "$@" ;;
  tasks) cmd_tasks "$@" ;;
  find) [ $# -ge 1 ] || die "find <query>"; cmd_find "$@" ;;
  new-feature) [ $# -ge 1 ] || die "new-feature <slug>"; cmd_new_feature "$@" ;;
  new-task) [ $# -ge 2 ] || die "new-task <feature> <slug>"; cmd_new_task "$@" ;;
  set-status) [ $# -ge 2 ] || die "set-status <task_path> <status>"; cmd_set_status "$@" ;;
  feature-status) [ $# -ge 2 ] || die "feature-status <slug> <status>"; cmd_feature_status "$@" ;;
  ""|-h|--help|help) usage ;;
  *) die "unknown command: $cmd" ;;
esac
