from __future__ import annotations

import csv
import io
import json
import sys
from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table


def ms_to_human(ms: int | float | None) -> str:
    if ms is None:
        return "-"
    total_minutes = int(ms / 60_000)
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.0f}%"


def _to_dicts(data: Any) -> list[dict]:
    if isinstance(data, BaseModel):
        return [data.model_dump(mode="json")]
    if isinstance(data, list):
        return [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in data]
    if isinstance(data, dict):
        return [data]
    return [data]


def _flatten(d: dict, prefix: str = "") -> dict:
    out: dict = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


# --- Formatters ---


def format_json(data: Any) -> str:
    if isinstance(data, BaseModel):
        return data.model_dump_json(indent=2)
    if isinstance(data, list):
        items = [item.model_dump(mode="json") if isinstance(item, BaseModel) else item for item in data]
        return json.dumps(items, indent=2, default=str)
    return json.dumps(data, indent=2, default=str)


def format_csv(data: Any) -> str:
    rows = [_flatten(d) for d in _to_dicts(data)]
    if not rows:
        return ""
    all_keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for k in row:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=all_keys)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def format_markdown_table(data: Any, title: str = "") -> str:
    """Format a list of records as a rich table rendered to string."""
    dicts = _to_dicts(data)
    if not dicts:
        return "No data."
    flat = [_flatten(d) for d in dicts]
    console = Console(file=io.StringIO(), force_terminal=True, width=120)
    table = Table(title=title or None, show_lines=False)
    keys = list(flat[0].keys())
    for key in keys:
        table.add_column(key)
    for row in flat:
        table.add_row(*[str(row.get(k, "")) for k in keys])
    console.print(table)
    output = console.file.getvalue()  # type: ignore[attr-defined]
    return output


def format_markdown_kv(data: Any, title: str = "") -> str:
    """Format a single record as key-value pairs."""
    dicts = _to_dicts(data)
    if not dicts:
        return "No data."
    d = _flatten(dicts[0])
    lines = []
    if title:
        lines.append(f"## {title}\n")
    for k, v in d.items():
        lines.append(f"**{k}**: {v}")
    return "\n".join(lines)


def format_markdown(data: Any, title: str = "") -> str:
    dicts = _to_dicts(data)
    if len(dicts) == 1:
        return format_markdown_kv(data, title)
    return format_markdown_table(data, title)


def output(data: Any, fmt: str | None = None, title: str = "") -> None:
    if fmt is None:
        fmt = "md" if sys.stdout.isatty() else "json"

    if fmt == "json":
        print(format_json(data))
    elif fmt == "csv":
        print(format_csv(data), end="")
    elif fmt == "md":
        print(format_markdown(data, title))
    else:
        print(format_json(data))
