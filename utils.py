"""Utilities for QuOps.Info."""

from typing import Any

import numpy as np


def is_nan_or_nan_string(val: Any) -> bool:
    if isinstance(val, float) and np.isnan(val):
        return True
    if isinstance(val, np.float64) and np.isnan(val):
        return True
    if isinstance(val, str) and val.strip().lower() == 'nan':
        return True
    return False
