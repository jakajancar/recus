from __future__ import annotations

from rich.console import Console
from rich.table import Table

console = Console(highlight=False)


def pretty(data: dict | list) -> None:
    """Pretty-print a JSON-serialisable object."""
    console.print_json(data=data)


def table(columns: list[str], rows: list[tuple[str, ...]], no_wrap_cols: set[str] | None = None) -> None:
    """Print a simple table."""
    t = Table()
    for col in columns:
        t.add_column(col, no_wrap=col in (no_wrap_cols or set()))
    for row in rows:
        t.add_row(*row)
    console.print(t)
