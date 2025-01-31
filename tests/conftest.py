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
