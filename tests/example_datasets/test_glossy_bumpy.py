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

    These values are produced by the R {{MLCM}} package, running
    ```
    mlcm(GlossyBumpy, modeltype="full")
    ```
    They should remain stable across changes, thus form regression testing.
    """
    scales_data = [
        (1, 1, 0.000000),
        (2, 1, -0.327530),
        (3, 1, 1.301358),
        (4, 1, 3.254507),
        (5, 1, 3.513034),
        (1, 2, 0.773183),
        (2, 2, 0.586811),
        (3, 2, 1.930494),
        (4, 2, 4.097627),
        (5, 2, 5.222958),
        (1, 3, 0.819287),
        (2, 3, 0.746685),
        (3, 3, 2.577413),
        (4, 3, 4.279270),
        (5, 3, 5.771482),
        (1, 4, 0.815532),
        (2, 4, 1.361006),
        (3, 4, 3.057501),
        (4, 4, 4.991377),
        (5, 4, 5.228731),
        (1, 5, 1.253929),
        (2, 5, 1.252005),
        (3, 5, 3.106025),
        (4, 5, 4.039719),
        (5, 5, 5.181385),
    ]
    return pd.DataFrame(scales_data, columns=["glossiness", "bumpiness", "scale"])


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
    )

    # Check that scales have correct shape (5 levels × 5 levels = 25 combinations)"""
    assert result["scales"].shape == (25, 3)

    # Test that scales have correct columns
    expected_columns = ["glossiness", "bumpiness", "scale"]
    assert list(scales_full.columns) == expected_columns

    # Check that scales match expected values (with tolerance for floating point)
    pd.testing.assert_frame_equal(
        result["scales"],
        scales_full,
        atol=1e-5,
    )
