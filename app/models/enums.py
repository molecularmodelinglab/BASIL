from enum import Enum
from typing import TYPE_CHECKING


class TargetMode(Enum):
    MIN = "Min"
    MAX = "Max"
    MATCH = "Match"


class TargetTransformation(Enum):
    LINEAR = "Linear"
    LOGARITHMIC = "Logarithmic"
    BELL = "Bell"
    TRIANGULAR = "Triangular"
    NONE = "None"


class BOSurrogateModel(str, Enum):
    """
    Surrogate models for Bayesian Optimization using BayBE.

    Attributes:
       display_name (str): The human-readable name for the surrogate model
    """

    if TYPE_CHECKING:
        display_name: str

    def __new__(cls, value: str, display_name: str):
        """
        Create a new instance of the enum member.

        Args:
            value: The machine-readable value for the enum member
        """
        member = str.__new__(cls, value)
        member._value_ = value
        member.display_name = display_name
        return member

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """
        Get the display name for a given enum value.

        Args:
            value: The machine-readable value of the enum member

        Returns:
            The corresponding human-readable display name
        """
        for member in cls:
            if member.value == value:
                return member.display_name
        raise ValueError(f"'{value}' is not a valid {cls.__name__}")

    GAUSSIAN_PROCESS_DEFAULT = ("GaussianProcess", "Gaussian Process (RBF)")
    GAUSSIAN_PROCESS_K1 = ("GaussianProcessK1", "Gaussian Process (K1)")
    RANDOM_FOREST = ("RandomForest", "Random Forest")
    GRADIENT_BOOSTING = ("NaturalGradientBoosting", "Natural Gradient Boosting")


class BOAcquisitionFunction(str, Enum):
    """
    Acquisition functions for Bayesian Optimization using BayBE.

    Attributes:
       display_name (str): The human-readable name for the acquisition function
    """

    if TYPE_CHECKING:
        display_name: str

    def __new__(cls, value: str, display_name: str):
        """
        Create a new instance of the enum member.

        Args:
            value: The machine-readable value for the enum member
        """
        member = str.__new__(cls, value)
        member._value_ = value
        member.display_name = display_name
        return member

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """
        Get the display name for a given enum value.

        Args:
            value: The machine-readable value of the enum member

        Returns:
            The corresponding human-readable display name
        """
        for member in cls:
            if member.value == value:
                return member.display_name
        raise ValueError(f"'{value}' is not a valid {cls.__name__}")

    QEI = ("qEI", "q-EI (Expected Improvement)")
    QLOGEI = ("qLogEI", "q-LogEI (Log Expected Improvement)")
    QNEI = ("qNEI", "q-NEI (Noisy Expected Improvement)")
    QLOGNEI = ("qLogNEI", "q-LogNEI (Log Noisy Expected Improvement)")
    QEHVI = ("qEHVI", "q-EHVI (Expected Hypervolume Improvement)")
    QNEHVI = ("qNEHVI", "q-NEHVI (Noisy Expected Hypervolume Improvement)")
    QUCB = ("qUCB", "q-UCB (Upper Confidence Bound)")
    QTS = ("qTS", "q-TS (Thompson Sampling)")
    RANDOM = ("Random", "Random")


class ParameterType(str, Enum):
    """
    Parameter types for campaign optimization, with UI-friendly display names.
    This enum uses a custom __new__ method to store both a machine-readable
    value and a human-readable display name for each member. This keeps the
    UI-specific information alongside the enum definition, making it easier
    to manage and reuse.

    Attributes:
        display_name (str): The human-readable name for the parameter type
    """

    if TYPE_CHECKING:
        display_name: str

    def __new__(cls, value: str, display_name: str):
        """
        Create a new instance of the enum member.

        Args:
            value: The machine-readable value for the enum member
            display_name: The human-readable name for the enum member
        """
        member = str.__new__(cls, value)
        member._value_ = value
        member.display_name = display_name
        return member

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """
        Get the display name for a given enum value.

        Args:
            value: The machine-readable value of the enum member

        Returns:
            The corresponding human-readable display name
        """
        for member in cls:
            if member.value == value:
                return member.display_name
        raise ValueError(f"'{value}' is not a valid {cls.__name__}")

    DISCRETE_NUMERICAL_REGULAR = (
        "discrete_numerical_regular",
        "Discrete Numerical (Regular)",
    )
    DISCRETE_NUMERICAL_IRREGULAR = (
        "discrete_numerical_irregular",
        "Discrete Numerical (Irregular)",
    )
    CONTINUOUS_NUMERICAL = ("continuous_numerical", "Continuous Numerical")
    CATEGORICAL = ("categorical", "Categorical")
    FIXED = ("fixed", "Fixed Value")
    SUBSTANCE = ("substance", "Substance (SMILES)")
