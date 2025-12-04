import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox

from app.models.workspace import Workspace
from app.screens.workspace.select_workspace import SelectWorkspaceScreen
from app.shared.components.workspace_card import WorkspaceCard
from app.shared.constants import WorkspaceConstants


@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance()
    if test_app is None:
        test_app = QApplication([])
    return test_app


@pytest.fixture
def temp_workspace_dir():
    """Create a temporary directory for workspace testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_workspace():
    """Create a mock workspace object for testing."""
    return Workspace(path="/path/to/workspace1", name="workspace1", accessed_at=datetime.now())


@pytest.fixture
def multiple_mock_workspaces():
    """Create multiple mock workspace objects for testing."""
    return [
        Workspace(path="/path/to/workspace1", name="workspace1", accessed_at=datetime.now()),
        Workspace(path="/path/to/workspace2", name="workspace2", accessed_at=datetime.now()),
        Workspace(path="/path/to/workspace3", name="workspace3", accessed_at=datetime.now()),
    ]


@pytest.fixture
def real_test_workspace(temp_workspace_dir):
    """Create a real workspace directory with proper BASIL structure."""
    workspace_path = Path(temp_workspace_dir) / "test_workspace"
    workspace_path.mkdir(exist_ok=True)

    # Create workspace config
    workspace_config = {
        WorkspaceConstants.WORKSPACE_NAME_KEY: "test_workspace",
        WorkspaceConstants.WORKSPACE_CREATED_KEY: datetime.now().isoformat(),
        WorkspaceConstants.WORKSPACE_VERSION_KEY: WorkspaceConstants.WORKSPACE_VERSION_VALUE,
    }

    # Write workspace config file
    workspace_file = workspace_path / WorkspaceConstants.WORKSPACE_CONFIG_FILENAME
    with open(workspace_file, "w") as f:
        json.dump(workspace_config, f, indent=2)

    # Create campaigns directory
    campaigns_dir = workspace_path / WorkspaceConstants.CAMPAIGNS_DIRNAME
    campaigns_dir.mkdir(exist_ok=True)

    yield str(workspace_path)

    # Cleanup is handled by temp_workspace_dir fixture


def create_test_workspace(base_path: str, workspace_name: str) -> str:
    """Helper function to create a test workspace with proper structure."""
    workspace_path = Path(base_path) / workspace_name
    workspace_path.mkdir(exist_ok=True)

    # Create workspace config
    workspace_config = {
        WorkspaceConstants.WORKSPACE_NAME_KEY: workspace_name,
        WorkspaceConstants.WORKSPACE_CREATED_KEY: datetime.now().isoformat(),
        WorkspaceConstants.WORKSPACE_VERSION_KEY: WorkspaceConstants.WORKSPACE_VERSION_VALUE,
    }

    # Write workspace config file
    workspace_file = workspace_path / WorkspaceConstants.WORKSPACE_CONFIG_FILENAME
    with open(workspace_file, "w") as f:
        json.dump(workspace_config, f, indent=2)

    # Create campaigns directory
    campaigns_dir = workspace_path / WorkspaceConstants.CAMPAIGNS_DIRNAME
    campaigns_dir.mkdir(exist_ok=True)

    return str(workspace_path)


# Existing tests...


def test_select_workspace_screen_init(app, qtbot):
    """Test the initialization of the select workspace screen."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    assert screen.windowTitle() == "BASIL - Select Workspace"


def test_recent_workspaces_section_not_shown_when_no_recent_workspaces(app, qtbot):
    """Test that recent workspaces section shows no cards when there are no recent workspaces."""
    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Check that no workspace cards are present
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 0


def test_recent_workspaces_section_shown_when_recent_workspaces_exist(app, qtbot, multiple_mock_workspaces):
    """Test that recent workspaces section is shown when there are recent workspaces."""
    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=multiple_mock_workspaces):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Check that recent workspaces header is present
        headers = [child for child in screen.findChildren(QLabel) if child.text() == "Recent Workspaces"]
        assert len(headers) == 1

        # Check that workspace cards are present
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == len(multiple_mock_workspaces)


def test_recent_workspaces_section_refreshed_on_show(app, qtbot, multiple_mock_workspaces):
    """Test that recent workspaces section is refreshed when screen is shown."""
    # Initial state with no recent workspaces
    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Check that no workspace cards are present initially
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 0

    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=multiple_mock_workspaces):
        # Simulate showing the screen (this should trigger showEvent)
        screen.show()

        # Check that workspace cards are now present
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == len(multiple_mock_workspaces)


def test_workspace_card_selection_emits_signal(app, qtbot, mock_workspace):
    """Test that clicking a workspace card emits the workspace_selected signal."""
    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[mock_workspace]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Find the workspace card
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 1

        workspace_card = workspace_cards[0]

        # Connect signal to test
        received_signals = []
        screen.workspace_selected.connect(received_signals.append)

        # Mock the workspace path to exist
        with patch("os.path.isdir", return_value=True):
            with patch("os.path.exists", return_value=True):
                # Simulate clicking the card
                qtbot.mouseClick(workspace_card, Qt.MouseButton.LeftButton)

                # Check that signal was emitted with correct path
                assert len(received_signals) == 1
                assert received_signals[0] == mock_workspace.path


def test_create_new_workspace_success_empty_folder(app, qtbot, temp_workspace_dir):
    """Test successful creation of a new workspace in an empty folder."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    new_workspace_path = os.path.join(temp_workspace_dir, "new_workspace")
    os.makedirs(new_workspace_path, exist_ok=True)

    with patch(
        "app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=new_workspace_path
    ):
        received_signals = []
        screen.workspace_selected.connect(received_signals.append)

        # Trigger create workspace action
        screen.create_new_btn.click()

        # Verify workspace was created with correct structure
        assert os.path.exists(os.path.join(new_workspace_path, WorkspaceConstants.WORKSPACE_CONFIG_FILENAME))
        assert os.path.exists(os.path.join(new_workspace_path, WorkspaceConstants.CAMPAIGNS_DIRNAME))

        # Verify config file has correct structure
        with open(os.path.join(new_workspace_path, WorkspaceConstants.WORKSPACE_CONFIG_FILENAME)) as f:
            config = json.load(f)
            assert WorkspaceConstants.WORKSPACE_NAME_KEY in config
            assert WorkspaceConstants.WORKSPACE_CREATED_KEY in config
            assert WorkspaceConstants.WORKSPACE_VERSION_KEY in config
            assert config[WorkspaceConstants.WORKSPACE_NAME_KEY] == "new_workspace"

        # Verify signal was emitted
        assert len(received_signals) == 1
        assert received_signals[0] == new_workspace_path


def test_create_new_workspace_cancelled(app, qtbot):
    """Test that cancelling workspace creation dialog doesn't create workspace."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    with patch("app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=""):
        received_signals = []
        screen.workspace_selected.connect(received_signals.append)

        screen.create_new_btn.click()

        # Verify no signal was emitted
        assert len(received_signals) == 0


def test_create_new_workspace_in_non_empty_folder_user_accepts(app, qtbot, temp_workspace_dir):
    """Test that workspace creation succeeds in non-empty folder when user accepts."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    # Create a non-empty directory
    non_empty_dir = os.path.join(temp_workspace_dir, "non_empty")
    os.makedirs(non_empty_dir)
    Path(non_empty_dir, "existing_file.txt").write_text("content")

    with patch("app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=non_empty_dir):
        with patch(
            "app.screens.workspace.select_workspace.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes
        ):
            received_signals = []
            screen.workspace_selected.connect(received_signals.append)

            screen.create_new_btn.click()

            # Verify workspace was created
            assert os.path.exists(os.path.join(non_empty_dir, WorkspaceConstants.WORKSPACE_CONFIG_FILENAME))
            assert os.path.exists(os.path.join(non_empty_dir, WorkspaceConstants.CAMPAIGNS_DIRNAME))

            # Verify signal was emitted
            assert len(received_signals) == 1
            assert received_signals[0] == non_empty_dir


def test_create_new_workspace_in_non_empty_folder_user_declines(app, qtbot, temp_workspace_dir):
    """Test that workspace creation is cancelled when user declines non-empty folder prompt."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    # Create a non-empty directory
    non_empty_dir = os.path.join(temp_workspace_dir, "non_empty")
    os.makedirs(non_empty_dir)
    Path(non_empty_dir, "existing_file.txt").write_text("content")

    with patch("app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=non_empty_dir):
        with patch(
            "app.screens.workspace.select_workspace.QMessageBox.question", return_value=QMessageBox.StandardButton.No
        ):
            received_signals = []
            screen.workspace_selected.connect(received_signals.append)

            screen.create_new_btn.click()

            # Verify workspace was NOT created
            assert not os.path.exists(os.path.join(non_empty_dir, WorkspaceConstants.WORKSPACE_CONFIG_FILENAME))

            # Verify no signal was emitted
            assert len(received_signals) == 0


def test_create_new_workspace_handles_exception(app, qtbot, temp_workspace_dir):
    """Test that workspace creation handles exceptions gracefully."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    new_workspace_path = os.path.join(temp_workspace_dir, "new_workspace")
    os.makedirs(new_workspace_path, exist_ok=True)

    with patch(
        "app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=new_workspace_path
    ):
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("app.screens.workspace.select_workspace.QMessageBox.critical") as mock_critical:
                received_signals = []
                screen.workspace_selected.connect(received_signals.append)

                screen.create_new_btn.click()

                # Verify error dialog was shown
                mock_critical.assert_called_once()

                # Verify no signal was emitted
                assert len(received_signals) == 0


# New tests for opening existing workspace


def test_open_existing_workspace_success(app, qtbot, real_test_workspace):
    """Test successfully opening a valid existing workspace."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    with patch(
        "app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=real_test_workspace
    ):
        received_signals = []
        screen.workspace_selected.connect(received_signals.append)

        screen.open_existing_btn.click()

        # Verify signal was emitted with correct path
        assert len(received_signals) == 1
        assert received_signals[0] == real_test_workspace


def test_open_existing_workspace_cancelled(app, qtbot):
    """Test that cancelling open workspace dialog doesn't emit signal."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    with patch("app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=""):
        received_signals = []
        screen.workspace_selected.connect(received_signals.append)

        screen.open_existing_btn.click()

        # Verify no signal was emitted
        assert len(received_signals) == 0


def test_open_existing_workspace_not_a_directory(app, qtbot, temp_workspace_dir):
    """Test that opening a non-directory shows error."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    # Create a file instead of directory
    file_path = os.path.join(temp_workspace_dir, "not_a_directory.txt")
    Path(file_path).write_text("content")

    with patch("app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=file_path):
        with patch("app.screens.workspace.select_workspace.QMessageBox.warning") as mock_warning:
            received_signals = []
            screen.workspace_selected.connect(received_signals.append)

            screen.open_existing_btn.click()

            # Verify warning was shown with correct text
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            assert SelectWorkspaceScreen.INVALID_WORKSPACE_TEXT in call_args
            assert SelectWorkspaceScreen.NOT_A_FOLDER_TEXT in call_args

            # Verify no signal was emitted
            assert len(received_signals) == 0


def test_open_existing_workspace_missing_config_file(app, qtbot, temp_workspace_dir):
    """Test that opening workspace without config file shows error."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    # Create directory without workspace config
    invalid_ws_path = os.path.join(temp_workspace_dir, "invalid_workspace")
    os.makedirs(invalid_ws_path)

    with patch("app.screens.workspace.select_workspace.QFileDialog.getExistingDirectory", return_value=invalid_ws_path):
        with patch("app.screens.workspace.select_workspace.QMessageBox.warning") as mock_warning:
            received_signals = []
            screen.workspace_selected.connect(received_signals.append)

            screen.open_existing_btn.click()

            # Verify warning was shown with correct text
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            assert SelectWorkspaceScreen.INVALID_WORKSPACE_TEXT in call_args
            assert SelectWorkspaceScreen.NOT_A_WORKSPACE_TEXT in call_args

            # Verify no signal was emitted
            assert len(received_signals) == 0


# Tests for workspace validation via cards


def test_workspace_card_validation_folder_does_not_exist(app, qtbot, mock_workspace):
    """Test that clicking workspace card with non-existent folder shows error."""
    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[mock_workspace]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 1

        workspace_card = workspace_cards[0]

        received_signals = []
        screen.workspace_selected.connect(received_signals.append)

        # Mock workspace path doesn't exist
        with patch("app.screens.workspace.select_workspace.QMessageBox.warning") as mock_warning:
            qtbot.mouseClick(workspace_card, Qt.MouseButton.LeftButton)

            # Verify warning was shown
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            assert SelectWorkspaceScreen.NOT_A_FOLDER_TEXT in call_args

            # Verify no signal was emitted
            assert len(received_signals) == 0


def test_workspace_card_validation_missing_config(app, qtbot, temp_workspace_dir):
    """Test that clicking workspace card without config file shows error."""
    # Create directory without workspace config
    invalid_ws_path = os.path.join(temp_workspace_dir, "invalid_workspace")
    os.makedirs(invalid_ws_path)

    workspace = Workspace(path=invalid_ws_path, name="Invalid Workspace", accessed_at=datetime.now())

    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[workspace]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 1

        received_signals = []
        screen.workspace_selected.connect(received_signals.append)

        with patch("app.screens.workspace.select_workspace.QMessageBox.warning") as mock_warning:
            qtbot.mouseClick(workspace_cards[0], Qt.MouseButton.LeftButton)

            # Verify warning was shown
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0]
            assert SelectWorkspaceScreen.NOT_A_WORKSPACE_TEXT in call_args

            # Verify no signal was emitted
            assert len(received_signals) == 0


def test_all_constants_defined(app, qtbot):
    """Test that all constants are properly defined."""
    # Check that all text constants are defined
    text_constants = [
        "WINDOW_TITLE",
        "HEADER_TEXT",
        "CREATE_NEW_BUTTON_TEXT",
        "OPEN_EXISTING_BUTTON_TEXT",
        "RECENT_WORKSPACES_HEADER_TEXT",
        "SELECT_NEW_WORKSPACE_FOLDER_TEXT",
        "SELECT_EXISTING_WORKSPACE_FOLDER_TEXT",
        "CREATE_WORKSPACE_TEXT",
        "FOLDER_NOT_EMPTY_TEXT",
        "INVALID_WORKSPACE_TEXT",
        "NOT_A_WORKSPACE_TEXT",
        "NOT_A_FOLDER_TEXT",
        "ERROR_TEXT",
        "FAILED_TO_CREATE_WORKSPACE_TEXT",
        "WORKSPACE_SELECTED_TEXT",
    ]

    for constant in text_constants:
        assert hasattr(SelectWorkspaceScreen, constant), f"Missing text constant: {constant}"

    # Check that all layout constants are defined
    layout_constants = [
        "MARGINS",
        "SPACING",
        "BUTTON_SPACING",
        "RECENT_WORKSPACES_SECTION_SPACING",
        "RECENT_WORKSPACES_HEADER_SPACING",
        "RECENT_WORKSPACES_CONTAINER_SPACING",
        "RECENT_WORKSPACES_CONTAINER_MARGINS",
    ]

    for constant in layout_constants:
        assert hasattr(SelectWorkspaceScreen, constant), f"Missing layout constant: {constant}"

    # Check that all style constants are defined
    style_constants = [
        "RECENT_WORKSPACES_HEADER_STYLE",
        "WORKSPACE_CARD_STYLES",
    ]

    for constant in style_constants:
        assert hasattr(SelectWorkspaceScreen, constant), f"Missing style constant: {constant}"


def test_workspace_card_displays_correct_information(app, qtbot):
    """Test that workspace cards display the correct workspace information."""
    test_workspace = Workspace(
        path="/path/to/my-project", name="My Project", accessed_at=datetime(2024, 12, 15, 10, 30, 0)
    )

    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[test_workspace]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Find the workspace card
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 1

        workspace_card = workspace_cards[0]

        # Check that the card has the correct workspace
        assert workspace_card.workspace.path == "/path/to/my-project"
        assert workspace_card.workspace.name == "My Project"
        assert workspace_card.workspace.accessed_at == datetime(2024, 12, 15, 10, 30, 0)


def test_empty_recent_workspaces_shows_header_but_no_cards(app, qtbot):
    """Test that with no recent workspaces, header is shown but no cards."""
    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Check that recent workspaces header is still present (even if no workspaces)
        headers = [child for child in screen.findChildren(QLabel) if child.text() == "Recent Workspaces"]
        assert len(headers) == 1

        # But no workspace cards should be present
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 0
