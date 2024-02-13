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
