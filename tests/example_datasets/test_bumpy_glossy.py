"""Tests for BumpyGlossy example dataset from R mlcm package

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
    """Load the BumpyGlossy trials CSV"""
    return pd.read_csv(Path(__file__).parent / "trials_BumpyGlossy.csv")


@pytest.fixture
def wrangled(trials):
    """Expected wrangled output for BumpyGlossy dataset"""
    return pd.read_csv(Path(__file__).parent / "wrangled_BumpyGlossy.csv")


@pytest.fixture
def scales_full():
    """Expected scales for BumpyGlossy dataset with full model

    These values are produced by the R {{MLCM}} package, running
    ```
    mlcm(BumpyGlossy, modeltype="full")
    ```
    They should remain stable across changes, thus form regression testing.
    """
    scales_data = [
        (1, 1, 0.000000),
        (2, 1, 1.201542),
        (3, 1, 1.116909),
        (4, 1, 1.960073),
        (5, 1, 1.728852),
        (1, 2, 2.926971),
        (2, 2, 2.951799),
        (3, 2, 3.117224),
        (4, 2, 3.446865),
        (5, 2, 3.210776),
        (1, 3, 4.303391),
        (2, 3, 4.069461),
        (3, 3, 4.449477),
        (4, 3, 4.333013),
        (5, 3, 4.820267),
        (1, 4, 5.579857),
        (2, 4, 5.551860),
        (3, 4, 5.504941),
        (4, 4, 5.931481),
        (5, 4, 6.078623),
        (1, 5, 6.331301),
        (2, 5, 6.731333),
        (3, 5, 6.520746),
        (4, 5, 6.884271),
        (5, 5, 7.250571),
    ]
    return pd.DataFrame(scales_data, columns=["glossiness", "bumpiness", "scale"])


def test_wrangle(trials, wrangled):
    """Test that wrangling BumpyGlossy trials produces expected output"""
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
