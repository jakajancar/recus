from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console(highlight=False)


def pretty(data: dict | list) -> None:
    """Pretty-print a JSON-serialisable object."""
    console.print_json(data=data)


def table(columns: list[str], rows: list[tuple[str, ...]]) -> None:
    """Print a simple table."""
    t = Table()
    for col in columns:
        t.add_column(col)
    for row in rows:
        t.add_row(*row)
    console.print(t)
