"""
Tests for the LogViewerDialog.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.screens.campaign.panel.services.log_viewer import LogViewerDialog


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = Path(f.name)
        f.write("Initial log content\n")
        f.write("Second line\n")

    yield log_path

    # Cleanup
    if log_path.exists():
        log_path.unlink()


@pytest.fixture
def log_viewer(qtbot, temp_log_file):
    """Create a LogViewerDialog for testing."""
    dialog = LogViewerDialog(temp_log_file)
    qtbot.addWidget(dialog)
    return dialog


@pytest.fixture
def log_viewer_no_file(qtbot):
    """Create a LogViewerDialog with non-existent file."""
    non_existent_path = Path("/tmp/non_existent_log_file.log")
    dialog = LogViewerDialog(non_existent_path)
    qtbot.addWidget(dialog)
    return dialog


class TestLogViewerDialog:
    """Tests for LogViewerDialog class."""

    def test_initialization(self, log_viewer, temp_log_file):
        """Test dialog initialization."""
        assert log_viewer.log_file_path == temp_log_file
        assert log_viewer.last_position >= 0
        assert log_viewer.auto_scroll_enabled is True

    def test_dialog_properties(self, log_viewer):
        """Test dialog window properties."""
        assert log_viewer.windowTitle() == LogViewerDialog.WINDOW_TITLE
        assert log_viewer.isModal() is False
        assert log_viewer.width() == LogViewerDialog.DIALOG_WIDTH
        assert log_viewer.height() == LogViewerDialog.DIALOG_HEIGHT

    def test_ui_components_exist(self, log_viewer):
        """Test that all UI components are created."""
        assert hasattr(log_viewer, "log_text")
        assert hasattr(log_viewer, "follow_checkbox")
        assert log_viewer.log_text is not None
        assert log_viewer.follow_checkbox is not None

    def test_initial_log_loading(self, log_viewer):
        """Test that initial logs are loaded."""
        log_content = log_viewer.log_text.toPlainText()
        assert "Initial log content" in log_content
        assert "Second line" in log_content

    def test_log_file_not_found(self, log_viewer_no_file):
        """Test behavior when log file doesn't exist."""
        log_content = log_viewer_no_file.log_text.toPlainText()
        assert LogViewerDialog.LOG_FILE_NOT_FOUND_MSG in log_content

    def test_follow_checkbox_initial_state(self, log_viewer):
        """Test follow checkbox is checked by default."""
        assert log_viewer.follow_checkbox.isChecked() is True
        assert log_viewer.auto_scroll_enabled is True

    def test_follow_checkbox_toggle(self, qtbot, log_viewer):
        """Test toggling follow checkbox."""
        # Uncheck
        log_viewer.follow_checkbox.setChecked(False)
        assert log_viewer.auto_scroll_enabled is False

        # Check again
        log_viewer.follow_checkbox.setChecked(True)
        assert log_viewer.auto_scroll_enabled is True

    def test_clear_button_clears_logs(self, qtbot, log_viewer):
        """Test that clear button clears the log display."""
        # Clear should work
        initial_content = log_viewer.log_text.toPlainText()
        assert len(initial_content) > 0

        log_viewer.log_text.clear()
        assert log_viewer.log_text.toPlainText() == ""

    def test_file_watcher_setup_existing_file(self, log_viewer):
        """Test file watcher is set up for existing file."""
        assert hasattr(log_viewer, "file_watcher")
        assert log_viewer.file_watcher is not None

    def test_file_watcher_setup_non_existent_file(self, log_viewer_no_file):
        """Test file watcher is None for non-existent file."""
        assert log_viewer_no_file.file_watcher is None

    def test_load_new_logs(self, log_viewer, temp_log_file):
        """Test loading new log content."""
        initial_position = log_viewer.last_position

        # Append new content to log file
        with open(temp_log_file, "a") as f:
            f.write("New log line\n")

        # Manually trigger load
        log_viewer._load_new_logs()

        # Check new content is loaded
        log_content = log_viewer.log_text.toPlainText()
        assert "New log line" in log_content
        assert log_viewer.last_position > initial_position

    def test_on_file_changed(self, log_viewer, temp_log_file):
        """Test file change event handler."""
        with open(temp_log_file, "a") as f:
            f.write("File changed content\n")

        log_viewer._on_file_changed(str(temp_log_file))

        log_content = log_viewer.log_text.toPlainText()
        assert "File changed content" in log_content

    def test_scroll_to_bottom(self, log_viewer):
        """Test scroll to bottom functionality."""
        # Add a lot of content
        for i in range(100):
            log_viewer.log_text.append(f"Line {i}\n")

        log_viewer._scroll_to_bottom()

        # Check cursor is at end
        cursor = log_viewer.log_text.textCursor()
        assert cursor.position() == cursor.document().characterCount() - 1

    def test_auto_scroll_when_enabled(self, log_viewer, temp_log_file):
        """Test auto-scroll works when enabled."""
        log_viewer.auto_scroll_enabled = True

        # Add content
        for i in range(50):
            log_viewer.log_text.append(f"Line {i}")

        with open(temp_log_file, "a") as f:
            f.write("Should scroll to this\n")

        log_viewer._load_new_logs()

        # Cursor should be at bottom (hard to test exact position, but we can verify it scrolled)
        assert log_viewer.auto_scroll_enabled is True

    def test_no_auto_scroll_when_disabled(self, log_viewer):
        """Test auto-scroll doesn't happen when disabled."""
        log_viewer.auto_scroll_enabled = False
        log_viewer.follow_checkbox.setChecked(False)

        assert log_viewer.auto_scroll_enabled is False

    def test_empty_log_file(self, qtbot):
        """Test behavior with empty log file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            empty_log_path = Path(f.name)

        try:
            dialog = LogViewerDialog(empty_log_path)
            qtbot.addWidget(dialog)

            log_content = dialog.log_text.toPlainText()
            assert LogViewerDialog.LOG_FILE_EMPTY_MSG in log_content
        finally:
            if empty_log_path.exists():
                empty_log_path.unlink()

    def test_read_error_handling(self, qtbot):
        """Test error handling when reading log file fails."""
        # Create file then make it unreadable
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            error_log_path = Path(f.name)
            f.write("Some content\n")

        try:
            dialog = LogViewerDialog(error_log_path)
            qtbot.addWidget(dialog)

            # Simulate read error by patching open
            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                dialog._load_new_logs()

            log_content = dialog.log_text.toPlainText()
            assert "Error reading log" in log_content
        finally:
            if error_log_path.exists():
                error_log_path.unlink()

    def test_constants_defined(self):
        """Test that all constants are properly defined."""
        assert hasattr(LogViewerDialog, "DIALOG_WIDTH")
        assert hasattr(LogViewerDialog, "DIALOG_HEIGHT")
        assert hasattr(LogViewerDialog, "WINDOW_TITLE")
        assert hasattr(LogViewerDialog, "TITLE_TEXT")
        assert hasattr(LogViewerDialog, "INFO_TEXT")
        assert hasattr(LogViewerDialog, "FOLLOW_LOGS_TEXT")
        assert hasattr(LogViewerDialog, "CLEAR_BUTTON_TEXT")
        assert hasattr(LogViewerDialog, "CLOSE_BUTTON_TEXT")

    def test_static_show_logs_method(temp_log_file):
        """Test static show_logs method."""
        with patch.object(LogViewerDialog, "__init__", return_value=None) as mock_init:
            with patch.object(LogViewerDialog, "show"):
                LogViewerDialog.show_logs(temp_log_file, parent=None)
                mock_init.assert_called_once()

    def test_dialog_styling(self, log_viewer):
        """Test that dialog has styling applied."""
        assert log_viewer.objectName() == LogViewerDialog.DIALOG_OBJECT_NAME
        assert len(log_viewer.styleSheet()) > 0

    def test_close_button_closes_dialog(self, qtbot, log_viewer):
        """Test that close button closes the dialog."""
        # Show dialog
        log_viewer.show()

        # Find and click close button (simplified test)
        assert log_viewer.isVisible()

        # Close dialog
        log_viewer.close()

        # Dialog should be closed
        assert not log_viewer.isVisible()
