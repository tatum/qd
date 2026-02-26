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


def _commit_count() -> int:
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return 0
    return int(result.stdout.strip())


_EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def resolve_range(n: int, ref_range: str | None) -> str:
    if ref_range:
        return ref_range
    total = _commit_count()
    n = min(n, total)
    if n >= total:
        # At or beyond root commit — diff against the empty tree
        return f"{_EMPTY_TREE}..HEAD"
    return f"HEAD~{n}..HEAD"


def parse_log_oneline(raw: str) -> list[tuple[str, str]]:
    if not raw.strip():
        return []
    results = []
    for line in raw.strip().split("\n"):
        hash_, _, message = line.partition(" ")
        results.append((hash_, message))
    return results


class GitError(Exception):
    pass


def _repo_root() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=_repo_root(),
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip())
    return result.stdout.strip()


def is_git_repo() -> bool:
    try:
        _run_git("rev-parse", "--git-dir")
        return True
    except GitError:
        return False


def get_file_stats(ref_range: str) -> list[FileStat]:
    raw = _run_git("diff", "--numstat", ref_range)
    return parse_numstat(raw)


def get_file_diff(ref_range: str, path: str) -> str:
    return _run_git("diff", ref_range, "--", path)


def get_commit_info(ref_range: str) -> list[tuple[str, str]]:
    raw = _run_git("log", "--oneline", "--first-parent", ref_range)
    return parse_log_oneline(raw)
