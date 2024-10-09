import numpy as np
import pandas as pd
from rpy2 import robjects

import utils

robjects.r.source("scale_estimation/analysis_mlcm.R")
analyze_mlcm = robjects.r["analyzemlcm"]


def extract_stim_levels(trial_responses, dim_names=("a", "b"), pair_names=(0, 1)):
    unique_levels = {}
    for dim in dim_names:
        unique_levels[dim] = pd.concat(
            [trial_responses[f"{dim}_{pair}"] for pair in pair_names]
        ).unique()

    return unique_levels


def extract_names(trials):
    dim_names = set()
    pair_names = set()
    for name in trials.columns:
        parts = name.split("_")
        dim_names.add("_".join(name.split("_")[:-1]))
        pair_names.add(parts[-1])
    dim_names = sorted(list(dim_names))
    pair_names = sorted(list(pair_names))

    return dim_names, pair_names


def choice_frequencies(trial_responses, choice, dim_names=("a", "b"), pair_names=(0, 1)):
    # Recode choices
    # Other response option
    other_name = [n for n in pair_names if n is not choice][0]
    s = (
        trial_responses.copy()
        # Code "choice" => 1, other response 0
        .replace({"response": {choice: 1, other_name: 0}})
        .astype({"response": int})  # response as int for summing
    )

    # Construct table of all possible stimulus pairings
    unique_levels = extract_stim_levels(
        trial_responses, dim_names=dim_names, pair_names=pair_names
    )

    # Calculate frequencies for complete set
    freqs = utils.conjoint_frequencies(
        s, stim_levels=unique_levels, col="response", pair_names=pair_names
    )
    freqs.index = freqs.index.reorder_levels(dim_names)
    freqs.columns = freqs.columns.reorder_levels(dim_names)
    freqs = freqs.sort_index(axis="index").sort_index(axis="columns")
    freqs.index.name, freqs.columns.name = pair_names

    return freqs


def conjoint_choice_frequencies(trial_responses, dim_names=("a", "b"), pair_names=(0, 1)):
    # For each choice, calculate frequencies
    freqs = []
    for name in pair_names:
        freqs.append(
            choice_frequencies(
                trial_responses, choice=name, dim_names=dim_names, pair_names=pair_names
            )
        )

    # Don't care about ordering of stimuli (i.e., mirroring)
    # so sum upper and lower triangles
    freqs_upper = utils.unmirror_frequencies(freqs[0].fillna(0).T + freqs[1])
    freqs_upper.index.name, freqs_upper.columns.name = ("A", "B")

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


def estimate_scales(
    trial_responses,
    dim_names,
    stim_levels,
    pair_names,
    modeltype="full",
    bootstrap_runs=0,
    results_file="sim_mlcm",
):
    # Save to .csv in the format the MLCM package needs
    reindexed_results = reindex_results(
        trial_responses=trial_responses, dim_names=dim_names, pair_names=pair_names
    )
    reindexed_results.to_csv(f"{results_file}.csv")

    # Estimate scales
    analyze_mlcm(
        results_file, modeltype=modeltype, do_bootstrap=(bootstrap_runs > 0), nsim=bootstrap_runs
    )

    # Extract scales and convert to DF
    robjects.r["load"](f"{results_file}_{modeltype}.glm.MLCM")
    scales = np.array(robjects.r["obs.scales"])
    scales = pd.DataFrame(scales)

    scales = reindex_scales(scales, dim_names=dim_names, stim_levels=stim_levels)

    return scales


def reindex_scales(scales, dim_names, stim_levels):
    # Rename
    DF = (
        # Column- and row-(index-) names
        scales.rename(
            columns={idx: val for idx, val in enumerate(sorted(stim_levels[dim_names[0]]))},
            index={idx: val for idx, val in enumerate(sorted(stim_levels[dim_names[1]]))},
        )
        # Headers
        .rename_axis(dim_names[1], axis="index")
        .rename_axis(dim_names[0], axis="columns")
    )

    return DF


def reorient_scales(scales, orient="wide"):
    if orient == "long":
        DF = scales.melt(value_name="scale", var_name=scales.columns.name, ignore_index=False)

    if orient == "row":
        DF = scales.stack().to_frame().T.reorder_levels(order=[-1, 0], axis="columns")

    return DF
