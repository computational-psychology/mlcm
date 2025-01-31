import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def wrangled_responses():
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
        columns=["Resp", "dimA_l", "dimA_r", "dimB_l", "dimB_r"],
    )
