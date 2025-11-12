#!/usr/bin/env python3
"""
CSV/Excel Automation Tool
Merges, filters, renames, and validates tabular data files.
"""
import argparse
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def read_table(path: Path) -> pd.DataFrame:
    """
    Reads CSV or Excel file with encoding fallback.
    
    Args:
        path: File path to read
        
    Returns:
        DataFrame with file contents
        
    Raises:
        ValueError: If file format is unsupported
        Exception: If file is corrupted or unreadable
    """
    try:
        if path.suffix.lower() in [".xlsx", ".xls"]:
            return pd.read_excel(path)
        if path.suffix.lower() == ".csv":
            try:
                return pd.read_csv(path, encoding='utf-8')
            except UnicodeDecodeError:
                logger.warning(f"{path.name} using latin1 encoding")
                return pd.read_csv(path, encoding='latin1')
    except Exception as e:
        logger.error(f"Failed to read {path.name}: {e}")
        raise
    
    raise ValueError(f"Unsupported format: {path}")


def merge_inputs(inputs: list[Path]) -> pd.DataFrame:
    """
    Concatenates multiple CSV/Excel files into single DataFrame.
    
    Args:
        inputs: List of file paths to merge
        
    Returns:
        Merged DataFrame with reset index
    """
    frames = []
    for p in inputs:
        df = read_table(p)
        logger.info(f"Loaded {p.name} → {len(df)} rows, {len(df.columns)} cols")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def parse_mapping(mapping_str: str) -> dict[str, str]:
    """
    Parses column rename mapping from string format.
    
    Args:
        mapping_str: Format 'old1:new1,old2:new2'
        
    Returns:
        Dictionary mapping old names to new names
    """
    mapping = {}
    if not mapping_str:
        return mapping
    for pair in mapping_str.split(","):
        old, new = pair.split(":")
        mapping[old.strip()] = new.strip()
    return mapping


def main() -> int:
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="CSV/Excel automation: merge, select, rename, validate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic merge
  python csv_tool.py --inputs a.csv b.csv --output merged.csv

  # Merge with column selection and rename
  python csv_tool.py \\
    --inputs data/*.csv \\
    --output result.xlsx \\
    --select "id,name,amount" \\
    --rename "name:client,amount:value"

  # With required column validation
  python csv_tool.py \\
    --inputs *.csv \\
    --output clean.csv \\
    --required "id,email"
        """
    )
    parser.add_argument(
        "--inputs", 
        nargs="+", 
        required=True, 
        type=Path,
        help="Input CSV/XLSX files"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        type=Path,
        help="Output file (.csv or .xlsx)"
    )
    parser.add_argument(
        "--select", 
        help="Columns to keep (comma-separated)"
    )
    parser.add_argument(
        "--rename", 
        help='Rename mapping: "old:new,old2:new2"'
    )
    parser.add_argument(
        "--required", 
        help="Required columns (comma-separated)"
    )
    args = parser.parse_args()

    try:
        # Merge input files
        df = merge_inputs(args.inputs)
        logger.info(f"Merged: {len(df)} total rows")

        # Column selection
        if args.select:
            cols = [c.strip() for c in args.select.split(",")]
            missing_cols = [c for c in cols if c not in df.columns]
            if missing_cols:
                logger.error(f"Columns not found: {missing_cols}")
                logger.info(f"Available: {list(df.columns)}")
                return 2
            df = df[cols]
            logger.info(f"Selected columns: {cols}")

        # Column renaming
        if args.rename:
            mapping = parse_mapping(args.rename)
            invalid = [old for old in mapping.keys() if old not in df.columns]
            if invalid:
                logger.warning(f"Cannot rename non-existent: {invalid}")
                mapping = {k: v for k, v in mapping.items() if k not in invalid}
            if mapping:
                df = df.rename(columns=mapping)
                logger.info(f"Renamed: {mapping}")

        # Required column validation
        if args.required:
            required_cols = [c.strip() for c in args.required.split(",")]
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                logger.error(f"Missing required columns: {missing}")
                return 2
            logger.info("✓ All required columns present")

        # Summary
        logger.info(f"Final: {len(df)} rows × {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")

        # Save output
        args.output.parent.mkdir(parents=True, exist_ok=True)
        
        if args.output.suffix.lower() == ".csv":
            df.to_csv(args.output, index=False)
        elif args.output.suffix.lower() in [".xlsx", ".xls"]:
            df.to_excel(args.output, index=False)
        else:
            raise ValueError("Output must be .csv or .xlsx")
        
        logger.info(f"✓ Saved: {args.output}")
        return 0

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())