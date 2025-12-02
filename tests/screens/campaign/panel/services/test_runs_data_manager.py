"""
Tests for the RunsDataManager service.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from app.models.campaign import Campaign, Target
from app.models.parameters.types import Categorical, ContinuousNumerical
from app.screens.campaign.panel.services.runs_data_manager import RunsDataManager


@pytest.fixture
def sample_campaign():
    """Create a sample campaign for testing."""
    campaign = Campaign()
    campaign.id = "test_campaign_123"
    campaign.name = "Test Campaign"
    campaign.description = "A test campaign"

    param1 = ContinuousNumerical("temperature", 20.0, 100.0)
    param2 = Categorical("solvent", ["water", "ethanol", "methanol"])

    campaign.parameters = [param1, param2]

    target = Target()
    target.name = "yield"
    target.mode = "MAX"
    campaign.targets = [target]

    return campaign


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir)
        # Create campaigns directory structure
        campaigns_dir = workspace_path / "campaigns"
        campaigns_dir.mkdir(exist_ok=True)
        yield str(workspace_path)


@pytest.fixture
def runs_manager(temp_workspace, sample_campaign):
    """Create a RunsDataManager for testing."""
    return RunsDataManager(temp_workspace, sample_campaign.id)


class TestRunsDataManager:
    """Tests for RunsDataManager class."""

    def test_initialization(self, runs_manager, temp_workspace, sample_campaign):
        """Test that the manager initializes correctly."""
        assert runs_manager.workspace_path == Path(temp_workspace)
        assert runs_manager.campaign_id == sample_campaign.id
        assert runs_manager.runs_file.parent.exists()

    def test_load_runs_empty(self, runs_manager):
        """Test loading runs when no data exists."""
        runs = runs_manager.load_runs()
        assert runs == []

    def test_save_and_load_runs(self, runs_manager):
        """Test saving and loading runs data."""
        sample_runs = [
            {
                "run_id": "test_run_1",
                "run_number": 1,
                "campaign_id": "test_campaign_123",
                "status": "completed",
                "experiments": [{"temperature": 25.0, "solvent": "water", "yield": 0.8}],
                "targets": [{"name": "yield", "mode": "MAX"}],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "experiment_count": 1,
                "completed_count": 1,
            }
        ]

        runs_manager.save_runs(sample_runs)
        loaded_runs = runs_manager.load_runs()

        assert len(loaded_runs) == 1
        assert loaded_runs[0]["run_id"] == "test_run_1"
        assert loaded_runs[0]["run_number"] == 1
        assert isinstance(loaded_runs[0]["created_at"], datetime)

    def test_add_run(self, runs_manager, sample_campaign):
        """Test adding a new run."""
        experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": None},
            {"temperature": 50.0, "solvent": "ethanol", "yield": None},
        ]

        run_number = runs_manager.add_run(experiments, sample_campaign)

        assert run_number == 1

        runs = runs_manager.load_runs()
        assert len(runs) == 1
        assert runs[0]["run_number"] == 1
        assert runs[0]["experiment_count"] == 2
        assert runs[0]["completed_count"] == 0
        assert len(runs[0]["experiments"]) == 2

    def test_add_multiple_runs(self, runs_manager, sample_campaign):
        """Test adding multiple runs."""
        experiments1 = [{"temperature": 25.0, "solvent": "water"}]
        experiments2 = [{"temperature": 50.0, "solvent": "ethanol"}]

        run_number1 = runs_manager.add_run(experiments1, sample_campaign)
        run_number2 = runs_manager.add_run(experiments2, sample_campaign)

        assert run_number1 == 1
        assert run_number2 == 2

        runs = runs_manager.load_runs()
        assert len(runs) == 2

    def test_update_run_experiments(self, runs_manager, sample_campaign):
        """Test updating experiments for a run."""
        experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": None},
            {"temperature": 50.0, "solvent": "ethanol", "yield": None},
        ]

        run_number = runs_manager.add_run(experiments, sample_campaign)

        # Update experiments with target values
        updated_experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": 0.8},
            {"temperature": 50.0, "solvent": "ethanol", "yield": 0.9},
        ]

        runs_manager.update_run_experiments(run_number, updated_experiments)

        runs = runs_manager.load_runs()
        assert len(runs) == 1
        assert runs[0]["completed_count"] == 2  # Both experiments now have target values
        assert runs[0]["experiments"][0]["yield"] == 0.8

    def test_get_run(self, runs_manager, sample_campaign):
        """Test getting a specific run."""
        experiments = [{"temperature": 25.0, "solvent": "water"}]
        run_number = runs_manager.add_run(experiments, sample_campaign)

        retrieved_run = runs_manager.get_run(run_number)

        assert retrieved_run is not None
        assert retrieved_run["run_number"] == run_number

    def test_get_run_nonexistent(self, runs_manager):
        """Test getting a non-existent run."""
        retrieved_run = runs_manager.get_run(999)
        assert retrieved_run is None

    def test_delete_run(self, runs_manager, sample_campaign):
        """Test deleting a run."""
        experiments1 = [{"temperature": 25.0, "solvent": "water"}]
        experiments2 = [{"temperature": 50.0, "solvent": "ethanol"}]
        experiments3 = [{"temperature": 75.0, "solvent": "methanol"}]

        runs_manager.add_run(experiments1, sample_campaign)
        runs_manager.add_run(experiments2, sample_campaign)
        runs_manager.add_run(experiments3, sample_campaign)

        # Delete the middle run
        runs_manager.delete_run(2)

        runs = runs_manager.load_runs()
        assert len(runs) == 2
        # Run numbers should be renumbered
        assert runs[0]["run_number"] == 1
        assert runs[1]["run_number"] == 2

    def test_get_run_count(self, runs_manager, sample_campaign):
        """Test getting the run count."""
        assert runs_manager.get_run_count() == 0

        experiments = [{"temperature": 25.0, "solvent": "water"}]
        runs_manager.add_run(experiments, sample_campaign)

        assert runs_manager.get_run_count() == 1

    def test_has_previous_data_false(self, runs_manager, sample_campaign):
        """Test has_previous_data returns False when no completed runs."""
        experiments = [{"temperature": 25.0, "solvent": "water", "yield": None}]
        runs_manager.add_run(experiments, sample_campaign)

        assert runs_manager.has_previous_data() is False

    def test_has_previous_data_true(self, runs_manager, sample_campaign):
        """Test has_previous_data returns True when completed runs exist."""
        experiments = [{"temperature": 25.0, "solvent": "water", "yield": None}]
        run_number = runs_manager.add_run(experiments, sample_campaign)

        # Update with target values
        updated_experiments = [{"temperature": 25.0, "solvent": "water", "yield": 0.8}]
        runs_manager.update_run_experiments(run_number, updated_experiments)

        assert runs_manager.has_previous_data() is True

    def test_load_runs_with_corrupted_json(self, runs_manager, monkeypatch):
        """Test loading runs when JSON file is corrupted."""
        captured = {}

        def fake_show_error(title, message, parent=None):
            captured["title"] = title
            captured["message"] = message
            captured["parent"] = parent

        # Patch the dialog method with a lightweight stub instead of a MagicMock
        monkeypatch.setattr(
            "app.screens.campaign.panel.services.runs_data_manager.ErrorDialog.show_error",
            fake_show_error,
        )

        # Corrupt the JSON file
        runs_manager.runs_file.parent.mkdir(exist_ok=True)
        runs_manager.runs_file.write_text("}{ invalid json :::", encoding="utf-8")

        runs = runs_manager.load_runs()

        # Should safely return empty list
        assert runs == []
        # Ensure our stub was invoked
        assert captured, "ErrorDialog.show_error was not called"
        assert captured["title"] == "Error loading runs data"
        assert "Expecting value" in captured["message"] or "Invalid" in captured["message"]
        assert captured["parent"] is None

    def test_datetime_serialization_deserialization(self, runs_manager, sample_campaign):
        """Test that datetime objects are properly serialized and deserialized."""

        runs_manager.add_run([{"temperature": 25.0, "solvent": "water"}], sample_campaign)

        # Load the raw JSON to verify datetime serialization
        with open(runs_manager.runs_file, "r") as f:
            raw_data = json.load(f)

        # Datetime should be serialized as ISO format string
        assert isinstance(raw_data[0]["created_at"], str)
        assert isinstance(raw_data[0]["updated_at"], str)

        # Load through manager should convert back to datetime
        runs = runs_manager.load_runs()
        assert isinstance(runs[0]["created_at"], datetime)
        assert isinstance(runs[0]["updated_at"], datetime)

    def test_completed_count_calculation(self, runs_manager, sample_campaign):
        """Test that completed_count is calculated correctly."""
        experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": None},
            {"temperature": 50.0, "solvent": "ethanol", "yield": 0.8},
            {"temperature": 75.0, "solvent": "methanol", "yield": None},
        ]

        run_number = runs_manager.add_run(experiments, sample_campaign)

        runs = runs_manager.load_runs()
        assert runs[0]["completed_count"] == 1  # Only one experiment has target value

        # Update to add more target values
        updated_experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": 0.9},  # Now has target
            {"temperature": 50.0, "solvent": "ethanol", "yield": 0.8},
            {"temperature": 75.0, "solvent": "methanol", "yield": None},
        ]

        runs_manager.update_run_experiments(run_number, updated_experiments)

        runs = runs_manager.load_runs()
        assert runs[0]["completed_count"] == 2  # Two experiments now have target values

    def test_completed_count_requires_all_targets(self, runs_manager, sample_campaign):
        """Completed experiments must contain every target value."""
        extra_target = Target()
        extra_target.name = "purity"
        extra_target.mode = "MAX"
        sample_campaign.targets.append(extra_target)

        experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": 0.8, "purity": None},
            {"temperature": 50.0, "solvent": "ethanol", "yield": 0.9, "purity": 0.95},
        ]

        run_number = runs_manager.add_run(experiments, sample_campaign)

        runs = runs_manager.load_runs()
        assert runs[0]["completed_count"] == 1  # Only second experiment has all targets
        assert runs[0]["status"] == "pending"

        updated_experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": 0.82, "purity": 0.91},
            {"temperature": 50.0, "solvent": "ethanol", "yield": 0.9, "purity": 0.95},
        ]

        runs_manager.update_run_experiments(run_number, updated_experiments)

        runs = runs_manager.load_runs()
        assert runs[0]["completed_count"] == 2
        assert runs[0]["status"] == "completed"

    def test_get_runs_missing_target_data(self, runs_manager, sample_campaign):
        """Runs missing target data should be reported until completed."""
        experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": None},
            {"temperature": 50.0, "solvent": "ethanol", "yield": None},
        ]

        run_number = runs_manager.add_run(experiments, sample_campaign)

        incomplete_runs = runs_manager.get_runs_missing_target_data()
        assert len(incomplete_runs) == 1
        assert incomplete_runs[0]["run_number"] == run_number

        updated_experiments = [
            {"temperature": 25.0, "solvent": "water", "yield": 0.8},
            {"temperature": 50.0, "solvent": "ethanol", "yield": 0.85},
        ]

        runs_manager.update_run_experiments(run_number, updated_experiments)

        assert runs_manager.get_runs_missing_target_data() == []
        latest_run = runs_manager.get_latest_run()
        assert latest_run
        assert latest_run["status"] == "completed"
