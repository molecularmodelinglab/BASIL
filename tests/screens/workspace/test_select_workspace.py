from datetime import datetime
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from app.models.workspace import Workspace
from app.screens.workspace.select_workspace import SelectWorkspaceScreen
from app.shared.components.workspace_card import WorkspaceCard


@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance()
    if test_app is None:
        test_app = QApplication([])
    return test_app


def test_select_workspace_screen_init(app, qtbot):
    """Test the initialization of the select workspace screen."""
    screen = SelectWorkspaceScreen()
    qtbot.addWidget(screen)

    assert screen.windowTitle() == "BASIL - Select Workspace"


def test_recent_workspaces_section_not_shown_when_no_recent_workspaces(app, qtbot):
    """Test that recent workspaces section is not shown when there are no recent workspaces."""
    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Check that no workspace cards are present
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 0


def test_recent_workspaces_section_shown_when_recent_workspaces_exist(app, qtbot):
    """Test that recent workspaces section is shown when there are recent workspaces."""
    # Create workspace objects instead of strings
    recent_workspaces = [
        Workspace(path="/path/to/workspace1", name="workspace1", accessed_at=datetime.now()),
        Workspace(path="/path/to/workspace2", name="workspace2", accessed_at=datetime.now()),
    ]

    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=recent_workspaces):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Check that recent workspaces header is present
        headers = [child for child in screen.findChildren(QLabel) if child.text() == "Recent Workspaces"]
        assert len(headers) == 1

        # Check that workspace cards are present
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == len(recent_workspaces)


def test_recent_workspaces_section_refreshed_on_show(app, qtbot):
    """Test that recent workspaces section is refreshed when screen is shown."""
    # Initial state with no recent workspaces
    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=[]):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Check that no workspace cards are present initially
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 0

    # Update mock to return recent workspaces
    recent_workspaces = [
        Workspace(path="/path/to/workspace1", name="workspace1", accessed_at=datetime.now()),
        Workspace(path="/path/to/workspace2", name="workspace2", accessed_at=datetime.now()),
    ]

    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=recent_workspaces):
        # Simulate showing the screen (this should trigger showEvent)
        screen.show()

        # Check that workspace cards are now present
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == len(recent_workspaces)


def test_workspace_card_selection_emits_signal(app, qtbot):
    """Test that clicking a workspace card emits the workspace_selected signal."""
    recent_workspaces = [Workspace(path="/path/to/workspace1", name="workspace1", accessed_at=datetime.now())]

    with patch("app.screens.workspace.select_workspace.get_recent_workspaces", return_value=recent_workspaces):
        screen = SelectWorkspaceScreen()
        qtbot.addWidget(screen)

        # Find the workspace card
        workspace_cards = screen.findChildren(WorkspaceCard)
        assert len(workspace_cards) == 1

        workspace_card = workspace_cards[0]

        # Connect signal to test
        received_signals = []
        screen.workspace_selected.connect(received_signals.append)

        # Simulate clicking the card
        qtbot.mouseClick(workspace_card, Qt.MouseButton.LeftButton)

        # Check that signal was emitted with correct path
        assert len(received_signals) == 1
        assert received_signals[0] == "/path/to/workspace1"


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

    # Check that all style constants are defined (updated for workspace cards)
    style_constants = [
        "RECENT_WORKSPACES_HEADER_STYLE",
        "WORKSPACE_CARD_STYLES",  # Updated from WORKSPACE_BUTTON_STYLE
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
