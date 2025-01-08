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
    expected = np.array([[0, 0], [7.795727, 0]])

    # call estimation function which calls R in the background
    scale_obj = scale_estimation._estimate(data, modeltype="add", method='glm.fit', epsilon=1e-14)

    # returns rpy2 pointer to the R object, we extract the scale values
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=3)


def test_estimate_full_tiny():
    data = tiny_data_df
    expected = np.array([[0, 0], [7.79569, 7.795741]])

    # call estimation function which calls R in the background
    scale_obj = scale_estimation._estimate(data, modeltype="full", method='glm.fit', epsilon=1e-14)

    # returns rpy2 pointer to the R object, we extract the scale values
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=3)


def test_estimate_full_tiny_smaller_epsilon():
    data = tiny_data_df
    expected = np.array([[0, 0], [4.166e+00, 4.166e+00]])

    # call estimation function which calls R in the background
    scale_obj = scale_estimation._estimate(data, modeltype="full", method='glm.fit', epsilon=1e-4)

    # returns rpy2 pointer to the R object, we extract the scale values
    result = np.array(scale_obj.rx2("pscale"))

    np.testing.assert_almost_equal(expected, result, decimal=3)
    

    
