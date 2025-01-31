import pytest
import warnings
import numpy as np
import pandas as pd

from mlcm import scale_estimation


def test_integration(): ...


def test_wrangle_data(): ...


def test_wrangle_scales(): ...


def test_model_comparison(): ...


def test_estimate_add_tiny(wrangled_responses):
    expected = np.array([[0, 0], [7.8, 0]])
    scale_obj = scale_estimation._estimate(wrangled_responses, modeltype="add", method='glm.fit', epsilon=1e-14)
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=2)


def test_estimate_full_tiny(wrangled_responses):
    expected = np.array([[0, 0], [7.8, 7.8]])
    scale_obj = scale_estimation._estimate(wrangled_responses, modeltype="full", method='glm.fit', epsilon=1e-14)
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=2)


def test_estimate_full_tiny_smaller_epsilon(wrangled_responses):
    expected = np.array([[0, 0], [4.17, 4.17]])
    scale_obj = scale_estimation._estimate(wrangled_responses, modeltype="full", method='glm.fit', epsilon=1e-4)
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=2)


def test_estimate_indep_tiny(wrangled_responses):
    expected = np.array([0, 7.8])
    scale_obj = scale_estimation._estimate(wrangled_responses, modeltype="ind", whichdim=1, method='glm.fit', epsilon=1e-14)
    result = np.squeeze(np.array(scale_obj.rx2("pscale")))

    np.testing.assert_almost_equal(expected, result, decimal=2)


def test_estimate_rises_for_ind_model(wrangled_responses):
    with pytest.raises(ValueError):
        scale_estimation._estimate(wrangled_responses, modeltype="ind", whichdim=None, method='glm.fit', epsilon=1e-14)

    with pytest.warns(UserWarning):
        scale_estimation._estimate(wrangled_responses, modeltype="add", whichdim=1, method='glm.fit', epsilon=1e-14)

