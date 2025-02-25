import pandas as pd


def extract_stim_levels(trials, dim_names=("dimX", "dimY"), pair_names=("left", "right")):
    """Extract unique stimulus levels for each dimension, from trial data

    Parameters
    ----------
    trials : pandas.DataFrame
        raw trials response data, with one column per dimension x pair combination
        e.g., "dimX_left", "dimY_left", "dimX_right", "dimY_right"
    dim_names : tuple[str], optional
        names for the stimulus dimensions, by default ("dimX", "dimY")
    pair_names : tuple[str], optional
        names for the stimulus pair members, by default ("left", "right")

    Returns
    -------
    dict[str, list]
        unique stimulus levels per stimulus dimension,
        e.g., {"dimX": [...], "dimY": [...]}
    """
    unique_levels = {}
    for dim in dim_names:
        levels = pd.concat([trials[f"{dim}_{pair}"] for pair in pair_names]).unique()
        levels.sort()
        unique_levels[dim] = levels

    return unique_levels


def dimension_combinations(stim_levels):
    """Returns all possible unique stimuli combinations from a given set of stimulus levels (along several stimulus dimensions)

        The function allows multiple stimulus dimensions.

    Parameters
    ----------
    stim_levels : dict[str, list]
        unique stimulus levels per stimulus dimension,
        e.g., {"dimX": [1, 2, 3], "dimY": [4, 5]}

    Returns
    -------
    pandas.MultiIndex
        all possible combinations of levels for the given stimulus dimensions
    """
    return (
        pd.MultiIndex.from_product(list(stim_levels.values()), names=stim_levels.keys())
        .reorder_levels(stim_levels.keys())
        .sort_values()
    )


def first_diff_char(a, b):
    """Return the first characters that differs between two strings

    Parameters
    ----------
    a : str
        first string
    b : str
        second string

    Returns
    -------
    dict[str, str]
        mapping of the two strings to the first differing character

    Raises
    ------
    ValueError
        if the two strings are identical

    Examples
    --------
    >>> first_diff_char("left", "right")
    {"left": "l", "right": "r"}
    >>> first_diff_char("l", "r")
    {"l": "l", "r": "r"}
    >>> first_diff_char("lef", "lex")
    {"lef": "f", "lex": "x"}

    """
    if a == b:
        raise ValueError("Strings are identical")

    for i, (a_char, b_char) in enumerate(zip(a, b)):
        if a_char != b_char:
            break

    return {a: a_char, b: b_char}
