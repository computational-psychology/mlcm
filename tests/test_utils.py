import pandas as pd

from mlcm import utils


def test_extract_stim_levels():
    trials = {
        "dimX_A": [1, 2, 3],
        "dimY_A": ["X", "Y", "X"],
        "dimX_B": [2, 3, 1],
        "dimY_B": ["Y", "Y", "X"],
        "response": ["A", "B", "A"],
    }
    trials = pd.DataFrame(trials)

    stim_levels = utils.extract_stim_levels(
        trials, dim_names=("dimX", "dimY"), pair_names=("A", "B")
    )

    assert tuple(stim_levels.keys()) == ("dimX", "dimY")
    assert all(stim_levels["dimX"] == (1, 2, 3))
    assert all(stim_levels["dimY"] == ("X", "Y"))


def test_dimension_combinations():
    stim_levels = {"dimX": [1, 2, 3], "dimY": ["X", "Y"]}

    unique_stimuli = utils.dimension_combinations(stim_levels)

    assert list(unique_stimuli.values) == [
        ("X", 1),
        ("X", 2),
        ("X", 3),
        ("Y", 1),
        ("Y", 2),
        ("Y", 3),
    ]
