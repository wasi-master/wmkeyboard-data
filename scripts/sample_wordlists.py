#!/usr/bin/env python3
"""
Sample evenly-spaced lines from each gz wordlist under data/.
Useful for human spot-checking and validation across the whole file.
"""

import argparse
import gzip
from pathlib import Path

from rich.console import Console

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def uniform_sample(path: Path, n: int) -> list[str]:
    lines: list[str] = []

    # Read all valid lines into memory
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)

    if not lines:
        return []

    total_lines = len(lines)

    # If the file has fewer lines than requested, just return them all
    if total_lines <= n:
        return lines

    # If only 1 line is requested, pick the middle one
    if n == 1:
        return [lines[total_lines // 2]]

    # Calculate evenly spaced indices from 0 (front) to total_lines - 1 (end)
    indices = [int(i * (total_lines - 1) / (n - 1)) for i in range(n)]

    return [lines[i] for i in indices]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample uniformly distributed lines (front to end) from each wordlist"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=5,
        help="Number of samples per file (default: 5)",
    )
    parser.add_argument(
        "--show-offensive",
        action="store_true",
        help="Show offensive words",
    )
    args = parser.parse_args()

    files = sorted(
        fp
        for lang_dir in DATA_DIR.iterdir()
        if lang_dir.is_dir()
        for fp in lang_dir.glob("*.txt.gz")
    )

    if not args.show_offensive:
        files = [fp for fp in files if "offensive" not in fp.name]

    console = Console()
    console.print(f"\n[bold underline]Uniform sample ({args.n} lines per file)[/bold underline]\n")

    for fp in files:
        lang_id = fp.parent.name
        label = fp.stem.replace(f"{lang_id}_", "")

        samples = uniform_sample(fp, args.n)

        # Skip printing the header if the file had no valid samples
        if not samples:
            continue

        # Print the Language and File label as a header
        console.print(f"[bold cyan]{lang_id}[/bold cyan] [dim]>[/dim] {label}")

        # Print the full sampled lines as an indented bulleted list
        for sample in samples:
            console.print(f"  [green]•[/green] {sample}")

        # Add a blank line between files for readability
        console.print()


if __name__ == "__main__":
    main()
