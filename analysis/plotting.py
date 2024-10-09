import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import seaborn.objects as so

sns.set_context("talk")
sns.set_style("ticks", {"xtick.direction": "in", "ytick.direction": "in"})

sns_theme = sns.plotting_context("talk")
sns_theme.update(sns.axes_style("white"))
sns_theme.update({"xtick.direction": "in", "ytick.direction": "in"})


def plot_scales(scales, CI=None, dim_names=("a", "b")):
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

    p = p.label(
        y=r"Perceptual scale $\hat\psi$",
        x="Luminance (norm.)",
        color=str.capitalize,
    ).layout(size=(5, 5))

    return p


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
