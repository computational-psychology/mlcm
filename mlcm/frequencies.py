import numpy as np
import pandas as pd

from . import utils


def conjoint(trials, col, dim_names=("dim1", "dim2"), pair_names=("A", "B")):
    """Conjoint proportion/frequencies/total per unique stimuli pairing, for given column

    Creates a pivot table, where for the specified `col`umn, the aggregated total
    is shown for every possible stimuli pairing (e.g. every dimensions x pair combinations).

    This is useful e.g., to show the number of repetitions set for each stimulus pairing,
    or choice frequencies (see conjoint_choice).

    For stimuli pairings not present in the data, will show NaN.

    Parameters
    ----------
    trials : pandas.DataFrame
        raw trials response data, with one column per dimension x pair combination
        e.g., "dim1_A", "dim2_A", "dim1_B", "dim2_B"
    col : str
        name of column (in trials) to calculate conjoint total for
    dim_names : tuple[str], optional
        names for the stimulus dimensions, by default ("dim1", "dim2")
    pair_names : tuple[str], optional
        names for the stimulus pair members, by default ("A", "B")

    Returns
    -------
    pandas.DataFrame
        pivot table of conjoint frequencies,
        where each row and each column is unique dimension-level combination (unique stimulus),
        and thus each cell represents a unique stimuli pairing
        (where order matters, i.e., ('A', 'B') != ('B', 'A') )
    """

    # Calculate frequencies (pivot table, summing over specified column)
    freqs = trials.pivot_table(
        index=[f"{dim_names[1]}_{pair_names[0]}", f"{dim_names[0]}_{pair_names[0]}"],
        columns=[f"{dim_names[1]}_{pair_names[1]}", f"{dim_names[0]}_{pair_names[1]}"],
        values=col,
        aggfunc="sum",
    )

    # Housekeeping: format dataframe
    # Construct all possible combinations, to fill out pivot table
    stim_levels = utils.extract_stim_levels(trials, dim_names=dim_names, pair_names=pair_names)
    multiindex_full = utils.dimension_combinations(stim_levels)
    # Fill out and sort indices
    freqs = (
        freqs.sort_index(axis="columns", level=[0, 1], ascending=True)
        .reindex(multiindex_full.copy(), fill_value=np.nan)
        .reindex(multiindex_full.copy(), fill_value=np.nan, axis="columns")
    )
    # Label indices
    freqs.index.name, freqs.columns.name = pair_names

    return freqs


def unmirror_frequencies(): ...


def conjoint_choice_frequencies(trial_responses, **options):
    # Check / set options

    # Loop over each possible choice

    # Recode responses to that choice := 1

    # Pivot conjoint frequencies

    # Sum over choices

    # "Unmirror"

    # Housekeeping: return dataframe
    ...
