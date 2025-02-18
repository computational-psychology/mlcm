import numpy as np
import pytest

from mlcm import scale_estimation


def test_integration(): ...


def test_wrangle_data(): ...


def test_wrangle_scales(): ...


def test_model_comparison(): ...


@pytest.mark.parametrize(
    "trials",
    ["wrangled_responses"],
)
@pytest.mark.parametrize(
    "modeltype,epsilon,expected",
    [
        ("add", 1e-14, "scales_add_idc"),
        ("add", 1e-4, "scales_add_idc"),
        ("full", 1e-14, "scales_full_idc"),
        ("full", 1e-4, "scales_full_idc"),
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
