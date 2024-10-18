import numpy as np
import pandas as pd

from mlcm import frequencies


def test_conjoint():
    trials = pd.DataFrame(
        {
            "dimX_left": [1, 2, 3],
            "dimY_left": ["X", "Y", "X"],
            "dimX_right": [2, 3, 1],
            "dimY_right": ["Y", "Y", "X"],
            "repeats": ["3", "2", "4"],
        }
    )

    freqs = frequencies.conjoint(trials, col="repeats")

    assert [freqs.index.name, freqs.columns.name] == ["left", "right"]
    assert freqs.index.names == freqs.columns.names == ["dimY", "dimX"]
    assert (
        list(freqs.columns)
        == list(freqs.index)
        == [
            ("X", 1),
            ("X", 2),
            ("X", 3),
            ("Y", 1),
            ("Y", 2),
            ("Y", 3),
        ]
    )

    np.testing.assert_array_equal(
        freqs.values.astype(float),
        np.array(
            [
                [np.nan, np.nan, np.nan, np.nan, 3, np.nan],
                [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
                [4, np.nan, np.nan, np.nan, np.nan, np.nan],
                [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
                [np.nan, np.nan, np.nan, np.nan, np.nan, 2],
                [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            ],
        ),
    )


def test_conjoint_choice():
    # Setup input trials
    trials = pd.DataFrame(
        {
            "dimX_left": [1, 2, 1],
            "dimY_left": ["X", "Y", "X"],
            "dimX_right": [2, 1, 1],
            "dimY_right": ["Y", "X", "X"],
            "response": ["left", "right", "right"],
        }
    )

    # Determine (conjoint) response choice frequencies
    freqs = frequencies.conjoint_choice(trials)

    np.testing.assert_array_equal(
        freqs.values,
        np.array(
            [
                [1.0, np.nan, np.nan, 0.0],
                [np.nan, np.nan, np.nan, np.nan],
                [np.nan, np.nan, np.nan, np.nan],
                [np.nan, np.nan, np.nan, np.nan],
            ]
        ),
    )


def test_response_choice():
    # Setup input trials
    trials = pd.DataFrame(
        {
            "dimX_left": [1, 2],
            "dimY_left": ["X", "Y"],
            "dimX_right": [2, 1],
            "dimY_right": ["Y", "Y"],
            "response": ["left", "right"],
        }
    )

    # Determine (conjoint) response choice frequencies for response "left"
    freqs = frequencies.response_choice(trials, choice="left")

    np.testing.assert_array_equal(
        freqs.values,
        np.array(
            [
                [np.nan, np.nan, np.nan, 1.0],
                [np.nan, np.nan, np.nan, np.nan],
                [np.nan, np.nan, np.nan, np.nan],
                [np.nan, 0.0, np.nan, np.nan],
            ]
        ),
    )


def test_collapse():
    freqs_row = pd.DataFrame(
        [
            [1.0, np.nan, np.nan, 1.0],
            [np.nan, np.nan, np.nan, np.nan],
            [np.nan, 2.0, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
        ]
    )
    freqs_col = pd.DataFrame(
        [
            [np.nan, np.nan, np.nan, np.nan],
            [0.0, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan],
            [1.0, np.nan, np.nan, np.nan],
        ]
    )

    freqs_upper = frequencies.collapse(freqs_row, freqs_col)

    np.array_equal(
        freqs_upper.values,
        np.array(
            [
                [1.0, 0.0, np.nan, 2.0],
                [np.nan, np.nan, 2.0, np.nan],
                [np.nan, np.nan, np.nan, np.nan],
                [np.nan, np.nan, np.nan, np.nan],
            ]
        ),
        equal_nan=True,
    )
