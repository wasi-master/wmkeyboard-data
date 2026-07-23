import argparse
import gzip
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich import print as rprint
import humanize
import langcodes

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


console = Console()

def count_words_in_gz(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        return sum(1 for line in f if line.strip())

def sort_key(item, sort_by):
    lang_id, entry = item
    if sort_by == "lang":
        return (langcodes.get(lang_id, lang_id).display_name().lower(), 0, 0)
    if sort_by == "full_words":
        full_count = entry.get("full.txt", (0, 0))[0]
        return (full_count, 0, 0)
    if sort_by == "size":
        total_size = sum(s for (_, s) in entry.values())
        return (total_size, 0, 0)
    if sort_by == "offensive_words":
        offensive = entry.get("offensive.txt")
        offensive_count = offensive[0] if offensive else -1
        full_count = entry.get("full.txt", (0, 0))[0]
        return (offensive_count, full_count, 0)
    return (0, 0, 0)

def main(args):
    files = sorted(
        fp
        for lang_dir in DATA_DIR.iterdir()
        if lang_dir.is_dir()
        for fp in lang_dir.glob("*.txt.gz")
    )

    rows = []
    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        "[progress.percentage]{task.percentage:>3.1f}%",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Counting words...", total=len(files))
        for fp in files:
            lang_dir = fp.parent.name
            try:
                count = count_words_in_gz(fp)
            except Exception as e:
                progress.log(f"[red]Error reading {fp}: {e}[/red]")
                progress.advance(task)
                continue
            label = fp.stem.replace(f"{lang_dir}_", "")
            rows.append((lang_dir, label, count, fp.stat().st_size))
            progress.advance(task)

    grouped = {}
    for lang_id, label, count, size in rows:
        grouped.setdefault(lang_id, {})[label] = (count, size)

    sorted_langs = sorted(grouped.items(), key=lambda item: sort_key(item, args.sort_by), reverse=args.reverse)

    table = Table(title="Wordlists")
    table.add_column("Language", justify="left", style="cyan", no_wrap=True)
    table.add_column("Full Words", justify="right", style="green")
    table.add_column("Full Size", justify="right", style="yellow")
    table.add_column("Offensive Words", justify="right", style="green")
    table.add_column("Offensive Size", justify="right", style="yellow")
    table.add_column("Romanized Words", justify="right", style="blue")
    table.add_column("Romanized Size", justify="right", style="magenta")

    total_full_words = 0
    total_offensive_words = 0
    total_rom_words = 0
    total_full_size = 0
    total_offensive_size = 0
    total_rom_size = 0

    for lang_id, entry in sorted_langs:
        full_count, full_size = entry.get("full.txt", (0, 0))
        offensive_count, offensive_size = entry.get("offensive.txt", (None, None))
        rom_count, rom_size = entry.get("rom.txt", (None, None))

        lang_name = langcodes.get(lang_id, lang_id).display_name()
        table.add_row(
            lang_name,
            f"{full_count:,}",
            humanize.naturalsize(full_size),
            f"{offensive_count:,}" if offensive_count is not None else "",
            humanize.naturalsize(offensive_size) if offensive_size is not None else "",
            f"{rom_count:,}" if rom_count is not None else "",
            humanize.naturalsize(rom_size) if rom_size is not None else "",
        )

        total_full_words += full_count
        total_full_size += full_size
        if offensive_count is not None:
            total_offensive_words += offensive_count
            total_offensive_size += offensive_size
        if rom_count is not None:
            total_rom_words += rom_count
            total_rom_size += rom_size

    table.add_section()
    total_size = total_full_size + total_offensive_size + total_rom_size
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_full_words:,}[/bold]",
        f"[bold]{humanize.naturalsize(total_full_size)}[/bold]",
        f"[bold]{total_offensive_words:,}[/bold]",
        f"[bold]{humanize.naturalsize(total_offensive_size)}[/bold]",
        f"[bold]{total_rom_words:,}[/bold]",
        f"[bold]{humanize.naturalsize(total_rom_size)}[/bold]",
    )

    console.print(table)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List wordlists with word counts")
    parser.add_argument(
        "--sort-by",
        choices=["lang", "full_words", "size", "offensive_words"],
        default="lang",
        help="Column to sort by (lowest to highest)",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Sort highest to lowest",
    )
    args = parser.parse_args()
    main(args)
