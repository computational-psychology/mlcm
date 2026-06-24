import numpy as np
import pandas as pd
import pytest

from mlcm import scale_estimation


@pytest.mark.parametrize(
    "trials,modeltype,normalized,expected",
    [
        ("trial_responses", "add", False, "scales_add"),
        ("trial_responses", "full", False, "scales_full"),
        ("trial_responses", "add", True, "scales_add_normalized"),
        ("trial_responses", "full", True, "scales_full_normalized"),
    ],
)
def test_integration(trials, pair_names, dim_names, modeltype, normalized, expected, request):
    trial_responses = request.getfixturevalue(trials)
    expected_scales = request.getfixturevalue(expected)

    result = scale_estimation.scale_estimation(
        trial_responses=trial_responses,
        pair_names=pair_names,
        dim_names=dim_names,
        modeltype=modeltype,
        normalized=normalized,
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
        ("wrangled_responses", 1, 1e-14, np.array([[0], [-0.967]])),
        ("wrangled_responses", 2, 1e-14, np.array([[0], [7.8]])),
        ("wrangled_responses", 1, 1e-4, np.array([[0], [-0.967]])),
        ("wrangled_responses", 2, 1e-4, np.array([[0], [3.93]])),
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


@pytest.mark.parametrize(
    "bootstrap_samples,alpha,modeltype,expected_lowers,expected_uppers",
    [
        # --- Constant bootstrap samples: quantiles are the same at any alpha ---
        # full model, alpha=0.05
        pytest.param(
            np.array([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0], [3.0, 3.0, 3.0]]),
            0.05,
            "full",
            # reshape [0,1,2,3] -> (2,2) -> .T -> [[0,2],[1,3]] -> melt
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
            id="constant-full-alpha0.05",
        ),
        # add model, alpha=0.05
        # bootstrap shape (2, nsim): row0=dim1 free, row1=dim2 free
        # quantile: [1, 2] → matrix [[0,2],[1,0]] → unwrangle row[1]=[0,2]+1=[1,3]
        # melt: [0, 1, 2, 3]
        pytest.param(
            np.array([[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]]),
            0.05,
            "add",
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0],
            id="constant-add-alpha0.05",
        ),
        # --- Varying bootstrap samples, alpha=0.05 (boundary=0.025) ---
        # quantile([1,3,5], 0.025)=1.1   quantile([1,3,5], 0.975)=4.9
        # quantile([2,4,6], 0.025)=2.1   quantile([2,4,6], 0.975)=5.9
        # quantile([10,20,30], 0.025)=10.5  quantile([10,20,30], 0.975)=29.5
        # full model
        # lowers: [0,1.1,2.1,10.5] -> (2,2).T -> [[0,2.1],[1.1,10.5]] -> melt
        # uppers: [0,4.9,5.9,29.5] -> (2,2).T -> [[0,5.9],[4.9,29.5]] -> melt
        pytest.param(
            np.array([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0], [10.0, 20.0, 30.0]]),
            0.05,
            "full",
            [0.0, 1.1, 2.1, 10.5],
            [0.0, 4.9, 5.9, 29.5],
            id="varying-full-alpha0.05",
        ),
        # add model, alpha=0.05
        # bootstrap shape (2, 3): dim1 free=[1,3,5], dim2 free=[2,4,6]
        # quantile(0.025): [1.1, 2.1] → matrix [[0,2.1],[1.1,0]]
        #   unwrangle: row[1]=[0,2.1]+1.1=[1.1,3.2] → melt: [0, 1.1, 2.1, 3.2]
        # quantile(0.975): [4.9, 5.9] → matrix [[0,5.9],[4.9,0]]
        #   unwrangle: row[1]=[0,5.9]+4.9=[4.9,10.8] → melt: [0, 4.9, 5.9, 10.8]
        pytest.param(
            np.array([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]]),
            0.05,
            "add",
            [0.0, 1.1, 2.1, 3.2],
            [0.0, 4.9, 5.9, 10.8],
            id="varying-add-alpha0.05",
        ),
        # --- Varying bootstrap samples, alpha=0.50 (boundary=0.25) ---
        # quantile([1,3,5], 0.25)=2.0  quantile([1,3,5], 0.75)=4.0
        # quantile([2,4,6], 0.25)=3.0  quantile([2,4,6], 0.75)=5.0
        # quantile([10,20,30], 0.25)=15.0  quantile([10,20,30], 0.75)=25.0
        # full model
        # lowers: [0,2,3,15] -> (2,2).T -> [[0,3],[2,15]] -> melt: [0,2,3,15]
        # uppers: [0,4,5,25] -> (2,2).T -> [[0,5],[4,25]] -> melt: [0,4,5,25]
        pytest.param(
            np.array([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0], [10.0, 20.0, 30.0]]),
            0.50,
            "full",
            [0.0, 2.0, 3.0, 15.0],
            [0.0, 4.0, 5.0, 25.0],
            id="varying-full-alpha0.50",
        ),
        # add model, alpha=0.50
        # quantile(0.25): [2, 3] → matrix [[0,3],[2,0]]
        #   unwrangle: row[1]=[0,3]+2=[2,5] → melt: [0, 2, 3, 5]
        # quantile(0.75): [4, 5] → matrix [[0,5],[4,0]]
        #   unwrangle: row[1]=[0,5]+4=[4,9] → melt: [0, 4, 5, 9]
        pytest.param(
            np.array([[1.0, 3.0, 5.0], [2.0, 4.0, 6.0]]),
            0.50,
            "add",
            [0.0, 2.0, 3.0, 5.0],
            [0.0, 4.0, 5.0, 9.0],
            id="varying-add-alpha0.50",
        ),
    ],
)
def test_ci_from_bootstrap(
    bootstrap_samples, alpha, modeltype, expected_lowers, expected_uppers, stim_levels, dim_names
):
    from mlcm._wrangle import CIs_from_bootstrap

    result = CIs_from_bootstrap(
        bootstrap_samples=bootstrap_samples,
        stim_levels=stim_levels,
        modeltype=modeltype,
        alpha=alpha,
    )

    boundary = alpha / 2
    lower_col = f"CI_{boundary:.3f}"
    upper_col = f"CI_{(1 - boundary):.3f}"

    # Check column names
    assert lower_col in result.columns
    assert upper_col in result.columns
    assert dim_names[0] in result.columns
    assert dim_names[1] in result.columns

    # Build expected DataFrame
    expected = pd.DataFrame(
        {
            dim_names[0]: stim_levels[dim_names[0]] * len(stim_levels[dim_names[1]]),
            dim_names[1]: [
                lvl for lvl in stim_levels[dim_names[1]] for _ in stim_levels[dim_names[0]]
            ],
            lower_col: expected_lowers,
            upper_col: expected_uppers,
        }
    )

    pd.testing.assert_frame_equal(result, expected)
