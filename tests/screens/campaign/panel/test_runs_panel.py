"""
Tests for the RunsPanel functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt

from app.models.campaign import Campaign, Target
from app.models.parameters.types import Categorical, ContinuousNumerical
from app.screens.campaign.panel.runs_panel import ExperimentGenerationWorker, RunsPanel


@pytest.fixture
def sample_campaign():
    """Create a sample campaign for testing."""
    campaign = Campaign()
    campaign.id = "test_campaign_123"
    campaign.name = "Test Campaign"
    campaign.description = "A test campaign"

    # Add parameters
    param1 = ContinuousNumerical("temperature", 20.0, 100.0)
    param2 = Categorical("solvent", ["water", "ethanol", "methanol"])

    campaign.parameters = [param1, param2]

    # Add targets
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
def runs_panel(qtbot, sample_campaign, temp_workspace):
    """Create a RunsPanel for testing."""
    panel = RunsPanel(sample_campaign, temp_workspace)
    qtbot.addWidget(panel)
    return panel


def test_runs_panel_creation(runs_panel):
    """Test that the runs panel is created correctly."""
    assert runs_panel is not None
    assert hasattr(runs_panel, "main_layout")
    assert hasattr(runs_panel, "stacked_widget")
    assert hasattr(runs_panel, "runs_manager")
    assert runs_panel.current_state == RunsPanel.EMPTY_STATE


def test_runs_panel_has_empty_state(runs_panel):
    """Test that the runs panel displays an empty state initially."""
    # The panel should have widgets (empty state card)
    assert runs_panel.main_layout.count() > 0
    assert runs_panel.stacked_widget.count() > 0
    assert runs_panel.current_state == RunsPanel.EMPTY_STATE


def test_runs_panel_signal_exists(runs_panel):
    """Test that the runs panel has the required signal."""
    assert hasattr(runs_panel, "new_run_requested")


def test_new_run_signal_emission(qtbot, runs_panel):
    """Test that the new run signal can be emitted."""
    with qtbot.waitSignal(runs_panel.new_run_requested, timeout=1000):
        runs_panel.new_run_requested.emit()


def test_get_panel_buttons_returns_generate_button_empty_state(runs_panel):
    """Test that get_panel_buttons returns the Generate New Run button in empty state."""
    buttons = runs_panel.get_panel_buttons()

    assert len(buttons) == 1
    assert buttons[0].text() == "Generate New Run"


def test_get_panel_buttons_returns_generate_button_experiments_table_state(runs_panel):
    """Test that get_panel_buttons returns the Generate New Run button in experiments table state."""
    # Switch to experiments table state
    sample_experiments = [
        {"temperature": 25.0, "solvent": "water", "yield": None},
        {"temperature": 50.0, "solvent": "ethanol", "yield": None},
    ]
    runs_panel._switch_to_experiments_table_state(sample_experiments, 1)

    buttons = runs_panel.get_panel_buttons()
    assert len(buttons) == 1
    assert buttons[0].text() == "Generate New Run"


@patch("app.shared.components.dialogs.GenerateExperimentsDialog.get_experiment_count_from_user")
def test_handle_generate_new_run_accepted(mock_dialog, qtbot, runs_panel):
    """Test handling of new run generation when dialog is accepted."""
    mock_dialog.return_value = (True, 5)  # accepted=True, count=5

    # Mock the generation method to avoid actual background processing
    with patch.object(runs_panel, "_start_experiment_generation") as mock_start:
        runs_panel._handle_generate_new_run()

        # Should switch to generation progress state
        assert runs_panel.current_state == RunsPanel.GENERATION_PROGRESS_STATE
        assert runs_panel.generation_progress_widget is not None
        mock_start.assert_called_once_with(5, False)  # has_previous_data should be False initially


@patch("app.shared.components.dialogs.GenerateExperimentsDialog.get_experiment_count_from_user")
def test_handle_generate_new_run_cancelled(mock_dialog, qtbot, runs_panel):
    """Test handling of new run generation when dialog is cancelled."""
    mock_dialog.return_value = (False, 0)  # accepted=False, count=0

    initial_state = runs_panel.current_state
    runs_panel._handle_generate_new_run()

    # State should remain unchanged
    assert runs_panel.current_state == initial_state


def test_switch_to_runs_list_state(runs_panel):
    """Test switching to runs list state."""
    sample_runs_data = [
        {"run_number": 1, "experiments": [{"temperature": 25.0, "solvent": "water"}], "status": "completed"}
    ]

    runs_panel._switch_to_runs_list_state(sample_runs_data)

    assert runs_panel.current_state == RunsPanel.RUNS_LIST_STATE
    assert runs_panel.runs_list_widget is not None


def test_switch_to_experiments_table_state(runs_panel):
    """Test switching to experiments table state."""
    sample_experiments = [
        {"temperature": 25.0, "solvent": "water", "yield": None},
        {"temperature": 50.0, "solvent": "ethanol", "yield": None},
    ]

    runs_panel._switch_to_experiments_table_state(sample_experiments, 1)

    assert runs_panel.current_state == RunsPanel.EXPERIMENTS_TABLE_STATE
    assert runs_panel.experiments_table_widget is not None


def test_switch_to_generation_progress_state(runs_panel):
    """Test switching to generation progress state."""
    runs_panel._switch_to_generation_progress_state(5, True)

    assert runs_panel.current_state == RunsPanel.GENERATION_PROGRESS_STATE
    assert runs_panel.generation_progress_widget is not None


def test_handle_run_selected(runs_panel):
    """Test handling of run selection."""
    # First add some test data to the data manager
    sample_experiments = [{"temperature": 25.0, "solvent": "water", "yield": 0.8}]
    run_number = runs_panel.runs_manager.add_run(sample_experiments, runs_panel.campaign)

    runs_panel._handle_run_selected(run_number)

    assert runs_panel.current_state == RunsPanel.EXPERIMENTS_TABLE_STATE
    assert runs_panel.current_run_number == run_number


def test_handle_back_to_runs_with_data(runs_panel):
    """Test handling back to runs when there's data."""
    # Add some test data
    sample_experiments = [{"temperature": 25.0, "solvent": "water", "yield": 0.8}]
    runs_panel.runs_manager.add_run(sample_experiments, runs_panel.campaign)

    runs_panel._handle_back_to_runs()

    assert runs_panel.current_state == RunsPanel.RUNS_LIST_STATE


def test_handle_back_to_runs_no_data(runs_panel):
    """Test handling back to runs when there's no data."""
    runs_panel._handle_back_to_runs()

    assert runs_panel.current_state == RunsPanel.EMPTY_STATE


def test_handle_save_results(runs_panel):
    """Test handling of save results without creating a real modal dialog."""
    sample_experiments = [{"temperature": 25.0, "solvent": "water", "yield": 0.8}]
    run_number = runs_panel.runs_manager.add_run(sample_experiments, runs_panel.campaign)
    runs_panel.current_run_number = run_number

    updated_experiments = [{"temperature": 25.0, "solvent": "water", "yield": 0.9}]

    # Patch both the data update and the info dialog to avoid GUI modal exec (causes 0x8001010d in headless/CI)
    with (
        patch.object(runs_panel.runs_manager, "update_run_experiments") as mock_update,
        patch("app.shared.components.dialogs.InfoDialog.show_info") as mock_info,
    ):
        runs_panel._handle_save_results(updated_experiments)
        mock_update.assert_called_once_with(run_number, updated_experiments)
        mock_info.assert_called_once()


def test_generate_button_emits_signal(qtbot, runs_panel):
    """Test that clicking the generate button emits the signal."""
    buttons = runs_panel.get_panel_buttons()
    generate_button = buttons[0]

    with patch("app.shared.components.dialogs.GenerateExperimentsDialog.get_experiment_count_from_user") as mock_dialog:
        mock_dialog.return_value = (True, 5)
        with patch.object(runs_panel, "_start_experiment_generation"):
            qtbot.mouseClick(generate_button, Qt.LeftButton)
            mock_dialog.assert_called_once()


def test_clock_icon_creation(runs_panel):
    """Test that the clock icon is created properly."""
    pixmap = runs_panel._get_clock_icon_pixmap()

    assert pixmap is not None
    assert pixmap.width() == 48
    assert pixmap.height() == 48


def test_handle_log_path_ready(runs_panel):
    """Test handling of log path ready signal."""
    # Create generation progress widget
    runs_panel._switch_to_generation_progress_state(5, True)

    test_log_path = Path("/test/path/to/logs/bayesian_generation.log")

    # Handle log path ready
    runs_panel._handle_log_path_ready(test_log_path)

    # Verify the log path was set
    assert runs_panel.generation_progress_widget.log_file_path == test_log_path


# Test ExperimentGenerationWorker
class TestExperimentGenerationWorker:
    """Tests for the ExperimentGenerationWorker class."""

    @pytest.fixture
    def worker(self, sample_campaign, temp_workspace):
        """Create a worker for testing."""
        return ExperimentGenerationWorker(sample_campaign, temp_workspace, 5, False)

    def test_worker_creation(self, worker):
        """Test that the worker is created correctly."""
        assert worker.campaign is not None
        assert worker.num_experiments == 5
        assert worker.has_previous_data is False
        assert worker.should_cancel is False

    def test_worker_cancel(self, worker):
        """Test that the worker can be cancelled."""
        worker.cancel()
        assert worker.should_cancel is True

    # @patch("app.bayesopt.baybe_service.MockBayBeService")
    # def test_worker_run_success(self, mock_baybe_service, qtbot, worker):
    #     """Test successful experiment generation."""
    #     mock_service_instance = Mock()
    #     mock_service_instance.generate_experiments.return_value = [
    #         {"temperature": 25.0, "solvent": "water"},
    #         {"temperature": 50.0, "solvent": "ethanol"},
    #     ]
    #     mock_baybe_service.return_value = mock_service_instance

    #     # Connect the worker to a QThread and start it
    #     thread = QThread()
    #     worker.moveToThread(thread)
    #     thread.started.connect(worker.run)

    #     with qtbot.waitSignal(worker.generation_completed, timeout=5000):
    #         thread.start()

    #     thread.quit()
    #     thread.wait()

    # @patch("app.bayesopt.baybe_service.MockBayBeService")
    # def test_worker_run_failure(self, mock_baybe_service, qtbot, worker):
    #     """Test failed experiment generation."""
    #     mock_baybe_service.side_effect = Exception("Generation failed")

    #     thread = QThread()
    #     worker.moveToThread(thread)
    #     thread.started.connect(worker.run)

    #     with qtbot.waitSignal(worker.generation_failed, timeout=5000) as blocker:
    #         thread.start()

    #     assert "Generation failed" in blocker.args[0]

    #     thread.quit()
    #     thread.wait()

    # @patch("app.bayesopt.baybe_service.MockBayBeService")
    # def test_worker_run_cancelled_early(self, mock_baybe_service, worker):
    #     """Test that worker stops early if cancelled."""
    #     worker.cancel()

    #     # Should return early without doing anything
    #     worker.run()

    #     mock_baybe_service.assert_not_called()
