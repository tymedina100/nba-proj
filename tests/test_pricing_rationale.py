from src.core.pricing import _rationale

def test_rationale_includes_role_minutes_mean_and_delta():
    prior = {"role":"sixth","min_mult":0.88,"rate_mult":1.02,"minutes_mean":29.1}
    pred  = {"minutes":30.0, "mean":22.4}
    s = _rationale(prior, pred, market="PTS", threshold=21.5)
    assert "role=sixth (min×0.88, rate×1.02)" in s
    assert "proj_min≈30.0" in s
    assert "sim_mean=22.40" in s
    assert "Δvs_PTS(21.5)=+0.90" in s
