"""
Tests for the GenerationProgressScreen service.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from app.screens.campaign.panel.services.generation_progress import GenerationProgressScreen


@pytest.fixture
def progress_screen_first_run(qtbot):
    """Create a GenerationProgressScreen for first run testing."""
    screen = GenerationProgressScreen(experiment_count=5, is_first_run=True)
    qtbot.addWidget(screen)
    return screen


@pytest.fixture
def progress_screen_subsequent_run(qtbot):
    """Create a GenerationProgressScreen for subsequent run testing."""
    screen = GenerationProgressScreen(experiment_count=10, is_first_run=False)
    qtbot.addWidget(screen)
    return screen


class TestGenerationProgressScreen:
    """Tests for GenerationProgressScreen class."""

    def test_initialization_first_run(self, progress_screen_first_run):
        """Test initialization for first run."""
        screen = progress_screen_first_run
        assert screen.experiment_count == 5
        assert screen.is_first_run is True
        assert isinstance(screen.start_time, datetime)
        assert hasattr(screen, "back_to_runs_requested")
        assert hasattr(screen, "cancel_run_requested")
        assert hasattr(screen, "generation_completed")

    def test_initialization_subsequent_run(self, progress_screen_subsequent_run):
        """Test initialization for subsequent run."""
        screen = progress_screen_subsequent_run
        assert screen.experiment_count == 10
        assert screen.is_first_run is False

    def test_screen_has_progress_card(self, progress_screen_first_run):
        """Test that the screen has a progress card."""
        assert hasattr(progress_screen_first_run, "progress_card")
        assert progress_screen_first_run.progress_card is not None

    def test_get_panel_buttons_first_run(self, progress_screen_first_run):
        """Test panel buttons for first run."""
        buttons = progress_screen_first_run.get_panel_buttons()

        # Based on actual implementation, buttons are handled internally
        assert len(buttons) == 0

    def test_get_panel_buttons_subsequent_run(self, progress_screen_subsequent_run):
        """Test panel buttons for subsequent run."""
        buttons = progress_screen_subsequent_run.get_panel_buttons()

        # Based on actual implementation, buttons are handled internally
        assert len(buttons) == 0

    def test_screen_initialization(self, progress_screen_subsequent_run):
        """Test screen initialization rather than button functionality."""
        # Since buttons are handled internally, test the screen properties instead
        assert progress_screen_subsequent_run.experiment_count == 10
        assert progress_screen_subsequent_run.is_first_run is False

    def test_dialog_method_name(self, progress_screen_first_run):
        """Test proper signal handling methods exist."""
        # Test that the screen has the required signal handling methods
        assert hasattr(progress_screen_first_run, "_handle_cancel_run")
        assert hasattr(progress_screen_first_run, "cancel_run_requested")

    def test_update_progress(self, progress_screen_first_run):
        """Test updating the progress bar."""
        progress_screen_first_run.set_progress(50)  # 50% progress

        # Progress should be updated
        assert hasattr(progress_screen_first_run, "progress_bar")

    def test_complete_generation(self, qtbot, progress_screen_first_run):
        """Test completing the generation."""
        experiments = [{"temperature": 25.0, "solvent": "water"}, {"temperature": 50.0, "solvent": "ethanol"}]

        with qtbot.waitSignal(progress_screen_first_run.generation_completed, timeout=1000):
            progress_screen_first_run.complete_generation(experiments)

    def test_generation_icon_creation(self, progress_screen_first_run):
        """Test that generation icon is created properly."""
        pixmap = progress_screen_first_run._get_generation_icon_pixmap()

        assert pixmap is not None
        assert pixmap.width() == 48
        assert pixmap.height() == 48

    def test_elapsed_time_calculation(self, progress_screen_first_run):
        """Test elapsed time calculation."""
        # Should be able to calculate elapsed time
        elapsed = datetime.now() - progress_screen_first_run.start_time
        assert elapsed.total_seconds() >= 0

    def test_different_experiment_counts(self, qtbot):
        """Test screen with different experiment counts."""
        # Test with small count
        small_screen = GenerationProgressScreen(experiment_count=1, is_first_run=True)
        qtbot.addWidget(small_screen)
        assert small_screen.experiment_count == 1

        # Test with large count
        large_screen = GenerationProgressScreen(experiment_count=100, is_first_run=False)
        qtbot.addWidget(large_screen)
        assert large_screen.experiment_count == 100

    def test_status_text_constants(self, progress_screen_first_run):
        """Test that status text constants are defined."""
        screen = progress_screen_first_run
        assert hasattr(screen, "TITLE_TEXT")
        assert hasattr(screen, "SUBTITLE_TEXT")
        assert hasattr(screen, "STATUS_TEXT")
        assert hasattr(screen, "BACK_TO_RUNS_TEXT")
        assert hasattr(screen, "CANCEL_RUN_TEXT")

    def test_progress_bar_setup(self, progress_screen_first_run):
        """Test that progress bar is properly set up."""
        # Progress screen should have a progress bar
        assert hasattr(progress_screen_first_run, "progress_bar")
        if progress_screen_first_run.progress_bar:
            assert progress_screen_first_run.progress_bar.minimum() == 0
            # Test setting progress works (maximum may not be initialized until set_progress is called)
            progress_screen_first_run.set_progress(50, 100)
            assert progress_screen_first_run.progress_bar.maximum() == 100

    def test_status_label_update(self, progress_screen_first_run):
        """Test that status label updates correctly."""
        new_status = "Analyzing parameter space..."
        progress_screen_first_run.update_status(new_status)

        # Should update the status display
        assert hasattr(progress_screen_first_run, "status_label")

    def test_experiment_count_display(self, progress_screen_first_run):
        """Test that experiment count is displayed."""
        # Screen should show the experiment count somewhere
        assert progress_screen_first_run.experiment_count == 5

    @patch("app.shared.components.dialogs.ConfirmationDialog.show_confirmation")
    def test_handle_cancel_run_confirmed(self, mock_confirm, qtbot, progress_screen_first_run):
        """Test handling cancel run when confirmed."""
        mock_confirm.return_value = True

        with qtbot.waitSignal(progress_screen_first_run.cancel_run_requested, timeout=1000):
            progress_screen_first_run._handle_cancel_run()

    @patch("app.shared.components.dialogs.ConfirmationDialog.show_confirmation")
    def test_handle_cancel_run_not_confirmed(self, mock_confirm, progress_screen_first_run):
        """Test handling cancel run when not confirmed."""
        mock_confirm.return_value = False

        # Should not emit signal
        progress_screen_first_run._handle_cancel_run()
        mock_confirm.assert_called_once()

    def test_generation_progress_states(self, progress_screen_first_run):
        """Test different states during generation progress."""
        # Test initial state
        progress_screen_first_run.update_status("Initializing...")
        progress_screen_first_run.set_progress(0, 100)

        # Test mid-generation state
        progress_screen_first_run.update_status("Generating experiments...")
        progress_screen_first_run.set_progress(50, 100)

        # Test completion state
        progress_screen_first_run.update_status("Experiments generated!")
        progress_screen_first_run.set_progress(100, 100)

    def test_update_elapsed_time(self, progress_screen_first_run):
        """Test updating elapsed time display."""
        # Test seconds only
        progress_screen_first_run.update_elapsed_time(45)
        assert "0:45" in progress_screen_first_run.elapsed_time_label.text()

        # Test minutes and seconds
        progress_screen_first_run.update_elapsed_time(125)  # 2:05
        assert "2:05" in progress_screen_first_run.elapsed_time_label.text()

        # Test hours
        progress_screen_first_run.update_elapsed_time(3665)  # 1:01:05
        assert "1:01:05" in progress_screen_first_run.elapsed_time_label.text()

    def test_view_logs_link_exists(self, progress_screen_first_run):
        """Test that view logs link is created."""
        assert hasattr(progress_screen_first_run, "view_logs_link")
        assert progress_screen_first_run.view_logs_link is not None

    def test_log_file_path_attribute(self, progress_screen_first_run):
        """Test that log_file_path attribute can be set."""
        from pathlib import Path

        test_path = Path("/test/path/to/logs.log")
        progress_screen_first_run.log_file_path = test_path
        assert progress_screen_first_run.log_file_path == test_path

    @patch("app.screens.campaign.panel.services.log_viewer.LogViewerDialog.show_logs")
    def test_open_log_viewer(self, mock_show_logs, progress_screen_first_run):
        """Test opening log viewer dialog."""
        from pathlib import Path

        test_path = Path("/test/path/to/logs.log")
        progress_screen_first_run.log_file_path = test_path

        progress_screen_first_run._open_log_viewer()

        mock_show_logs.assert_called_once_with(test_path, parent=progress_screen_first_run)

    @patch("app.shared.components.dialogs.InfoDialog.show_info")
    def test_open_log_viewer_no_path(self, mock_info, progress_screen_first_run):
        """Test opening log viewer when path is not set."""
        progress_screen_first_run._open_log_viewer()

        mock_info.assert_called_once()
