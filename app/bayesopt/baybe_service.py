"""
BayBe integration service for experiment generation and optimization.
"""

import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from baybe import Campaign as BayBeCampaign
from baybe.recommenders import (
    BotorchRecommender,
    RandomRecommender,
    TwoPhaseMetaRecommender,
)

from app.bayesopt.objective import ObjectiveConverter
from app.bayesopt.parameters import ParameterConverter
from app.bayesopt.surrogate import get_surrogate_model
from app.models.campaign import Campaign
from app.models.parameters.base import BaseParameter
from app.shared.constants import WorkspaceConstants


class BayBeIntegrationService:
    """Service for integrating with BayBe optimization library."""

    LOG_FOLDERNAME = "logs"
    RUNS_FOLDERNAME = "runs"
    LOG_FILENAME = "bayesian_generation.log"

    def __init__(self, campaign: Campaign, workspace_path: str):
        self.campaign = campaign
        self.workspace_path = workspace_path
        self.campaign_folder = Path(workspace_path) / WorkspaceConstants.CAMPAIGNS_DIRNAME / f"{self.campaign.id}"
        self.logger = self._setup_logging()
        self.baybe_campaign: Optional[BayBeCampaign] = None

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for BayBe operations."""
        logger = logging.getLogger("baybe_integration")
        logger.setLevel(logging.INFO)

        logs_dir = self.campaign_folder / self.LOG_FOLDERNAME
        logs_dir.mkdir(exist_ok=True)

        log_file = str(logs_dir / self.LOG_FILENAME)

        if not any(
            isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == log_file for h in logger.handlers
        ):
            # File handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)

            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
        return logger

    def generate_experiments(self, num_experiments: int, has_previous_data: bool = False) -> List[Dict[str, Any]]:
        """
        Generate experiments using BayBe.

        Args:
            num_experiments: Number of experiments to generate
            has_previous_data: Whether there is previous experimental data

        Returns:
            List of experiment dictionaries

        Raises:
            Exception: If experiment generation fails
        """
        self.logger.info(f"Starting generation of {num_experiments} experiments using BayBE")
        self.logger.info(f"Campaign: {self.campaign.name}")
        self.logger.info(f"Parameters: {len(self.campaign.parameters)}")
        self.logger.info(f"Targets: {len(self.campaign.targets)}")
        self.logger.info(f"Has previous data: {has_previous_data}")

        try:
            # Initialize or update BayBE campaign
            if not has_previous_data:
                self._initialize_baybe_campaign()
            else:
                self._update_baybe_campaign_from_file()

            if self.baybe_campaign is None:
                raise RuntimeError("BayBe campaign was not initialized")

            recommendations = self.baybe_campaign.recommend(batch_size=num_experiments)

            experiments = recommendations.to_dict("records")

            self.logger.info(f"Successfully generated {len(experiments)} experiments using BayBE")

            self._save_baybe_campaign_state()

            self.logger.info("Saved BayBE campaign state")

            return experiments

        except Exception as e:
            self.logger.error(f"Error generating experiments with BayBE: {str(e)}")
            return []

    def _save_baybe_campaign_state(self) -> None:
        """Save the current state of the BayBE campaign."""
        if self.baybe_campaign is None:
            raise RuntimeError("BayBe campaign was not initialized")
        else:
            try:
                self.logger.info("Saving BayBE campaign state")
                with open(self.campaign_folder / f"baybe_{self.campaign.id}.json", "w") as f:
                    json.dump(self.baybe_campaign.to_json(), f, ensure_ascii=False, indent=4)
            except Exception as e:
                self.logger.error(f"Error saving BayBE campaign state: {str(e)}")

    def _load_baybe_campaign_state(self) -> None:
        """Load the saved state of the BayBE campaign."""
        try:
            with open(self.campaign_folder / f"baybe_{self.campaign.id}.json", "r") as f:
                campaign_data = json.load(f)
                self.baybe_campaign = BayBeCampaign.from_json(campaign_data)
        except FileNotFoundError:
            self.logger.warning("No saved BayBE campaign state found")
        except Exception as e:
            self.logger.error(f"Error loading BayBE campaign state: {str(e)}")

    def _load_existing_experimental_data(self) -> Optional[pd.DataFrame]:
        """
        Load existing experimental data from campaign folder.

        Returns:
            DataFrame with existing experimental data, or None if not found
        """
        try:
            runs_dir = self.campaign_folder / self.RUNS_FOLDERNAME
            if not runs_dir.exists():
                return None

            csv_files = list(runs_dir.glob("*.csv"))
            if not csv_files:
                return None

            # Use the most recent CSV file in runs folder
            latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
            self.logger.info(f"Loading data from: {latest_file}")

            df = pd.read_csv(latest_file)

            target_names = ObjectiveConverter.get_target_names(self.campaign.targets)
            missing_targets = [name for name in target_names if name not in df.columns]

            if missing_targets:
                self.logger.warning(f"Missing target columns in data: {missing_targets}")
                for target_name in missing_targets:
                    df[target_name] = None

            return df

        except Exception as e:
            self.logger.error(f"Error loading existing data: {str(e)}")
            return None

    def _initialize_baybe_campaign(self) -> None:
        """Initialize a new BayBE campaign."""
        self.logger.info("Initializing new BayBE campaign")

        # Validate campaign configuration
        validation_errors = self._validate_campaign()
        if validation_errors:
            raise ValueError(f"Campaign validation failed: {'; '.join(validation_errors)}")

        # Convert parameters to BayBE search space
        search_space = ParameterConverter.create_search_space(self.campaign.parameters)
        self.logger.info(f"Created search space with {len(search_space.parameters)} parameters")

        # Convert targets to BayBE objective
        objective = ObjectiveConverter.create_objective(self.campaign.targets)

        # Log objective information
        if len(self.campaign.targets) == 1:
            self.logger.info(f"Created single-target objective: {self.campaign.targets[0].name}")
        else:
            self.logger.info(f"Created desirability objective with {len(self.campaign.targets)} targets")
            weights = ObjectiveConverter.calculate_desirability_weights(self.campaign.targets)
            for target_name, weight in weights.items():
                self.logger.info(f"  - {target_name}: {weight:.3f} weight ({weight * 100:.1f}%)")

        # Log multi-objective note if applicable
        multi_obj_note = ObjectiveConverter.create_multi_objective_note(self.campaign.targets)
        if multi_obj_note:
            self.logger.info(multi_obj_note)

        bo_recommender = TwoPhaseMetaRecommender(
            initial_recommender=RandomRecommender(),
            recommender=BotorchRecommender(
                surrogate_model=get_surrogate_model(self.campaign),
                acquisition_function=self.campaign.acquisition_function,
            ),
        )

        self.baybe_campaign = BayBeCampaign(searchspace=search_space, objective=objective, recommender=bo_recommender)

    def _update_baybe_campaign_from_file(self) -> None:
        """Load BayBE campaign from saved state file."""
        self.logger.info("Loading BayBE campaign from saved state file")
        self._load_baybe_campaign_state()

        latest_data = self._load_existing_experimental_data()
        if latest_data is not None and self.baybe_campaign is not None:
            self.logger.info(f"Updating BayBE campaign with {len(latest_data)} existing data points")
            try:
                self.baybe_campaign.add_measurements(latest_data, numerical_measurements_must_be_within_tolerance=False)
                self.logger.info("Successfully updateds BayBE campaign with existing data")
            except Exception as e:
                self.logger.error(f"Error adding measurements to BayBE campaign: {str(e)}")
        if self.baybe_campaign is None:
            raise RuntimeError("Failed to load BayBe campaign from file")

    def _validate_campaign(self) -> List[str]:
        """
        Validate campaign configuration for BayBE.

        Returns:
            List of validation error messages
        """
        errors = []

        # Check parameters
        if not self.campaign.parameters:
            errors.append("No parameters defined")
        else:
            # Validate individual parameters
            valid_params = 0
            for param in self.campaign.parameters:
                if ParameterConverter.validate_parameter_constraints(param):
                    valid_params += 1
                else:
                    errors.append(f"Invalid parameter configuration: {param.name}")

            if valid_params == 0:
                errors.append("No valid parameters for optimization")

        target_errors = ObjectiveConverter.validate_targets(self.campaign.targets)
        errors.extend(target_errors)

        return errors

    def _generate_random_experiments(self, num_experiments: int) -> List[Dict[str, Any]]:
        """
        Fallback method to generate random experiments when BayBE fails.

        Args:
            num_experiments: Number of experiments to generate

        Returns:
            List of experiment dictionaries
        """
        self.logger.info(f"Generating {num_experiments} random experiments as fallback")

        experiments = []
        for i in range(num_experiments):
            experiment = {}
            for param in self.campaign.parameters:
                experiment[param.name] = self._generate_random_parameter_value(param)
            experiments.append(experiment)

        return experiments

    def _generate_random_parameter_value(self, parameter: BaseParameter) -> Any:
        """
        Generate a random value for a parameter.
        This is a mock implementation - replace with BayBe logic.
        """
        param_type = getattr(parameter, "type", "numerical")

        if param_type == "numerical":
            min_val = getattr(parameter, "min_value", 0.0)
            max_val = getattr(parameter, "max_value", 100.0)
            return round(random.uniform(min_val, max_val), 3)

        elif param_type == "categorical":
            categories = getattr(parameter, "values", ["A", "B", "C"])
            return random.choice(categories)

        elif param_type == "integer":
            min_val = int(getattr(parameter, "min_value", 1))
            max_val = int(getattr(parameter, "max_value", 100))
            return random.randint(min_val, max_val)

        else:
            return random.uniform(0, 100)

    def get_log_file_path(self) -> Path:
        """Get the path to the BayBe log file."""
        return self.campaign_folder / self.LOG_FOLDERNAME / self.LOG_FILENAME

    def get_last_log_update_time(self) -> Optional[datetime]:
        """Get the last modification time of the log file."""
        log_file = self.get_log_file_path()
        if log_file.exists():
            timestamp = log_file.stat().st_mtime
            return datetime.fromtimestamp(timestamp)
        return None

    def get_campaign_info(self) -> Dict[str, Any]:
        """
        Get information about the BayBE campaign status.

        Returns:
            Dictionary with campaign information
        """
        info = {
            "campaign_initialized": self.baybe_campaign is not None,
            "parameter_count": len(self.campaign.parameters),
            "target_count": len(self.campaign.targets),
            "valid_parameters": 0,
            "validation_errors": [],
        }

        # Count valid parameters
        for param in self.campaign.parameters:
            if ParameterConverter.validate_parameter_constraints(param):
                info["valid_parameters"] += 1

        # Get validation errors
        info["validation_errors"] = self._validate_campaign()

        if self.baybe_campaign is not None:
            # Add BayBE-specific information
            try:
                info["measurements_count"] = len(self.baybe_campaign.measurements)
            except Exception as e:
                self.logger.error(f"Error retrieving measurements count: {str(e)}")
                info["measurements_count"] = 0

        return info

    def get_desirability_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the desirability function if using multi-objective optimization.

        Returns:
            Dictionary with desirability information, or None if single-objective
        """
        if len(self.campaign.targets) <= 1:
            return None

        weights = ObjectiveConverter.calculate_desirability_weights(self.campaign.targets)
        explanation = ObjectiveConverter.explain_desirability_function(self.campaign.targets)

        return {
            "target_count": len(self.campaign.targets),
            "target_weights": weights,
            "explanation": explanation,
            "targets": [
                {
                    "name": target.name,
                    "mode": target.mode,
                    "weight": target.weight,
                    "normalized_weight": weights[target.name],
                }
                for target in self.campaign.targets
            ],
        }


class BayBeService(BayBeIntegrationService):
    """
    Main BayBe service for production use.
    Inherits from BayBeIntegrationService and can be extended with production-specific logic.
    """

    pass


class MockBayBeService(BayBeIntegrationService):
    """
    Mock BayBe service for development and testing.
    Uses the real BayBE implementation but adds simulated delays and fallback behavior.
    """

    def generate_experiments(self, num_experiments: int, has_previous_data: bool = False) -> List[Dict[str, Any]]:
        """
        Generate experiments with simulated processing time and fallback to random if BayBE fails.
        """
        import time

        self.logger.info("Using Mock BayBe Service for development")

        # Simulate processing time (faster for first run, slower for subsequent)
        if not has_previous_data:
            # First run is quick
            time.sleep(0.5)
        else:
            # Subsequent runs take longer (optimization)
            time.sleep(1 + (num_experiments * 0.05))

        try:
            # Try to use real BayBE implementation
            return super().generate_experiments(num_experiments, has_previous_data)
        except Exception as e:
            self.logger.warning(f"BayBE failed, using random generation: {str(e)}")
            # Always fall back to random generation in mock mode
            return self._generate_random_experiments(num_experiments)
