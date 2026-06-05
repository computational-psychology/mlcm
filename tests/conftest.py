"""
Defining fixtures for testing scale estimation.

It contains:

-  a 'mock' toy dataset of two dimensions, two levels per dimension, and 7 trials.
- the expected scale output for this toy dataset, for all mlcm models
(independent, additive and full).

Fixtures are used by test_wranging.py and test_scale_estimation.py
"""

import numpy as np
import pandas as pd
import pytest

from mlcm.utils import first_diff_char


@pytest.fixture
def pair_names():
    return ("left", "right")


@pytest.fixture
def p_names():
    return {"left": "l", "right": "r"}


@pytest.fixture
def dim_names():
    return ("dimA", "dimB")


@pytest.fixture
def stim_levels(dim_names):
    return {dim_names[0]: [0.5, 3.0], dim_names[1]: ["high", "low"]}


@pytest.fixture
def trial_responses(dim_names, pair_names):
    columns = [f"{dim}_{side}" for dim in dim_names for side in pair_names]
    return pd.DataFrame.from_records(
        [
            # Same dimB (high), right has higher dimA
            (pair_names[1], 0.5, 3.0, "high", "high"),
            # Same dimB (high), left has higher dimA
            (pair_names[0], 3.0, 0.5, "high", "high"),
            # Same dimB (low), right has higher dimA
            (pair_names[1], 0.5, 3.0, "low", "low"),
            # Same dimB (low), left has higher dimA
            (pair_names[0], 3.0, 0.5, "low", "low"),
            # Same dimA (3.0), right has higher dimB
            (pair_names[1], 3.0, 3.0, "low", "high"),
            # Different dimA and dimB, right wins on both
            (pair_names[1], 0.5, 3.0, "low", "high"),
            # Different dimA and dimB, dimB vs dimA conflict
            (pair_names[0], 0.5, 3.0, "high", "low"),
        ],
        columns=["response", *columns],
    )


@pytest.fixture
def wrangled_responses(dim_names, pair_names):
    p_names = first_diff_char(*pair_names)
    columns = [f"{dim}_{side}" for dim in dim_names for side in p_names.values()]
    return pd.DataFrame(
        np.array(
            [
                # Same dimB (high), right has higher dimA
                [1, 1, 2, 1, 1],
                # Same dimB (high), left has higher dimA
                [0, 2, 1, 1, 1],
                # Same dimB (low), right has higher dimA
                [1, 1, 2, 2, 2],
                # Same dimB (low), left has higher dimA
                [0, 2, 1, 2, 2],
                # Same dimA (3.0), right has higher dimB
                [1, 2, 2, 2, 1],
                # Different dimA and dimB, right wins on both
                [1, 1, 2, 2, 1],
                # Different dimA and dimB, dimB vs dimA conflict
                [0, 1, 2, 1, 2],
            ]
        ),
        columns=["Resp", *columns],
    )


@pytest.fixture
def scales_array_full(epsilon):
    """Raw scales from 'full' model

    Parameters
    ----------
    epsilon : float
        Tolerance for convergence used in the fitting algorithm

    Returns
    -------
    numpy.NDarray
        scales
    """
    match epsilon:
        case 1e-14:
            return np.array([[0, 16.616466108594388], [-8.30664663681216, 8.211698785130059]])
        case 1e-4:
            return np.array([[0, 9.91], [-4.97, 4.86]])
        case _:
            raise ValueError("Invalid epsilon")


@pytest.fixture
def scales_array_add(epsilon):
    """Raw scales from 'add' model

    Parameters
    ----------
    epsilon : float
        Tolerance for convergence used in the fitting algorithm, by default 1e-14

    Returns
    -------
    numpy.NDarray
        scales
    """
    match epsilon:
        case 1e-14:
            return np.array([[0, 0], [-8.35971347787794, 16.57]])
        case 1e-4:
            return np.array([[0, 0], [-5.01, 9.87]])
        case _:
            raise ValueError("Invalid epsilon")


@pytest.fixture
def scales_add(stim_levels, dim_names):
    scales = pd.concat(
        [
            pd.Series(
                stim_levels[dim_names[0]] * len(stim_levels[dim_names[1]]), name=dim_names[0]
            ),
            pd.Series(
                [
                    item
                    for item in stim_levels[dim_names[1]]
                    for i in range(len(stim_levels[dim_names[0]]))
                ],
                name=dim_names[1],
            ),
            pd.Series([0, -8.35971347787794, 0, -8.35971347787794], name="scale"),
        ],
        axis="columns",
    )

    return scales


@pytest.fixture
def scales_add_normalized(scales_add):
    scales = scales_add
    scales["scale"] = (scales["scale"] - np.min(scales["scale"])) / (
        np.max(scales["scale"]) - np.min(scales["scale"])
    )

    return scales


@pytest.fixture
def scales_full(stim_levels, dim_names):
    scales = pd.concat(
        [
            pd.Series(
                stim_levels[dim_names[0]] * len(stim_levels[dim_names[1]]), name=dim_names[0]
            ),
            pd.Series(
                [
                    item
                    for item in stim_levels[dim_names[1]]
                    for i in range(len(stim_levels[dim_names[0]]))
                ],
                name=dim_names[1],
            ),
            pd.Series([0, -8.30664663681216, 16.616466108594388, 8.211698785130059], name="scale"),
        ],
        axis="columns",
    )
    return scales


@pytest.fixture
def scales_full_normalized(scales_full):
    scales = scales_full
    scales["scale"] = (scales["scale"] - np.min(scales["scale"])) / (
        np.max(scales["scale"]) - np.min(scales["scale"])
    )

    return scales


@pytest.fixture
def scales_full_idc(stim_levels, dim_names):
    scales = pd.concat(
        [
            pd.Series(
                [*range(1, len(stim_levels[dim_names[0]]) + 1)] * len(stim_levels[dim_names[1]]),
                name=dim_names[0],
            ),
            pd.Series(
                [
                    item + 1
                    for item in range(len(stim_levels[dim_names[1]]))
                    for i in range(len(stim_levels[dim_names[0]]))
                ],
                name=dim_names[1],
            ),
            pd.Series([0, -8.30664663681216, 16.616466108594388, 8.211698785130059], name="scale"),
        ],
        axis="columns",
    )
    return scales


@pytest.fixture
def scales_add_idc(stim_levels, dim_names):
    scales = pd.concat(
        [
            pd.Series(
                [*range(1, len(stim_levels[dim_names[0]]) + 1)] * len(stim_levels[dim_names[1]]),
                name=dim_names[0],
            ),
            pd.Series(
                [
                    item + 1
                    for item in range(len(stim_levels[dim_names[1]]))
                    for i in range(len(stim_levels[dim_names[0]]))
                ],
                name=dim_names[1],
            ),
            pd.Series([0, -8.35971347787794, 0, -8.35971347787794], name="scale"),
        ],
        axis="columns",
    )
    return scales
