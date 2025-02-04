import numpy as np


# EXPERIMENTAL
def normalize_observation(
        values: np.array,
        min_vals: np.array,
        max_vals: np.array,
        range_min: np.array,
        range_max: np.array
) -> np.array:
    normalized = (values - min_vals) / (max_vals - min_vals)
    scaled = normalized * (range_max - range_min) + range_min
    return scaled
