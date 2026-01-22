"""
Objective and target conversion utilities for BayBE integration.

This module handles the conversion between BASIL targets and BayBE objectives.
"""

from typing import Dict, List, Optional

from baybe.objectives import DesirabilityObjective, ParetoObjective, SingleTargetObjective
from baybe.targets import NumericalTarget

from app.models.campaign import Target
from app.models.enums import MultiObjectiveStrategy, ObjectiveScope


class ObjectiveConverter:
    """Converts BASIL targets to BayBE objectives."""

    @staticmethod
    def convert_target(basil_target: Target) -> NumericalTarget:
        """
        Convert a BASIL target to a BayBE target.

        Args:
            basil_target: BASIL target to convert

        Returns:
            BayBE NumericalTarget

        Raises:
            ValueError: If target configuration is invalid
        """
        # Determine the mode
        if basil_target.mode.upper() == "MAX":
            minimize = False
        elif basil_target.mode.upper() == "MIN":
            minimize = True
        elif basil_target.mode.upper() == "MATCH":
            minimize = None
        else:
            raise ValueError(f"Unsupported target mode: {basil_target.mode}")

        # Create the target
        target_kwargs = {
            "name": basil_target.name,
            "minimize": minimize,
        }

        if basil_target.mode.upper() == "MATCH":
            if basil_target.min_value is None or basil_target.max_value is None:
                raise ValueError("MATCH mode requires both min_value and max_value")
            match_value = (basil_target.min_value + basil_target.max_value) / 2
            return NumericalTarget.match_triangular(
                name=basil_target.name,
                match_value=match_value,
                cutoffs=(basil_target.min_value, basil_target.max_value),
            )

        if basil_target.min_value is None or basil_target.max_value is None:
            return NumericalTarget(**target_kwargs, _enforce_modern_interface=True)
        else:
            return NumericalTarget.normalized_ramp(
                name=basil_target.name, descending=minimize, cutoffs=(basil_target.min_value, basil_target.max_value)
            )

    @staticmethod
    def create_objective(
        basil_targets: List[Target],
        objective_scope: Optional[str] = None,
        multi_objective_strategy: Optional[str] = None,
    ):
        """
        Create a BayBE objective from BASIL targets.

        For single targets, creates a SingleTargetObjective.
        For multiple targets, creates a DesirabilityObjective or ParetoObjective based on strategy.

        Args:
            basil_targets: List of BASIL targets

        Returns:
            BayBE SingleTargetObjective or DesirabilityObjective

        Raises:
            ValueError: If no valid targets found
        """
        if not basil_targets:
            raise ValueError("No targets provided for optimization")

        resolved_scope = objective_scope or (
            ObjectiveScope.MULTI.value if len(basil_targets) > 1 else ObjectiveScope.SINGLE.value
        )
        resolved_strategy = multi_objective_strategy or MultiObjectiveStrategy.DESIRABILITY.value

        if resolved_scope == ObjectiveScope.SINGLE.value and len(basil_targets) > 1:
            resolved_scope = ObjectiveScope.MULTI.value

        if resolved_scope == ObjectiveScope.SINGLE.value:
            if len(basil_targets) != 1:
                raise ValueError("Single-objective optimization requires exactly one target")
            baybe_target = ObjectiveConverter.convert_target(basil_targets[0])
            return SingleTargetObjective(target=baybe_target)

        if resolved_strategy == MultiObjectiveStrategy.PARETO.value:
            baybe_targets = [ObjectiveConverter.convert_target(target) for target in basil_targets]
            return ParetoObjective(baybe_targets)

        return ObjectiveConverter._create_desirability_objective(basil_targets)

    @staticmethod
    def _create_desirability_objective(basil_targets: List[Target]) -> DesirabilityObjective:
        """
        Create a DesirabilityObjective for multi-target optimization.

        The desirability function combines multiple targets into a single score
        where each target contributes based on its weight (default weight = 1.0).

        Args:
            basil_targets: List of BASIL targets

        Returns:
            BayBE DesirabilityObjective

        Raises:
            ValueError: If target configuration is invalid
        """
        baybe_targets = []
        weights = []

        for target in basil_targets:
            # Convert target
            baybe_target = ObjectiveConverter.convert_target(target)
            baybe_targets.append(baybe_target)

            # Use specified weight or default to 1.0
            weight = target.weight if target.weight is not None else 1.0
            weights.append(weight)

        return DesirabilityObjective(targets=baybe_targets, weights=weights)

    @staticmethod
    def validate_targets(
        basil_targets: List[Target],
        objective_scope: Optional[str] = None,
        multi_objective_strategy: Optional[str] = None,
    ) -> List[str]:
        """
        Validate BASIL targets for BayBE conversion.

        Args:
            basil_targets: List of BASIL targets to validate

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []

        if not basil_targets:
            errors.append("At least one target must be specified")
            return errors

        resolved_scope = objective_scope or (
            ObjectiveScope.MULTI.value if len(basil_targets) > 1 else ObjectiveScope.SINGLE.value
        )
        resolved_strategy = multi_objective_strategy or MultiObjectiveStrategy.DESIRABILITY.value

        if resolved_scope == ObjectiveScope.SINGLE.value and len(basil_targets) > 1:
            resolved_scope = ObjectiveScope.MULTI.value

        if resolved_scope == ObjectiveScope.SINGLE.value and len(basil_targets) != 1:
            errors.append("Single-objective optimization requires exactly one target")

        if resolved_scope == ObjectiveScope.MULTI.value and len(basil_targets) < 2:
            errors.append("Multi-objective optimization requires at least two targets")

        for i, target in enumerate(basil_targets):
            target_errors = ObjectiveConverter._validate_single_target(target, i)
            errors.extend(target_errors)

        # Check for duplicate target names
        target_names = [t.name for t in basil_targets]
        duplicates = set([name for name in target_names if target_names.count(name) > 1])
        if duplicates:
            errors.append(f"Duplicate target names found: {', '.join(duplicates)}")

        if (
            resolved_scope == ObjectiveScope.MULTI.value
            and resolved_strategy == MultiObjectiveStrategy.DESIRABILITY.value
            and len(basil_targets) > 1
        ):
            missing_weights = [t.name or f"Target {i + 1}" for i, t in enumerate(basil_targets) if t.weight is None]
            if missing_weights:
                errors.append(
                    "Desirability optimization requires weights for all targets: " + ", ".join(missing_weights)
                )

        return errors

    @staticmethod
    def _validate_single_target(target: Target, index: int) -> List[str]:
        """
        Validate a single target.

        Args:
            target: Target to validate
            index: Index of target in list (for error messages)

        Returns:
            List of validation error messages
        """
        errors = []
        target_id = f"Target {index + 1} ({target.name})" if target.name else f"Target {index + 1}"

        # Check target name
        if not target.name or not target.name.strip():
            errors.append(f"{target_id}: Target name cannot be empty")

        # Check mode
        valid_modes = ["MAX", "MIN", "MATCH"]
        if target.mode.upper() not in valid_modes:
            errors.append(f"{target_id}: Invalid mode '{target.mode}'. Must be one of: {', '.join(valid_modes)}")

        # Check bounds for MATCH mode- TODO for Me (Kelvin) - PROPER MATCHING
        if target.mode.upper() == "MATCH":
            if target.min_value is None or target.max_value is None:
                errors.append(f"{target_id}: MATCH mode requires both min_value and max_value")
            elif target.min_value >= target.max_value:
                errors.append(f"{target_id}: min_value must be less than max_value")

        if target.min_value is not None and target.max_value is not None:
            if target.min_value >= target.max_value:
                errors.append(
                    f"{target_id}: min_value ({target.min_value}) must be less than max_value ({target.max_value})"
                )

        if target.weight is not None and target.weight <= 0:
            errors.append(f"{target_id}: Weight must be positive")

        return errors

    @staticmethod
    def get_target_names(basil_targets: List[Target]) -> List[str]:
        """
        Get list of target names for DataFrame column creation.

        Args:
            basil_targets: List of BASIL targets

        Returns:
            List of target names
        """
        return [target.name for target in basil_targets]

    @staticmethod
    def create_multi_objective_note(
        targets: List[Target],
        multi_objective_strategy: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a note about multi-objective handling.

        Args:
            targets: List of targets

        Returns:
            Note string explaining optimization approach, None if single target
        """
        if len(targets) <= 1:
            return None

        resolved_strategy = multi_objective_strategy or MultiObjectiveStrategy.DESIRABILITY.value

        if resolved_strategy == MultiObjectiveStrategy.PARETO.value:
            target_info = ", ".join([f"'{target.name}'" for target in targets])
            note = "Multi-objective optimization using Pareto frontier. "
            note += f"Targets: {target_info}. "
            note += "All targets are optimized simultaneously without explicit weights."
            return note

        total_weight = sum(t.weight if t.weight is not None else 1.0 for t in targets)
        target_info = []

        for target in targets:
            weight = target.weight if target.weight is not None else 1.0
            weight_pct = (weight / total_weight) * 100
            target_info.append(f"'{target.name}' ({weight_pct:.1f}%)")

        note = "Multi-objective optimization using desirability function. "
        note += f"Targets and weights: {', '.join(target_info)}. "
        note += "All targets are simultaneously optimized based on their relative weights."

        return note

    @staticmethod
    def calculate_desirability_weights(targets: List[Target]) -> Dict[str, float]:
        """
        Calculate normalized weights for desirability function.

        Args:
            targets: List of targets

        Returns:
            Dictionary mapping target names to normalized weights
        """
        if not targets:
            return {}

        # Get raw weights (default to 1.0 if not specified)
        raw_weights = {}
        for target in targets:
            weight = target.weight if target.weight is not None else 1.0
            raw_weights[target.name] = weight

        # Normalize weights to sum to 1.0
        total_weight = sum(raw_weights.values())
        if total_weight == 0:
            # All weights are zero, distribute equally
            equal_weight = 1.0 / len(targets)
            return {name: equal_weight for name in raw_weights.keys()}

        return {name: weight / total_weight for name, weight in raw_weights.items()}

    @staticmethod
    def explain_desirability_function(targets: List[Target]) -> str:
        """
        Generate an explanation of how the desirability function works.

        Args:
            targets: List of targets

        Returns:
            Detailed explanation string
        """
        if len(targets) <= 1:
            return "Single target optimization - no desirability function needed."

        explanation = "Desirability Function Explanation:\n\n"
        explanation += "The desirability function combines multiple targets into a single optimization score. "
        explanation += "Each target is transformed to a 0-1 scale where:\n"
        explanation += "- 1.0 = perfect achievement of the target\n"
        explanation += "- 0.0 = worst possible value for the target\n\n"

        explanation += "Target Details:\n"
        weights = ObjectiveConverter.calculate_desirability_weights(targets)

        for target in targets:
            weight_pct = weights[target.name] * 100
            explanation += f"• {target.name} ({target.mode}, weight: {weight_pct:.1f}%)\n"

            if target.mode.upper() == "MAX":
                explanation += "  Higher values are better\n"
            elif target.mode.upper() == "MIN":
                explanation += "  Lower values are better\n"
            elif target.mode.upper() == "MATCH":
                if target.min_value is not None and target.max_value is not None:
                    explanation += f"  Target range: {target.min_value} - {target.max_value}\n"
                else:
                    explanation += "  Target specific value\n"

        explanation += "\nFinal Score = Weighted geometric mean of individual desirabilities\n"
        explanation += "The optimizer maximizes this combined desirability score."

        return explanation
