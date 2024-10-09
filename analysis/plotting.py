import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import seaborn.objects as so

# data visualization parameters
sns.set_context("talk")
sns.set_style("ticks", {"xtick.direction": "in", "ytick.direction": "in"})

sns_theme = sns.plotting_context("talk")
sns_theme.update(sns.axes_style("white"))
sns_theme.update({"xtick.direction": "in", "ytick.direction": "in"})

palette = {"on black": "#252525", "on white": "#969696"}

red = "#e41a1c"
blue = "#377eb8"
green = "#4daf4a"


def plot_scales(scales, CI=None, encoding_funcs=None, dim_names=("a", "b")):
    if CI is None:
        if "CI_high" in scales and "CI_low" in scales:
            CI = True
        else:
            CI = False

    p = so.Plot(
        data=scales.reset_index(),
        x=dim_names[1],
        y="scale",
        color="context",
    ).add(so.Dot())

    if CI:
        p = p.add(so.Range(), ymin="CI_low", ymax="CI_high")

    if encoding_funcs:
        df = evaluate_encoding_funcs(encoding_funcs, dim_names=dim_names).rename(
            {"psi": "scale"}, axis="columns"
        )
        p = p.add(so.Lines(), data=df)

    p = p.label(
        y=r"Perceptual scale $\hat\psi$",
        x="Luminance (norm.)",
        color=str.capitalize,
    ).layout(size=(5, 5))

    return p


def evaluate_encoding_funcs(encoding_funcs, xlim=(0.0, 1.0), nsamples=1000, dim_names=("a", "b")):
    xs = pd.Series(np.linspace(*xlim, nsamples), name=dim_names[1])

    psis = []
    for level, fun in encoding_funcs.items():
        psi = pd.Series(fun(xs), name=level)
        psis.append(psi)

    df = pd.concat([xs, *psis], axis="columns")
    df = df.melt(id_vars=dim_names[1], var_name=dim_names[0], value_name="psi")
    return df


def plot_encoding_funcs(encoding_funcs, xlim=(0.0, 1.0), nsamples=1000, dim_names=("a", "b")):
    df = evaluate_encoding_funcs(encoding_funcs, xlim=xlim, nsamples=nsamples, dim_names=dim_names)
    p = so.Plot(
        data=df,
        x=dim_names[1],
        y="psi",
        color=dim_names[0],
    ).add(so.Lines())

    return p


def plotError(sim_repeats, nrepeat, orepeat, static, error=[], error_confidence=[]):
    # Create names for error plot and .csv file
    file_name = os.path.join("error", f"error_{sim_repeats}_{nrepeat}_{orepeat}_{static}.csv")
    error_name = os.path.join("error", f"error_{sim_repeats}_{nrepeat}_{orepeat}_{static}.pdf")

    # Load error based on arguments
    if os.path.exists(file_name) and error == []:
        # print("Loading error successful")
        error = np.loadtxt(file_name, delimiter=",")
    elif not os.path.exists(file_name) and error == []:
        print("Error is not defined.")
        exit(1)

    plt.figure(figsize=(8, 4.8))

    # Noise range
    plt.plot(np.arange(0, 0.11, 0.01), error, color="gray")

    # Set the x-axis and y-axis labels
    plt.xlabel("Noise level at decision Stage")
    plt.ylabel("RMSE")

    # Set the plot title
    # plt.title('RMSE and Noise Level')

    # Add dotted lines for range of noise
    plt.axvline(
        x=0.0321, color="steelblue", linestyle="dotted", label="Lowest measured noise level"
    )
    plt.axvline(
        x=0.0672, color="indianred", linestyle="dotted", label="Highest measured noise level"
    )

    # Add a legend with position in the upper right corner
    plt.legend(loc="upper right", fontsize="small")

    plt.fill_between(
        np.arange(0, 0.11, 0.01),
        error_confidence[:, 0],
        error_confidence[:, 1],
        alpha=0.3,
        label="Confidence Interval",
    )

    if sim_repeats >= 1000:
        plt.savefig(error_name)

        np.savetxt(file_name, error, delimiter=",")

    # Show the plot
    plt.show()

    plt.close()


def conjoint_proportions(freqs, N=15):
    """Plot heatmap of conjoint choice proportions
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
    mlcm_analysis.conjoint_choice_frequencies
    """
    names = freqs.index.names + freqs.columns.names
    dim_names = set()
    pair_names = set()
    for name in names:
        parts = name.split("_")
        dim_names.add("_".join(name.split("_")[:-1]))
        pair_names.add(parts[-1])
    dim_names = sorted(list(dim_names))
    pair_names = sorted(list(pair_names))

    outer_levels = sorted(list({column[0] for column in freqs.columns}))
    inner_levels = sorted(list(freqs[freqs.columns[0][0]].columns))

    ax = sns.heatmap(
        freqs / N,
        center=0.5,
        cmap="coolwarm",
        annot=True,
        mask=np.tril(np.ones_like(freqs)),
        yticklabels=[f"{i:.2f}" for c, i in freqs.index],
        xticklabels=[f"{i:.2f}" for c, i in freqs.index],
    )
    ax.set_box_aspect(1)

    # X-axis
    ax.xaxis.tick_top()
    plt.xticks(rotation=45)
    ax.set_xlabel(f"stimulus {pair_names[1]}")
    ax.xaxis.set_label_position("top")

    # Mark the outer levels
    sec2 = ax.secondary_xaxis(location=1.05)
    sec2.set_xticks([0, len(inner_levels), len(inner_levels) * 2], labels=[])
    sec2.tick_params("x", length=40, width=1.5)
    sec = ax.secondary_xaxis(location=1.05)
    sec.set_xticks([len(inner_levels) * 0.5, len(inner_levels) * 1.5], labels=outer_levels)
    sec.tick_params("x", length=0)

    # Y-axis
    ax.set_ylabel(f"stimulus {pair_names[0]}")
    ax.set_title(f"Frequency of choosing stimulus {pair_names[1]}")
    secyl = ax.secondary_yaxis(location=-0.05)
    secyl.set_yticks([0, len(inner_levels), len(inner_levels) * 2], labels=[])
    secyl.tick_params("y", length=40, width=1.5)
    secy = ax.secondary_yaxis(location=-0.05)
    secy.set_yticks([len(inner_levels) * 0.5, len(inner_levels) * 1.5], labels=outer_levels)
    secy.tick_params("y", length=0)

    return ax
