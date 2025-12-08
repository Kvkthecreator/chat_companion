import re
from pathlib import Path


def parse_table(sql: str, table: str) -> list[dict[str, str | bool]]:
    pattern = rf"CREATE TABLE public.{table} \((.*?)\);"
    m = re.search(pattern, sql, re.S)
    if not m:
        raise ValueError(f"Table {table} not found")
    body = m.group(1)
    cols: list[dict[str, str | bool]] = []
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if not line or line.startswith("CONSTRAINT"):
            continue
        parts = line.split()
        name, type_ = parts[0], parts[1]
        required = "NOT NULL" in line
        if type_ == "uuid":
            py = "UUID"
            ts = "string"
        elif type_.startswith("timestamp"):
            py = "datetime"
            ts = "string"
        elif type_ == "jsonb":
            py = "dict"
            ts = "Record<string, any>"
        elif type_ == "text":
            py = "str"
            ts = "string"
        elif type_ == "integer":
            py = "int"
            ts = "number"
        else:
            py = "str"
            ts = "string"
        cols.append({"name": name, "py": py, "ts": ts, "required": required})
    return cols


def render_py(table: str, cols: list[dict[str, str | bool]]) -> str:
    lines = [
        "from __future__ import annotations",
        "",
        "from datetime import datetime",
        "from uuid import UUID",
        "from typing import Optional",
        "",
        "from pydantic import BaseModel",
        "",
        f'class {table.rstrip("s").title().replace("_", "")}(BaseModel):',
    ]
    for col in cols:
        field = f"{col['name']}: "
        if col["required"]:
            field += col["py"]
        else:
            field += f"Optional[{col['py']}] = None"
        lines.append(f"    {field}")
    lines.append("")
    return "\n".join(lines)


def render_ts_database(tables: dict[str, list[dict[str, str | bool]]]) -> str:
    lines = [
        "export type Json = string | number | boolean | null | { [key: string]: Json } | Json[];",
        "",
        "export interface Database {",
        "  public: {",
        "    Tables: {",
    ]
    for table, cols in tables.items():
        lines.append(f"      {table}: {{")
        lines.append("        Row: {")
        for col in cols:
            t = col["ts"]
            if not col["required"]:
                t += " | null"
            lines.append(f"          {col['name']}: {t};")
        lines.append("        }")
        lines.append("      }")
    lines.extend(
        [
            "    }",
            "  }",
            "}",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    sql = Path("docs/SCHEMA_SNAPSHOT.sql").read_text()
    out_dir = Path("api/src/app/models")
    out_dir.mkdir(parents=True, exist_ok=True)
    tables = ["blocks", "baskets", "events"]
    table_cols: dict[str, list[dict[str, str | bool]]] = {}
    for table in tables:
        cols = parse_table(sql, table)
        table_cols[table] = cols
        model_py = render_py(table, cols)
        Path(out_dir / f"{table[:-1]}.py").write_text(model_py)

    ts_schema = render_ts_database(table_cols)
    Path("web/lib/dbTypes.ts").write_text(ts_schema + "\n")
    print("Pydantic models and TypeScript types generated.")


if __name__ == "__main__":
    main()
