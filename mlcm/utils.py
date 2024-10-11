import pandas as pd


def extract_stim_levels(trials, dim_names=("dim1", "dim2"), pair_names=("A", "B")):
    """Extract unique stimulus levels for each dimension, from trial data

    Parameters
    ----------
    trials : pandas.DataFrame
        raw trials response data, with one column per dimension x pair combination
        e.g., "dim1_A", "dim2_A", "dim1_B", "dim2_B"
    dim_names : tuple[str], optional
        names for the stimulus dimensions, by default ("dim1", "dim2")
    pair_names : tuple[str], optional
        names for the stimulus pair members, by default ("A", "B")

    Returns
    -------
    dict[str, list]
        unique stimulus levels per stimulus dimension,
        e.g., {"dim1": [...], "dim2": [...]}
    """
    unique_levels = {}
    for dim in dim_names:
        unique_levels[dim] = pd.concat([trials[f"{dim}_{pair}"] for pair in pair_names]).unique()

    return unique_levels
