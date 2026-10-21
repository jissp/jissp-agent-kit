#!/usr/bin/env python3
"""
Slack 스레드 수집 및 정규화된 Thread Dump 마크다운 생성 스크립트.

특징:
1. Python 표준 라이브러리(urllib, json, re 등)만 사용하여 외부 의존성 없음
2. 토큰 획득: CLI 옵션 -> 환경 변수 -> macOS Keychain 자동 조회
3. 1-depth 링크된 스레드 자동 수집 및 무한 재귀 방지
4. Slack 멘션/채널/링크 마크다운 변환 및 유저 이름 캐싱
5. Thread Dump 마크다운 규격(jissp-slack-thread-reader 계약) 준수
6. 0-jissp-docs 문서 명명 규칙 준수 및 자동 파일 저장 / 요약 출력
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

KST = datetime.timezone(datetime.timedelta(hours=9))


def query_keychain(service: str, account: str = None) -> str:
    """macOS Keychain에서 generic password를 조회합니다."""
    cmd = ["/usr/bin/security", "find-generic-password", "-s", service, "-w"]
    if account:
        cmd.extend(["-a", account])
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return proc.stdout.strip()
    except Exception:
        return None


def get_slack_token(args) -> str:
    """우선순위(CLI -> 환경변수 -> 키체인)에 따라 Slack 토큰을 가져옵니다."""
    # 1. CLI Argument
    if getattr(args, "token", None):
        return args.token.strip()

    # 2. Environment Variables
    for env_var in ("SLACK_USER_TOKEN", "SLACK_BOT_TOKEN", "SLACK_TOKEN"):
        val = os.environ.get(env_var)
        if val:
            return val.strip()

    # 3. macOS Keychain
    keychain_services = []
    if getattr(args, "keychain_service", None):
        keychain_services.append(args.keychain_service)
    else:
        keychain_services.extend([
            "slack-user-token",
            "slack-token",
            "slack-bot-token",
        ])

    account = getattr(args, "keychain_account", None)
    for svc in keychain_services:
        token = query_keychain(svc, account)
        if token:
            return token

    return None


def parse_slack_url(url: str):
    """
    슬랙 메시지/스레드 URL에서 channel_id와 thread_ts를 추출합니다.
    - https://workspace.slack.com/archives/C0XXXXXX/p1712345678901234
    - https://workspace.slack.com/archives/C0XXXXXX/p1712345678901234?thread_ts=1712345678.901234&cid=C0XXXXXX
    """
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)

    channel_id = None
    thread_ts = None

    if "thread_ts" in query_params:
        thread_ts = query_params["thread_ts"][0]
    if "cid" in query_params:
        channel_id = query_params["cid"][0]

    # /archives/C0XXXXXX/p1712345678901234
    match = re.search(r"/archives/([A-Z0-9]+)/p([0-9]{10})([0-9]{6})", parsed.path)
    if match:
        if not channel_id:
            channel_id = match.group(1)
        if not thread_ts:
            thread_ts = f"{match.group(2)}.{match.group(3)}"

    if not thread_ts:
        m2 = re.search(r"/p([0-9]{10})([0-9]{6})", parsed.path)
        if m2:
            thread_ts = f"{m2.group(1)}.{m2.group(2)}"

    return channel_id, thread_ts


class SlackClient:
    def __init__(self, token: str):
        self.token = token
        self.user_cache = {}
        self.channel_cache = {}
        self.has_users_read_scope = True
        self._init_auth()

    def _init_auth(self):
        try:
            auth_res = self._api_call("auth.test")
            my_uid = auth_res.get("user_id")
            my_name = auth_res.get("user")
            if my_uid and my_name:
                self.user_cache[my_uid] = my_name
        except Exception:
            pass

    def _api_call(self, endpoint: str, params: dict = None) -> dict:
        url = f"https://slack.com/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }
        data = urllib.parse.urlencode(params or {}).encode("utf-8") if params else None

        max_retries = 3
        for attempt in range(max_retries):
            req = urllib.request.Request(url, data=data, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    body = resp.read().decode("utf-8")
                    data_json = json.loads(body)
                    if not data_json.get("ok"):
                        err = data_json.get("error", "unknown_error")
                        if err == "ratelimited" and attempt < max_retries - 1:
                            retry_after = int(resp.headers.get("Retry-After", 1))
                            time.sleep(retry_after)
                            continue
                        raise RuntimeError(f"Slack API error ({endpoint}): {err}")
                    return data_json
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < max_retries - 1:
                    retry_after = int(e.headers.get("Retry-After", 1))
                    time.sleep(retry_after)
                    continue
                err_body = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {e.code} on {endpoint}: {err_body}")
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise e

    def get_channel_name(self, channel_id: str) -> str:
        if not channel_id:
            return "#unknown"
        if channel_id in self.channel_cache:
            return self.channel_cache[channel_id]
        try:
            res = self._api_call("conversations.info", {"channel": channel_id})
            name = res.get("channel", {}).get("name")
            if name:
                cname = f"#{name}"
                self.channel_cache[channel_id] = cname
                return cname
        except Exception:
            pass
        fallback = f"#{channel_id}"
        self.channel_cache[channel_id] = fallback
        return fallback

    def get_user_name(self, user_id: str, default_name: str = None) -> str:
        if not user_id:
            return default_name or "알 수 없음"
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        try:
            res = self._api_call("users.info", {"user": user_id})
            user_data = res.get("user", {})
            profile = user_data.get("profile", {})
            name = (
                profile.get("display_name")
                or profile.get("real_name")
                or user_data.get("real_name")
                or user_data.get("name")
            )
            if name:
                self.user_cache[user_id] = name
                return name
        except Exception as e:
            if "missing_scope" in str(e) and self.has_users_read_scope:
                self.has_users_read_scope = False
                sys.stderr.write(
                    "[안내] Slack 토큰에 'users:read' 권한이 없습니다.\n"
                    "  -> api.slack.com/apps 에서 User Token Scopes에 'users:read'를 추가하시면\n"
                    "     사용자 ID 대신 실제 실명/닉네임으로 자동 변환됩니다.\n"
                )
        # users:read 권한이 없을 경우:
        # '작성자'/'요청자' 같은 중복 명칭 대신 고유 유저 ID를 표시하여 화자를 구분합니다.
        name = user_id or default_name or "알 수 없음"
        self.user_cache[user_id] = name
        return name

    def fetch_thread_replies(self, channel_id: str, thread_ts: str) -> list:
        messages = []
        cursor = None
        while True:
            params = {
                "channel": channel_id,
                "ts": thread_ts,
                "limit": 100,
            }
            if cursor:
                params["cursor"] = cursor
            res = self._api_call("conversations.replies", params)
            msgs = res.get("messages", [])
            messages.extend(msgs)

            cursor = res.get("response_metadata", {}).get("next_cursor")
            if not cursor or not res.get("has_more", False):
                break
        return messages

    def format_slack_text(self, text: str) -> str:
        if not text:
            return ""

        # User mentions: <@U12345> or <@U12345|name>
        def replace_user(m):
            uid = m.group(1)
            name = m.group(2) if len(m.groups()) > 1 and m.group(2) else None
            return f"@{self.get_user_name(uid, name)}"

        text = re.sub(r"<@([A-Z0-9]+)(?:\|([^>]+))?>", replace_user, text)

        # Channel mentions: <#C12345|chan_name> or <#C12345>
        def replace_channel(m):
            cid = m.group(1)
            cname = m.group(2) if len(m.groups()) > 1 and m.group(2) else None
            return f"#{cname}" if cname else self.get_channel_name(cid)

        text = re.sub(r"<#([A-Z0-9]+)(?:\|([^>]+))?>", replace_channel, text)

        # Subteam mentions: <!subteam^S123|@team>
        text = re.sub(r"<!subteam\^[A-Z0-9]+(?:\|(@[^>]+))?>", r"\1", text)

        # Special mentions
        text = text.replace("<!here>", "@here").replace("<!channel>", "@channel").replace("<!everyone>", "@everyone")

        # Links: <http://url|label> or <http://url>
        def replace_link(m):
            url = m.group(1)
            label = m.group(2) if len(m.groups()) > 1 and m.group(2) else None
            if label and label != url:
                return f"[{label}]({url})"
            return url

        text = re.sub(r"<(https?://[^|>]+)(?:\|([^>]+))?>", replace_link, text)

        # Unescape HTML entities
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        return text


def extract_links_from_text(text: str) -> list:
    # Slack 원문 링크는 <url|label> 형태이므로 '|' 앞까지만 URL로 취급
    urls = re.findall(r"https?://[^\s|<)\]>\"']+", text or "")
    cleaned = []
    for u in urls:
        u = u.replace("&amp;", "&").rstrip(".,;:)")
        if u and u not in cleaned:
            cleaned.append(u)
    return cleaned


def classify_link(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    if "figma.com" in domain:
        return "Figma"
    elif "slack.com" in domain and "/archives/" in parsed.path:
        return "Slack"
    elif "notion.so" in domain or "notion.site" in domain or "notion.com" in domain:
        return "Notion"
    elif "github.com" in domain:
        return "GitHub"
    else:
        return "기타"


def ts_to_kst_str(ts_val) -> str:
    try:
        dt = datetime.datetime.fromtimestamp(float(ts_val), tz=KST)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts_val)


def fetch_linked_threads(client: SlackClient, messages: list, root_channel: str, root_ts: str) -> dict:
    linked_data = {}
    for m in messages:
        text = m.get("text", "")
        for url in extract_links_from_text(text):
            if classify_link(url) == "Slack":
                cid, ts = parse_slack_url(url)
                if cid and ts:
                    if cid == root_channel and ts == root_ts:
                        continue
                    if url not in linked_data:
                        try:
                            l_msgs = client.fetch_thread_replies(cid, ts)
                            if l_msgs:
                                linked_data[url] = l_msgs
                        except Exception as e:
                            sys.stderr.write(f"[경고] 링크된 스레드({url}) 수집 실패: {e}\n")
    return linked_data


def build_thread_dump_markdown(
    client: SlackClient,
    source_url: str,
    channel_id: str,
    thread_ts: str,
    messages: list,
    linked_threads_data: dict,
) -> str:
    parent = messages[0] if messages else {}
    parent_ts = parent.get("ts", thread_ts)
    req_time = ts_to_kst_str(parent_ts)

    sender_id = parent.get("user")
    bot_id = parent.get("bot_id")
    sender_name = client.get_user_name(sender_id, parent.get("username") or ("Bot" if bot_id else None))
    channel_name = client.get_channel_name(channel_id)

    # 링크 수집
    all_links = []
    seen_links = set()
    for m in messages:
        for l in extract_links_from_text(m.get("text", "")):
            if l not in seen_links:
                seen_links.add(l)
                all_links.append(l)

    classified_links = []
    linked_slack_urls = set(linked_threads_data.keys())
    for l in all_links:
        category = classify_link(l)
        if category == "Slack" and l in linked_slack_urls:
            classified_links.append(f"- [{category}] {l} — Linked Threads에 수집됨")
        else:
            classified_links.append(f"- [{category}] {l}")

    lines = []
    lines.append("# Thread Dump")
    lines.append(f"- source: {source_url}")
    lines.append(f"- channel_id: {channel_id}")
    lines.append(f"- thread_ts: {thread_ts}")
    lines.append(f"- channel: {channel_name}")
    lines.append(f"- 요청자: {sender_name}")
    lines.append(f"- 요청 시각: {req_time}")
    lines.append("- links:")
    if classified_links:
        for cl in classified_links:
            lines.append(f"  {cl}")
    else:
        lines.append("  - (없음)")
    lines.append("")
    lines.append("## Messages")

    for m in messages:
        m_user = client.get_user_name(m.get("user"), m.get("username") or ("Bot" if m.get("bot_id") else None))
        m_time = ts_to_kst_str(m.get("ts"))
        m_text = client.format_slack_text(m.get("text", ""))
        lines.append(f"- [{m_user}, {m_time}] {m_text}")

        files = m.get("files", [])
        for f in files:
            fname = f.get("name", "첨부파일")
            mimetype = f.get("mimetype", f.get("filetype", "파일"))
            lines.append(f"  - (첨부: {fname} — {mimetype})")

    if linked_threads_data:
        lines.append("")
        lines.append("## Linked Threads (1-depth)")
        for l_url, l_msgs in linked_threads_data.items():
            lines.append(f"### {l_url}")
            for lm in l_msgs:
                lm_user = client.get_user_name(
                    lm.get("user"), lm.get("username") or ("Bot" if lm.get("bot_id") else "작성자")
                )
                lm_time = ts_to_kst_str(lm.get("ts"))
                lm_text = client.format_slack_text(lm.get("text", ""))
                lines.append(f"- [{lm_user}, {lm_time}] {lm_text}")
                for lf in lm.get("files", []):
                    lfname = lf.get("name", "첨부파일")
                    lmimetype = lf.get("mimetype", lf.get("filetype", "파일"))
                    lines.append(f"  - (첨부: {lfname} — {lmimetype})")

    return "\n".join(lines) + "\n"


def get_default_output_path(channel_name: str) -> str:
    now_str = datetime.datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    clean_chan = re.sub(r"[^a-zA-Z0-9_-]", "", channel_name.replace("#", "")) or "thread"
    filename = f"{now_str}_slack-thread-{clean_chan}.md"

    # 스레드 원문(문의 내용 등)이 담기므로 본인만 읽을 수 있게 만든다.
    target_dir = "/tmp/slack-messages"
    os.makedirs(target_dir, mode=0o700, exist_ok=True)
    os.chmod(target_dir, 0o700)
    return os.path.join(target_dir, filename)


def main():
    parser = argparse.ArgumentParser(
        description="Slack 스레드 전체를 수집하여 Thread Dump 마크다운 파일로 생성합니다."
    )
    parser.add_argument("url", help="슬랙 메시지/스레드 URL (또는 --channel/--ts 사용)")
    parser.add_argument(
        "--token",
        help="Slack API 토큰 (비권장: 셸 히스토리·프로세스 목록에 남습니다. 키체인 또는 환경변수를 사용하세요)",
    )
    parser.add_argument(
        "--keychain-service",
        default=os.environ.get("SLACK_KEYCHAIN_SERVICE"),
        help="macOS Keychain의 서비스명 (기본값: 환경변수 SLACK_KEYCHAIN_SERVICE, 없으면 slack-user-token 등 기본 목록 순회)",
    )
    parser.add_argument("--keychain-account", help="macOS Keychain 계정명 (생략 가능)")
    parser.add_argument("-o", "--output", help="결과를 저장할 마크다운 파일 경로")
    parser.add_argument("--stdout", action="store_true", help="결과 마크다운을 표준 출력으로 직접 출력")
    parser.add_argument("--no-linked", action="store_true", help="링크된 스레드(1-depth)를 수집하지 않음")

    args = parser.parse_args()

    # 1. 토큰 확인
    token = get_slack_token(args)
    if not token:
        sys.stderr.write(
            "[오류] Slack 토큰을 찾을 수 없습니다.\n"
            "다음 중 하나의 방법으로 토큰을 설정해 주세요:\n"
            "  1. macOS Keychain에 등록 (권장):\n"
            "     security add-generic-password -a \"$USER\" -s \"slack-user-token\" -w\n"
            "     (-w 뒤에 값을 붙이지 않으면 토큰을 프롬프트로 입력받아 셸 히스토리에 남지 않습니다)\n"
            "     다른 서비스명으로 등록했다면 export SLACK_KEYCHAIN_SERVICE=\"<서비스명>\"\n"
            "  2. 환경 변수 설정:\n"
            "     export SLACK_USER_TOKEN=\"xoxp-...\"\n"
        )
        sys.exit(1)

    # 2. URL 파싱
    channel_id, thread_ts = parse_slack_url(args.url)
    if not channel_id or not thread_ts:
        sys.stderr.write(
            f"[오류] 슬랙 URL에서 channel_id 또는 thread_ts를 추출할 수 없습니다: {args.url}\n"
            "올바른 예: https://<workspace>.slack.com/archives/C0XXXXXX/p1712345678901234\n"
        )
        sys.exit(1)

    # 3. API 클라이언트 생성 및 스레드 수집
    client = SlackClient(token)
    try:
        messages = client.fetch_thread_replies(channel_id, thread_ts)
    except Exception as e:
        sys.stderr.write(f"[오류] 스레드 수집 실패: {e}\n")
        sys.exit(1)

    if not messages:
        sys.stderr.write("[오류] 스레드에 메시지가 없습니다.\n")
        sys.exit(1)

    # 4. 1-depth 링크된 스레드 수집
    linked_threads_data = {}
    if not args.no_linked:
        linked_threads_data = fetch_linked_threads(client, messages, channel_id, thread_ts)

    # 5. 마크다운 생성
    dump_md = build_thread_dump_markdown(
        client=client,
        source_url=args.url,
        channel_id=channel_id,
        thread_ts=thread_ts,
        messages=messages,
        linked_threads_data=linked_threads_data,
    )

    # 6. 출력 처리
    if args.stdout:
        sys.stdout.write(dump_md)
        return

    out_path = args.output
    if not out_path:
        out_path = get_default_output_path(client.get_channel_name(channel_id))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fd = os.open(out_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(dump_md)

    msg_count = len(messages)
    linked_count = len(linked_threads_data)
    print(f"스레드 수집 완료 — 메시지 {msg_count}건, 링크된 스레드 {linked_count}건 (저장: {out_path})")


if __name__ == "__main__":
    main()
