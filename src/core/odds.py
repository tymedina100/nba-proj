from __future__ import annotations
import pandas as pd

REQUIRED = ["player_id","market","side","line","decimal_odds"]
ALLOWED_SIDES = {"OVER","UNDER"}

def validate_odds(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SystemExit(f"[odds] missing columns: {missing}")
    out = df.copy()
    out["player_id"] = out["player_id"].astype(str)
    out["market"] = out["market"].astype(str)
    out["side"] = out["side"].astype(str).str.upper().str.strip()
    out["line"] = pd.to_numeric(out["line"], errors="coerce")
    out["decimal_odds"] = pd.to_numeric(out["decimal_odds"], errors="coerce")

    bad_side = ~out["side"].isin(ALLOWED_SIDES)
    bad_num = out["line"].isna() | out["decimal_odds"].isna() | (out["decimal_odds"] <= 1.0)
    errs = out[bad_side | bad_num]
    if not errs.empty:
        raise SystemExit(
            "[odds] invalid rows:\n"
            + errs.to_string(index=False)
            + "\nRules: side in {OVER,UNDER}; decimal_odds>1; numeric line."
        )
    return out