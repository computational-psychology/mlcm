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


def collapse(freqs_row, freqs_col):
    """Collapse frequencies over symmetrical pairings

    In the conjoint frequencies,
    each row and each column is unique dimension-level combination (unique stimulus),
    and thus each cell represents a unique stimuli pairing
    (where order matters, i.e., ('A', 'B') != ('B', 'A') ).

    In most cases, we assume that stimulus ordering doesn't matter, e.g., for choice frequencies.
    We assume that response "B" to ("stim_1", "stim_2") == "A" to ("stim_2", "stim_1").
    Then, we can sum these frequencies across equivalent choices,
    i.e., over the diagonal in the conjoint frequencies.
    That way we're left with just the upper triangle in the conjoint frequencies.

    Parameters
    ----------
    freqs_row : pandas.DataFrame
        pivot table of conjoint frequencies of (choosing) stimulus defined by row
    freqs_col : pandas.DataFrame
        pivot table of conjoint frequencies of (choosing) stimulus defined by column

    Returns
    -------
    pandas.DataFrame
        only upper triangle of pivot table of conjoint frequencies,
        i.e., freqncies of (choosing) stimulus defined by column, regardless of ordering
    """
    # Combine over choices
    freqs = np.stack([freqs_row.T, freqs_col])  # transposing one, makes corresponding to other
    freqs = np.nansum(freqs, axis=0)  # sum over choices, treating NaNs as 0s

    # Since frequencies are now symmetrical, collapse over diagnoal
    # freqs_upper = np.tril(freqs, k=-1).T + np.triu(freqs)
    freqs_upper = np.triu(freqs)

    # Set lower triangle to NaN
    freqs_upper[np.tril_indices_from(freqs_upper, k=-1)] = np.nan

    # Mask all conjoints that were not actually in freqs, as NaNs
    mask = np.isnan(freqs_row.T) & np.isnan(freqs_col)
    mask = np.tril(mask).T & np.triu(mask)
    freqs_upper[mask] = np.nan

    # Housekeeping
    freqs_upper = pd.DataFrame(freqs_upper, columns=freqs_col.index, index=freqs_col.index)

    return freqs_upper


def conjoint_choice(trials, dim_names=("dim1", "dim2"), pair_names=("A", "B")):
    """Conjoint choice frequencies for all unique stimulus pairings

    Each stimulus in the pairing e.g. ("A", "B")
    is defined by its levels for that stimulus, e.g., ("dim1_A", "dim2_A").
    For each of the possible unique pairings of unique stimuli,
    determine the frequency of one stimulus being chosen over the other.

    Assumes that stimulus ordering doesn't matter.
    Then, e.g., for choice frequencies, ("stim_A", "stim_B") == ("stim_A", "stim_B"),
    and we can sum the frequencies mirrored across the diagonal.
    That way we're left with just the upper triangle in the conjoint frequencies.

    Parameters
    ----------
    trials : pandas.DataFrame
        raw trials response data, with column "response" containing participant responses,
        and one column per dimension x pair combination
        e.g., "dim1_A", "dim2_A", "dim1_B", "dim2_B",
    dim_names : tuple[str], optional
        names for the stimulus dimensions, by default ("dim1", "dim2")
    pair_names : tuple[str], optional
        names for the stimulus pair members, by default ("A", "B")

    Returns
    -------
    pandas.DataFrame
        upper triangle of pivot table of conjoint frequencies,
        where each row and each column is unique dimension-level combination (unique stimulus),
        and thus each cell represents a unique stimuli pairing
        (where order doesn't matter, i.e., ('A', 'B') == ('B', 'A') )
        and the value each cell is the frequency of the column-defined stimulus being chosen.
    """
    # Check / set options

    # Loop over each possible choice
    # For each choice, calculate frequencies
    freqs = []
    for name in pair_names:
        freqs.append(
            response_choice(trials, choice=name, dim_names=dim_names, pair_names=pair_names)
        )

    # Collapse over symmetrical pairs
    # Don't care about ordering of stimuli (i.e., mirroring) so sum
    freqs_upper = collapse(*freqs)

    # Housekeeping: return dataframe
    freqs_upper.index.name, freqs_upper.columns.name = ("A", "B")

    return freqs_upper


def response_choice(trials, choice, dim_names=("dim1", "dim2"), pair_names=("A", "B")):
    """Choice frequency for specified response option in trial data

    Parameters
    ----------
    trials : pandas.DataFrame
        raw trials response data, with column "response" containing participant responses,
        and one column per dimension x pair combination
        e.g., "dim1_A", "dim2_A", "dim1_B", "dim2_B",
    choice : Any
        label in "response" column to determine choice frequency for
    dim_names : tuple[str], optional
        names for the stimulus dimensions, by default ("dim1", "dim2")
    pair_names : tuple[str], optional
        names for the stimulus pair members, by default ("A", "B")

    Returns
    -------
    freqs : pandas.DataFrame
        pivot table of conjoint choice frequencies,
        where each row and each column is unique dimension-level combination (unique stimulus),
        and thus each cell represents a unique stimuli pairing
        (where order matters, i.e., ('A', 'B') != ('B', 'A') )
        and the value each cell is the frequency of specified response being chosen
    """
    # Recode response such that choice := 1
    recoded = trials.copy()
    recoded["response"] = (recoded["response"] == choice).astype(int)

    # Calculate frequencies for complete set
    freqs = conjoint(trials=recoded, col="response", dim_names=dim_names, pair_names=pair_names)

    # Housekeeping: return dataframe
    freqs.index = freqs.index.reorder_levels(dim_names)
    freqs.columns = freqs.columns.reorder_levels(dim_names)
    freqs = freqs.sort_index(axis="index").sort_index(axis="columns")
    freqs.index.name, freqs.columns.name = pair_names

    return freqs
