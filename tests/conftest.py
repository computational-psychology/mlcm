import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def pair_names():
    return ("l", "r")


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
            ("r", "high", "high", 0.5, 3.0),
            ("r", "high", "high", 3.0, 0.5),
            ("r", "high", "high", 3.0, 3.0),
            ("l", "high", "low", 3.0, 0.5),
            ("l", "high", "low", 3.0, 3.0),
            ("r", "low", "high", 3.0, 3.0),
        ],
        columns=["response", *columns],
    )


@pytest.fixture
def wrangled_responses(dim_names, pair_names):
    columns = [f"{dim}_{side}" for dim in dim_names for side in pair_names]
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
def scales_full_idc(epsilon):
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
def scales_add_idc(epsilon):
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
