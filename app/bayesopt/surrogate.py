"""
Surrogate model utilities for BayBE integration.

This module provides information and utilities for working with
surrogate models in Bayesian optimization.
"""

from typing import Dict, Optional

from baybe.surrogates import (
    GaussianProcessSurrogate,
    NGBoostSurrogate,
    RandomForestSurrogate,
)

from app.bayesopt.kernels.k1 import gp_kernel
from app.models.campaign import Campaign
from app.models.enums import BOSurrogateModel


def get_surrogate_model(campaign: Campaign) -> Optional[object]:
    """Get the surrogate model for a given campaign."""
    if campaign.surrogate_model == BOSurrogateModel.GAUSSIAN_PROCESS_DEFAULT.value:
        return GaussianProcessSurrogate()
    elif campaign.surrogate_model == BOSurrogateModel.GAUSSIAN_PROCESS_K1.value:
        return GaussianProcessSurrogate(kernel_or_factory=gp_kernel())
    elif campaign.surrogate_model == BOSurrogateModel.RANDOM_FOREST.value:
        return RandomForestSurrogate()
    elif campaign.surrogate_model == BOSurrogateModel.GRADIENT_BOOSTING.value:
        return NGBoostSurrogate()
    else:
        raise ValueError(f"Unsupported surrogate model: {campaign.surrogate_model}")
