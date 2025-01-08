import numpy as np
import pandas as pd
import pytest

from mlcm import scale_estimation


@pytest.mark.parametrize(
    "trials,modeltype,expected",
    [
        ("trial_responses", "add", "scales_add"),
        ("trial_responses", "full", "scales_full"),
    ],
)
def test_integration(trials, pair_names, dim_names, modeltype, expected, request):
    trial_responses = request.getfixturevalue(trials)
    expected_scales = request.getfixturevalue(expected)

    result = scale_estimation.scale_estimation(
        trial_responses=trial_responses,
        pair_names=pair_names,
        dim_names=dim_names,
        modeltype=modeltype,
    )

    pd.testing.assert_frame_equal(result["scales"], expected_scales)


@pytest.mark.parametrize(
    "trials,modeltype,expected",
    [
        ("wrangled_responses", "add", "scales_add_idc"),
        ("wrangled_responses", "full", "scales_full_idc"),
    ],
)
def test_already_wrangled(trials, pair_names, p_names, dim_names, modeltype, expected, request):
    trial_responses = request.getfixturevalue(trials)
    expected_scales = request.getfixturevalue(expected)

    result = scale_estimation.scale_estimation(
        trial_responses=trial_responses,
        pair_names=p_names.values(),
        dim_names=dim_names,
        modeltype=modeltype,
    )

    pd.testing.assert_frame_equal(result["scales"], expected_scales)


def test_model_comparison(): ...


@pytest.mark.parametrize(
    "trials",
    ["wrangled_responses"],
)
@pytest.mark.parametrize(
    "modeltype,epsilon,expected",
    [
        ("add", 1e-14, "scales_array_add"),
        ("add", 1e-4, "scales_array_add"),
        ("full", 1e-14, "scales_array_full"),
        ("full", 1e-4, "scales_array_full"),
    ],
)
def test_estimate(trials, modeltype, epsilon, expected, request):
    trial_responses = request.getfixturevalue(trials)
    expected = request.getfixturevalue(expected)

    scale_obj = scale_estimation._estimate(
        trial_responses, modeltype=modeltype, method="glm.fit", epsilon=epsilon
    )
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(result, expected, decimal=2)


@pytest.mark.parametrize(
    "trials,whichdim,epsilon,expected",
    [
        ("wrangled_responses", 1, 1e-14, np.array([[0], [7.80]])),
        ("wrangled_responses", 2, 1e-14, np.array([[0], [-0.43]])),
    ],
)
def test_estimate_indep(trials, whichdim, epsilon, expected, request):
    trial_responses = request.getfixturevalue(trials)
    scale_obj = scale_estimation._estimate(
        trial_responses, modeltype="ind", whichdim=whichdim, method="glm.fit", epsilon=epsilon
    )
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(result, expected, decimal=2)


def test_estimate_raises_for_ind_model(wrangled_responses):
    with pytest.raises(ValueError):
        scale_estimation._estimate(
            wrangled_responses, modeltype="ind", whichdim=None, method="glm.fit", epsilon=1e-14
        )

    with pytest.warns(UserWarning):
        scale_estimation._estimate(
            wrangled_responses, modeltype="add", whichdim=1, method="glm.fit", epsilon=1e-14
        )


@pytest.mark.parametrize(
    "trials",
    ["wrangled_responses"],
)
@pytest.mark.parametrize("modeltype, nparams", [("add", 3), ("full", 4)])
@pytest.mark.parametrize("nsim", [10, 50])
def test_boostrap(trials, modeltype, nparams, nsim, request):
    trial_responses = request.getfixturevalue(trials)
    scale_obj = scale_estimation._estimate(
        trial_responses, modeltype=modeltype, method="glm.fit", epsilon=1e-14
    )
    result = scale_estimation._bootstrap(scale_obj, nsim=nsim)
    assert result.shape == (nparams - 1, nsim)



