import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from preprocess import choice_frequencies

from surround_brightness import data_management

sns.set_style(
    "white",
    {
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 4,
        "ytick.major.size": 4,
    },
)
sns.set_context("talk")

palette = {"black": "#252525", "white": "#969696"}


def heatmap(freqs, N=15):
    """Plot heatmap of choice frequencies

    Parameters
    ----------
    freqs : pandas.DataFrame
        upper triangle of choice frequencies
    N : int, optional
        number of repeats, by default 15

    Returns
    -------
    matplotlib.Axes
        Axes-object containing heatmap

    See also
    --------
    preprocess.choice_frequencies
    """
    ax = sns.heatmap(
        freqs,
        center=N / 2,
        cmap="coolwarm",
        annot=True,
        mask=np.tril(np.ones_like(freqs)),
        yticklabels=[f"{c}, {i}" if i == 0.01 else f"{i}" for c, i in freqs.index],
        xticklabels=[f"{i}, {c}" if i == 0.01 else f"{i}" for c, i in freqs.index],
    )

    ax.xaxis.tick_top()
    plt.xticks(rotation=45)
    ax.set_xlabel("Right stimulus")
    ax.xaxis.set_label_position("top")
    ax.set_ylabel("Left stimulus")

    return ax


def scales_participant(scales, palette=palette, CI=None):
    """Plot percpetual scales (for single participant)

    Parameters
    ----------
    scales : pandas.DataFrame
        estimated scales, with columns "intensity", "context", "scale",
        and optionally "scale_CI_low"/"_high".
    palette : dict, optional
        color palette to use, mapping "context" to colors, by default plotting.palette
    CI : bool, optional
        whether to plot CIs.
        If None (default), will plot CIs _if_ columns are present in dataframe,
        but won't throw an exception if they aren't.

    Returns
    -------
    matplotlib.Axes
        Axes-object containing scales plot
    """
    if CI is None and ("scale_CI_low" in scales and "scale_CI_high" in scales):
        CI = True

    ax = sns.scatterplot(data=scales, x="intensity", y="scale", hue="context", palette=palette)
    if CI:
        for context in scales["context"].unique():
            curr = scales[scales["context"] == context]
            yerr = (curr["scale"] - curr["scale_CI_low"], curr["scale_CI_high"] - curr["scale"])
            ax.errorbar(
                curr["intensity"],
                curr["scale"],
                yerr=yerr,
                fmt="none",
                ecolor=palette[context],
                capsize=0,
            )

    ax.set_ylabel("Perceptual scale")
    ax.set_xlabel("Luminance [$cdm^{-2}$]")

    return ax


def scales_all(scales, palette=palette, CI=None):
    """Plot all given percpetual scales, facetted by stimulus (row), participant (col))

    Parameters
    ----------
    scales : pandas.DataFrame
        estimated scales, with columns "intensity", "context", "scale", "participant", "stim",
        and optionally "scale_CI_low"/"_high".
    palette : dict, optional
        color palette to use, mapping "context" to colors, by default plotting.palette
    CI : bool, optional
        whether to plot CIs.
        If None (default), will plot CIs _if_ columns are present in dataframe,
        but won't throw an exception if they aren't.

    Returns
    -------
    matplotlib.Axes
        Axes-object containing scales plot
    """
    if CI is None and ("scale_CI_low" in scales and "scale_CI_high" in scales):
        CI = True

    G = sns.FacetGrid(
        scales,
        col="participant",
        row="stim",
        hue="context",
        xlim=(-.1, 1.2),
        ylim=(-.1, 1.2),
        palette=palette,
        margin_titles=True,
        subplot_kws={'aspect': 'equal'}
    )
    G.set_titles(col_template='{col_name}', row_template='{row_name}')
    G.map(sns.scatterplot, "intensity", "scale")
    G.add_legend()

    if CI:
        for (stim, participant), axes in G.axes_dict.items():
            subset = scales.query(f'participant == "{participant}" & stim == "{stim}"')

            for context in subset["context"].unique():
                curr = subset[subset["context"] == context]
                yerr = (curr["scale"] - curr["scale_CI_low"], curr["scale_CI_high"] - curr["scale"])
                axes.errorbar(
                    curr["intensity"],
                    curr["scale"],
                    yerr=yerr,
                    fmt="none",
                    ecolor=palette[context],
                    capsize=0,
                )

    return G


if __name__ == "__main__":
    # All conjoint proportion plots (choice-frequency heatmaps)
    for participant in data_management.participants:
        results = pd.read_csv(
            data_management.results_dir / participant / "analyzed" / f"{participant}.csv"
        )

        for stim, res in results.groupby("stim"):
            plt.figure(figsize=(11.7, 8.3))  # A4 in portrait
            freqs = choice_frequencies(res)
            heatmap(freqs, N=5)
            plt.title(f"{participant} - {stim}")
            plt.savefig(
                data_management.fig_path
                / f"{participant}_{stim.replace('_', '-')}.choice_freqs.pdf"
            )
            plt.close()

    # All scales
    scales = pd.read_csv(data_management.results_dir / "ALL.scales.csv", sep=",")
    plt.figure()
    G = scales_all(scales)
    plt.savefig(data_management.fig_path / "ALL.scales.pdf")
    plt.close()

    # Scales per participant x stimulus
    for (participant, stim), df in scales.groupby(["participant", "stim"]):
        # Plot scales
        plt.figure(figsize=(8, 8))
        scales_participant(df)
        plt.savefig(
            data_management.fig_path / f"{participant}_{stim.replace('_', '-')}.scales.pdf"
        )
        plt.close()
