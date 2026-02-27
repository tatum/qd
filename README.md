# qd

A CLI tool for quickly reviewing recent git changes. Designed for workflows where you want to see exactly what changed in the last commit(s) before moving on.

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install globally
uv tool install . --force

# Or run directly from the project
uv sync
uv run qd
```

## Usage

Run `qd` inside any git repository.

```bash
qd              # summary table for the last commit
qd -n 3         # last 3 commits combined
qd main..HEAD   # arbitrary ref range
qd -f           # full diff (all files)
qd -i           # interactive: pick files to view
qd -l           # log view: commits with files changed
```

### Flags

| Flag | Description | Default |
|------|-------------|---------|
| `-n, --num-commits` | Number of recent commits to review | 1 (10 in log mode) |
| `-f, --full-diff` | Show full diff for all files | off |
| `-i, --interactive` | Interactive per-file review | off |
| `-l, --log` | Show commits with files modified | off |

### Examples

**Default output** shows a summary table:

```
 qd — 1 commit (a1b2c3f → "feat: add login page")

 #  File                        +    -   Status
 1  src/components/Login.tsx    47    0   added
 2  src/api/auth.ts             12    3   modified
 3  tests/login.test.ts         31    0   added

 3 files changed, 90 insertions, 3 deletions
```

**Interactive mode** (`qd -i`) shows the summary then prompts you to pick files by number to view their diffs. Type `q` to quit.

**Log mode** (`qd -l`) shows a compact commit list with changed files:

```
  a1b2c3f feat: add login page
    src/components/Login.tsx
    src/api/auth.ts
  b2c3d4e fix: typo in config
    config.yaml
```

## License

MIT
