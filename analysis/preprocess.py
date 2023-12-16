from pathlib import Path

import pandas as pd

# Experiment path:
project_path = Path(__file__).parents[1].absolute()

# Overall datapath
datapath = project_path / "data"
if not datapath.exists():
    raise SystemExit("No datadir -- exiting.")

# Results-path
resultspath = datapath / "results"
dirs = resultspath.walk()
(rootpath, participants, root_files) = next(dirs)
assert Path(rootpath) == resultspath

participant_results = {}
for path, subdirs, files in dirs:
    participant = path.stem
    participant_results[participant] = [path / file for file in files]


def merge_results(files):
    """_summary_

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
    """_summary_

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
    participant = "NJ-PILOT"

    merged = merge_results(participant_results[participant])
    # print(merged)
    per_stim = merged.groupby("stim")
    # print(per_stim)

    # stim_name = "checkerboard"
    # subset = merged.query(f"stim == '{stim_name}'")
    # print(subset)
    # reindexed = reindex_results(subset)
    # print(reindexed)
    # reindexed.to_csv(
    #     resultspath / participant / f"{participant}_{stim_name}.csv", sep=",", index=False
    # )

    reindexed = per_stim.apply(reindex_results)

    for stim_name, df in reindexed.groupby("stim"):
        stim_name = stim_name.replace("_", "-")
        df.to_csv(
            resultspath / participant / f"{participant}_{stim_name}.csv", sep=",", index=False
        )
