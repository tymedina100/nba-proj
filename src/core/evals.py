# src/core/evals.py
import argparse, json, pathlib

def main(run_date: str):
    diag = dict(
        date=run_date,
        notes="Diagnostics placeholder. Add CLV and calibration once real outcomes exist.",
        metrics=dict(samples=0, coverage80=None, reliability=None)
    )
    out = pathlib.Path(f"runs/{run_date}/diagnostics.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(diag, indent=2))
    print(f"[diag] wrote {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    main(args.date)
