#!/usr/bin/env python3
"""jissp-agent-kit/skills 원본을 기준으로 Claude / Gemini 스킬 디렉토리의 링크 상태를 점검·반영합니다.

사용법:
  sync_skill.py check [skill ...]                          # 점검만 (인자 없으면 전체)
  sync_skill.py apply skill [skill ...] [--side claude|gemini]  # 자동 반영 가능한 항목만 반영

자동 반영 대상: 스킬 디렉토리 생성, 빠진 링크 생성, manifest.json 생성·description 갱신.
실제 파일·디렉토리, 다른 곳을 가리키는 링크, 원본에 없는 항목은 건드리지 않고 보고만 합니다.
"""
import json
import os
import re
import sys

BASE = os.path.expanduser("~/jissp-agent-kit/skills")
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
FIXABLE = {"MISSING_DIR", "MISSING_LINK", "MANIFEST_MISSING", "MANIFEST_STALE"}


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
        path = os.path.join(dst_dir, name)
        if os.path.islink(path):
            actual = os.readlink(path)
            if actual != target:
                issues.append(("WRONG_TARGET", name, f"{actual} (기대: {target})", side))
            elif not os.path.exists(path):
                issues.append(("BROKEN", name, actual, side))
        elif os.path.exists(path):
            issues.append(("NOT_LINK", name, "실제 파일·디렉토리가 있음 (복제본 의심)", side))
        else:
            issues.append(("MISSING_LINK", name, target, side))

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
            if status == "MISSING_LINK":
                os.symlink(detail, os.path.join(dst_dir, item))
                done.append((side, "LINK", f"{item} -> {detail}"))
            elif status in ("MANIFEST_MISSING", "MANIFEST_STALE"):
                write_manifest(skill)
                done.append((side, "MANIFEST", "manifest.json 작성·검증"))
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
        skills = rest or sorted(d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)) and not d.startswith("."))
        for skill in skills:
            for status, item, detail, side in check_skill(skill):
                fix = "auto" if status in FIXABLE else "manual"
                print("\t".join([skill, side, status, fix, item, detail]))
        return 0

    if not rest:
        print("apply 에는 스킬명이 필요합니다.")
        return 2
    for skill in rest:
        for side, action, detail in apply_skill(skill, sides):
            print("\t".join([skill, side, action, detail]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
