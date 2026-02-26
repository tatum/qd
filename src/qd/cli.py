import sys

import click

from qd.git import (
    GitError,
    get_commit_info,
    get_commit_log,
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
    print_log,
    print_summary,
)


@click.command()
@click.argument("ref_range", required=False, default=None)
@click.option("-n", "num_commits", type=int, default=None, help="Number of recent commits to review.")
@click.option("-f", "full_diff", is_flag=True, help="Show full diff for all files.")
@click.option("-i", "interactive", is_flag=True, help="Interactive per-file review mode.")
@click.option("-l", "log", is_flag=True, help="Show commits with files modified.")
def main(ref_range: str | None, num_commits: int | None, full_diff: bool, interactive: bool, log: bool):
    """Quick diff review for recent git changes."""
    if not is_git_repo():
        console.print("[red]qd: not a git repo[/red]")
        sys.exit(1)

    if num_commits is None:
        num_commits = 10 if log else 1

    resolved = resolve_range(num_commits, ref_range)

    try:
        stats = get_file_stats(resolved)
        commits = get_commit_info(resolved)
    except GitError as e:
        console.print(f"[red]qd: {e}[/red]")
        sys.exit(1)

    if log:
        commit_details = get_commit_log(resolved)
        print_log(commit_details)
        return

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
