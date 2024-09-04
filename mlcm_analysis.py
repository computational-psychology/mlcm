import pandas as pd


def extract_stim_levels(trial_responses, dim_names=("a", "b"), pair_names=(0, 1)):
    unique_levels = {}
    for dim in dim_names:
        unique_levels[dim] = pd.concat(
            [trial_responses[f"{dim}_{pair}"] for pair in pair_names]
        ).unique()

    return unique_levels