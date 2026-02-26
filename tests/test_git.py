import os
import subprocess

from qd.git import FileStat, parse_numstat, resolve_range, parse_log_oneline, get_file_stats, get_file_diff, get_commit_info


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


def test_parse_log_oneline_single():
    raw = "a1b2c3f feat: add login page"
    result = parse_log_oneline(raw)
    assert result == [("a1b2c3f", "feat: add login page")]


def test_parse_log_oneline_multiple():
    raw = "a1b2c3f feat: add login\nb2c3d4e fix: typo"
    result = parse_log_oneline(raw)
    assert len(result) == 2
    assert result[1] == ("b2c3d4e", "fix: typo")


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
    subprocess.run(["git", "commit", "-m", "init"], check=True, capture_output=True)

    (tmp_path / "f.txt").write_text("y\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "my commit msg"], check=True, capture_output=True)

    info = get_commit_info("HEAD~1..HEAD")
    assert len(info) == 1
    assert info[0][1] == "my commit msg"


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


def test_get_file_stats_n_exceeds_history(tmp_path):
    """Requesting more commits than exist should not crash."""
    os.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], check=True, capture_output=True)

    (tmp_path / "f.txt").write_text("x\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "only commit"], check=True, capture_output=True)

    # resolve_range clamps n=100 to actual commit count (1)
    resolved = resolve_range(n=100, ref_range=None)
    stats = get_file_stats(resolved)
    assert len(stats) == 1
    assert stats[0].path == "f.txt"
