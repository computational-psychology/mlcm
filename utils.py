import itertools

import numpy as np
import pandas as pd


def dimension_combinations(stim_levels):
    return (
        pd.MultiIndex.from_product(list(stim_levels.values()), names=stim_levels.keys())
        .swaplevel()
        .sort_values()
    )


def dimension_combinations_list(stim_levels):
    # Unique stimuli (dimension-combinations)
    dim_names = list(stim_levels.keys())
    return list(itertools.product(stim_levels[dim_names[0]], stim_levels[dim_names[1]]))


def conjoint_frequencies(trials, stim_levels, col, pair_names=(0, 1)):
    dim_names = list(stim_levels.keys())
    multiindex = dimension_combinations(stim_levels)

    freqs = (
        trials.pivot_table(
            index=[f"{dim_names[1]}_{pair_names[0]}", f"{dim_names[0]}_{pair_names[0]}"],
            columns=[f"{dim_names[1]}_{pair_names[1]}", f"{dim_names[0]}_{pair_names[1]}"],
            values=col,
            aggfunc="sum",
        )
        .sort_index(axis="columns", level=[0, 1], ascending=True)
        .reindex(multiindex, fill_value=np.nan)
        .reindex(multiindex, fill_value=np.nan, axis="columns")
    )
    freqs.index.name, freqs.columns.name = pair_names

    return freqs


def unmirror_frequencies(freqs):
    freqs_upper = np.tril(freqs.fillna(0)).T + np.triu(freqs.fillna(0))
    freqs_upper[np.tril_indices(freqs_upper.shape[0])] = np.nan
    freqs_upper = pd.DataFrame(freqs_upper, columns=freqs.columns, index=freqs.index)

    return freqs_upper
