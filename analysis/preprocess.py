import numpy as np
import pandas as pd

from surround_brightness import data_management

# The target is hypothesized to look
# lighter in the white context than in the black context.
# We tell MLCM to anchor at `0.0` for the lowest intensity in the black carrier,
# by setting black to be the first context
CONTEXTS_TO_IDC = {"black": 1, "white": 2}


def merge_results(files):
    """Merge several (results-)CSV-files into single dataframe

    All specified `files` must  have the same columns.

    Parameters
    ----------
    files : Iterable(Path | str)
        filepaths of CSV files to be merged into single DF

    Returns
    -------
    pandas.DataFrame
        all data from specified CSV files concatenated into single dataframe

    See also
    --------
    plotting.heatmap
    """
    merged = []
    for file in files:
        merged.append(pd.read_csv(file, sep=","))

    return pd.concat(merged)  # .reset_index(drop=True, inplace=True)


def choice_frequencies(results):
    """Summarise results in choice frequencies,

    For each unique stimulus pair, how often is one chosen over the other.

    Parameters
    ----------
    results : pandas.DataFrame
        raw data from experiment code, concatenated

    Returns
    -------
    pandas.DataFrame
        choice frequency for each stimulus pair, ignoring stimulus ordering (i.e., mirroring),
        thus only upper triangle
    """
    freqs_left = (
        results.replace({"response": {"Left": 1, "Right": 0}})
        .groupby(
            ["context_left", "intensity_target_left", "context_right", "intensity_target_right"]
        )
        .aggregate({"response": "sum"})
        .unstack(level=["context_right", "intensity_target_right"], sort=True, fill_value=0.0)
        .droplevel(axis="columns", level=0)  # remove "response" index
        .sort_index(axis="columns", level=[-2, -1])
    )
    freqs_right = (
        results.replace({"response": {"Left": 0, "Right": 1}})
        .groupby(
            ["context_left", "intensity_target_left", "context_right", "intensity_target_right"]
        )
        .aggregate({"response": "sum"})
        .unstack(level=["context_right", "intensity_target_right"], sort=True, fill_value=0.0)
        .droplevel(axis="columns", level=0)  # remove "response" index
        .sort_index(axis="columns", level=[-2, -1])
    )

    # Don't care about ordering of stimuli (i.e., mirroring)
    # so sum upper and lower triangles
    x = np.triu(freqs_left) + np.tril(freqs_right).T
    x[np.tril_indices(x.shape[0], -1)] = np.nan
    freqs_upper = pd.DataFrame(x, columns=freqs_left.columns, index=freqs_left.index)

    return freqs_upper


def reindex_results(df):
    """Transform results dataframe to format required by {MLCM}

    The `{MLCM}` package requires the data CSV in a very specific format:
    - every row is a trial
    - the first column is called 'Resp', which contains the binary response to the trial.
    - the four columns containing the stimuli indices presented in that trial.

    In this case we use `I1` and `C1`
    to code the intensity and context of the first stimulus, respectively.
    Similarly `I2` and `C2` code the intensity and context of the second stimulus.
    The entries are integers starting from `1`.

    For the intensity dimension there is no limit or restriction on the amount of values.
    However, the current implementation allows only 2 contexts,
    i.e., the columns `C1` and `C2` can only contain the integers `1` or `2`.

    Parameters
    ----------
    df : pandas.DataFrame
        raw data from experiment code

    Returns
    -------
    pandas.DataFrame
        reindexed data in the format that MLCM requires
    """

    # Intensities
    intensities = pd.concat([df["intensity_target_left"], df["intensity_target_right"]]).unique()
    intensities.sort()
    # print(f"Intensity values: {intensities}")
    intensities_to_idc = {intensity: idx + 1 for idx, intensity in enumerate(intensities)}
    L1 = df["intensity_target_left"].replace(intensities_to_idc).astype(int).rename("I1")
    L2 = df["intensity_target_right"].replace(intensities_to_idc).astype(int).rename("I2")

    # Contexts
    C1 = df["context_left"].replace(CONTEXTS_TO_IDC).astype(int).rename("C1")
    C2 = df["context_right"].replace(CONTEXTS_TO_IDC).astype(int).rename("C2")

    # Results
    responses_to_idc = {"Left": 1, "Right": 0}
    Resp = df["response"].replace(responses_to_idc).astype(float).rename("Resp")

    return pd.concat([Resp, L1, L2, C1, C2], axis=1)


if __name__ == "__main__":
    for participant in data_management.participants:
        # Merge all results (sessions, blocks, stimuli) per participant
        # This will work as long as the results CSV have the same columns,
        # i.e., if we use the same variables for all blocks/stimuli.
        # In the current experimental setup, that should be the case.
        merged = merge_results(data_management.participant_results[participant])
        filepath = data_management.results_dir / participant / "analyzed" / f"{participant}.csv"
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True)
        merged.to_csv(
            filepath,
            sep=",",
            index=False,
        )
        # print(merged)

        # This merged dataframe can be queried (subset) for specific stimulus,
        # or specific date, block, etc.
        # stim_name = "checkerboard"
        # subset = merged.query(f"stim == '{stim_name}'")
        # print(subset)

        # Group the merged dataframe by stimulus
        stim_keys = ["stim", "target_size", "n_surrounds"]
        group_keys = [k for k in stim_keys if k in merged.columns]
        per_stim = merged.groupby(group_keys, dropna=False)
        # print(per_stim)

        # Then, reformat the dataframe to the format required by `{MLCM}` R-package
        # reindexed = reindex_results(subset)
        # print(reindexed)
        reindexed = per_stim.apply(reindex_results)

        # Save reindexed stimulus-specific results to file
        # reindexed.to_csv(
        #     resultspath / participant / f"{participant}_{stim_name}.csv", sep=",", index=False
        # )
        for group_id, df in reindexed.groupby(group_keys, dropna=False):
            parts = {k: group_id[i] for i, k in enumerate(group_keys)}
            parts["stim"] = parts["stim"].replace("_", "-")
            if "target_size" in parts and not pd.isna(parts["target_size"]):
                parts["target_size"] = f"{parts["target_size"]:.2f}"
            if "n_surrounds" in parts and not pd.isna(parts["n_surrounds"]):
                parts["n_surrounds"] = f"{int(parts["n_surrounds"])}"

            stim_id = "-".join([f"{parts[k]}" for k in group_keys if not pd.isna(parts[k])])
            df.to_csv(
                data_management.results_dir
                / participant
                / "analyzed"
                / f"{participant}_{stim_id}.csv",
                sep=",",
                index=False,
            )
