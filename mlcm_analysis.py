import itertools

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
