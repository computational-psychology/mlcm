# imports


def _estimate(): ...


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


def scale_estimation(trial_responses, **options):
    # Check / set options
    ...

    # Wrangle data
    # 1. rename columns
    # 2. reindex physical stim values
    #     - keep index mappings
    # 3. reindex choice
    #     - keep choice mapping
    ...

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
    # Pass through rpy2 to R function
    #   - ideally directly to {{MLCM}}
    #   - thin wrapper may be necessary (?)
    # - re-reindex output scales
    ...

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
    ...
