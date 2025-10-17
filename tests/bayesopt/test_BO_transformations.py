import pytest

from app.bayesopt.transformations import get_transformation
from app.models.enums import TargetTransformation


def test_get_transformation_identity():
    t = get_transformation(TargetTransformation.LINEAR.value)
    assert t.__class__.__name__ == "IdentityTransformation"


def test_get_transformation_none():
    t = get_transformation(TargetTransformation.NONE.value)
    assert t is None


def test_get_transformation_invalid():
    with pytest.raises(ValueError):
        get_transformation("UNKNOWN")
