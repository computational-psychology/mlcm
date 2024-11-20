import pandas as pd

from mlcm import scale_estimation


def test_wrangle_responses(trial_responses, wrangled_responses):
    wrangled = scale_estimation.wrangle_responses(trial_responses)

    pd.testing.assert_frame_equal(wrangled, wrangled_responses)


def test_unwrangle_responses(wrangled_responses, stim_levels, trial_responses):
    unwrangled = scale_estimation.unwrangle_responses(wrangled_responses, stim_levels=stim_levels)

    pd.testing.assert_frame_equal(unwrangled, trial_responses, atol=1e-2)


def test_unwrangle_scales(scales_idc, scales_natural):
    unwrangled = scale_estimation.unwrangle_scales(scales_idc)

    pd.testing.assert_frame_equal(unwrangled, scales_natural)
