import numpy as np
import pandas as pd

from mlcm.utils import extract_stim_levels, first_diff_char


def wrangle_responses(
    trial_responses,
    dim_names=("dimX", "dimY"),
    pair_names=("left", "right"),
    response_col="response",
    stim_levels=None,
):
    """Wrangle "raw" trial results dataframe to format required by {{MLCM}} R package

    The `{{MLCM}}` R package requires the data in a very specific format:
    - every row is one trial
    - first column 'Resp'onses, coded as index `0` or `1`, indicating stimulus `1` or `2` resp.
    - pairs of columns `[dimname]_1` and `[dimname]_2` for each stimulus dimension,
    - which contain the index along that stimulus dimension for the two paired stimuli

    | Resp | dimX_1 | dimX_2 | dimY_1 | dimY_2 |
    |------|--------|--------|--------|--------|
    |  0   |   2    |    1   |    1   |    1   |

    Parameters
    ----------
    trial_responses : pandas.DataFrame
        raw trial response data, e.g., from experiment code, for N trials.
        Should contain `response_col` containing responses that match one of the `pair_names`.
        Should also contain pairs of columns in the form of `[dimX]_[pair]`,
        e.g., "dimX_left", "dimY_right".
        Column-order does not matter.
    dim_names : tuple[str], optional
        names for the stimulus dimensions, by default ("dimX", "dimY")
    pair_names : tuple[str], optional
        names for the stimulus pair members, by default ("left", "right")
    response_col : str, optional
        name of column containing raw responses, by default 'response'

    Returns
    -------
    pandas.DataFrame
        (N x 5) DataFrame with experimental data containing N trials,
        with column 'Resp'onses, coded as index `0` or `1`, indicating stimulus `1` or `2` resp.
        and pairs of columns `[dimname]_1` and `[dimname]_2` for each stimulus dimension,
        indicating the index along that stimulus dimension for the two paired stimuli.
    """

    ## Rename & reorder columns/variables

    # Setup column-renaming mapping
    column_mapper = {response_col: "Resp"}  # insert response column first
    p_names = first_diff_char(*pair_names)
    for dim in dim_names:
        column_mapper.update({f"{dim}_{name}": f"{dim}_{p_names[name]}" for name in pair_names})

    wrangled = trial_responses.rename(columns=column_mapper)[[*column_mapper.values()]]

    ## Map stimulus levels, responses, to indices
    # Determine stimulus levels per dimension
    if not stim_levels:
        unique_levels = extract_stim_levels(
            trial_responses, dim_names=dim_names, pair_names=pair_names
        )
    else:
        unique_levels = stim_levels

    # Setup index-mappings, per stimulus dimension
    indexing = {}
    for dim in dim_names:
        indexing[dim] = {level: idx + 1 for idx, level in enumerate(unique_levels[dim])}

    # Setup index-mappings, per column
    indexing = {f"{dim}_{name}": indexing[dim] for dim in dim_names for name in p_names.values()}

    # Setup index-mapping for responses (0 or 1)
    indexing["Resp"] = {name: idx for idx, name in enumerate(pair_names)}

    # Recode values to indices
    for dim in dim_names:
        wrangled = wrangled.replace(indexing)
    wrangled = wrangled.astype("int")

    return wrangled


def unwrangle_responses(
    wrangled_responses: pd.DataFrame,
    stim_levels,
    pair_names=("l", "r"),
    response_col="response",
):
    """Unwrangle responses from the format of {{MLCM}} to a more human-readable format

    Parameters
    ----------
    wrangled_responses : pandas.DataFrame
        (N x 5) DataFrame with experimental data containing N trials,
    stim_levels : dict[str, list]
        dictionary mapping stimulus dimension names to lists of unique levels.
    pair_names : tuple[str], optional
        names for the stimulus pair members, by default ("l", "r")
    response_col : str, optional
        name for column of responses, by default "response"

    Returns
    -------
    pandas.DataFrame
        raw-format trial response data, e.g., from experiment code, for N trials.
        With `response_col` containing responses that match one of the `pair_names`.
        Also contain pairs of columns in the form of `[dimX]_[pair]`,
        e.g., "dimX_left", "dimY_right".
    """

    ## Map index values to stimulus levels
    # dict mapping from [1,> indices to stimulus levels, per stim dimension
    stim_idc = {
        dim: {idx: level for idx, level in enumerate(levels, start=1)}
        for dim, levels in stim_levels.items()
    }
    # dict determining remapping, per column
    mapper = {
        col: stim_idc[dim]
        for dim in stim_idc
        for col in wrangled_responses.columns[wrangled_responses.columns.str.startswith(dim)]
    }
    # Apply mapping
    trial_responses = wrangled_responses.replace(mapper)

    ## Map responses to pair names
    resp_mapper = {idx: name for idx, name in enumerate(pair_names)}
    trial_responses = trial_responses.replace({"Resp": resp_mapper})

    ## Rename column(s)
    column_mapper = {"Resp": response_col}  # insert response column first
    p_names = first_diff_char(*pair_names)
    for dim in stim_idc:
        column_mapper.update({f"{dim}_{p_names[name]}": f"{dim}_{name}" for name in pair_names})

    trial_responses = trial_responses.rename(columns=column_mapper)[[*column_mapper.values()]]

    return trial_responses.infer_objects()


def unwrangle_scales(scales_idc, stim_levels, modeltype):
    """Unwrangle scales from the {{MLCM}} R package to a more human-readable format

    Parameters
    ----------
    scales_idc : numpy.ndarray
        (2 x N) array of scales, where N is the number of unique levels in the stimulus dimensions.
    stim_levels : dict[str, list]
        dictionary mapping stimulus dimension names to lists of unique levels.
    modeltype : str
        model type, either 'add' or 'full'

    Returns
    -------
    pandas.DataFrame
        DataFrame with scales, where rows and columns are named after the stimulus levels.
    """
    # For additive model, need to add constant shift to first scale, to get second scale
    if modeltype == "add":
        scales_idc[1, :] = scales_idc[0, :] + scales_idc[1, 0]

    # Cast to dataframe
    scales_natural = pd.DataFrame(scales_idc)

    # Use indices to retrieve levels and name columns, rows
    row_dim, col_dim = (key for key in stim_levels)
    scales_natural.index = stim_levels[row_dim]
    scales_natural.columns = stim_levels[col_dim]
    scales_natural.columns.name = col_dim

    scales_natural[row_dim] = scales_natural.index
    scales_natural = scales_natural.melt(id_vars=row_dim, value_name="scale")

    scales_natural = scales_natural.infer_objects()

    return scales_natural


def reshape_bootstrap_samples(bootstrap_samples, stim_levels, modeltype):
    """Reshape bootstrap samples from free-parameter layout to the pscale grid.

    The _bootstrap function returns bootstrap samples as a
    ``(n_free_params, nsim)`` array.  This function expands each sample into the
    ``(n_levels_dim1, n_levels_dim2)`` pscale matrix, yielding a
    ``(n_levels_dim1, n_levels_dim2, nsim)`` array.

    For the **full** model the free parameters are a flattened grid (minus
    the first zero at position ``[0, 0]``).

    For the **add**\\ itive model the free parameters are per-dimension scales
    concatenated: ``[dim1_free…, dim2_free…]``, placed in the first column
    and first row of the grid respectively.

    Parameters
    ----------
    bootstrap_samples : numpy.ndarray
        ``(n_free_params, nsim)`` array of bootstrap samples.
    stim_levels : dict[str, array-like]
        Stimulus levels per dimension.
    modeltype : ``'add'`` | ``'full'``
        Model type.

    Returns
    -------
    numpy.ndarray
        ``(n_levels_dim1, n_levels_dim2, nsim)`` array.
    """
    n_levels = [len(v) for v in stim_levels.values()]
    nsim = bootstrap_samples.shape[1]

    if modeltype == "add":
        n_free = [n - 1 for n in n_levels]
        grid = np.zeros((*n_levels, nsim))
        grid[1:, 0, :] = bootstrap_samples[: n_free[0], :]  # dim1 free → first column
        grid[0, 1:, :] = bootstrap_samples[n_free[0] :, :]  # dim2 free → first row
    else:
        # Insert the fixed-zero first parameter, then reshape
        samples = np.vstack([np.zeros((1, nsim)), bootstrap_samples])  # (n_free+1, nsim)
        shape = list(reversed(n_levels))  # (n_levels_dim2, n_levels_dim1)
        grid = samples.reshape(*shape, nsim).transpose(1, 0, 2)  # → (dim1, dim2, nsim)

    return grid


def CIs_from_bootstrap(bootstrap_samples, stim_levels, modeltype, alpha=0.05):
    """Compute confidence intervals from bootstrap samples.

    Parameters
    ----------
    bootstrap_samples : numpy.ndarray
        ``(n_free_params, nsim)`` array of bootstrap samples, as returned by
        :func:`_bootstrap`.
    stim_levels : dict[str, array-like]
        Stimulus levels per dimension.
    modeltype : ``'add'`` | ``'full'``
        Model type.
    alpha : float, optional
        Significance level, by default 0.05.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns for each stimulus dimension and the lower/upper
        CI bounds.
    """
    boundary = alpha / 2

    # Reshape to pscale grid: (n_levels_dim1, n_levels_dim2, nsim)
    grid = reshape_bootstrap_samples(bootstrap_samples, stim_levels, modeltype)

    # Quantiles over bootstrap axis → (n_levels_dim1, n_levels_dim2)
    ci_lowers = np.quantile(grid, boundary, axis=-1)
    ci_uppers = np.quantile(grid, 1 - boundary, axis=-1)

    ci_lowers = unwrangle_scales(
        scales_idc=ci_lowers,
        stim_levels=stim_levels,
        modeltype=modeltype,
    ).rename(columns={"scale": f"CI_{boundary:.3f}"})
    ci_uppers = unwrangle_scales(
        scales_idc=ci_uppers,
        stim_levels=stim_levels,
        modeltype=modeltype,
    ).rename(columns={"scale": f"CI_{(1 - boundary):.3f}"})

    # Concat
    ci = pd.merge(ci_lowers, ci_uppers, on=list(stim_levels.keys()))

    return ci
