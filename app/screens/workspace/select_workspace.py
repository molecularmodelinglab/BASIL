"""
Select workspace screen for the application
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QMessageBox, QSizePolicy, QVBoxLayout, QWidget

from app.core.base import BaseScreen
from app.core.settings import get_recent_workspaces
from app.shared.components.buttons import PrimaryButton, SecondaryButton
from app.shared.components.headers import MainHeader
from app.shared.components.workspace_card import WorkspaceCard
from app.shared.constants import WorkspaceConstants
from app.shared.styles.theme import get_widget_styles


class SelectWorkspaceScreen(BaseScreen):
    """
    Select workspace screen for BASIL application
    """

    # Signals for navigation
    workspace_selected = pyqtSignal(str)

    # UI Text
    WINDOW_TITLE = "BASIL - Select Workspace"
    HEADER_TEXT = "BASIL"
    CREATE_NEW_BUTTON_TEXT = "Create New Workspace"
    OPEN_EXISTING_BUTTON_TEXT = "Open Existing Workspace"
    RECENT_WORKSPACES_HEADER_TEXT = "Recent Workspaces"
    SELECT_NEW_WORKSPACE_FOLDER_TEXT = "Select Folder for New Workspace"
    SELECT_EXISTING_WORKSPACE_FOLDER_TEXT = "Select Existing Workspace Folder"
    CREATE_WORKSPACE_TEXT = "Create Workspace"
    FOLDER_NOT_EMPTY_TEXT = "The selected folder is not empty.\nCreate workspace here anyway?"
    INVALID_WORKSPACE_TEXT = "Invalid Workspace"
    NOT_A_WORKSPACE_TEXT = (
        "The selected folder is not a valid BASIL workspace.\n"
        "Please select a folder containing a workspace configuration file."
    )
    ERROR_TEXT = "Error"
    FAILED_TO_CREATE_WORKSPACE_TEXT = "Failed to create workspace:\n{}"
    WORKSPACE_SELECTED_TEXT = "Workspace selected: {}"

    # UI Layout
    MARGINS = (30, 30, 30, 30)
    SPACING = 25
    BUTTON_SPACING = 15
    RECENT_WORKSPACES_SECTION_SPACING = 30
    RECENT_WORKSPACES_HEADER_SPACING = 10
    RECENT_WORKSPACES_CONTAINER_SPACING = 5
    RECENT_WORKSPACES_CONTAINER_MARGINS = (0, 0, 0, 0)

    # UI Styles
    RECENT_WORKSPACES_HEADER_STYLE = "font-size: 16px; font-weight: bold; color: #333;"

    # Workspace Card Styles
    WORKSPACE_CARD_STYLES = """
        /* Workspace Cards */
        #WorkspaceCard {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 0px;
        }

        #WorkspaceCard[hovered="true"] {
            border-color: #007BFF;
            background-color: #f8f9fa;
        }

        #WorkspaceName {
            font-size: 16px;
            font-weight: 600;
            color: #333333;
            margin: 0px;
        }

        #WorkspaceDetails {
            font-size: 13px;
            color: #666666;
            margin: 0px;
        }

        #WorkspaceDate {
            font-size: 12px;
            color: #999999;
            margin: 0px;
        }
    """

    def __init__(self, parent=None):
        self.logger = logging.getLogger(__name__)
        super().__init__(parent)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.recent_workspaces_container = None

    def _setup_screen(self):
        """Setup the start screen UI."""
        # Set central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(*self.MARGINS)
        self.main_layout.setSpacing(self.SPACING)

        # Create UI sections
        self._create_header()
        self._create_action_buttons()
        self._create_recent_workspaces_section()

        # Add stretch to push content to top
        self.main_layout.addStretch()

    def _create_header(self):
        """Create the application header."""
        header = MainHeader(self.HEADER_TEXT)
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.main_layout.addWidget(header)

    def _create_action_buttons(self):
        """Create main action buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(self.BUTTON_SPACING)

        # Create New Workspace button
        self.create_new_btn = PrimaryButton(self.CREATE_NEW_BUTTON_TEXT)
        self.create_new_btn.clicked.connect(self._on_create_new_workspace)

        # Open Existing Workspace button
        self.open_existing_btn = SecondaryButton(self.OPEN_EXISTING_BUTTON_TEXT)
        self.open_existing_btn.clicked.connect(self._on_open_existing_workspace)

        button_layout.addWidget(self.create_new_btn)
        button_layout.addWidget(self.open_existing_btn)
        button_layout.addStretch()  # Push buttons to left

        self.main_layout.addLayout(button_layout)

    def _create_recent_workspaces_section(self):
        """Create section to display recent workspaces."""

        self.recent_workspaces_container = QWidget()
        self.recent_workspaces_layout = QVBoxLayout(self.recent_workspaces_container)
        self.recent_workspaces_layout.setSpacing(self.RECENT_WORKSPACES_CONTAINER_SPACING)
        self.recent_workspaces_layout.setContentsMargins(*self.RECENT_WORKSPACES_CONTAINER_MARGINS)

        self.main_layout.addSpacing(self.RECENT_WORKSPACES_SECTION_SPACING)

        header = QLabel(self.RECENT_WORKSPACES_HEADER_TEXT)
        header.setStyleSheet(self.RECENT_WORKSPACES_HEADER_STYLE)
        self.main_layout.addWidget(header)

        self.main_layout.addSpacing(self.RECENT_WORKSPACES_HEADER_SPACING)

        self.main_layout.addWidget(self.recent_workspaces_container)

        self._populate_recent_workspaces()

    def _populate_recent_workspaces(self):
        """Populate the recent workspaces container with workspace cards."""
        # Clear existing widgets
        while self.recent_workspaces_layout.count():
            child = self.recent_workspaces_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        recent_workspaces = get_recent_workspaces()  # Returns List[Workspace]

        for workspace in recent_workspaces:
            workspace_card = WorkspaceCard(workspace)
            workspace_card.workspace_selected.connect(self._workspace_selected)
            self.recent_workspaces_layout.addWidget(workspace_card)

    def _on_create_new_workspace(self):
        """Handle creating a new workspace."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.SELECT_NEW_WORKSPACE_FOLDER_TEXT,
            str(Path.home()),  # Start in home directory
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder_path:  # User didn't cancel
            self._create_new_workspace(folder_path)

    def _on_open_existing_workspace(self):
        """Handle opening an existing workspace."""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.SELECT_EXISTING_WORKSPACE_FOLDER_TEXT,
            "",  # Start in home directory
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder_path:  # User didn't cancel
            self._open_existing_workspace(folder_path)

    def _create_new_workspace(self, folder_path):
        """Create a new workspace in the selected folder."""
        # Check if folder is not empty and ask for confirmation
        if os.listdir(folder_path):
            reply = QMessageBox.question(
                self,
                self.CREATE_WORKSPACE_TEXT,
                self.FOLDER_NOT_EMPTY_TEXT,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            # Create workspace configuration
            workspace_config = {
                WorkspaceConstants.WORKSPACE_NAME_KEY: os.path.basename(folder_path),
                WorkspaceConstants.WORKSPACE_CREATED_KEY: datetime.now().isoformat(),
                WorkspaceConstants.WORKSPACE_VERSION_KEY: WorkspaceConstants.WORKSPACE_VERSION_VALUE,
            }

            # Write workspace config file
            workspace_file = os.path.join(folder_path, WorkspaceConstants.WORKSPACE_CONFIG_FILENAME)
            with open(workspace_file, "w") as f:
                json.dump(workspace_config, f, indent=2)

            # Create campaigns directory
            campaigns_dir = os.path.join(folder_path, WorkspaceConstants.CAMPAIGNS_DIRNAME)
            os.makedirs(campaigns_dir, exist_ok=True)

            self._workspace_selected(folder_path)

        except Exception as e:
            QMessageBox.critical(self, self.ERROR_TEXT, self.FAILED_TO_CREATE_WORKSPACE_TEXT.format(e))

    def _open_existing_workspace(self, folder_path):
        """Open an existing workspace."""
        # Validate that it's a valid workspace
        workspace_file = os.path.join(folder_path, WorkspaceConstants.WORKSPACE_CONFIG_FILENAME)

        if not os.path.exists(workspace_file):
            QMessageBox.warning(
                self,
                self.INVALID_WORKSPACE_TEXT,
                self.NOT_A_WORKSPACE_TEXT,
            )
            return

        # TODO: Could add more validation here (check config file format, etc.)
        self._workspace_selected(folder_path)

    def _workspace_selected(self, folder_path):
        """Called when a workspace is successfully selected."""
        self.logger.info(self.WORKSPACE_SELECTED_TEXT.format(folder_path))
        self.workspace_selected.emit(folder_path)

    def _apply_styles(self):
        """Apply screen-specific styles."""
        self.setStyleSheet(get_widget_styles() + self.WORKSPACE_CARD_STYLES)

    def showEvent(self, event):
        """Refresh recent workspaces when the screen is shown."""
        super().showEvent(event)
        if hasattr(self, "_populate_recent_workspaces"):
            self._populate_recent_workspaces()
