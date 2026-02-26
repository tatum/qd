# qd Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `qd`, a CLI tool for quickly reviewing recent git changes with an interactive per-file diff viewer.

**Architecture:** Three-module Python package — `git.py` handles subprocess calls and parses git output into dataclasses, `display.py` renders with `rich`, `cli.py` wires them together via `click`. Installed as a global tool via `uv tool install`.

**Tech Stack:** Python 3.11+, click, rich, pytest

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/qd/__init__.py`
- Create: `src/qd/cli.py` (stub)
- Create: `src/qd/git.py` (stub)
- Create: `src/qd/display.py` (stub)
- Create: `tests/__init__.py`
- Create: `tests/test_git.py` (stub)

**Step 1: Create pyproject.toml**

```toml
[project]
name = "qd"
version = "0.1.0"
description = "Quick diff review tool for recent git changes"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
]

[project.scripts]
qd = "qd.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/qd"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[dependency-groups]
dev = ["pytest>=8.0"]
```

**Step 2: Create package stubs**

`src/qd/__init__.py`:
```python
```

`src/qd/cli.py`:
```python
import click


@click.command()
def main():
    click.echo("qd")


if __name__ == "__main__":
    main()
```

`src/qd/git.py`:
```python
```

`src/qd/display.py`:
```python
```

`tests/__init__.py`:
```python
```

`tests/test_git.py`:
```python
```

**Step 3: Install and verify**

Run: `uv sync`
Run: `uv run qd`
Expected: prints "qd"

**Step 4: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: scaffold qd project with click entry point"
```

---

### Task 2: Git Data Layer — Parse File Stats

**Files:**
- Create: `src/qd/git.py`
- Create: `tests/test_git.py`

**Step 1: Write the failing test for parsing git numstat output**

`tests/test_git.py`:
```python
from qd.git import parse_numstat


def test_parse_numstat_modified_file():
    raw = "12\t3\tsrc/api/auth.ts"
    result = parse_numstat(raw)
    assert len(result) == 1
    assert result[0].path == "src/api/auth.ts"
    assert result[0].insertions == 12
    assert result[0].deletions == 3
    assert result[0].is_binary is False


def test_parse_numstat_added_file():
    raw = "47\t0\tsrc/components/Login.tsx"
    result = parse_numstat(raw)
    assert result[0].insertions == 47
    assert result[0].deletions == 0


def test_parse_numstat_binary_file():
    raw = "-\t-\timage.png"
    result = parse_numstat(raw)
    assert result[0].is_binary is True
    assert result[0].insertions == 0
    assert result[0].deletions == 0


def test_parse_numstat_multiple_files():
    raw = "12\t3\tsrc/api/auth.ts\n47\t0\tsrc/Login.tsx\n-\t-\timg.png"
    result = parse_numstat(raw)
    assert len(result) == 3


def test_parse_numstat_empty():
    result = parse_numstat("")
    assert result == []
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_git.py -v`
Expected: FAIL — `cannot import name 'parse_numstat'`

**Step 3: Write minimal implementation**

`src/qd/git.py`:
```python
from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class FileStat:
    path: str
    insertions: int
    deletions: int
    is_binary: bool

    @property
    def status(self) -> str:
        if self.is_binary:
            return "binary"
        if self.deletions == 0 and self.insertions > 0:
            return "added"
        if self.insertions == 0 and self.deletions > 0:
            return "deleted"
        return "modified"


def parse_numstat(raw: str) -> list[FileStat]:
    if not raw.strip():
        return []
    results = []
    for line in raw.strip().split("\n"):
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        ins_str, del_str, path = parts
        is_binary = ins_str == "-"
        results.append(FileStat(
            path=path,
            insertions=0 if is_binary else int(ins_str),
            deletions=0 if is_binary else int(del_str),
            is_binary=is_binary,
        ))
    return results
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_git.py -v`
Expected: all 5 tests PASS

**Step 5: Commit**

```bash
git add src/qd/git.py tests/test_git.py
git commit -m "feat: parse git numstat output into FileStat dataclasses"
```

---

### Task 3: Git Data Layer — Resolve Ranges and Fetch Data

**Files:**
- Modify: `src/qd/git.py`
- Modify: `tests/test_git.py`

**Step 1: Write failing tests for range resolution**

Append to `tests/test_git.py`:
```python
from qd.git import resolve_range


def test_resolve_range_default():
    """Default: last 1 commit."""
    result = resolve_range(n=1, ref_range=None)
    assert result == "HEAD~1..HEAD"


def test_resolve_range_n_commits():
    result = resolve_range(n=3, ref_range=None)
    assert result == "HEAD~3..HEAD"


def test_resolve_range_explicit():
    result = resolve_range(n=1, ref_range="main..HEAD")
    assert result == "main..HEAD"


def test_resolve_range_explicit_overrides_n():
    """Explicit range takes priority over -n."""
    result = resolve_range(n=5, ref_range="main..feature")
    assert result == "main..feature"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_git.py::test_resolve_range_default -v`
Expected: FAIL — `cannot import name 'resolve_range'`

**Step 3: Implement resolve_range**

Add to `src/qd/git.py`:
```python
def resolve_range(n: int, ref_range: str | None) -> str:
    if ref_range:
        return ref_range
    return f"HEAD~{n}..HEAD"
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_git.py -v`
Expected: all 9 tests PASS

**Step 5: Write failing test for get_commit_summary**

Append to `tests/test_git.py`:
```python
from qd.git import parse_log_oneline


def test_parse_log_oneline_single():
    raw = "a1b2c3f feat: add login page"
    result = parse_log_oneline(raw)
    assert result == [("a1b2c3f", "feat: add login page")]


def test_parse_log_oneline_multiple():
    raw = "a1b2c3f feat: add login\nb2c3d4e fix: typo"
    result = parse_log_oneline(raw)
    assert len(result) == 2
    assert result[1] == ("b2c3d4e", "fix: typo")
```

**Step 6: Implement parse_log_oneline**

Add to `src/qd/git.py`:
```python
def parse_log_oneline(raw: str) -> list[tuple[str, str]]:
    if not raw.strip():
        return []
    results = []
    for line in raw.strip().split("\n"):
        hash_, _, message = line.partition(" ")
        results.append((hash_, message))
    return results
```

**Step 7: Write failing test for get_diff (integration-style, needs real git repo)**

Append to `tests/test_git.py`:
```python
import os
import tempfile

from qd.git import get_file_stats, get_file_diff, get_commit_info


def test_get_file_stats_real_repo(tmp_path):
    """Integration test using a real temporary git repo."""
    os.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True, capture_output=True)

    # Initial commit
    (tmp_path / "hello.txt").write_text("hello\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], check=True, capture_output=True)

    # Second commit
    (tmp_path / "hello.txt").write_text("hello\nworld\n")
    (tmp_path / "new.txt").write_text("new file\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add stuff"], check=True, capture_output=True)

    stats = get_file_stats("HEAD~1..HEAD")
    assert len(stats) == 2
    paths = [s.path for s in stats]
    assert "hello.txt" in paths
    assert "new.txt" in paths


def test_get_file_diff_real_repo(tmp_path):
    os.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True, capture_output=True)

    (tmp_path / "hello.txt").write_text("hello\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], check=True, capture_output=True)

    (tmp_path / "hello.txt").write_text("hello\nworld\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "edit"], check=True, capture_output=True)

    diff = get_file_diff("HEAD~1..HEAD", "hello.txt")
    assert "+world" in diff


def test_get_commit_info_real_repo(tmp_path):
    os.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True, capture_output=True)

    (tmp_path / "f.txt").write_text("x\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "my commit msg"], check=True, capture_output=True)

    info = get_commit_info("HEAD~1..HEAD")
    assert len(info) == 1
    assert info[0][1] == "my commit msg"
```

**Step 8: Implement git subprocess functions**

Add to `src/qd/git.py`:
```python
def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip())
    return result.stdout.strip()


class GitError(Exception):
    pass


def is_git_repo() -> bool:
    try:
        _run_git("rev-parse", "--git-dir")
        return True
    except GitError:
        return False


def get_file_stats(ref_range: str) -> list[FileStat]:
    raw = _run_git("diff", "--numstat", "--first-parent", ref_range)
    return parse_numstat(raw)


def get_file_diff(ref_range: str, path: str) -> str:
    return _run_git("diff", "--first-parent", ref_range, "--", path)


def get_commit_info(ref_range: str) -> list[tuple[str, str]]:
    raw = _run_git("log", "--oneline", "--first-parent", ref_range)
    return parse_log_oneline(raw)
```

**Step 9: Run all tests**

Run: `uv run pytest tests/test_git.py -v`
Expected: all tests PASS

**Step 10: Commit**

```bash
git add src/qd/git.py tests/test_git.py
git commit -m "feat: git data layer with range resolution, file stats, and diffs"
```

---

### Task 4: Display Layer — Summary Table

**Files:**
- Create: `src/qd/display.py`

**Step 1: Implement the summary table renderer**

`src/qd/display.py`:
```python
from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text

from qd.git import FileStat

console = Console()

MAX_DIFF_LINES = 200


def print_summary(
    stats: list[FileStat],
    commits: list[tuple[str, str]],
    ref_range: str,
) -> None:
    if not stats:
        console.print("[yellow]No changes found[/yellow]")
        return

    # Header
    if len(commits) == 1:
        hash_, msg = commits[0]
        console.print(f"\n [bold]qd[/bold] — 1 commit ({hash_} → \"{msg}\")\n")
    else:
        console.print(f"\n [bold]qd[/bold] — {len(commits)} commits ({ref_range})\n")

    # Table
    table = Table(show_header=True, header_style="bold", pad_edge=True, box=None)
    table.add_column("#", style="dim", width=4)
    table.add_column("File", no_wrap=True)
    table.add_column("+", justify="right", style="green")
    table.add_column("-", justify="right", style="red")
    table.add_column("Status")

    total_ins = 0
    total_del = 0

    for i, stat in enumerate(stats, 1):
        ins_str = "[binary]" if stat.is_binary else str(stat.insertions)
        del_str = "" if stat.is_binary else str(stat.deletions)
        status_style = {
            "added": "green",
            "deleted": "red",
            "modified": "yellow",
            "binary": "dim",
        }.get(stat.status, "")
        table.add_row(
            str(i),
            stat.path,
            ins_str,
            del_str,
            Text(stat.status, style=status_style),
        )
        total_ins += stat.insertions
        total_del += stat.deletions

    console.print(table)
    console.print(
        f"\n {len(stats)} file{'s' if len(stats) != 1 else ''} changed, "
        f"[green]{total_ins} insertion{'s' if total_ins != 1 else ''}[/green], "
        f"[red]{total_del} deletion{'s' if total_del != 1 else ''}[/red]\n"
    )


def print_hint() -> None:
    console.print(" [dim]Run[/dim] qd -i [dim]to review, or[/dim] qd -f [dim]for full diff[/dim]\n")


def print_full_diff(diff: str) -> None:
    if not diff.strip():
        console.print("[yellow]No diff content[/yellow]")
        return
    syntax = Syntax(diff, "diff", theme="monokai")
    console.print(syntax)


def print_file_diff(diff: str, path: str) -> None:
    if not diff.strip():
        console.print(f"[yellow]No changes in {path}[/yellow]")
        return
    lines = diff.split("\n")
    if len(lines) > MAX_DIFF_LINES:
        truncated = "\n".join(lines[:MAX_DIFF_LINES])
        syntax = Syntax(truncated, "diff", theme="monokai")
        console.print(syntax)
        console.print(
            f"\n [dim]... truncated ({len(lines)} lines total). "
            f"Use[/dim] qd -f | less [dim]for full output.[/dim]\n"
        )
    else:
        syntax = Syntax(diff, "diff", theme="monokai")
        console.print(syntax)


def interactive_loop(stats: list[FileStat], ref_range: str) -> None:
    while True:
        try:
            choice = console.input("\n[bold]File number[/bold] (q to quit): ")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if choice.strip().lower() == "q":
            break

        try:
            idx = int(choice.strip()) - 1
            if idx < 0 or idx >= len(stats):
                console.print(f"[red]Pick 1-{len(stats)}[/red]")
                continue
        except ValueError:
            console.print(f"[red]Pick 1-{len(stats)} or q[/red]")
            continue

        stat = stats[idx]
        if stat.is_binary:
            console.print(f"[dim]{stat.path} is a binary file[/dim]")
            continue

        from qd.git import get_file_diff
        diff = get_file_diff(ref_range, stat.path)
        console.print()
        print_file_diff(diff, stat.path)
```

**Step 2: Verify it imports cleanly**

Run: `uv run python -c "from qd.display import print_summary; print('ok')"`
Expected: `ok`

**Step 3: Commit**

```bash
git add src/qd/display.py
git commit -m "feat: rich display layer with summary table, diff viewer, and interactive loop"
```

---

### Task 5: CLI Entry Point — Wire Everything Together

**Files:**
- Modify: `src/qd/cli.py`

**Step 1: Implement the full CLI**

`src/qd/cli.py`:
```python
import sys

import click

from qd.git import (
    GitError,
    get_commit_info,
    get_file_diff,
    get_file_stats,
    is_git_repo,
    resolve_range,
)
from qd.display import (
    console,
    interactive_loop,
    print_full_diff,
    print_hint,
    print_summary,
)


@click.command()
@click.argument("ref_range", required=False, default=None)
@click.option("-n", "num_commits", type=int, default=1, help="Number of recent commits to review.")
@click.option("-f", "full_diff", is_flag=True, help="Show full diff for all files.")
@click.option("-i", "interactive", is_flag=True, help="Interactive per-file review mode.")
def main(ref_range: str | None, num_commits: int, full_diff: bool, interactive: bool):
    """Quick diff review for recent git changes."""
    if not is_git_repo():
        console.print("[red]qd: not a git repo[/red]")
        sys.exit(1)

    resolved = resolve_range(num_commits, ref_range)

    try:
        stats = get_file_stats(resolved)
        commits = get_commit_info(resolved)
    except GitError as e:
        console.print(f"[red]qd: {e}[/red]")
        sys.exit(1)

    if full_diff:
        for stat in stats:
            diff = get_file_diff(resolved, stat.path)
            print_full_diff(diff)
        return

    print_summary(stats, commits, resolved)

    if interactive:
        interactive_loop(stats, resolved)
    else:
        if stats:
            print_hint()


if __name__ == "__main__":
    main()
```

**Step 2: Test manually in this repo**

Run: `uv run qd`
Expected: summary table showing recent commit files

Run: `uv run qd -n 3`
Expected: summary table for last 3 commits

Run: `uv run qd -i`
Expected: summary table, then interactive prompt

Run: `uv run qd -f`
Expected: full colored diff output

**Step 3: Commit**

```bash
git add src/qd/cli.py
git commit -m "feat: wire CLI entry point with all modes"
```

---

### Task 6: Edge Cases and Polish

**Files:**
- Modify: `tests/test_git.py`
- Modify: `src/qd/git.py`

**Step 1: Write test for status detection on FileStat**

Append to `tests/test_git.py`:
```python
from qd.git import FileStat


def test_filestat_status_added():
    assert FileStat("f.txt", 10, 0, False).status == "added"


def test_filestat_status_deleted():
    assert FileStat("f.txt", 0, 10, False).status == "deleted"


def test_filestat_status_modified():
    assert FileStat("f.txt", 5, 3, False).status == "modified"


def test_filestat_status_binary():
    assert FileStat("f.png", 0, 0, True).status == "binary"


def test_filestat_status_empty_modified():
    """A file with 0 insertions and 0 deletions but not binary is modified (e.g. mode change)."""
    assert FileStat("f.txt", 0, 0, False).status == "modified"
```

**Step 2: Run tests**

Run: `uv run pytest tests/test_git.py -v`
Expected: all PASS

**Step 3: Fix FileStat.status if needed**

The current `status` property returns "modified" for the 0/0 non-binary case because neither the `deletions == 0` nor `insertions == 0` early returns trigger. This is correct for mode changes — no code fix needed.

**Step 4: Write test for n-clamping with real repo**

Append to `tests/test_git.py`:
```python
def test_get_file_stats_n_exceeds_history(tmp_path):
    """Requesting more commits than exist should not crash."""
    os.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True, capture_output=True)

    (tmp_path / "f.txt").write_text("x\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "only commit"], check=True, capture_output=True)

    # HEAD~100..HEAD on a 1-commit repo — git handles this gracefully
    stats = get_file_stats("HEAD~100..HEAD")
    assert len(stats) == 1
    assert stats[0].path == "f.txt"
```

**Step 5: Run tests**

Run: `uv run pytest tests/test_git.py -v`
Expected: all PASS (git handles this natively)

**Step 6: Commit**

```bash
git add tests/test_git.py
git commit -m "test: edge cases for file status detection and history clamping"
```

---

### Task 7: Global Install and Claude Code Slash Command

**Files:**
- Verify: `pyproject.toml` (already has entry point)

**Step 1: Install globally**

Run: `uv tool install . --force`
Run: `qd` (from project root, should work)
Run: `qd -i` (interactive mode)

**Step 2: Verify it works from another directory**

Run: `cd /tmp && git clone --depth=5 https://github.com/pallets/click.git /tmp/qd-test-repo && cd /tmp/qd-test-repo && qd && cd -`

Or just `cd` to any local git repo and run `qd`.

**Step 3: Commit any final adjustments**

```bash
git add -A
git commit -m "chore: finalize qd for global installation"
```

(Only if there are changes to commit.)

---

### Task 8: Final Integration Test

**Step 1: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: all tests PASS

**Step 2: Manual smoke test of all modes**

Run each and verify output:
```bash
qd
qd -n 3
qd -f
qd -i
```

**Step 3: Final commit if needed**

```bash
git add -A
git commit -m "chore: final polish"
```
