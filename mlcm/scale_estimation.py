# imports
import numpy as np
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr

importr("MLCM")


def _estimate(parsed_trial_responses, modeltype="add", method="glm.fit", epsilon=1e-4):
    """Run MLCM in R to get the point estimates for the scale.


    Parameters
    ----------
    parsed_trial_responses : pandas Dataframe
        (n x 5) DataFrame with experimental data containing n trials.
        First column has observeris repsonses coded with 0 or 1,
        Second column contains the stimuli index for dimension 1, stimulus 1,
        Third column contains the stimuli index for dimension 1, stimulus 2,
        Fourth column contains the stimuli index for dimension 2, stimulus 1,
        Fifth column contains the stimuli index for dimension 2, stimulus 2
        (This format is the same as in the MLCM R package.)
    modeltype : str, optional
        Type of MLCM model to be fit from set ['indep', 'add' or 'full'].
        The default is 'add'.
    method : str, optional
        Fitting routine. Options are ['glm.fit', 'brglm.fit']. The default is
        'glm.fit'.
    epsilon : float, optional
        Convergence tolerance. The default is 1e-4.

    Returns
    -------
    Rpy2 object with output from MLCM package

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
