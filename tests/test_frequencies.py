import numpy as np
import pandas as pd

from mlcm import frequencies


def test_conjoint():
    trials = pd.DataFrame(
        {
            "dim1_A": [1, 2, 3],
            "dim2_A": ["X", "Y", "X"],
            "dim1_B": [2, 3, 1],
            "dim2_B": ["Y", "Y", "X"],
            "repeats": ["3", "2", "4"],
        }
    )

    freqs = frequencies.conjoint(trials, col="repeats")

    assert [freqs.index.name, freqs.columns.name] == ["A", "B"]
    assert freqs.index.names == freqs.columns.names == ["dim2", "dim1"]
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

    assert np.array_equal(
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
        equal_nan=True,
    )


def test_frequencies(): ...


def test_response_choice():
    # Setup input trials
    trials = pd.DataFrame(
        {
            "dim1_A": [1, 2],
            "dim2_A": ["X", "Y"],
            "dim1_B": [2, 1],
            "dim2_B": ["Y", "Y"],
            "response": ["A", "B"],
        }
    )

    # Determine (conjoint) response choice frequencies for response "A"
    freqs = frequencies.response_choice(trials, choice="A")

    assert np.array_equal(
        freqs.values,
        np.array(
            [
                [np.nan, np.nan, np.nan, 1.0],
                [np.nan, np.nan, np.nan, np.nan],
                [np.nan, np.nan, np.nan, np.nan],
                [np.nan, 0.0, np.nan, np.nan],
            ]
        ),
        equal_nan=True,
    )


def test_collapse():
    freqs = pd.DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

    freqs_upper = frequencies.collapse(freqs)

    np.array_equal(
        freqs_upper.values,
        np.array(
            [
                [np.nan, 6, 10],
                [np.nan, np.nan, 14],
                [np.nan, np.nan, np.nan],
            ]
        ),
        equal_nan=True,
    )
