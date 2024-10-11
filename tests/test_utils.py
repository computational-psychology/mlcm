import pandas as pd

from mlcm import utils


def test_extract_stim_levels():
    trials = {
        "dim1_A": [1, 2, 3],
        "dim2_A": ["X", "Y", "X"],
        "dim1_B": [2, 3, 1],
        "dim2_B": ["Y", "Y", "X"],
        "response": ["A", "B", "A"],
    }
    trials = pd.DataFrame(trials)

    stim_levels = utils.extract_stim_levels(
        trials, dim_names=("dim1", "dim2"), pair_names=("A", "B")
    )

    assert tuple(stim_levels.keys()) == ("dim1", "dim2")
    assert all(stim_levels["dim1"] == (1, 2, 3))
    assert all(stim_levels["dim2"] == ("X", "Y"))


def test_dimension_combinations():
    stim_levels = {"dim1": [1, 2, 3], "dim2": ["X", "Y"]}

    unique_stimuli = utils.dimension_combinations(stim_levels)

    assert list(unique_stimuli.values) == [
        ("X", 1),
        ("X", 2),
        ("X", 3),
        ("Y", 1),
        ("Y", 2),
        ("Y", 3),
    ]
