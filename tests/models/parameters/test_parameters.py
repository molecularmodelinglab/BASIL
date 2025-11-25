import pytest

from app.models.enums import ParameterType
from app.models.parameters.base import BaseParameter
from app.models.parameters.types import (
    Categorical,
    ContinuousNumerical,
    DiscreteNumericalIrregular,
    DiscreteNumericalRegular,
    Fixed,
    Substance,
)


def test_base_parameter_creation():
    # Test successful creation
    param = DiscreteNumericalRegular(name="test_param", min_val=0, max_val=1, step=0.1)
    assert param.name == "test_param"

    # Test empty name
    param = DiscreteNumericalRegular(name="", min_val=0, max_val=1, step=0.1)
    assert param.name == ""

    # Test blank name
    param = DiscreteNumericalRegular(name="  ", min_val=0, max_val=1, step=0.1)
    assert param.name == ""


@pytest.mark.parametrize(
    "param_type, expected_class",
    [
        (ParameterType.DISCRETE_NUMERICAL_REGULAR, DiscreteNumericalRegular),
        (ParameterType.DISCRETE_NUMERICAL_IRREGULAR, DiscreteNumericalIrregular),
        (ParameterType.CONTINUOUS_NUMERICAL, ContinuousNumerical),
        (ParameterType.CATEGORICAL, Categorical),
        (ParameterType.FIXED, Fixed),
        (ParameterType.SUBSTANCE, Substance),
    ],
)
def test_base_parameter_registry(param_type, expected_class):
    assert param_type in BaseParameter._registry
    assert BaseParameter._registry[param_type] == expected_class


@pytest.mark.parametrize(
    "param_type, expected_class",
    [
        (ParameterType.DISCRETE_NUMERICAL_REGULAR, DiscreteNumericalRegular),
        (ParameterType.DISCRETE_NUMERICAL_IRREGULAR, DiscreteNumericalIrregular),
        (ParameterType.CONTINUOUS_NUMERICAL, ContinuousNumerical),
        (ParameterType.CATEGORICAL, Categorical),
        (ParameterType.FIXED, Fixed),
        (ParameterType.SUBSTANCE, Substance),
    ],
)
def test_create_from_type(param_type, expected_class):
    param = BaseParameter.create_from_type(param_type, "test")
    assert isinstance(param, expected_class)
    assert param.name == "test"


@pytest.mark.parametrize(
    "param_dict, expected_type, expected_attrs",
    [
        (
            {
                "name": "temperature",
                "type": "discrete_numerical_regular",
                "constraints": {"min": 20, "max": 100, "step": 5},
            },
            DiscreteNumericalRegular,
            {"min_val": 20, "max_val": 100, "step": 5},
        ),
        (
            {
                "name": "ph",
                "type": "discrete_numerical_irregular",
                "constraints": {"values": [7, 7.2, 7.4]},
            },
            DiscreteNumericalIrregular,
            {"values": [7, 7.2, 7.4]},
        ),
        (
            {
                "name": "concentration",
                "type": "continuous_numerical",
                "constraints": {"min": 0.1, "max": 0.9},
            },
            ContinuousNumerical,
            {"min_val": 0.1, "max_val": 0.9},
        ),
        (
            {
                "name": "solvent",
                "type": "categorical",
                "constraints": {"values": ["water", "ethanol"]},
            },
            Categorical,
            {"values": ["water", "ethanol"]},
        ),
        (
            {"name": "pressure", "type": "fixed", "constraints": {"value": 1.0}},
            Fixed,
            {"value": 1.0},
        ),
        (
            {
                "name": "reagent",
                "type": "substance",
                "constraints": {"values": ["CCO", "CCC"]},
            },
            Substance,
            {"smiles": ["CCO", "CCC"]},
        ),
    ],
)
def test_from_dict(param_dict, expected_type, expected_attrs):
    param = BaseParameter.from_dict(param_dict)
    assert isinstance(param, expected_type)
    assert param.name == param_dict["name"]
    for attr, value in expected_attrs.items():
        assert getattr(param, attr) == value


def test_discrete_numerical_regular():
    param = DiscreteNumericalRegular("test", 0, 10, 2)
    assert param.validate() == (True, None)
    assert param.validate_value(4) == (True, "")
    assert param.validate_value(5) == (False, "Value 5 does not align with step size 2")
    assert param.validate_value(12) == (False, "Value 12 is outside range [0, 10]")
    random_val = param.get_random_valid_value()
    assert 0 <= random_val <= 10
    assert (random_val % 2) == 0


def test_discrete_numerical_regular_invalid_config():
    # Min >= Max
    param = DiscreteNumericalRegular("test", 10, 0, 2)
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Minimum value must be less than maximum value" in msg

    # Step <= 0
    param = DiscreteNumericalRegular("test", 0, 10, 0)
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Step size must be positive" in msg

    # Step > range
    param = DiscreteNumericalRegular("test", 0, 10, 12)
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Step size cannot be larger than the range" in msg

    param = DiscreteNumericalRegular("test", 0, 10, 3)
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Step size does not evenly divide the range" in msg


def test_discrete_numerical_irregular():
    param = DiscreteNumericalIrregular("test", [1, 2, 5])
    assert param.validate() == (True, None)
    assert param.validate_value(2) == (True, "")
    assert param.validate_value(3) == (
        False,
        "Value 3 is not in allowed values [1, 2, 5]",
    )
    assert param.get_random_valid_value() in [1, 2, 5]


def test_discrete_numerical_irregular_invalid_config():
    # Empty values
    param = DiscreteNumericalIrregular("test", [])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "At least one value is required" in msg

    # Non-numeric values
    param = DiscreteNumericalIrregular("test", [1, "a", 3])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "not a number" in msg

    # Duplicate values
    param = DiscreteNumericalIrregular("test", [1, 2, 2])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Duplicate values are not allowed" in msg


def test_continuous_numerical():
    param = ContinuousNumerical("test", 0, 1)
    assert param.validate() == (True, None)
    assert param.validate_value(0.5) == (True, "")
    assert param.validate_value(1.5) == (False, "Value 1.5 is outside range [0, 1]")
    assert 0 <= param.get_random_valid_value() <= 1


def test_continuous_numerical_invalid_config():
    param = ContinuousNumerical("test", 1, 0)
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Minimum value must be less than maximum value" in msg


def test_categorical():
    param = Categorical("test", ["A", "B", "C"])
    assert param.validate() == (True, None)
    assert param.validate_value("B") == (True, "")
    assert param.validate_value("D") == (
        False,
        "Value 'D' is not in allowed categories ['A', 'B', 'C']",
    )
    assert param.get_random_valid_value() in ["A", "B", "C"]


def test_categorical_invalid_config():
    # Empty values
    param = Categorical("test", [])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "At least one category is required" in msg

    # Empty string in values
    param = Categorical("test", ["A", " ", "C"])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "cannot be empty" in msg

    # Duplicate values
    param = Categorical("test", ["A", "B", "A"])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Duplicate categories are not allowed" in msg


def test_fixed():
    param = Fixed("test", 5)
    assert param.validate() == (True, None)
    assert param.validate_value(5) == (True, "")
    assert param.validate_value(6) == (
        False,
        "Value '6' does not match fixed value '5'",
    )
    assert param.get_random_valid_value() == 5


def test_fixed_invalid_config():
    param = Fixed("test", None)
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Fixed value cannot be None" in msg


def test_substance():
    param = Substance("test", ["CCO", "CCCCO"])
    assert param.validate() == (True, None)
    assert param.validate_value("CCO") == (True, "")
    assert param.validate_value("C") == (
        False,
        "SMILES 'C' is not in allowed list ['CCO', 'CCCCO']",
    )
    assert param.get_random_valid_value() in ["CCO", "CCCCO"]


def test_substance_invalid_config():
    # Empty smiles
    param = Substance("test", [])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "At least one SMILES string is required" in msg

    # Empty string in smiles
    param = Substance("test", ["CCO", ""])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "cannot be empty" in msg

    # Duplicate smiles
    param = Substance("test", ["CCO", "CCO"])
    is_valid, msg = param.validate()
    assert not is_valid
    assert "Duplicate SMILES strings are not allowed" in msg


@pytest.mark.parametrize(
    "param_instance",
    [
        DiscreteNumericalRegular("temp", 10, 90, 5),
        DiscreteNumericalIrregular("ph", [7.0, 7.2, 7.4, 8.0]),
        ContinuousNumerical("conc", 0.1, 0.8),
        Categorical("solvent", ["water", "ethanol", "methanol"]),
        Fixed("pressure", 1.01),
        Substance("reagent", ["CCO", "CCCCO", "c1ccccc1"]),
    ],
)
def test_serialization_round_trip(param_instance):
    """Test that a parameter can be serialized and deserialized without data loss."""
    # Convert to dict
    param_dict = param_instance.to_dict()

    # Convert back to object
    reconstituted_param = BaseParameter.from_dict(param_dict)

    # Check that the reconstituted object is identical
    assert isinstance(reconstituted_param, type(param_instance))
    assert reconstituted_param.name == param_instance.name
    assert reconstituted_param.to_dict() == param_instance.to_dict()
