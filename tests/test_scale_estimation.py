import pytest
import warnings
import numpy as np
import pandas as pd

from mlcm import scale_estimation

tiny_data = np.array(
    [
        [1, 1, 1, 1, 2],
        [1, 1, 1, 2, 1],
        [1, 1, 1, 2, 2],
        [0, 1, 2, 2, 1],
        [0, 1, 2, 2, 2],
        [1, 2, 1, 2, 2],
    ]
)

tiny_data_df = pd.DataFrame(tiny_data, columns=["Resp", "dimA_1", "dimA_2", "dimB_1", "dimB_2"])


def test_integration(): ...


def test_wrangle_data(): ...


def test_wrangle_scales(): ...


def test_model_comparison(): ...


def test_estimate_add_tiny():
    data = tiny_data_df
    expected = np.array([[0, 0], [7.8, 0]])

    scale_obj = scale_estimation._estimate(data, modeltype="add", method='glm.fit', epsilon=1e-14)
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=2)


def test_estimate_full_tiny():
    data = tiny_data_df
    expected = np.array([[0, 0], [7.8, 7.8]])

    scale_obj = scale_estimation._estimate(data, modeltype="full", method='glm.fit', epsilon=1e-14)
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=2)


def test_estimate_full_tiny_smaller_epsilon():
    data = tiny_data_df
    expected = np.array([[0, 0], [4.17, 4.17]])

    scale_obj = scale_estimation._estimate(data, modeltype="full", method='glm.fit', epsilon=1e-4)
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=2)


def test_estimate_indep_tiny():
    data = tiny_data_df
    expected = np.array([0, 7.8])

    scale_obj = scale_estimation._estimate(data, modeltype="ind", whichdim=1, method='glm.fit', epsilon=1e-14)
    result = np.squeeze(np.array(scale_obj.rx2("pscale")))

    np.testing.assert_almost_equal(expected, result, decimal=2)


def test_estimate_rises_for_ind_model():
    data = tiny_data_df
    with pytest.raises(ValueError):
        scale_estimation._estimate(data, modeltype="ind", whichdim=None, method='glm.fit', epsilon=1e-14)

    with pytest.warns(UserWarning):
        scale_estimation._estimate(data, modeltype="add", whichdim=1, method='glm.fit', epsilon=1e-14)


# testing bootstrap
@pytest.mark.parametrize("modeltype, nparams", [("add", 3), ("full", 4)])
@pytest.mark.parametrize("nsim", [10, 50])
def test_boostrap(modeltype, nparams, nsim):
	data = tiny_data_df
	scale_obj = scale_estimation._estimate(data, modeltype=modeltype, method='glm.fit', epsilon=1e-14)
	
	result = scale_estimation._bootstrap(scale_obj, nsim=nsim)
	assert(result.shape == (nparams-1, nsim)) 
		

