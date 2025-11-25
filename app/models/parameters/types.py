import random
from typing import Any, Dict, List, Optional, Union

from app.models.enums import ParameterType
from app.models.parameters.base import BaseParameter

TOL = 1e-10


class DiscreteNumericalRegular(BaseParameter):
    """Discrete numerical parameter with regular spacing (min, max, step)."""

    TYPE = ParameterType.DISCRETE_NUMERICAL_REGULAR

    def __init__(self, name: str, min_val: float, max_val: float, step: float) -> None:
        super().__init__(name)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

    @classmethod
    def create_default(cls, name: str) -> "DiscreteNumericalRegular":
        """Create parameter with default values."""
        return cls(name, 0.0, 10.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.parameter_type.value,
            "constraints": {
                "min": self.min_val,
                "max": self.max_val,
                "step": self.step,
            },
        }

    def load_constraints(self, constraints: Dict[str, Any]) -> None:
        """Load constraints from dictionary."""
        self.min_val = constraints.get("min", 0.0)
        self.max_val = constraints.get("max", 10.0)
        self.step = constraints.get("step", 1.0)

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate parameter configuration."""
        if self.min_val >= self.max_val:
            return False, "Minimum value must be less than maximum value"

        if self.step <= 0:
            return False, "Step size must be positive"

        if self.step > (self.max_val - self.min_val):
            return False, "Step size cannot be larger than the range"

        max_step = int((self.max_val - self.min_val) / self.step)
        if self.max_val - (self.min_val + max_step * self.step) > TOL:
            return False, "Step size does not evenly divide the range"

        return True, None

    def get_random_valid_value(self) -> float:
        """Generate random valid value within min/max range respecting step size."""
        # Calculate all possible values
        num_steps = int((self.max_val - self.min_val) / self.step) + 1
        random_step = random.randint(0, num_steps - 1)

        value = self.min_val + (random_step * self.step)
        return min(value, self.max_val)  # Ensure we don't exceed max

    def convert_value(self, raw_value: str) -> float:
        """Convert string value to float for numerical parameter."""
        return float(raw_value)

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate that value meets discrete numerical regular constraints."""
        try:
            # Convert to float if needed
            float_value = float(value) if not isinstance(value, (int, float)) else value

            # Check if value is within range
            if not (self.min_val <= float_value <= self.max_val):
                return (
                    False,
                    f"Value {float_value} is outside range [{self.min_val}, {self.max_val}]",
                )

            # Check if value aligns with step size
            steps_from_min = (float_value - self.min_val) / self.step
            if abs(steps_from_min - round(steps_from_min)) > TOL:
                return (
                    False,
                    f"Value {float_value} does not align with step size {self.step}",
                )

            return True, ""

        except (ValueError, TypeError):
            return False, f"Value '{value}' cannot be converted to number"


class DiscreteNumericalIrregular(BaseParameter):
    """Discrete numerical parameter with irregular spacing (list of values)."""

    TYPE = ParameterType.DISCRETE_NUMERICAL_IRREGULAR

    def __init__(self, name: str, values: List[Union[int, float]]) -> None:
        super().__init__(name)
        self.values = list(values)

    @classmethod
    def create_default(cls, name: str) -> "DiscreteNumericalIrregular":
        """Create parameter with default values."""
        return cls(name, [1, 2, 5])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.parameter_type.value,
            "constraints": {"values": self.values},
        }

    def load_constraints(self, constraints: Dict[str, Any]) -> None:
        """Load constraints from dictionary."""
        self.values = constraints.get("values", [])

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate parameter configuration."""
        if not self.values:
            return False, "At least one value is required"

        for i, value in enumerate(self.values):
            if not isinstance(value, (int, float)):
                return False, f"Value at index {i} ({value}) is not a number"

        if len(self.values) != len(set(self.values)):
            return False, "Duplicate values are not allowed"

        return True, None

    def get_random_valid_value(self) -> Union[int, float]:
        """Generate random value from the configured values list."""
        if not self.values:
            return 1.0  # Fallback

        return random.choice(self.values)

    def convert_value(self, raw_value: str) -> float:
        """Convert string value to float for numerical parameter."""
        return float(raw_value)

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate that value is in the list of allowed values."""
        try:
            # Convert to number if needed
            if isinstance(value, str):
                numeric_value = float(value)
            else:
                numeric_value = value

            # Check if value is in allowed list
            if numeric_value in self.values:
                return True, ""
            else:
                return (
                    False,
                    f"Value {numeric_value} is not in allowed values {self.values}",
                )

        except (ValueError, TypeError):
            return False, f"Value '{value}' cannot be converted to number"


class ContinuousNumerical(BaseParameter):
    """Continuous numerical parameter with range (min, max)."""

    TYPE = ParameterType.CONTINUOUS_NUMERICAL

    def __init__(self, name: str, min_val: float, max_val: float) -> None:
        super().__init__(name)
        self.min_val = min_val
        self.max_val = max_val

    @classmethod
    def create_default(cls, name: str) -> "ContinuousNumerical":
        """Create parameter with default values."""
        return cls(name, 0.0, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.parameter_type.value,
            "constraints": {"min": self.min_val, "max": self.max_val},
        }

    def load_constraints(self, constraints: Dict[str, Any]) -> None:
        """Load constraints from dictionary."""
        self.min_val = constraints.get("min", 0.0)
        self.max_val = constraints.get("max", 1.0)

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate parameter configuration."""
        if self.min_val >= self.max_val:
            return False, "Minimum value must be less than maximum value"

        return True, None

    def get_random_valid_value(self) -> float:
        """Generate random value within the continuous range."""
        value = random.uniform(self.min_val, self.max_val)
        return round(value, 3)

    def convert_value(self, raw_value: str) -> float:
        """Convert string value to float for numerical parameter."""
        return float(raw_value)

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate that value is within the continuous range."""
        try:
            # Convert to float if needed
            float_value = float(value) if not isinstance(value, (int, float)) else value

            # Check if value is within range
            if self.min_val <= float_value <= self.max_val:
                return True, ""
            else:
                return (
                    False,
                    f"Value {float_value} is outside range [{self.min_val}, {self.max_val}]",
                )

        except (ValueError, TypeError):
            return False, f"Value '{value}' cannot be converted to number"


class Categorical(BaseParameter):
    """Categorical parameter with string values."""

    TYPE = ParameterType.CATEGORICAL

    def __init__(self, name: str, values: List[str]) -> None:
        super().__init__(name)
        self.values = [str(v).strip() for v in values]  # Ensure strings and strip whitespace

    @classmethod
    def create_default(cls, name: str) -> "Categorical":
        """Create parameter with default values."""
        return cls(name, ["A", "B", "C"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.parameter_type.value,
            "constraints": {"values": self.values},
        }

    def load_constraints(self, constraints: Dict[str, Any]) -> None:
        """Load constraints from dictionary."""
        values = constraints.get("values", [])
        self.values = [str(v).strip() for v in values]

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate parameter configuration."""
        if not self.values:
            return False, "At least one category is required"

        for i, value in enumerate(self.values):
            if not value:
                return False, f"Category at index {i} cannot be empty"

        # Check for duplicates
        if len(self.values) != len(set(self.values)):
            return False, "Duplicate categories are not allowed"

        return True, None

    def get_random_valid_value(self) -> str:
        """Generate random category from the configured list."""
        if not self.values:
            return "Category_A"  # Fallback

        return random.choice(self.values)

    def convert_value(self, raw_value: str) -> str:
        """Convert and clean string value for categorical parameter."""
        return raw_value.strip()

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate that value is one of the allowed categories."""
        # Convert to string and strip whitespace
        str_value = str(value).strip()

        if str_value in self.values:
            return True, ""
        else:
            return (
                False,
                f"Value '{str_value}' is not in allowed categories {self.values}",
            )


class Fixed(BaseParameter):
    """Fixed parameter with a single value."""

    TYPE = ParameterType.FIXED

    def __init__(self, name: str, value: Union[int, float, str]) -> None:
        super().__init__(name)
        self.value = value

    @classmethod
    def create_default(cls, name: str) -> "Fixed":
        """Create parameter with default values."""
        return cls(name, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.parameter_type.value,
            "constraints": {"value": self.value},
        }

    def load_constraints(self, constraints: Dict[str, Any]) -> None:
        """Load constraints from dictionary."""
        self.value = constraints.get("value", 1.0)

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate parameter configuration."""
        if self.value is None:
            return False, "Fixed value cannot be None"

        return True, None

    def get_random_valid_value(self) -> Union[str, float, int]:
        """Return the fixed value (always the same)."""
        return self.value

    def convert_value(self, raw_value: str) -> Union[str, float, int]:
        """Convert string value to appropriate type based on fixed value type."""
        if isinstance(self.value, (int, float)):
            return float(raw_value)
        else:
            return raw_value.strip()

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate that value exactly matches the fixed value."""
        if value == self.value:
            return True, ""

        if isinstance(self.value, (int, float)):
            try:
                numeric_value = float(value)
                if numeric_value == float(self.value):
                    return True, ""
            except (ValueError, TypeError):
                pass

        return False, f"Value '{value}' does not match fixed value '{self.value}'"


class Substance(BaseParameter):
    """Substance parameter with SMILES strings."""

    TYPE = ParameterType.SUBSTANCE

    def __init__(self, name: str, smiles: List[str]) -> None:
        super().__init__(name)
        self.smiles = [str(s).strip() for s in smiles]  # Ensure strings and strip whitespace

    @classmethod
    def create_default(cls, name: str) -> "Substance":
        """Create parameter with default values."""
        return cls(name, ["CCO", "CCCCO"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.parameter_type.value,
            "constraints": {"values": self.smiles},
        }

    def load_constraints(self, constraints: Dict[str, Any]) -> None:
        """Load constraints from dictionary."""
        values = constraints.get("values", [])
        self.smiles = [str(s).strip() for s in values]

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate parameter configuration."""
        if not self.smiles:
            return False, "At least one SMILES string is required"

        for i, smiles in enumerate(self.smiles):
            if not smiles:
                return False, f"SMILES at index {i} cannot be empty"

        if len(self.smiles) != len(set(self.smiles)):
            return False, "Duplicate SMILES strings are not allowed"

        # Basic SMILES validation (just check for obviously invalid characters)
        invalid_chars = set(" \t\n\r")
        for i, smiles in enumerate(self.smiles):
            if any(char in invalid_chars for char in smiles):
                return (
                    False,
                    f"SMILES at index {i} contains invalid whitespace characters",
                )

        return True, None

    def get_random_valid_value(self) -> str:
        """Generate random SMILES string from the configured list."""
        if not self.smiles:
            return "CCO"  # Fallback (ethanol SMILES)

        return random.choice(self.smiles)

    def convert_value(self, raw_value: str) -> str:
        """Convert and clean string value for SMILES parameter."""
        return raw_value.strip()

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate that value is one of the allowed SMILES strings."""
        # Convert to string and strip whitespace
        str_value = str(value).strip()

        if str_value in self.smiles:
            return True, ""
        else:
            return False, f"SMILES '{str_value}' is not in allowed list {self.smiles}"
