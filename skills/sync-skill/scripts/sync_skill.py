#!/usr/bin/env python3
"""jissp-agent-kit 원본을 기준으로 Claude / Gemini 스킬 디렉토리와 Claude 서브에이전트 디렉토리의 링크 상태를 점검·반영합니다.

사용법:
  sync_skill.py check [skill|subagents|hooks ...]                          # 점검만 (인자 없으면 스킬 전체 + 서브에이전트 + hooks)
  sync_skill.py apply skill|subagents|hooks [...] [--side claude|gemini]   # 자동 반영 가능한 항목만 반영

`subagents` 는 예약 대상명으로, jissp-agent-kit/subagents 전체를 반영합니다.
  <name>.claude.md → ~/.claude/agents/<name>.md (+ shared/ 공용 문서)
  <name>.gemini.md → ~/.gemini/config/agents/<name>.md

`hooks` 는 예약 대상명으로, jissp-agent-kit/hooks 전체를 각 에이전트 settings.json 에 등록합니다.
  <name>/claude.sh → ~/.claude/settings.json hooks (<name>/hook.json 의 claude 이벤트·matcher)
  <name>/gemini.sh → ~/.gemini/settings.json hooks (<name>/hook.json 의 gemini 이벤트·matcher)

자동 반영 대상: 스킬 디렉토리 생성, 빠진 링크 생성, 저장소 안의 옛 위치를 가리키는 링크 재연결,
manifest.json 생성·description 갱신, settings.json 에 빠진 hook 등록 추가.
실제 파일·디렉토리, 다른 곳을 가리키는 링크, 원본에 없는 항목은 건드리지 않고 보고만 합니다.
"""
import json
import os
import re
import sys
import tempfile

KIT_ROOT = os.path.expanduser("~/jissp-agent-kit")
BASE = os.path.join(KIT_ROOT, "skills")
SUBAGENT_SRC = os.path.join(KIT_ROOT, "subagents")
SUBAGENTS = "subagents"  # check / apply 의 예약 대상명
SUBAGENT_SIDES = {
    "claude": {"root": os.path.expanduser("~/.claude/agents"), "suffix": ".claude.md", "shared": True},
    "gemini": {"root": os.path.expanduser("~/.gemini/config/agents"), "suffix": ".gemini.md", "shared": False},
}
SUBAGENT_SUFFIXES = tuple(c["suffix"] for c in SUBAGENT_SIDES.values())
HOOK_SRC = os.path.join(KIT_ROOT, "hooks")
HOOKS = "hooks"  # check / apply 의 예약 대상명
HOOK_META = "hook.json"  # 쪽별 등록 이벤트·matcher·timeout
HOOK_SIDES = {
    "claude": {"settings": os.path.expanduser("~/.claude/settings.json"), "script": "claude.sh"},
    "gemini": {"settings": os.path.expanduser("~/.gemini/settings.json"), "script": "gemini.sh"},
}
SIDES = {
    "claude": {"root": os.path.expanduser("~/.claude/skills"), "skill_file": "SKILL.claude.md"},
    "gemini": {"root": os.path.expanduser("~/.gemini/antigravity-cli/skills"), "skill_file": "SKILL.gemini.md"},
}
SKILL_FILES = {"SKILL.claude.md", "SKILL.gemini.md"}
MANIFEST_INSTRUCTIONS = (
    "SKILL.md 파일에 명시된 규칙, 포맷, 제약 사항을 완벽하게 숙지하고, "
    "사용자의 요청을 처리할 때 그 지침을 엄격하게 적용하여 답변을 생성하십시오."
)

# 자동 반영 가능한 상태
FIXABLE = {"MISSING_DIR", "MISSING_LINK", "STALE_LINK", "MANIFEST_MISSING", "MANIFEST_STALE", "MISSING_HOOK"}


def read_description(skill_md_path):
    """frontmatter 의 description 을 manifest 용 한 줄 문자열로 변환합니다."""
    with open(skill_md_path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    lines = m.group(1).split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        head = line[len("description:"):].strip()
        parts = [] if head in ("", ">", ">-", "|", "|-") else [head.strip("\"'")]
        for nxt in lines[i + 1:]:
            if nxt.startswith((" ", "\t")):
                parts.append(nxt.strip())
            else:
                break
        return " ".join(p for p in parts if p).replace('"', "'")
    return None


def skill_entries(skill):
    """에이전트 쪽에 링크해야 할 원본 항목 (SKILL 파일 제외, 숨김 파일 제외)."""
    return sorted(
        n for n in os.listdir(os.path.join(BASE, skill))
        if not n.startswith(".") and n not in SKILL_FILES
    )


def check_side(skill, side):
    """(status, item, detail, side) 목록을 반환합니다."""
    conf = SIDES[side]
    src_dir = os.path.join(BASE, skill)
    dst_dir = os.path.join(conf["root"], skill)
    skill_src = os.path.join(src_dir, conf["skill_file"])
    issues = []

    if not os.path.isfile(skill_src):
        return [("NO_SOURCE", conf["skill_file"], "원본에 이 에이전트용 SKILL 파일이 없음", side)]

    if not os.path.isdir(dst_dir):
        return [("MISSING_DIR", "", dst_dir, side)]

    # 링크 대상: SKILL.md → SKILL.<side>.md, 나머지 원본 항목 → 같은 이름
    expected = {"SKILL.md": skill_src}
    for name in skill_entries(skill):
        expected[name] = os.path.join(src_dir, name)

    for name, target in expected.items():
        issue = link_status(os.path.join(dst_dir, name), target, name)
        if issue:
            issues.append(issue + (side,))

    # 원본에 없는데 에이전트 쪽에만 있는 항목
    for name in sorted(os.listdir(dst_dir)):
        if name.startswith(".") or name in expected or (side == "gemini" and name == "manifest.json"):
            continue
        issues.append(("EXTRA", name, "원본에 없는 항목", side))

    if side == "gemini":
        manifest = os.path.join(dst_dir, "manifest.json")
        desc = read_description(skill_src)
        if not os.path.exists(manifest):
            issues.append(("MANIFEST_MISSING", "manifest.json", "", side))
        else:
            try:
                with open(manifest, encoding="utf-8") as f:
                    data = json.load(f)
                if desc is not None and data.get("description") != desc:
                    issues.append(("MANIFEST_STALE", "manifest.json", "description 이 SKILL.gemini.md 와 다름", side))
            except (json.JSONDecodeError, OSError) as e:
                issues.append(("MANIFEST_INVALID", "manifest.json", str(e), side))
    return issues


def check_skill(skill):
    src_dir = os.path.join(BASE, skill)
    if not os.path.isdir(src_dir):
        return [("NO_SKILL", "", f"{src_dir} 없음", "-")]
    if not any(os.path.isfile(os.path.join(src_dir, f)) for f in SKILL_FILES):
        return [("NONSTANDARD", "", "SKILL.claude.md / SKILL.gemini.md 가 없는 비표준 구조", "-")]
    if os.path.exists(os.path.join(src_dir, "SKILL.md")):
        return [("NONSTANDARD", "SKILL.md", "원본에 SKILL.md 가 있어 에이전트 쪽 SKILL.md 링크와 이름이 겹침", "-")]
    return [i for side in SIDES for i in check_side(skill, side)]


def write_manifest(skill):
    src = os.path.join(BASE, skill, SIDES["gemini"]["skill_file"])
    path = os.path.join(SIDES["gemini"]["root"], skill, "manifest.json")
    data = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
    data.update({"name": skill, "description": read_description(src) or ""})
    data.setdefault("instructions", MANIFEST_INSTRUCTIONS)
    data.setdefault("agent_settings", {"thinking_level": "high"})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(path, encoding="utf-8") as f:
        json.load(f)  # 파싱 검증


def apply_skill(skill, sides):
    done = []
    for side in sides:
        conf = SIDES[side]
        dst_dir = os.path.join(conf["root"], skill)
        if any(s in ("NO_SKILL", "NONSTANDARD") for s, *_ in check_skill(skill)):
            break
        issues = check_side(skill, side)
        if any(s == "NO_SOURCE" for s, *_ in issues):
            continue
        if any(s == "MISSING_DIR" for s, *_ in issues):
            os.makedirs(dst_dir)
            done.append((side, "MKDIR", dst_dir))
            issues = check_side(skill, side)
        for status, item, detail, _ in issues:
            if status in ("MISSING_LINK", "STALE_LINK"):
                relink(os.path.join(dst_dir, item), detail)
                done.append((side, "LINK" if status == "MISSING_LINK" else "RELINK", f"{item} -> {detail}"))
            elif status in ("MANIFEST_MISSING", "MANIFEST_STALE"):
                write_manifest(skill)
                done.append((side, "MANIFEST", "manifest.json 작성·검증"))
    return done


def link_status(path, target, item):
    """에이전트 쪽 경로 하나가 원본 target 을 가리키는지 판정합니다. 정상이면 None."""
    if os.path.islink(path):
        actual = os.readlink(path)
        if actual != target:
            # 이 저장소 안의 다른 위치를 가리키는 링크는 원본 이동·이름 변경으로 낡은 것이므로 다시 연결한다.
            if actual.startswith(KIT_ROOT + os.sep):
                return ("STALE_LINK", item, target)
            return ("WRONG_TARGET", item, f"{actual} (기대: {target})")
        if not os.path.exists(path):
            return ("BROKEN", item, actual)
        return None
    if os.path.exists(path):
        return ("NOT_LINK", item, "실제 파일이 있음 (복제본 의심)")
    return ("MISSING_LINK", item, target)


def subagent_entries(side):
    """(원본 경로 또는 None, 에이전트 쪽 상대 경로) 목록. 원본이 None 이면 이 쪽 원본 파일이 없는 서브에이전트입니다."""
    suffix = SUBAGENT_SIDES[side]["suffix"]
    names = sorted({
        n[: -len(sfx)] for n in os.listdir(SUBAGENT_SRC)
        for sfx in SUBAGENT_SUFFIXES if n.endswith(sfx)
    })
    entries = []
    for name in names:
        src = os.path.join(SUBAGENT_SRC, name + suffix)
        entries.append((src if os.path.isfile(src) else None, name + ".md"))
    # 공용 문서(shared/ 등)는 Claude 쪽에만 파일 단위로 링크한다. (Gemini 본문은 저장소 경로를 직접 읽는다)
    if SUBAGENT_SIDES[side]["shared"]:
        for d in sorted(os.listdir(SUBAGENT_SRC)):
            sub = os.path.join(SUBAGENT_SRC, d)
            if d.startswith(".") or not os.path.isdir(sub):
                continue
            for f in sorted(os.listdir(sub)):
                if not f.startswith(".") and f.endswith(".md"):
                    entries.append((os.path.join(sub, f), os.path.join(d, f)))
    return entries


def check_subagents(sides=None):
    """(status, item, detail, side) 목록을 반환합니다."""
    if not os.path.isdir(SUBAGENT_SRC):
        return [("NO_SKILL", "", f"{SUBAGENT_SRC} 없음", "-")]
    issues = []
    for side in sides or SUBAGENT_SIDES:
        dst = SUBAGENT_SIDES[side]["root"]
        expected = set()
        for src, rel in subagent_entries(side):
            expected.add(rel)
            if src is None:
                issues.append(("NO_SOURCE", rel, f"원본에 이 에이전트용 {rel[:-3]}{SUBAGENT_SIDES[side]['suffix']} 가 없음", side))
                continue
            issue = link_status(os.path.join(dst, rel), src, rel)
            if issue:
                issues.append(issue + (side,))
        # 원본이 사라졌는데 남아 있는 링크 (원본을 가리키던 링크만 — 개인 에이전트는 건드리지 않음)
        if os.path.isdir(dst):
            for root, dirs, files in os.walk(dst):
                for name in dirs + files:
                    path = os.path.join(root, name)
                    rel = os.path.relpath(path, dst)
                    if (os.path.islink(path) and rel not in expected
                            and os.readlink(path).startswith(SUBAGENT_SRC + os.sep)):
                        issues.append(("EXTRA", rel, "원본에 없는 서브에이전트를 가리키는 링크", side))
    return issues


def relink(path, target):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.islink(path):
        os.unlink(path)
    os.symlink(target, path)


def apply_subagents(sides):
    done = []
    for status, item, detail, side in check_subagents(sides):
        if status in ("MISSING_LINK", "STALE_LINK"):
            relink(os.path.join(SUBAGENT_SIDES[side]["root"], item), detail)
            done.append((side, "LINK" if status == "MISSING_LINK" else "RELINK", f"{item} -> {detail}"))
    return done


def hook_command(script):
    """settings.json 에 적을 command. 홈 아래 경로는 PC 마다 같도록 ~/ 형태로 적습니다."""
    home = os.path.expanduser("~")
    return "~/" + os.path.relpath(script, home) if script.startswith(home + os.sep) else script


def command_path(command):
    """등록된 command 문자열이 실행하는 스크립트의 절대 경로."""
    parts = (command or "").split()
    return os.path.normpath(os.path.expanduser(parts[0])) if parts else ""


def load_settings(path):
    """(settings dict, 에러 메시지). 파일이 없으면 빈 설정으로 봅니다."""
    if not os.path.exists(path):
        return {}, None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except (json.JSONDecodeError, OSError) as e:
        return None, str(e)


def registered_hooks(settings):
    """settings 의 (event, matcher, command 절대 경로) 목록."""
    found = []
    for event, groups in (settings.get("hooks") or {}).items():
        if not isinstance(groups, list):
            continue
        for group in groups:
            for h in group.get("hooks") or []:
                found.append((event, group.get("matcher"), command_path(h.get("command"))))
    return found


def hook_entries(side):
    """(hook 이름, 원본 스크립트 경로, 등록 설정 또는 None, 문제 상태 또는 None) 목록."""
    entries = []
    for name in sorted(os.listdir(HOOK_SRC)):
        src_dir = os.path.join(HOOK_SRC, name)
        if name.startswith(".") or not os.path.isdir(src_dir):
            continue
        script = os.path.join(src_dir, HOOK_SIDES[side]["script"])
        meta_path = os.path.join(src_dir, HOOK_META)
        if not os.path.isfile(meta_path):
            entries.append((name, script, None, ("NONSTANDARD", f"{HOOK_META} 가 없는 비표준 구조")))
            continue
        try:
            with open(meta_path, encoding="utf-8") as f:
                conf = json.load(f).get(side)
        except (json.JSONDecodeError, OSError) as e:
            entries.append((name, script, None, ("MANIFEST_INVALID", f"{HOOK_META}: {e}")))
            continue
        if not conf or not os.path.isfile(script):
            entries.append((name, script, None, ("NO_SOURCE", f"원본에 이 에이전트용 {HOOK_SIDES[side]['script']} 또는 {HOOK_META} 설정이 없음")))
            continue
        if not os.access(script, os.X_OK):
            entries.append((name, script, conf, ("NOT_EXECUTABLE", f"{script} 에 실행 권한이 없음")))
            continue
        entries.append((name, script, conf, None))
    return entries


def check_hooks(sides=None):
    """(status, item, detail, side) 목록을 반환합니다."""
    if not os.path.isdir(HOOK_SRC):
        return [("NO_SKILL", "", f"{HOOK_SRC} 없음", "-")]
    issues = []
    for side in sides or HOOK_SIDES:
        settings_path = HOOK_SIDES[side]["settings"]
        settings, err = load_settings(settings_path)
        if err:
            issues.append(("SETTINGS_INVALID", os.path.basename(settings_path), f"{settings_path}: {err}", side))
            continue
        registered = registered_hooks(settings)
        expected = set()
        for name, script, conf, problem in hook_entries(side):
            expected.add(os.path.normpath(script))
            if problem:
                issues.append((problem[0], name, problem[1], side))
                continue
            matches = [(e, m) for e, m, p in registered if p == os.path.normpath(script)]
            if not matches:
                issues.append(("MISSING_HOOK", name, f"{conf['event']} / {conf.get('matcher', '')} -> {hook_command(script)}", side))
            elif (conf["event"], conf.get("matcher")) not in matches:
                actual = ", ".join(f"{e} / {m}" for e, m in matches)
                issues.append(("HOOK_MISMATCH", name, f"{actual} 에 등록됨 (기대: {conf['event']} / {conf.get('matcher')})", side))
        # 원본이 사라졌는데 남아 있는 등록 (이 저장소의 hooks 를 가리키는 것만)
        for event, matcher, path in registered:
            if path.startswith(HOOK_SRC + os.sep) and path not in expected:
                issues.append(("EXTRA", os.path.relpath(path, HOOK_SRC), f"원본에 없는 hook 등록 ({event} / {matcher})", side))
    return issues


def write_json_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".sync_skill.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(tmp, encoding="utf-8") as f:
        json.load(f)  # 파싱 검증
    if os.path.exists(path):
        os.chmod(tmp, os.stat(path).st_mode & 0o777)
    os.replace(tmp, path)


def apply_hooks(sides):
    """빠진 hook 등록만 settings.json 에 추가합니다. 기존 등록은 고치거나 지우지 않습니다."""
    done = []
    for side in sides:
        missing = {item for status, item, _, s in check_hooks([side]) if s == side and status == "MISSING_HOOK"}
        if not missing:
            continue
        settings_path = HOOK_SIDES[side]["settings"]
        settings, _ = load_settings(settings_path)
        for name, script, conf, _ in hook_entries(side):
            if name not in missing:
                continue
            entry = {"type": "command", "command": hook_command(script)}
            if "timeout" in conf:
                entry["timeout"] = conf["timeout"]
            groups = settings.setdefault("hooks", {}).setdefault(conf["event"], [])
            group = next((g for g in groups if g.get("matcher") == conf.get("matcher")), None)
            if group is None:
                group = {"matcher": conf["matcher"], "hooks": []} if "matcher" in conf else {"hooks": []}
                groups.append(group)
            group.setdefault("hooks", []).append(entry)
            done.append((side, "HOOK", f"{name}: {conf['event']} / {conf.get('matcher', '')} -> {entry['command']}"))
        write_json_atomic(settings_path, settings)
    return done


def main(argv):
    if not argv or argv[0] not in ("check", "apply"):
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    sides = list(SIDES)
    if "--side" in rest:
        i = rest.index("--side")
        sides = [rest[i + 1]]
        rest = rest[:i] + rest[i + 2:]

    if cmd == "check":
        skills = rest or sorted(d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)) and not d.startswith(".")) + [SUBAGENTS, HOOKS]
        for skill in skills:
            if skill == SUBAGENTS:
                issues = check_subagents(sides)
            elif skill == HOOKS:
                issues = check_hooks(sides)
            else:
                issues = check_skill(skill)
            for status, item, detail, side in issues:
                fix = "auto" if status in FIXABLE else "manual"
                print("\t".join([skill, side, status, fix, item, detail]))
        return 0

    if not rest:
        print("apply 에는 스킬명이 필요합니다.")
        return 2
    for skill in rest:
        if skill == SUBAGENTS:
            results = apply_subagents(sides)
        elif skill == HOOKS:
            results = apply_hooks(sides)
        else:
            results = apply_skill(skill, sides)
        for side, action, detail in results:
            print("\t".join([skill, side, action, detail]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
