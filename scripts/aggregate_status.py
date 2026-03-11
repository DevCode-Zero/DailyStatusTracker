#!/usr/bin/env python3
"""Aggregate daily/weekly status files into a single Excel workbook."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

COMPLETED_KEYWORDS = {"done", "completed", "closed", "resolved", "finished"}

COLUMN_ALIASES = {
    "assignee": ["assignee", "assigned to", "name", "owner", "resource"],
    "description": ["description", "task", "task description", "work item", "summary"],
    "status": ["status", "state", "current status"],
    "time": ["time", "time spent", "hours", "effort", "spent"],
}


@dataclass
class ProcessResult:
    source_file: str
    records: int


def normalize_col_name(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized = {normalize_col_name(c): c for c in df.columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def to_canonical(df: pd.DataFrame, source_file: Path) -> pd.DataFrame:
    cols: dict[str, str] = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        col = find_column(df, aliases)
        if col:
            cols[canonical] = col

    required = {"assignee", "description", "status"}
    missing = required - set(cols)
    if missing:
        raise ValueError(f"Missing required columns {sorted(missing)} in {source_file.name}")

    result = pd.DataFrame(
        {
            "Assignee": df[cols["assignee"]].astype(str).str.strip(),
            "Description": df[cols["description"]].astype(str).str.strip(),
            "Status": df[cols["status"]].astype(str).str.strip(),
            "Time": df[cols["time"]].astype(str).str.strip() if "time" in cols else "",
            "SourceFile": source_file.name,
        }
    )

    return result[(result["Assignee"] != "") | (result["Description"] != "")].copy()


def read_source(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file format: {path}")


def load_all(input_dir: Path) -> tuple[pd.DataFrame, list[ProcessResult]]:
    files = sorted(
        [
            p
            for p in input_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".xlsx", ".xls", ".csv"}
        ]
    )

    if not files:
        raise ValueError(f"No source files found in {input_dir}")

    frames: list[pd.DataFrame] = []
    results: list[ProcessResult] = []

    for file in files:
        raw = read_source(file)
        canonical = to_canonical(raw, file)
        frames.append(canonical)
        results.append(ProcessResult(source_file=file.name, records=len(canonical)))

    return pd.concat(frames, ignore_index=True), results


def is_completed(status: str) -> bool:
    status_norm = normalize_col_name(status)
    return any(keyword in status_norm for keyword in COMPLETED_KEYWORDS)


def create_summary(all_data: pd.DataFrame, mode: str) -> pd.DataFrame:
    completed_mask = all_data["Status"].astype(str).apply(is_completed)
    completed = all_data[completed_mask]
    non_completed = all_data[~completed_mask]

    rows = [
        ("Mode", mode),
        ("Total tasks", len(all_data)),
        ("Completed tasks", len(completed)),
        ("InProgress/Incomplete tasks", len(non_completed)),
        ("Unique people with completed tasks", completed["Assignee"].nunique()),
        ("Unique people with inprogress/incomplete tasks", non_completed["Assignee"].nunique()),
    ]

    summary = pd.DataFrame(rows, columns=["Metric", "Value"])

    status_counts = (
        all_data.assign(_status=all_data["Status"].astype(str).str.strip())
        .groupby("_status", dropna=False)
        .size()
        .reset_index(name="Count")
        .rename(columns={"_status": "Status"})
        .sort_values(by=["Count", "Status"], ascending=[False, True])
    )

    non_completed_assignee = (
        non_completed.assign(_assignee=non_completed["Assignee"].astype(str).str.strip())
        .groupby("_assignee", dropna=False)
        .size()
        .reset_index(name="InProgress/Incomplete Count")
        .rename(columns={"_assignee": "Assignee"})
        .sort_values(by=["InProgress/Incomplete Count", "Assignee"], ascending=[False, True])
    )

    separator = pd.DataFrame([["", ""]], columns=["Metric", "Value"])
    status_section_header = pd.DataFrame([["Status breakdown", ""]], columns=["Metric", "Value"])
    assignee_header = pd.DataFrame([["InProgress/Incomplete by assignee", ""]], columns=["Metric", "Value"])

    status_section = status_counts.rename(columns={"Status": "Metric", "Count": "Value"})
    assignee_section = non_completed_assignee.rename(
        columns={"Assignee": "Metric", "InProgress/Incomplete Count": "Value"}
    )

    return pd.concat(
        [
            summary,
            separator,
            status_section_header,
            status_section,
            separator,
            assignee_header,
            assignee_section,
        ],
        ignore_index=True,
    )


def write_output(all_data: pd.DataFrame, output_file: Path, mode: str) -> None:
    completed_mask = all_data["Status"].astype(str).apply(is_completed)
    completed = all_data[completed_mask].sort_values(by=["Assignee", "Status", "Description"])
    non_completed = all_data[~completed_mask].sort_values(by=["Assignee", "Status", "Description"])
    summary = create_summary(all_data, mode=mode)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        completed.to_excel(writer, index=False, sheet_name="Completed")
        non_completed.to_excel(writer, index=False, sheet_name="InProgress_or_Incomplete")
        summary.to_excel(writer, index=False, sheet_name="Summary")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate team status files to one workbook")
    parser.add_argument("--input-dir", required=True, type=Path, help="Folder containing .xlsx/.xls/.csv files")
    parser.add_argument("--output-file", required=True, type=Path, help="Output .xlsx path")
    parser.add_argument(
        "--mode",
        choices=["daily", "weekly"],
        default="daily",
        help="Used in summary to indicate reporting mode",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    all_data, result_rows = load_all(args.input_dir)
    write_output(all_data, args.output_file, args.mode)

    print(f"Created: {args.output_file}")
    print("Files processed:")
    for row in result_rows:
        print(f"- {row.source_file}: {row.records} record(s)")


if __name__ == "__main__":
    main()
