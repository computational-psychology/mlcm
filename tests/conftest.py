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
    return {dim_names[0]: ["high", "low"], dim_names[1]: [0.5, 3.0]}


@pytest.fixture
def trial_responses(dim_names, pair_names):
    columns = [f"{dim}_{side}" for dim in dim_names for side in pair_names]
    return pd.DataFrame.from_records(
        [
            ("right", "high", "high", 0.5, 3.0),
            ("right", "high", "high", 3.0, 0.5),
            ("right", "high", "high", 3.0, 3.0),
            ("left", "high", "low", 3.0, 0.5),
            ("left", "high", "low", 3.0, 3.0),
            ("right", "low", "high", 3.0, 3.0),
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
                [1, 1, 1, 1, 2],
                [1, 1, 1, 2, 1],
                [1, 1, 1, 2, 2],
                [0, 1, 2, 2, 1],
                [0, 1, 2, 2, 2],
                [1, 2, 1, 2, 2],
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
            return np.array([[0, 0], [7.80, 7.80]])
        case 1e-4:
            return np.array([[0, 0], [4.17, 4.17]])
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
            return np.array([[0, 0], [7.80, 0]])
        case 1e-4:
            return np.array([[0, 0], [4.17, 0]])
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
            pd.Series([0, 7.795727, 0, 7.795727], name="scale"),
        ],
        axis="columns",
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
            pd.Series([0, 7.795727, 0, 7.795741], name="scale"),
        ],
        axis="columns",
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
            pd.Series([0, 7.795727, 0, 7.795741], name="scale"),
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
            pd.Series([0, 7.795727, 0, 7.795727], name="scale"),
        ],
        axis="columns",
    )
    return scales
