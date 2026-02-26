from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text

from qd.git import CommitDetail, FileStat

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


def print_log(commits: list[CommitDetail]) -> None:
    if not commits:
        console.print("[yellow]No commits found[/yellow]")
        return
    for commit in commits:
        console.print(f"  [bold yellow]{commit.hash}[/bold yellow] {commit.message}")
        for f in commit.files:
            console.print(f"    [dim]{f}[/dim]")
    console.print()


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
