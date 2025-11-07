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
    raise ValueError(f"Formato no soportado: {path}")

def merge_inputs(inputs):
    frames = []
    for p in inputs:
        df = read_table(p)
        logging.info("Cargado %s -> %s filas, %s cols", p.name, len(df), len(df.columns))
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def parse_mapping(mapping_str: str) -> dict:
    # Formato: "old1:new1,old2:new2"
    mapping = {}
    if not mapping_str:
        return mapping
    for pair in mapping_str.split(","):
        old, new = pair.split(":")
        mapping[old.strip()] = new.strip()
    return mapping

def main():
    parser = argparse.ArgumentParser(description="Automatización de CSV/Excel: merge, selección, renombrado, validación.")
    parser.add_argument("--inputs", nargs="+", required=True, type=Path, help="Archivos CSV/XLSX de entrada")
    parser.add_argument("--output", required=True, type=Path, help="Archivo de salida (.csv o .xlsx)")
    parser.add_argument("--select", help="Columnas a mantener, separadas por coma")
    parser.add_argument("--rename", help='Mapa "old:new,old2:new2"')
    parser.add_argument("--required", help="Columnas obligatorias, separadas por coma")
    args = parser.parse_args()

    df = merge_inputs(args.inputs)

    if args.select:
        cols = [c.strip() for c in args.select.split(",")]
        df = df[cols]
        logging.info("Selección de columnas: %s", cols)

    if args.rename:
        mapping = parse_mapping(args.rename)
        df = df.rename(columns=mapping)
        logging.info("Renombrado aplicado: %s", mapping)

    if args.required:
        required_cols = [c.strip() for c in args.required.split(",")]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logging.error("Faltan columnas requeridas: %s", missing)
            sys.exit(2)
        logging.info("Validación OK. Todas las columnas requeridas presentes.")

    if args.output.suffix.lower() == ".csv":
        df.to_csv(args.output, index=False)
    elif args.output.suffix.lower() in [".xlsx", ".xls"]:
        df.to_excel(args.output, index=False)
    else:
        raise ValueError("Salida debe ser .csv o .xlsx")
    logging.info("Guardado: %s (%s filas)", args.output, len(df))

if __name__ == "__main__":
    main()