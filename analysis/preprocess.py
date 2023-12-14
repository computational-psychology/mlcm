from pathlib import Path

import pandas as pd

# Project directory
project_path = Path(__file__).parents[1].absolute()

# Overall data directory
datapath = project_path / "data"
if not datapath.exists():
    raise SystemExit("No datadir -- exiting.")

# Results directories
resultspath = datapath / "results"
dirs = resultspath.walk()
(rootpath, participants, root_files) = next(dirs)
assert Path(rootpath) == resultspath

# Tree results per participant
participant_results = {}
for path, subdirs, files in dirs:
    participant = path.stem
    participant_results[participant] = [path / file for file in files]


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
    """
    merged = []
    for file in files:
        merged.append(pd.read_csv(file, sep=","))

    return pd.concat(merged)  # .reset_index(drop=True, inplace=True)


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
    intensities_to_idc = {intensity: idx for idx, intensity in enumerate(intensities)}
    L1 = df["intensity_target_left"].replace(intensities_to_idc).astype(int).rename("I1")
    L2 = df["intensity_target_right"].replace(intensities_to_idc).astype(int).rename("I2")

    # Contexts
    # The target will look lighter in the white context than in the black context,
    # so code the 1st index as the one in white.
    # This sets the MLCM anchor at `0.0` for the lowest intensity in the white carrier
    contexts_to_idc = {"black": 2, "white": 1}
    C1 = df["context_left"].replace(contexts_to_idc).astype(int).rename("C1")
    C2 = df["context_right"].replace(contexts_to_idc).astype(int).rename("C2")

    # Results
    responses_to_idc = {"Left": 1, "Right": 0}
    Resp = df["response"].replace(responses_to_idc).astype(float).rename("Resp")

    return pd.concat([Resp, L1, L2, C1, C2], axis=1)


if __name__ == "__main__":
    for participant in participants:
        # Merge all results (sessions, blocks, stimuli) per participant
        # This will work as long as the results CSV have the same columns,
        # i.e., if we use the same variables for all blocks/stimuli.
        # In the current experimental setup, that should be the case.
        merged = merge_results(participant_results[participant])
        merged.to_csv(resultspath / participant / f"{participant}.csv", sep=",", index=False)
        # print(merged)

        # This merged dataframe can be queried (subset) for specific stimulus,
        # or specific date, block, etc.
        # stim_name = "checkerboard"
        # subset = merged.query(f"stim == '{stim_name}'")
        # print(subset)

        # Group the merged dataframe by stimulus
        per_stim = merged.groupby("stim")
        # print(per_stim)

        # Then, reformat the dataframe to the format required by `{MLCM}` R-package
        # reindexed = reindex_results(subset)
        # print(reindexed)
        reindexed = per_stim.apply(reindex_results)

        # Save reindexed stimulus-specific results to file
        # reindexed.to_csv(
        #     resultspath / participant / f"{participant}_{stim_name}.csv", sep=",", index=False
        # )
        for stim_name, df in reindexed.groupby("stim"):
            stim_name = stim_name.replace("_", "-")
            df.to_csv(
                resultspath / participant / f"{participant}_{stim_name}.csv", sep=",", index=False
            )
