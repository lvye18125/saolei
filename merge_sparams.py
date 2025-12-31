#!/usr/bin/env python3
"""Merge CPW CSV S-parameter files into one table.

Usage:
  python merge_sparams.py --input-dir . --output merged.csv

The script scans for CSV files in the input directory, detects prefixes
like "long", "short", and "thru" in filenames, and merges S-parameter
columns under names such as long_S11_dB, long_S11_deg, etc.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


PREFIX_PATTERNS = {
    "long": re.compile(r"long", re.IGNORECASE),
    "short": re.compile(r"short", re.IGNORECASE),
    "thru": re.compile(r"thru", re.IGNORECASE),
}


def find_header_index(lines: list[str]) -> int:
    for idx, line in enumerate(lines):
        if line.strip().startswith("Freq(Hz)"):
            return idx
    raise ValueError("Header line starting with 'Freq(Hz)' not found.")


def load_sparams(path: Path, prefix: str) -> pd.DataFrame:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    header_index = find_header_index(lines)
    df = pd.read_csv(path, skiprows=header_index)

    expected_cols = [
        "Freq(Hz)",
        "S11(dB)",
        "S11(deg)",
        "S21(dB)",
        "S21(deg)",
        "S12(dB)",
        "S12(deg)",
        "S22(dB)",
        "S22(deg)",
    ]

    available_cols = [col for col in expected_cols if col in df.columns]
    if len(available_cols) < len(expected_cols):
        missing = sorted(set(expected_cols) - set(available_cols))
        raise ValueError(f"Missing expected columns in {path.name}: {missing}")

    df = df[expected_cols]
    rename_map = {
        "S11(dB)": f"{prefix}_S11_dB",
        "S11(deg)": f"{prefix}_S11_deg",
        "S21(dB)": f"{prefix}_S21_dB",
        "S21(deg)": f"{prefix}_S21_deg",
        "S12(dB)": f"{prefix}_S12_dB",
        "S12(deg)": f"{prefix}_S12_deg",
        "S22(dB)": f"{prefix}_S22_dB",
        "S22(deg)": f"{prefix}_S22_deg",
    }
    return df.rename(columns=rename_map)


def detect_prefix(filename: str) -> str | None:
    for prefix, pattern in PREFIX_PATTERNS.items():
        if pattern.search(filename):
            return prefix
    return None


def detect_group(filename: str) -> str:
    match = re.search(r"(\d+)(?=\.[^.]+$)", filename)
    return match.group(1) if match else filename


def merge_group(files: list[Path]) -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for path in files:
        prefix = detect_prefix(path.name)
        if not prefix:
            continue
        df = load_sparams(path, prefix)
        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, on="Freq(Hz)", how="outer")

    if merged is None:
        raise ValueError("No matching files with long/short/thru prefixes found.")

    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge CPW CSV S-parameter data.")
    parser.add_argument("--input-dir", default=".", help="Directory with CSV files.")
    parser.add_argument("--output", default="merged_sparams.csv", help="Output CSV path.")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    csv_files = sorted(input_dir.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found in {input_dir}")

    grouped: dict[str, list[Path]] = {}
    for path in csv_files:
        prefix = detect_prefix(path.name)
        if not prefix:
            continue
        group = detect_group(path.name)
        grouped.setdefault(group, []).append(path)

    if not grouped:
        raise SystemExit("No CSV files matched long/short/thru prefixes.")

    merged_frames = []
    for group_id, files in sorted(grouped.items()):
        merged = merge_group(files)
        merged.insert(0, "set_id", group_id)
        merged_frames.append(merged)

    output = pd.concat(merged_frames, ignore_index=True)
    output.to_csv(args.output, index=False)
    print(f"Wrote {len(output)} rows to {args.output}")


if __name__ == "__main__":
    main()
