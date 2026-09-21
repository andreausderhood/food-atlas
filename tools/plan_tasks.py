#!/usr/bin/env python3
"""Split an implementation plan into per-task briefs and guard a task's diff.

Executor-agnostic on purpose: any agent (Hermes, Antigravity, a human) gets the same
self-contained brief and is held to the same check.

    plan_tasks.py split PLAN.md OUTDIR        write 00-context.md and one brief per task
    plan_tasks.py guard BRIEF.md [--base REF] fail if the working tree touches files the task does not list
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

TASK = re.compile(r"^### Task (\d+): (.+)$", re.M)
HEADING = re.compile(r"^## ", re.M)
GATE = "[HUMAN GATE]"
FORBIDDEN = ("src/atlas/build.py", "src/atlas/research/*", "data/raw/*", "data/research/*", ".env", ".env.*")
APPROVALS = Path.home() / ".food-atlas-approvals"   # outside the repo: a tripwire, not a security boundary

PROTOCOL = """
---

## Ausführungsprotokoll (gilt für jeden Ausführer)

1. Existiert `data/research/STOP`, arbeite nicht weiter und melde das.
2. Arbeite nur in deinem eigenen Git-Worktree, nie im Hauptcheckout. Führe alle Befehle mit `PYTHONPATH=src` aus.
3. Genau dieser eine Task, in der Reihenfolge der Schritte. Test zuerst, Fehlschlag sehen, dann implementieren.
   Führe nur die Tests dieses Tasks aus; die volle Suite (~7 Minuten) nur einmal am Ende, im Hintergrund.
4. Ändere nie einen Test, um ihn grün zu machen. Lösche keinen Test.
5. Vor dem Commit: `python tools/plan_tasks.py guard <diese Datei>` muss 0 liefern.
6. Committe nur Dateien dieses Tasks (`git add <Pfade>`, nie `git add -A`). Kein Push, kein Deploy.
7. Fehlschlag mit demselben Grund zweimal: `data/research/STOP` mit Begründung anlegen und melden.
8. Melde in höchstens acht Zeilen: erledigt oder blockiert, Beleg (Testausgabe), Commit, nächster Schritt.
"""


def _fenced(plan: str) -> list[tuple[int, int]]:
    """Spans of fenced code blocks; headings inside them are example text, not structure."""
    spans, start = [], None
    for m in re.finditer(r"^```.*$", plan, re.M):
        if start is None:
            start = m.start()
        else:
            spans.append((start, m.end()))
            start = None
    return spans


def _outside(plan: str, pattern: re.Pattern, pos: int = 0):
    spans = _fenced(plan)
    return [m for m in pattern.finditer(plan, pos) if not any(a <= m.start() < b for a, b in spans)]


def task_blocks(plan: str) -> list[tuple[int, str, str]]:
    found = _outside(plan, TASK)
    headings = [m.start() for m in _outside(plan, HEADING)]
    blocks = []
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(plan)
        end = min([end] + [h for h in headings if h > m.start()])
        blocks.append((int(m.group(1)), m.group(2).strip(), plan[m.start():end].rstrip().rstrip("-").rstrip() + "\n"))
    return blocks


def section(plan: str, pattern: str) -> str:
    starts = _outside(plan, re.compile(pattern, re.M))
    if not starts:
        return ""
    begin = starts[0].start()
    later = [h.start() for h in _outside(plan, HEADING) if h.start() > begin]
    return plan[begin:later[0] if later else len(plan)].rstrip().rstrip("-").rstrip() + "\n"


def context(plan: str) -> str:
    """What every task needs: the plan header, the global constraints and the rules under review."""
    first = _outside(plan, HEADING)
    parts = [plan[:first[0].start()].rstrip() + "\n" if first else plan]
    parts += [section(plan, r"^## Global Constraints.*$"), section(plan, r"^## 1a\..*$")]
    return "\n".join(p for p in parts if p)


UMLAUTS = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "′": "", "’": ""})


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower().translate(UMLAUTS)).strip("-")[:64].strip("-")


def split(plan_path: Path, out: Path) -> list[Path]:
    plan = plan_path.read_text(encoding="utf-8")
    out.mkdir(parents=True, exist_ok=True)
    ctx = context(plan)
    written = [out / "00-context.md"]
    written[0].write_text(ctx, encoding="utf-8")
    for n, title, body in task_blocks(plan):
        path = out / f"{n:02d}-{slug(title)}.md"
        path.write_text(f"{ctx}\n---\n\n{body}{PROTOCOL}", encoding="utf-8")
        written.append(path)
    return written


def allowed_paths(brief: str) -> list[str]:
    m = re.search(r"\*\*Files:\*\*\n(.*?)\n\n", brief, re.S)
    if not m:
        return []
    out: list[str] = []
    for line in m.group(1).splitlines():
        line = re.sub(r"\([^)]*\)", "", line)
        directory = ""
        for token in re.findall(r"`([^`]+)`", line):
            token = re.sub(r":\d+(-\d+)?$", "", token)
            if "/" in token:
                directory = token.rsplit("/", 1)[0] + "/"
                out.append(token)
            elif "." in token:
                out.append(directory + token)
    return out


def changed_files(base: str, cwd: Path) -> list[str]:
    def git(*args: str) -> list[str]:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
        return [line for line in r.stdout.splitlines() if line]
    return sorted(set(git("diff", "--name-only", base) + git("ls-files", "--others", "--exclude-standard")))


def guard(brief_path: Path, base: str = "HEAD", cwd: Path = Path("."), approvals: Path = APPROVALS) -> list[str]:
    brief = brief_path.read_text(encoding="utf-8")
    title = TASK.search(brief)
    problems: list[str] = []
    if title and GATE in title.group(2):
        if not (approvals / f"task-{int(title.group(1))}.ok").is_file():
            problems.append(f"human gate: {approvals}/task-{int(title.group(1))}.ok is missing")
    allowed = allowed_paths(brief)
    for f in changed_files(base, cwd):
        listed = any(fnmatch.fnmatch(f, pat) for pat in allowed)
        if not listed and any(fnmatch.fnmatch(f, pat) for pat in FORBIDDEN):
            problems.append(f"forbidden path: {f}")
        elif not listed:
            problems.append(f"not listed in this task: {f}")
    return problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="plan_tasks")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("plan", type=Path)
    s.add_argument("out", type=Path)
    g = sub.add_parser("guard")
    g.add_argument("brief", type=Path)
    g.add_argument("--base", default="HEAD")
    args = p.parse_args(argv)
    if args.cmd == "split":
        for path in split(args.plan, args.out):
            print(path)
        return 0
    problems = guard(args.brief, args.base)
    for line in problems:
        print("GUARD", line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
