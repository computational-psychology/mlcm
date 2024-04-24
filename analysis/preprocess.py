from pathlib import Path

import numpy as np
import pandas as pd

from surround_brightness import data_management


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
        results.replace({"response": {"Left": "1", "Right": "0"}})
        .astype({"response": "int"})
        .groupby(
            ["context_left", "intensity_target_left", "context_right", "intensity_target_right"]
        )
        .aggregate({"response": "sum"})
        .unstack(level=["context_right", "intensity_target_right"], sort=True, fill_value=0.0)
        .droplevel(axis="columns", level=0)  # remove "response" index
        .sort_index(axis="columns", level=[-2, -1])
    )
    freqs_right = (
        results.replace({"response": {"Left": "0", "Right": "1"}})
        .astype({"response": "int"})
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


def nominal_luminance(intensity, lutfile=Path(__file__).parents[1] / "experiment" / "lut_viewpixx.csv"):
    """Convert given intensity(s) to nominal luminances, using given Lookup Table

    Parameters
    ----------
    intensity : float or Sequence[float]
        intensity(s) to convert to nominal luminances
    lutfile : Path or str, optional
        path to csv file containing LookUp Tabl,
        by default Path(__file__).parents[1]/"experiment"/"lut_viewpixx.csv"

    Returns
    -------
    float, or List[float]
        nominal luminance(s) for each intensity
    """
    lut = pd.read_csv(lutfile, delim_whitespace=True)

    luminances = []
    try:
        for i in intensity:
            # lookup i in LUT
            l = lut.iloc[(lut["IntensityIn"]-i).abs().argsort()[:2]]["Luminance"].mean()
            luminances.append(l)
    except TypeError:
        luminances = lut.iloc[(lut["IntensityIn"]-intensity).abs().argsort()[:2]]["Luminance"].mean()

    return luminances


def add_nominal_luminances(df, lutfile=Path(__file__).parents[1] / "experiment" / "lut_viewpixx.csv"):
    """Add nominal luminance of given intensities to dataframe

    Parameters
    ----------
    df : pandas.DataFrame
        dataframe to convert intensities to luminances for
    lutfile : Path or str
        path to LUT-csv to use for luminance lookup

    Returns
    -------
    pandas.DataFrame
        df, with added column "luminance_nominal_cdm2"
    """
    lums = pd.Series(nominal_luminance(df["intensity"].unique(), lutfile=lutfile), name="luminance_nominal_cdm2")

    lut = pd.concat([pd.Series(df["intensity"].unique(), name="intensity"), lums], axis="columns")

    df = df.merge(lut)

    return df


if __name__ == "__main__":
    for participant in data_management.participants:
        # Merge all results (sessions, blocks, stimuli) per participant
        # This will work as long as the results CSV have the same columns,
        # i.e., if we use the same variables for all blocks/stimuli.
        # In the current experimental setup, that should be the case.
        merged = merge_results(data_management.participant_results()[participant])
        merged = merged.sort_values(by="start_time")

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
