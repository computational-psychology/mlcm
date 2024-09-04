import itertools

import numpy as np
import pandas as pd


def extract_stim_levels(trial_responses, dim_names=("a", "b"), pair_names=(0, 1)):
    unique_levels = {}
    for dim in dim_names:
        unique_levels[dim] = pd.concat(
            [trial_responses[f"{dim}_{pair}"] for pair in pair_names]
        ).unique()

    return unique_levels


def dimension_combinations(unique_levels):
    dim_names = list(unique_levels.keys())
    return list(itertools.product(unique_levels[dim_names[0]], unique_levels[dim_names[1]]))


def pairwise_product(unique_levels, pair_names=(0, 1)):
    dim_combis = dimension_combinations(unique_levels)
    dim_names = list(unique_levels.keys())

    # All pairwise stimulus products (including mirroreds)
    stim_pairs = []
    for c in list(itertools.product(dim_combis, dim_combis)):
        stim_pairs.append((c[0][0], c[0][1], c[1][0], c[1][1]))

    # Convert to DataFrame
    col_names = [[f"{dim_names[0]}_{name}", f"{dim_names[1]}_{name}"] for name in pair_names]
    col_names = [x for xs in col_names for x in xs]
    return pd.DataFrame(stim_pairs, columns=col_names)


def choice_frequencies(trial_responses, choice, dim_names=("a", "b"), pair_names=(0, 1)):

    # Construct table of all possible stimulus pairings
    unique_levels = extract_stim_levels(
        trial_responses, dim_names=dim_names, pair_names=pair_names
    )
    full_pairs = pairwise_product(unique_levels, pair_names=pair_names)

    # Pivot to long: columns to index-levels
    full_pairs = full_pairs.set_index(keys=list(full_pairs.columns))

    # Add 0.0 response to all entries
    full_pairs["response"] = 0.0

    # Other response option
    other_name = [n for n in pair_names if n is not choice][0]

    freqs = (
        trial_responses.copy()
        # Code "choice" => 1, other response 0
        .replace({"response": {choice: 1, other_name: 0}})
        .astype({"response": int})  # response as int for summing
        # Count per cell, i.e., conjoint stimulus levels
        .groupby(
            [f"{dim}_{pair}" for pair, dim in itertools.product(pair_names, dim_names)]
        )  # group trials by stimulus levels, i.e., conjoint
        .aggregate({"response": "sum"})  # sum responses per conjoint cell
        # Fill-out table, adding in combos not shown
        .join(
            full_pairs, how="outer", rsuffix="_freqs"
        )  # join full set of pairings, to get balanced table
        .drop(columns="response_freqs")
        # Format
        .unstack(
            level=[f"{dim}_{pair}" for dim, pair in itertools.product(dim_names, [pair_names[1]])],
            sort=True,
            fill_value=0.0,
        )
        .droplevel(axis="columns", level=0)  # remove "response" index
        .sort_index(axis="columns", level=[-2, -1])
    )

    return freqs


def conjoint_choice_frequencies(trial_responses, dim_names=("a", "b"), pair_names=(0, 1)):
    freqs = []
    for name in pair_names:
        freqs.append(choice_frequencies(trial_responses, choice=name, dim_names=dim_names))

    # Don't care about ordering of stimuli (i.e., mirroring)
    # so sum upper and lower triangles
    freqs_upper = np.triu(freqs[1].fillna(0)) + np.tril(freqs[0].fillna(0)).T
    freqs_upper[np.tril_indices(freqs_upper.shape[0])] = np.nan
    freqs_upper = pd.DataFrame(freqs_upper, columns=freqs[0].columns, index=freqs[0].index)

    return freqs_upper


def reindex_results(trial_responses, dim_names, pair_names):
    """Transform results dataframe to format required by {MLCM}

    The `{MLCM}` package requires the data CSV in a very specific format:
    - every row is a trial
    - the first column is called 'Resp', which contains the binary response to the trial.
    - the four columns containing the stimuli indices presented in that trial.

    In this case we use `L1` and `C1`
    to code the luminance and context of the first stimulus, respectively.
    Similarly `L2` and `C2` code the luminance and context of the second stimulus.
    The entries are integers starting from `1`.

    For the luminance dimension there is no limit or restriction on the amount of values.
    However, the current implementation allows only 2 contexts,
    i.e., the columns `C1` and `C2` can only contain the integers `1` or `2`.

    Parameters
    ----------
    trial_responses : pandas.DataFrame
        raw data from experiment code

    Returns
    -------
    pandas.DataFrame
        reindexed data in the format that MLCM requires
    """

    # Determine stimulus levels per dimension
    unique_levels = extract_stim_levels(
        trial_responses, dim_names=dim_names, pair_names=pair_names
    )

    # Setup index-mappings, per stimulus dimension
    indexing = {}
    for dim in dim_names:
        indexing[dim] = {level: idx + 1 for idx, level in enumerate(sorted(unique_levels[dim]))}

    # Setup index-mapping for responses (0 or 1)
    indexing["response"] = {name: idx for idx, name in enumerate(reversed(pair_names))}

    # Setup column-renaming mapping
    columns = {"response": "Resp"}
    for dim in dim_names:
        columns.update(
            {f"{dim}_{name}": f"{dim[0].upper()}{idx+1}" for idx, name in enumerate(pair_names)}
        )

    # Rename columns
    reindexed = trial_responses.rename(columns=columns)[[*columns.values()]]

    # Remap values
    for dim in dim_names:
        reindexed = reindexed.replace(
            {f"{dim[0].upper()}1": indexing[dim], f"{dim[0].upper()}2": indexing[dim]}
        )
    reindexed = reindexed.replace({"Resp": indexing["response"]})
    reindexed = reindexed.astype("int")

    return reindexed
