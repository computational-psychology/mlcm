import pandas as pd


def extract_stim_levels(trials, dim_names=("dimX", "dimY"), pair_names=("A", "B")):
    """Extract unique stimulus levels for each dimension, from trial data

    Parameters
    ----------
    trials : pandas.DataFrame
        raw trials response data, with one column per dimension x pair combination
        e.g., "dimX_A", "dimY_A", "dimX_B", "dimY_B"
    dim_names : tuple[str], optional
        names for the stimulus dimensions, by default ("dimX", "dimY")
    pair_names : tuple[str], optional
        names for the stimulus pair members, by default ("A", "B")

    Returns
    -------
    dict[str, list]
        unique stimulus levels per stimulus dimension,
        e.g., {"dimX": [...], "dimY": [...]}
    """
    unique_levels = {}
    for dim in dim_names:
        unique_levels[dim] = pd.concat([trials[f"{dim}_{pair}"] for pair in pair_names]).unique()

    return unique_levels


def dimension_combinations(stim_levels):
    """All possible unique stimuli, i.e., combinations of levels for stimulus dimensions

    The Cartesian product, i.e., all possible combinations of `dimX` x `dimY`

    Parameters
    ----------
    stim_levels : dict[str, list]
        unique stimulus levels per stimulus dimension,
        e.g., {"dimX": [...], "dimY": [...]}

    Returns
    -------
    pandas.MultiIndex
        all possible combinations of levels for the stimulus dimensions
    """
    return (
        pd.MultiIndex.from_product(list(stim_levels.values()), names=stim_levels.keys())
        .swaplevel()
        .sort_values()
    )
