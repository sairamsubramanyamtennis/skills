"""harvest.py — mine Claude Code transcripts for Suffet interactions that never got written down.

The voluntary write path (journal an exchange at the end of an answer) fails the way all
voluntary logging fails: the interactions that most need recording are the ones where
something went wrong and attention was elsewhere. This is the mechanical backstop. It reads
the raw session transcripts, finds every exchange where Suffet was involved, pairs each one
with what Sai said NEXT — which is where the calibration signal actually lives — and stages
the ones that are missing from memory/journal.md.

It never writes to lessons.md, calls.md, or journal.md. It writes candidates to
memory/_harvest_inbox.md for triage. Promotion is a judgment call and stays with Suffet.

    python scripts/harvest.py                 # all projects, everything unharvested
    python scripts/harvest.py --since 2026-08-01
    python scripts/harvest.py --limit 30 --stdout
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
MEMORY = os.path.join(SKILL, "memory")
JOURNAL = os.path.join(MEMORY, "journal.md")
INBOX = os.path.join(MEMORY, "_harvest_inbox.md")
PROJECTS = os.path.join(os.path.expanduser("~"), ".claude", "projects")

# An exchange counts as Suffet's if the skill was invoked, or if Sai addressed it by name.
NAME_RE = re.compile(r"(?:^|\W)/?suffet\b", re.I)

CMD_NAME = re.compile(r"<command-name>\s*/?([\w-]+)", re.I)
CMD_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.I | re.S)

# Turns the harness injects into the user role that Sai never typed.
INJECTED = ("<system-reminder", "<local-command", "<user-memory-input", "Caveat:",
            "Base directory for this skill:", "<command-message>")

REACTION = [
    ("correction", re.compile(
        r"\b(no,|nope|wrong|that'?s not|not right|incorrect|you missed|missed the|"
        r"didn'?t ask|not what i|redo|rework|try again|stop|don'?t do that|"
        r"where did you get|are you sure|that can'?t be)\b", re.I)),
    ("approval", re.compile(
        r"\b(good (call|catch|work|choice)|great|perfect|exactly|nice|well done|"
        r"correct|makes sense|agreed|love (it|this)|go ahead|proceed|ship it|"
        r"that'?s (it|right|helpful))\b", re.I)),
    ("deepening", re.compile(
        r"^\s*(why|how|what about|what if|and if|explain|show me|walk me|dig|go deeper)\b", re.I)),
    ("scope-change", re.compile(
        r"\b(also|additionally|now do|next,|can you also|instead|rather than)\b", re.I)),
]


def text_of(message):
    """Message content is either a string or a list of typed blocks."""
    if message is None:
        return ""
    content = message.get("content") if isinstance(message, dict) else message
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    out = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            out.append(block.get("text") or "")
    return "\n".join(out)


def skill_calls(message):
    """Skill names invoked by an assistant turn."""
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    names = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
            inp = block.get("input") or {}
            if isinstance(inp, dict) and inp.get("skill"):
                names.append(str(inp["skill"]))
    return names


def is_human_prompt(rec):
    """A prompt Sai actually typed — not a tool result, hook, or injected reminder."""
    if rec.get("type") != "user":
        return False
    if rec.get("isSidechain"):
        return False
    if rec.get("promptSource") not in (None, "typed"):
        return False
    origin = rec.get("origin") or {}
    if isinstance(origin, dict) and origin.get("kind") not in (None, "human"):
        return False
    body = text_of(rec.get("message"))
    if not body.strip():
        return False
    stripped = body.lstrip()
    # A slash command is a real prompt; its expanded skill body, injected next, is not.
    if CMD_NAME.search(stripped[:400]):
        return True
    if stripped.startswith(INJECTED):
        return False
    return True


def unwrap(body):
    """Return (prompt_text, slash_command_or_None) for a possibly command-wrapped turn."""
    m = CMD_NAME.search(body[:400])
    if not m:
        return body.strip(), None
    args = CMD_ARGS.search(body)
    text = (args.group(1).strip() if args else "")
    return (text or "(bare /%s invocation)" % m.group(1)), m.group(1).lower()


def classify(reaction_text):
    if not reaction_text:
        return "no-reaction"
    for label, rx in REACTION:
        if rx.search(reaction_text):
            return label
    return "continuation"


def read_session(path):
    """Return (title, [records]) for one transcript, tolerating partial lines."""
    title = None
    recs = []
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") == "ai-title":
                title = rec.get("aiTitle")
            elif rec.get("type") in ("user", "assistant"):
                recs.append(rec)
    return title, recs


def exchanges(path):
    """Yield one dict per Suffet-involved exchange in a transcript."""
    title, recs = read_session(path)
    session = os.path.splitext(os.path.basename(path))[0]

    # Index human prompts so each can be paired with the next one (the reaction).
    humans = [i for i, r in enumerate(recs) if is_human_prompt(r)]
    for n, idx in enumerate(humans):
        rec = recs[idx]
        prompt, command = unwrap(text_of(rec.get("message")))
        end = humans[n + 1] if n + 1 < len(humans) else len(recs)

        invoked, answer = [], []
        for r in recs[idx + 1:end]:
            if r.get("type") != "assistant":
                continue
            invoked += skill_calls(r.get("message") or {})
            answer.append(text_of(r.get("message")))
        answer_text = "\n".join(t for t in answer if t).strip()

        involved = ("suffet" in [s.lower() for s in invoked]
                    or command == "suffet"
                    or bool(NAME_RE.search(prompt)))
        if command == "suffet":
            invoked.append("suffet")
        if not involved:
            continue

        reaction = ""
        if n + 1 < len(humans):
            reaction = unwrap(text_of(recs[humans[n + 1]].get("message")))[0]

        yield {
            "session": session,
            "title": title or "(untitled)",
            "ts": (rec.get("timestamp") or "")[:19],
            "prompt": prompt,
            "answer": answer_text,
            "reaction": reaction,
            "reaction_kind": classify(reaction),
            "invoked": sorted(set(invoked)),
        }


def already_journaled():
    """Keys already present in journal.md, so harvest is idempotent."""
    if not os.path.exists(JOURNAL):
        return set()
    body = io.open(JOURNAL, encoding="utf-8", errors="replace").read()
    return set(re.findall(r"`([0-9a-f]{8})/(\d{4}-\d\d-\d\dT\d\d:\d\d)", body)) | \
           set(re.findall(r"key:\s*([0-9a-f]{8}/\d{4}-\d\d-\d\dT\d\d:\d\d)", body))


def key_of(ex):
    return "%s/%s" % (ex["session"][:8], ex["ts"][:16])


def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n - 1] + "…"


def main():
    try:                                              # the console here is not utf-8 by default
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="YYYY-MM-DD; only exchanges on or after this date")
    ap.add_argument("--limit", type=int, default=0, help="cap the number staged (newest first)")
    ap.add_argument("--project", default="", help="substring of the project dir to restrict to")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing the inbox")
    ap.add_argument("--all", action="store_true", help="include exchanges already in journal.md")
    args = ap.parse_args()

    if not os.path.isdir(PROJECTS):
        sys.exit("no transcript store at %s" % PROJECTS)

    paths = []
    for root, _dirs, files in os.walk(PROJECTS):
        if args.project and args.project.lower() not in root.lower():
            continue
        paths += [os.path.join(root, f) for f in files if f.endswith(".jsonl")]

    seen = set() if args.all else already_journaled()
    found = []
    for p in sorted(paths):
        try:
            for ex in exchanges(p):
                if args.since and ex["ts"][:10] < args.since:
                    continue
                ex["key"] = key_of(ex)
                if ex["key"] in seen or (ex["session"][:8], ex["ts"][:16]) in seen:
                    continue
                found.append(ex)
        except Exception as exc:                      # a corrupt transcript must not stop the sweep
            print("  [skipped %s: %s]" % (os.path.basename(p), exc), file=sys.stderr)

    found.sort(key=lambda e: e["ts"], reverse=True)
    if args.limit:
        found = found[:args.limit]

    lines = [
        "# Suffet — harvest inbox",
        "",
        "Generated %s by `scripts/harvest.py`. **Staging only.** Triage each block, then delete it:" % dt.date.today(),
        "promote to `journal.md` (always), to `lessons.md` (only if it implies a repeatable behavioural",
        "change), to `calls.md` (only if a falsifiable view was stated and never logged). Nothing here is",
        "memory until it has been moved. Re-running regenerates this file from scratch.",
        "",
        "Reaction kinds are keyword guesses — read the text and overrule them.",
        "",
        "---",
        "",
    ]
    if not found:
        lines.append("Nothing unharvested. Every Suffet exchange in the transcript store is already in `journal.md`.")
    for ex in found:
        lines += [
            "## %s — %s" % (ex["ts"][:16].replace("T", " "), clip(ex["title"], 60)),
            "key: %s" % ex["key"],
            "",
            "**Asked:** %s" % clip(ex["prompt"], 700),
            "",
            "**Answered:** %s" % clip(ex["answer"], 700),
            "",
            "**Reaction [%s]:** %s" % (ex["reaction_kind"], clip(ex["reaction"], 500) or "— (end of session)"),
            "",
            "**Triage:** route? · call stated but unlogged? · lesson? · nothing?",
            "",
            "---",
            "",
        ]

    out = "\n".join(lines)
    if args.stdout:
        print(out)
    else:
        io.open(INBOX, "w", encoding="utf-8").write(out)
        print("%d unharvested exchange(s) staged in memory/_harvest_inbox.md" % len(found))
        kinds = {}
        for ex in found:
            kinds[ex["reaction_kind"]] = kinds.get(ex["reaction_kind"], 0) + 1
        for k in sorted(kinds, key=lambda k: -kinds[k]):
            print("   %-14s %d" % (k, kinds[k]))


if __name__ == "__main__":
    main()
