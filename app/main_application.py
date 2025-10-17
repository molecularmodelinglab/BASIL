"""
Main application window for BASIL.
Manages navigation between different screens.
"""

import logging
import os
from typing import Optional

from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QMenu,
    QMenuBar,
    QSizePolicy,
    QStackedWidget,
)

from app.core import settings
from app.core.about import build_about_text
from app.models.campaign import Campaign
from app.screens.campaign.campaign_wizard import CampaignWizard
from app.screens.campaign.panel.campaign_panel import CampaignPanelScreen
from app.screens.start.start_screen import StartScreen
from app.screens.workspace.select_workspace import SelectWorkspaceScreen
from app.shared.constants import ScreenName, WorkspaceConstants


class MainApplication(QMainWindow):
    """
    Main application window that manages navigation between screens.

    Uses a QStackedWidget to handle different screens:
    - Start screen (welcome/home)
    - Campaign wizard (multi-step campaign creation)
    - Additional screens can be easily added
    """

    DEFAULT_WINDOW_TITLE = "BASIL"
    WELCOME_WINDOW_TITLE = "BASIL - Welcome"
    CREATE_CAMPAIGN_WINDOW_TITLE = "BASIL - Create Campaign"
    GEOMETRY = (100, 100, 1200, 800)
    MIN_SIZE = (900, 600)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle(self.DEFAULT_WINDOW_TITLE)
        self.setGeometry(*self.GEOMETRY)
        self.setMinimumSize(*self.MIN_SIZE)

        # Setup main navigation
        self._setup_navigation()
        # Connect screen navigation
        self._connect_navigation()
        # Setup menubar (Help > About)
        self._setup_menubar()
        # Load initial screen
        self._load_initial_screen()

    def _load_initial_screen(self):
        """Loads the last workspace or shows the selection screen."""
        last_workspace = settings.get_last_workspace()
        if last_workspace and self._is_valid_workspace(last_workspace):
            self._on_workspace_selected(last_workspace)
        else:
            self.show_select_workspace()

    def _is_valid_workspace(self, path: str) -> bool:
        """Checks if a given path is a valid workspace."""
        config_file = os.path.join(path, WorkspaceConstants.WORKSPACE_CONFIG_FILENAME)
        return os.path.isdir(path) and os.path.exists(config_file)

    def _setup_navigation(self):
        """Setup the main navigation structure."""
        # Create stacked widget for screen management
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(self.stacked_widget)

        # Create screens
        self.start_screen = StartScreen()
        self.campaign_wizard = CampaignWizard()
        self.select_workspace = SelectWorkspaceScreen()
        self.campaign_panel = None  # Placeholder for the campaign panel

        # Add screens to stack
        self.stacked_widget.addWidget(self.start_screen)
        self.stacked_widget.addWidget(self.campaign_wizard)
        self.stacked_widget.addWidget(self.select_workspace)

    def _setup_menubar(self):
        """Create the application menu bar with Help > About."""
        try:
            menubar: QMenuBar = self.menuBar()
            menubar.setNativeMenuBar(True)
            help_menu: QMenu = menubar.addMenu("&Help")
            about_action = QAction("About BASIL", self)
            about_action.setMenuRole(QAction.MenuRole.NoRole)
            about_action.triggered.connect(self._show_about_dialog)
            help_menu.addAction(about_action)
        except Exception as e:
            self.logger.error(f"Failed to build menu bar: {e}")

    def _connect_navigation(self):
        """Connect navigation signals between screens."""
        # From workspace selection to the start screen
        self.select_workspace.workspace_selected.connect(self._on_workspace_selected)

        # Start screen navigation
        self.start_screen.new_campaign_requested.connect(self.show_campaign_wizard)
        self.start_screen.back_requested.connect(self.show_select_workspace)
        self.start_screen.campaign_selected.connect(self.show_campaign_panel)

        # Campaign wizard navigation
        self.campaign_wizard.back_to_start_requested.connect(self.show_start_screen)
        self.campaign_wizard.campaign_created.connect(self.on_campaign_created)

    def show_start_screen(self):
        """Navigate to the start screen."""
        self.start_screen.set_workspace(self.current_workspace)
        self.stacked_widget.setCurrentWidget(self.start_screen)
        self.setWindowTitle(self.WELCOME_WINDOW_TITLE)

    def show_select_workspace(self):
        """Navigate to the start screen."""
        self.stacked_widget.setCurrentWidget(self.select_workspace)
        self.setWindowTitle(self.WELCOME_WINDOW_TITLE)

    def show_campaign_wizard(self):
        """Navigate to campaign creation wizard."""
        # Reset wizard state when starting new campaign
        self.campaign_wizard.reset_wizard()
        self.campaign_wizard.workspace_path = self.current_workspace
        self.campaign_wizard.campaign.workspace_path = self.current_workspace
        self.stacked_widget.setCurrentWidget(self.campaign_wizard)
        self.setWindowTitle(self.CREATE_CAMPAIGN_WINDOW_TITLE)

    def show_campaign_panel(self, campaign: Campaign):
        """Navigate to the campaign panel screen."""
        if self.campaign_panel:
            self.stacked_widget.removeWidget(self.campaign_panel)
            self.campaign_panel.deleteLater()

        self.campaign_panel = CampaignPanelScreen(campaign, self.current_workspace)
        self.campaign_panel.home_requested.connect(self.show_start_screen)
        self.stacked_widget.addWidget(self.campaign_panel)
        self.stacked_widget.setCurrentWidget(self.campaign_panel)
        self.setWindowTitle(f"BASIL - {campaign.name}")

    def _show_about_dialog(self):
        """Show the About dialog with programmers and institution."""
        try:
            from app.shared.components.dialogs import InfoDialog

            about_text = build_about_text(app_name="")
            InfoDialog.show_info("About BASIL", about_text, parent=self)
        except Exception as e:
            # Fallback to simple message box if styled dialog fails
            try:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.information(self, "About BASIL", build_about_text(app_name=self.DEFAULT_WINDOW_TITLE))
            except Exception:
                self.logger.error(f"Could not display About dialog: {e}")

    def on_campaign_created(self, campaign: Campaign):
        self.logger.info(f"Campaign created successfully: {campaign.name}")

        # TODO: Show success message
        self.show_start_screen()

    def _on_workspace_selected(self, workspace_path):
        """Handle workspace selection."""
        self.current_workspace = workspace_path
        settings.save_last_workspace(workspace_path)
        self.show_start_screen()

    def resizeEvent(self, event):
        """Ensure child screens can respond if they need custom resize handling."""
        # If individual screens need custom behavior, expose a hook:
        current = self.stacked_widget.currentWidget()
        if hasattr(current, "on_parent_resized"):
            try:
                current.on_parent_resized(event.size())
            except Exception as e:
                self.logger.error(f"Resize hook error: {e}")
        super().resizeEvent(event)

    def navigate_to(self, screen_name: ScreenName, data: Optional[dict] = None):
        """
        Generic navigation method for screen-to-screen communication.

        Args:
            screen_name: Name of the target screen
            data: Optional data to pass to the target screen
        """
        if screen_name == ScreenName.START:
            self.show_start_screen()
        elif screen_name == ScreenName.CAMPAIGN_WIZARD:
            self.show_campaign_wizard()
        elif screen_name == ScreenName.SELECT_WORKSPACE:
            self.show_select_workspace()
        else:
            self.logger.warning(f"Unknown screen: {screen_name}")

    def closeEvent(self, event):
        """Handle application close event."""
        # TODO: Add any cleanup logic here
        # TODO: Ask user to save unsaved changes
        event.accept()
