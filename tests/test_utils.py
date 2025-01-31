import pandas as pd

from mlcm import utils


def test_extract_stim_levels(pair_names, dim_names):
    trials = {
        "dimA_l": [1, 2, 3],
        "dimB_l": ["X", "Y", "X"],
        "dimA_r": [2, 3, 1],
        "dimB_r": ["Y", "Y", "X"],
        "response": ["l", "r", "l"],
    }
    trials = pd.DataFrame(trials)

    stim_levels = utils.extract_stim_levels(trials, dim_names=dim_names, pair_names=pair_names)

    assert tuple(stim_levels.keys()) == dim_names
    assert all(stim_levels["dimA"] == (1, 2, 3))
    assert all(stim_levels["dimB"] == ("X", "Y"))


def test_extract_3_dim_levels(pair_names):
    trials = {
        "dimX_l": [1, 2, 3],
        "dimY_l": ["X", "Y", "X"],
        "dimZ_l": [0.5, 5.0, 5.0],
        "dimX_r": [2, 3, 1],
        "dimY_r": ["Y", "Y", "X"],
        "dimZ_r": [2.0, 0.5, 2.0],
        "response": ["l", "r", "l"],
    }
    trials = pd.DataFrame(trials)

    stim_levels = utils.extract_stim_levels(
        trials, dim_names=("dimX", "dimY", "dimZ"), pair_names=pair_names
    )

    assert tuple(stim_levels.keys()) == ("dimX", "dimY", "dimZ")
    assert all(stim_levels["dimX"] == (1, 2, 3))
    assert all(stim_levels["dimY"] == ("X", "Y"))
    assert all(stim_levels["dimZ"] == (0.5, 2.0, 5.0))


def test_dimension_combinations():
    stim_levels = {"dimY": ["X", "Y"], "dimX": [1, 2, 3]}

    unique_stimuli = utils.dimension_combinations(stim_levels)

    assert list(unique_stimuli.values) == [
        ("X", 1),
        ("X", 2),
        ("X", 3),
        ("Y", 1),
        ("Y", 2),
        ("Y", 3),
    ]


def test_three_dimension_combinations():
    stim_levels = {"dimY": ["X", "Y"], "dimX": [1, 2, 3], "dimZ": [0.5, 2.0, 5.0]}

    unique_stimuli = utils.dimension_combinations(stim_levels)

    assert list(unique_stimuli.values) == [
        ("X", 1, 0.5),
        ("X", 1, 2.0),
        ("X", 1, 5.0),
        ("X", 2, 0.5),
        ("X", 2, 2.0),
        ("X", 2, 5.0),
        ("X", 3, 0.5),
        ("X", 3, 2.0),
        ("X", 3, 5.0),
        ("Y", 1, 0.5),
        ("Y", 1, 2.0),
        ("Y", 1, 5.0),
        ("Y", 2, 0.5),
        ("Y", 2, 2.0),
        ("Y", 2, 5.0),
        ("Y", 3, 0.5),
        ("Y", 3, 2.0),
        ("Y", 3, 5.0),
    ]
