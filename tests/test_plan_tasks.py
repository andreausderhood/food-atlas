import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import plan_tasks  # noqa: E402

PLAN = """# Demo Plan

**Goal:** demo

## Global Constraints

- keep it honest

---

## 1a. Regeln

Regel 6 gilt.

## 2. Freigaben

nur Hintergrund.

### Task 0: Worktree

**Files:** keine.

- [ ] **Step 1: x**

### Task 1: Store

**Files:**
- Create: `src/atlas/unified/cells.py`, `fields.py`
- Modify: `src/atlas/cli.py` (3 Zeilen, siehe `Task 5`)
- Delete: `data/images/*.jpg` (7 Dateien)
- Test: `tests/test_unified_store.py`

**Interfaces:**
- Produces: nothing

- [ ] **Step 1: y**

### Task 2: Regel ändern [HUMAN GATE]

**Files:**
- Modify: `src/atlas/contract.py:10-20`

- [ ] **Step 1: z**

## 5. Roadmap

nicht Teil eines Tasks.
"""


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@t")
    git(tmp_path, "config", "user.name", "t")
    for f in ("src/atlas/build.py", "src/atlas/cli.py", "src/atlas/contract.py"):
        (tmp_path / f).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / f).write_text("x\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def test_split_writes_context_and_self_contained_briefs(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text(PLAN)
    files = plan_tasks.split(plan, tmp_path / "out")
    assert [f.name for f in files] == ["00-context.md", "00-worktree.md", "01-store.md", "02-regel-aendern-human-gate.md"]
    brief = (tmp_path / "out" / "01-store.md").read_text()
    assert "keep it honest" in brief and "Regel 6 gilt." in brief          # context is embedded
    assert "nur Hintergrund" not in brief and "nicht Teil eines Tasks" not in brief
    assert "Ausführungsprotokoll" in brief and "### Task 1: Store" in brief


def test_allowed_paths_handle_multi_token_bullets_and_comments():
    body = plan_tasks.task_blocks(PLAN)[1][2]
    assert plan_tasks.allowed_paths(body) == [
        "src/atlas/unified/cells.py", "src/atlas/unified/fields.py", "src/atlas/cli.py",
        "data/images/*.jpg", "tests/test_unified_store.py"]
    assert plan_tasks.allowed_paths(plan_tasks.task_blocks(PLAN)[0][2]) == []
    assert plan_tasks.allowed_paths(plan_tasks.task_blocks(PLAN)[2][2]) == ["src/atlas/contract.py"]


def test_guard_passes_only_listed_files(tmp_path):
    root = repo(tmp_path)
    plan = root / "plan.md"
    plan.write_text(PLAN)
    plan_tasks.split(plan, root / "briefs")
    brief = next((root / "briefs").glob("01-*.md"))
    (root / "src/atlas/unified").mkdir(parents=True)
    (root / "src/atlas/unified/cells.py").write_text("ok\n")
    problems = plan_tasks.guard(brief, cwd=root, approvals=root / "ap")
    assert not any("cells.py" in p for p in problems)          # the listed file passes
    assert "not listed in this task: plan.md" in problems      # everything else is reported


def test_guard_flags_forbidden_and_unlisted_paths(tmp_path):
    root = repo(tmp_path)
    plan = root / "plan.md"
    plan.write_text(PLAN)
    plan_tasks.split(plan, tmp_path.parent / (tmp_path.name + "-briefs"))
    brief = next((tmp_path.parent / (tmp_path.name + "-briefs")).glob("01-*.md"))
    (root / "src/atlas/build.py").write_text("changed\n")
    (root / "src/atlas/unified").mkdir(parents=True)
    (root / "src/atlas/unified/cells.py").write_text("ok\n")
    (root / "stray.txt").write_text("x\n")
    problems = plan_tasks.guard(brief, cwd=root, approvals=root / "ap")
    assert "forbidden path: src/atlas/build.py" in problems
    assert "not listed in this task: stray.txt" in problems
    assert not any("cells.py" in p for p in problems)


def test_human_gate_needs_an_approval_file_outside_the_task(tmp_path):
    root = repo(tmp_path)
    briefs = tmp_path.parent / (tmp_path.name + "-b2")
    plan = tmp_path.parent / (tmp_path.name + "-plan.md")
    plan.write_text(PLAN)
    plan_tasks.split(plan, briefs)
    brief = next(briefs.glob("02-*.md"))
    ap = tmp_path.parent / (tmp_path.name + "-ap")
    assert any("human gate" in p for p in plan_tasks.guard(brief, cwd=root, approvals=ap))
    ap.mkdir()
    (ap / "task-2.ok").write_text("ok")
    assert plan_tasks.guard(brief, cwd=root, approvals=ap) == []


def test_headings_inside_code_fences_are_examples_not_structure():
    fenced = PLAN.replace("### Task 1: Store\n", "### Task 1: Store\n\n```python\nX = \"\"\"\n### Task 9: fake\n## Fake heading\n\"\"\"\n```\n")
    blocks = plan_tasks.task_blocks(fenced)
    assert [b[0] for b in blocks] == [0, 1, 2]
    assert "## Fake heading" in blocks[1][2] and "**Interfaces:**" in blocks[1][2]   # not cut at the fake heading


def test_slug_transliterates_german():
    assert plan_tasks.slug("Identität — Kanten, Cluster") == "identitaet-kanten-cluster"
    assert plan_tasks.slug("Regel 6′ — Produktdatensätze") == "regel-6-produktdatensaetze"
