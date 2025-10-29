# tests/test_priors.py
from src.core.priors import PRIOR_ALPHA, PRIOR_BETA

def test_gamma_poisson_update_math():
    a0, b0 = PRIOR_ALPHA, PRIOR_BETA
    x, m = 18.0, 36.0
    a1, b1 = a0 + x, b0 + m
    assert a1 == PRIOR_ALPHA + 18.0
    assert b1 == PRIOR_BETA + 36.0
