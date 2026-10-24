#!/bin/bash
# Gemini CLI BeforeTool(run_shell_command) hook
# 0-jissp-docs 의 git add/commit, 전체 스테이징, git push 를 차단합니다.
# 차단 시 stderr 에 사유를 남기고 exit 2 로 종료합니다. (Gemini 는 stdout 을 JSON 으로 파싱하므로 stdout 출력 금지)

input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
cwd=$(jq -r '.cwd // empty' <<<"$input")

# git 명령이 아니면 통과
echo "$cmd" | grep -qE '(^|[;&|(`[:space:]])git([[:space:]]|$)' || exit 0

deny() { echo "BLOCKED: $1" >&2; exit 2; }

# 정규화: 커밋 메시지(-m "...")를 제거하고, git 전역 옵션(-C path, -c k=v, --git-dir=... 등)을 걷어내
# 하위 명령이 git 바로 뒤에 오도록 맞춥니다.
norm=$(echo "$cmd" \
  | sed -E -e "s/-m[[:space:]]*\"[^\"]*\"//g" -e "s/-m[[:space:]]*'[^']*'//g" \
  | sed -E -e ':a' \
      -e 's/(git)[[:space:]]+(-[Cc][[:space:]]+[^[:space:]]+|--[a-z-]+=[^[:space:]]+|--no-pager|-P)/\1/' \
      -e 'ta')

# 1) 0-jissp-docs 경로를 add/commit 대상으로 직접 지정
echo "$norm" | grep -qE 'git[[:space:]]+(add|commit|stage)[^;&|]*0-jissp-docs' \
  && deny "0-jissp-docs 는 git add/commit 대상이 아닙니다."

# 2) 전체 스테이징 (git add . / -A / --all / -u / --update / :/ / *)
echo "$norm" | grep -qE 'git[[:space:]]+(add|stage)([[:space:]]+[^;&|]*)?[[:space:]](\.|\./|-A|--all|-u|--update|:/|\*)([[:space:]]|$|[;&|])' \
  && deny "git add 는 개별 파일 경로로만 지정하세요."

# 3) git commit -a / -am / --all
echo "$norm" | grep -qE 'git[[:space:]]+commit([[:space:]]+[^;&|]*)?[[:space:]](-[a-zA-Z]*a[a-zA-Z]*|--all)([[:space:]]|$|[;&|])' \
  && deny "git commit -a 는 사용할 수 없습니다."

# 4) commit 시점에 이미 스테이징된 0-jissp-docs 파일이 있으면 차단
if echo "$norm" | grep -qE 'git[[:space:]]+commit'; then
  git -C "${cwd:-.}" diff --cached --name-only 2>/dev/null | grep -q '0-jissp-docs' \
    && deny "스테이징 영역에 0-jissp-docs 파일이 있습니다. 사용자에게 보고하세요."
fi

# 5) push 차단
echo "$norm" | grep -qE 'git[[:space:]]+push' && deny "git push 는 금지되어 있습니다."

exit 0
