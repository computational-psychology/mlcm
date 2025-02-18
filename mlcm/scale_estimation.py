# imports
import warnings

import numpy as np
import pandas as pd
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr

from mlcm.utils import extract_stim_levels, first_diff_char

importr("MLCM")


def _estimate(parsed_trial_responses, modeltype, method, epsilon, whichdim=None):
    """Fit point estimate for the scales, using the {{MLCM}} R package.

    Uses rpy2 to convert the input data frame to an R dataframe,
    and then runs the MLCM::mlcm(...) function on that data.

    Thus, requires the `rpy2` Python package, R, and the {{MLCM}} R package installed.

    Input data needs to be in the correct format required by the {{MLCM}} R package:

    | Resp | dimX_1 | dimX_2 | dimY_1 | dimY_2 |
    |------|--------|--------|--------|--------|
    |  0   |   2    |    1   |    3   |    4   |

    Parameters
    ----------
    parsed_trial_responses : pandas.Dataframe
        (N x 5) DataFrame with experimental data containing N trials,
        with column 'Resp' containing the observer responses, coded as index `0` or `1`,
        and pairs of columns `[dimname]_1` and `[dimname]_2` for each stimulus dimension,
        indicating the stimulus *index* along that stimulus dimension for the two stimuli.
    modeltype : ['add', 'ind', 'full']
        whether to fit an `add`itive, `ind`ependent, or `full` model.
    method : ['glm.fit', 'brglm.fit']
        whether to use the regular glm ('glm') or the bias-reduced glm ('brglm.fit') fitting routine.
    epsilon : float
        convergence tolerance, by default 1e-4.
    whichdim : int, optional
        which dimension to consider in the independent model. Only valid for this modeltype

    Returns
    -------
    rpy2.robject
        output from {{MLCM}} R package

    """
    # validate whichdim argument
    if modeltype == "ind" and whichdim is None:
        raise ValueError("Argument `whichdim` cannot be None for the independent model.")

    if modeltype != "ind" and whichdim is not None:
        warnings.warn(
            "Warning. Omitting argument `whichdim` as the model is not the independent one."
        )

    # gets R function pointers
    r_mlcm = robjects.r["mlcm"]
    r_as_mlcm_df = robjects.r["as.mlcm.df"]
    r_glm_control = robjects.r["glm.control"]

    # converts pandas DataFrame to R DataFrame
    with (robjects.default_converter + pandas2ri.converter).context():
        r_data = robjects.conversion.get_conversion().py2rpy(parsed_trial_responses)

    # as.mlcm.df()
    r_data = r_as_mlcm_df(r_data)

    # estimation itself by calling mlcm(....)
    if modeltype == "ind":
        scale_obj = r_mlcm(
            r_data,
            model=modeltype,
            whichdim=whichdim,
            control=r_glm_control(epsilon=epsilon, maxit=50000),
        )
    else:
        scale_obj = r_mlcm(
            r_data, model=modeltype, control=r_glm_control(epsilon=epsilon, maxit=50000)
        )

    return scale_obj


def compare_models():
    # Estimate models
    _estimate(modeltype="full")
    _estimate(modeltype="add")

    # Compare
    modeltype = ...

    return modeltype


def bootstrap_confidence(): ...


def remove_outliers(): ...


def goodness_of_fit(): ...


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
        Witho `response_col` containing responses that match one of the `pair_names`.
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

    return trial_responses


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


def scale_estimation(
    trial_responses,
    dim_names=("dimX", "dimY"),
    pair_names=("left", "right"),
    stim_levels=None,
    response_col="response",
    modeltype="add",
    method="glm.fit",
    epsilon=1e-14,
    **options,
):
    # Check / set options
    ...

    # Wrangle data
    # 1. rename columns
    # 2. reindex physical stim values
    #     - keep index mappings
    # 3. reindex choice
    #     - keep choice mapping
    if stim_levels is None:
        stim_levels = extract_stim_levels(
            trial_responses, dim_names=dim_names, pair_names=pair_names
        )
    parsed_trial_responses = wrangle_responses(
        trial_responses,
        stim_levels=stim_levels,
        dim_names=dim_names,
        pair_names=pair_names,
        response_col=response_col,
    )

    # MODEL SELECTION
    # Estimate add:
    # Pass through rpy2 to R function
    #   - ideally directly to {{MLCM}}

    # Estimate full:
    # Pass through rpy2 to R function
    #   - ideally directly to {{MLCM}}

    # Compare
    # Pass through rpy2 to R chisq
    ...

    # OPTIONALLY: GoF / outlier removal
    # -
    ...

    # Estimate:
    r_scale_obj = _estimate(
        parsed_trial_responses, modeltype=modeltype, method=method, epsilon=epsilon
    )
    # - re-reindex output scales
    point_estimate = np.array(r_scale_obj.rx2("pscale"))

    # OPTIONALLY: Confidence Intervals
    # - bootstrap
    # - calculate CIs
    # - re-reindex CIs
    ...

    # Housekeeping: package output
    # - estimation output
    #   - scales
    #   - sigma
    # - CIs
    # - options
    #
    result = {}
    result["point_estimate"] = point_estimate
    result["scales"] = unwrangle_scales(
        scales_idc=point_estimate, stim_levels=stim_levels, modeltype=modeltype
    )

    return result
