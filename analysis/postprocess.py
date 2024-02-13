import pandas as pd

from surround_brightness import data_management
from surround_brightness.analysis.plotting import scales_participant
from surround_brightness.analysis.preprocess import CONTEXTS_TO_IDC
from surround_brightness.experiment.design import intensities as exp_intensities

intensities_nominal = exp_intensities

IDC_TO_CONTEXTS = {val: key for key, val in CONTEXTS_TO_IDC.items()}


def reindex_scales(scales):
    # Index contexts
    scales["context"] = scales["context"].replace(IDC_TO_CONTEXTS)

    # Index intensities
    ints = {idx + 1: intensity for idx, intensity in enumerate(intensities_nominal)}
    scales["intensity"] = scales["intensity"].replace(ints).astype(float)

    return scales


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    participant = "DEMO"
    stim = "whites"
    modeltype = "full"
    filename = f"{participant}_{stim}_{modeltype}_trimmed_{modeltype}_norm.scales.csv"
    filepath = data_management.results_dir / participant / "analyzed" / filename

    s = reindex_scales(pd.read_csv(filepath, sep=","))
    s.to_csv(filepath, sep=",", index=False)

    plt.figure(figsize=(6, 6))
    scales_participant(s)
    plt.show()
