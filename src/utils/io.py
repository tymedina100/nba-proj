# src/utils/io.py
import pathlib, pandas as pd, glob

def ensure_dir(path):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

def write_csv(df: pd.DataFrame, path):
    ensure_dir(path)
    df.to_csv(path, index=False)

def read_csv_glob(pattern):
    files = glob.glob(pattern)
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
