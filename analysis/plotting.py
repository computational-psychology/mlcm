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

palette = {"in black": "#252525", "in white": "#969696"}


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


if __name__ == "__main__":
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
