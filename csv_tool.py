#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path
import sys
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported format: {path}")

def merge_inputs(inputs):
    frames = []
    for p in inputs:
        df = read_table(p)
        logging.info("Loaded %s -> %s rows, %s cols", p.name, len(df), len(df.columns))
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def parse_mapping(mapping_str: str) -> dict:
    # Format: "old1:new1,old2:new2"
    mapping = {}
    if not mapping_str:
        return mapping
    for pair in mapping_str.split(","):
        old, new = pair.split(":")
        mapping[old.strip()] = new.strip()
    return mapping

def main():
    parser = argparse.ArgumentParser(
        description="CSV/Excel automation: merge, select, rename, validate."
    )
    parser.add_argument("--inputs", nargs="+", required=True, type=Path,
                        help="Input CSV/XLSX files")
    parser.add_argument("--output", required=True, type=Path,
                        help="Output file (.csv or .xlsx)")
    parser.add_argument("--select", help="Columns to keep, comma-separated")
    parser.add_argument("--rename", help='Mapping "old:new,old2:new2"')
    parser.add_argument("--required", help="Required columns, comma-separated")
    args = parser.parse_args()

    df = merge_inputs(args.inputs)

    if args.select:
        cols = [c.strip() for c in args.select.split(",")]
        df = df[cols]
        logging.info("Column selection: %s", cols)

    if args.rename:
        mapping = parse_mapping(args.rename)
        df = df.rename(columns=mapping)
        logging.info("Rename applied: %s", mapping)

    if args.required:
        required_cols = [c.strip() for c in args.required.split(",")]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logging.error("Missing required columns: %s", missing)
            sys.exit(2)
        logging.info("Validation OK. All required columns are present.")

    if args.output.suffix.lower() == ".csv":
        df.to_csv(args.output, index=False)
    elif args.output.suffix.lower() in [".xlsx", ".xls"]:
        df.to_excel(args.output, index=False)
    else:
        raise ValueError("Output must be .csv or .xlsx")
    logging.info("Saved: %s (%s rows)", args.output, len(df))

if __name__ == "__main__":
    main()