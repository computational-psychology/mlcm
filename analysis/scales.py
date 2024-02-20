import subprocess
from pathlib import Path

import pandas as pd

from surround_brightness import data_management
from surround_brightness.analysis import preprocess
from surround_brightness.analysis.plotting import scales_participant
from surround_brightness.experiment.design import intensities as exp_intensities

ANALYSIS_FILE = Path(__file__).parent / "analysis-mlcm.Rmd"

# The target is hypothesized to look
# lighter in the white context than in the black context.
# We tell MLCM to anchor at `0.0` for the lowest intensity in the black carrier,
# by setting black to be the first context
CONTEXTS_TO_IDC = {"black": 1, "white": 2}
IDC_TO_CONTEXTS = {val: key for key, val in CONTEXTS_TO_IDC.items()}


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


def reindex_scales(scales, intensities=exp_intensities):
    # Index contexts
    scales["context"] = scales["context"].replace(IDC_TO_CONTEXTS)

    # Index intensities
    ints = {idx + 1: intensity for idx, intensity in enumerate(intensities)}
    scales["intensity"] = scales["intensity"].replace(ints).astype(float)

    return scales


def estimate_scales(participant, stimulus):
    """Estimate perceptual scale for given participant and stimulus

    Renders the RMarkdown-file `analysis-mclm.Rmd`
    with the provided participant and stimulus names as parameter values.
    The rendered `.pdf` version will be output to the participant's "analyzed" data directory,
    as will the `.csv`-files that the scale estimation produces.

    Parameters
    ----------
    participant : string
        initials/ID of participant
    stimulus : string
        full stimulus name
    """
    output_filename = f"{participant}_{stimulus}.analysis.pdf"
    output_filepath = data_management.results_dir / participant / "analyzed" / output_filename

    call = f"""rmarkdown::render('{ANALYSIS_FILE}',
                params=list(
                    participant='{participant}',
                    stimulus='{stimulus}'
                ),
                output_file='{output_filepath}'
            )"""

    subprocess.call(["Rscript", "--vanilla", "-e", call])


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    scales_filepaths = []

    for participant in data_management.participants:
        # participant = "NJ-PILOT"

        # Get the total results-file for this participant
        results_filepath = (
            data_management.results_dir / participant / "analyzed" / f"{participant}.csv"
        )
        participant_merged = pd.read_csv(results_filepath, sep=",")

        # This merged dataframe can be queried (subset) for specific stimulus,
        # or specific date, block, etc.
        # stim_name = "checkerboard"
        # subset = merged.query(f"stim == '{stim_name}'")

        # Group the merged dataframe by stimulus
        per_stim = participant_merged.groupby("stim")

        # Then, reformat the dataframe to the format required by `{MLCM}` R-package
        # reindexed = reindex_results(subset)
        reindexed = per_stim.apply(reindex_results)

        # Estimate scales for each stimululs
        for stim_name, df in reindexed.groupby("stim"):
            # Save reindexed, stimulus-specific results to .csv file
            # This file is what gets ingested by the scale-estimation Rmd
            stim_name = stim_name.replace("_", "-")
            df.to_csv(
                data_management.results_dir
                / participant
                / "analyzed"
                / f"{participant}_{stim_name}.csv",
                sep=",",
                index=False,
            )

            # Actually estimate the scales
            estimate_scales(participant, stim_name)

            # Load scales
            try:
                modeltype = "full"
                filename = (
                    f"{participant}_{stim_name}_{modeltype}_trimmed_{modeltype}_norm.scales.csv"
                )
                scales_filepath = data_management.results_dir / participant / "analyzed" / filename
                scales = pd.read_csv(scales_filepath, sep=",")
            except FileNotFoundError:
                continue

            # Reindex back
            scales = reindex_scales(scales)

            # Add participant, stimulus, info
            scales.insert(loc=0, column="stim", value=stim_name)
            scales.insert(loc=0, column="participant", value=participant)

            # Save reindexed scales, overwriting
            scales.to_csv(scales_filepath, sep=",", index=False)

            # Plot scales
            plt.figure(figsize=(6, 6))
            scales_participant(scales)
            plt.savefig(
                data_management.fig_path
                / f"{participant}_{stim_name.replace('_', '-')}.scales.pdf"
            )

            # Aggregate filepaths to scales
            scales_filepaths.append(scales_filepath)

    # Merge all scales into single CSV
    scales_merged = preprocess.merge_results(scales_filepaths)
    scales_merged.to_csv(
        data_management.results_dir / f"ALL_{modeltype.upper()}.scales.csv", sep=",", index=False
    )
