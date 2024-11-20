# imports
import warnings

import numpy as np
import pandas as pd
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr

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


def wrangle_responses(): ...


def unwrangle_responses(
    wrangled_responses: pd.DataFrame,
    stim_levels={},
    pair_names=("l", "r"),
    response_col="response",
):
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
    trial_responses = trial_responses.rename(columns={"Resp": response_col})

    return trial_responses


def wrangle_scales(): ...


def scale_estimation(trial_responses, modeltype="add", method="glm.fit", epsilon=1e-14, **options):
    # Check / set options
    ...

    # Wrangle data
    # 1. rename columns
    # 2. reindex physical stim values
    #     - keep index mappings
    # 3. reindex choice
    #     - keep choice mapping
    parsed_trial_responses = ...

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

    return result
