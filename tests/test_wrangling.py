import pandas as pd

from mlcm import scale_estimation


def test_unwrangle_responses(wrangled_responses, stim_levels, trial_responses):
    unwrangled = scale_estimation.unwrangle_responses(wrangled_responses, stim_levels=stim_levels)

    pd.testing.assert_frame_equal(unwrangled, trial_responses, atol=1e-2)
