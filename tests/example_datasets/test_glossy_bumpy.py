"""Tests for GlossyBumpy example dataset from R mlcm package

These tests serve as regression tests to ensure:
1. The wrangling process produces consistent output
2. The scale estimation produces consistent results matching the R implementation
"""

from pathlib import Path

import pandas as pd
import pytest

from mlcm import _wrangle, scale_estimation

DIM_NAMES = ("glossiness", "bumpiness")
PAIR_NAMES = ("1", "2")


@pytest.fixture
def trials():
    """Load the GlossyBumpy trials CSV"""
    return pd.read_csv(Path(__file__).parent / "trials_GlossyBumpy.csv")


@pytest.fixture
def wrangled(trials):
    """Expected wrangled output for GlossyBumpy dataset"""
    return pd.read_csv(Path(__file__).parent / "wrangled_GlossyBumpy.csv")


@pytest.fixture
def scales_full():
    """Expected scales for GlossyBumpy dataset with full model

    These values are produced by the R {{MLCM}} package
    running the R code in `tests/example_datasets/test_GlossyBumpy.R`.

    They should remain stable across changes, thus form regression testing.
    """
    return pd.read_csv(Path(__file__).parent / "scales_GlossyBumpy.csv")


def test_wrangle(trials, wrangled):
    """Test that wrangling GlossyBumpy trials produces expected output"""
    result = _wrangle.wrangle_responses(
        trials,
        dim_names=DIM_NAMES,
        pair_names=PAIR_NAMES,
    )

    assert result.shape == wrangled.shape
    assert list(wrangled.columns) == list(result.columns)
    assert all(result.dtypes == "int64")
    pd.testing.assert_frame_equal(result, wrangled)


def test_scale_estimation_full_model(trials, scales_full):
    """Test that scale estimation with full model produces expected results

    This is a regression test - the expected values come from running the
    code and should remain stable to detect any changes in the algorithm.
    """
    result = scale_estimation.scale_estimation(
        trial_responses=trials,
        modeltype="full",
        dim_names=DIM_NAMES,
        pair_names=PAIR_NAMES,
        bootstrap_nsim=1000,
        seed=123,
    )

    # Check that scales have correct shape (5 levels × 5 levels = 25 combinations)"""
    assert result["scales"].shape == (25, 3)
    assert result["CIs"].shape == (25, 4)

    # Merge
    scales = pd.merge(result["scales"], result["CIs"], on=["glossiness", "bumpiness"])
    scales.rename(columns={"CI_0.025": "CI_low", "CI_0.975": "CI_high"}, inplace=True)

    # Test that scales have correct columns
    assert list(scales.columns) == list(scales_full.columns)

    # Check that scales match expected values (with tolerance for floating point)
    pd.testing.assert_frame_equal(
        scales,
        scales_full,
        atol=1e-5,
    )
