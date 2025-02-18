import pandas as pd
import pytest

from mlcm import scale_estimation


def test_wrangle_responses(trial_responses, wrangled_responses, pair_names, dim_names):
    wrangled = scale_estimation.wrangle_responses(
        trial_responses, dim_names=dim_names, pair_names=pair_names
    )

    pd.testing.assert_frame_equal(wrangled, wrangled_responses, atol=1e-2)


def test_unwrangle_responses(wrangled_responses, stim_levels, pair_names, trial_responses):
    unwrangled = scale_estimation.unwrangle_responses(
        wrangled_responses, stim_levels=stim_levels, pair_names=pair_names
    )

    pd.testing.assert_frame_equal(unwrangled, trial_responses, atol=1e-2)


@pytest.mark.parametrize(
    "idc, modeltype, expected, epsilon",
    [
        ("scales_add_idc", "add", "scales_add", 1e-14),
        ("scales_full_idc", "full", "scales_full", 1e-14),
    ],
)
def test_unwrangle_scales(idc, epsilon, expected, modeltype, stim_levels, request):
    scales_idc = request.getfixturevalue(idc)
    scales_natural = request.getfixturevalue(expected)

    unwrangled = scale_estimation.unwrangle_scales(
        scales_idc, stim_levels=stim_levels, modeltype=modeltype
    )

    pd.testing.assert_frame_equal(unwrangled, scales_natural, atol=1e-2)
