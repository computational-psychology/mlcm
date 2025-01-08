# imports
import warnings

import numpy as np
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr

from mlcm._wrangle import unwrangle_scales, wrangle_responses
from mlcm.utils import extract_stim_levels

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


def _bootstrap(scale_obj, nsim):
    r_bootmlcm = robjects.r["boot.mlcm"]
    res = r_bootmlcm(scale_obj, nsim=nsim)
    samples = np.array(res.rx2("boot.samp"))

    return samples


def remove_outliers(): ...


def goodness_of_fit(): ...


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
    nsim = 1000  # default number of bootstrap samples

    # Wrangle data
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
    bootstrap_samples = _bootstrap(r_scale_obj, nsim=nsim)
    
    # - calculate CIs
    # - re-reindex CIs
    ...

    # Housekeeping: package output
    result = {}
    result["scales"] = unwrangle_scales(
        scales_idc=point_estimate, stim_levels=stim_levels, modeltype=modeltype
    )
    result["point_estimate"] = point_estimate
    result["sigma"] = r_scale_obj.rx2("sigma")[0]

    # TODO: output CIs, optionally

    # Document options
    result["modeltype"] = r_scale_obj.rx2("model")[0]
    result["method"] = r_scale_obj.rx2("method")[0]
    result["link_function"] = r_scale_obj.rx2("link")[0]
    result["epsilon"] = epsilon

    return result
