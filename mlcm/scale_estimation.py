# imports
import numpy as np
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr

importr("MLCM")


def _estimate(parsed_trial_responses, modeltype="add", method="glm.fit", epsilon=1e-4):
    """Fit point estimate for the scales, using the {{MLCM}} R package.

    Uses rpy2 to convert the input data frame to an R dataframe,
    and then runs the MLCM::mlcm(...) function on that data.

    Thus, requires the `rpy2` Python package, R, and the {{MLCM}} R package installed.


    Parameters
    ----------
    parsed_trial_responses : pandas.Dataframe
        (N x 5) DataFrame with experimental data containing N trials, which columns:
        - 'Resp'onses, coded as index `0` or `1`, indicating stimulus `1` or `2` resp.
        - '[dimA_]_1': stimuli index for first stimulus dimension, e.g., `dimA_`, stimulus 1,
        - '[dimA_]_2': stimuli index for first stimulus dimension, e.g., `dimA_`, stimulus 2,
        - '[dimB_]_1': stimuli index for second stimulus dimension, e.g., `dimB_`, stimulus 1,
        - '[dimB_]_2': stimuli index for second stimulus dimension, e.g., `dimB_`, stimulus 2.
        This format is required by the {{MLCM}} R package.)
    modeltype : ['add', 'indep', 'full']
        whether to fit an `add`itive, `indep`endent, or `full` model,
        by default 'add'.
    method : ['glm.fit', 'brglm.fit']
        whether to use a regular `glm` or `b`ias-`r`educed glm fitting routine,
        by default 'glm.fit'.
    epsilon : float, optional
        convergence tolerance, by default 1e-4.

    Returns
    -------
    rpy2.robject
        output from {{MLCM}} R package

    """
    r_mlcm = robjects.r["mlcm"]
    r_as_mlcm_df = robjects.r["as.mlcm.df"]

    # converts pandas DataFrame to R DataFrame
    with (robjects.default_converter + pandas2ri.converter).context():
        r_data = robjects.conversion.get_conversion().py2rpy(parsed_trial_responses)

    # as.mlcm.df()
    r_data = r_as_mlcm_df(r_data)

    # estimation itself by calling mlcm(....)
    scale_obj = r_mlcm(r_data, model=modeltype)

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


def wrangle_scales(): ...


def scale_estimation(trial_responses, modeltype="add", method="glm.fit", epsilon=1e-4, **options):
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
