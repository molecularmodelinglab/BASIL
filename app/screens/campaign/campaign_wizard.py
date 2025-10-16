"""
Campaign creation wizard screen.
Multi-step process for creating new campaigns.
"""

import json
import logging
import os

from PySide6.QtCore import Signal as Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.base import BaseScreen
from app.models.campaign import Campaign
from app.screens.campaign.setup.campaign_info_step import CampaignInfoStep
from app.screens.campaign.setup.data_import_step import DataImportStep
from app.screens.campaign.setup.parameters_step import ParametersStep
from app.shared.components.buttons import NavigationButton
from app.shared.components.dialogs import ErrorDialog
from app.shared.constants import WorkspaceConstants
from app.shared.styles.theme import get_navigation_styles, get_widget_styles


class CampaignWizard(BaseScreen):
    """
    Campaign creation wizard with multiple steps.

    Manages navigation between campaign setup steps and
    collects all necessary data for campaign creation.
    """

    # Navigation signals
    back_to_start_requested = Signal()
    campaign_created = Signal(Campaign)  # Emits campaign data when created

    # UI Text Constants
    WINDOW_TITLE = "BASIL - Create Campaign"
    BACK_BUTTON_TEXT = "← Back"
    NEXT_BUTTON_TEXT = "Next →"
    CREATE_CAMPAIGN_BUTTON_TEXT = "Create Campaign"

    # Error Dialog Constants
    CAMPAIGN_CREATION_FAILED_TITLE = "Campaign Creation Failed"
    CAMPAIGN_CREATION_FAILED_MESSAGE = "An unexpected error occurred while creating the campaign. Please try again."
    CONFIGURATION_ERROR_TITLE = "Configuration Error"
    WORKSPACE_NOT_CONFIGURED_MESSAGE = (
        "Workspace path is not configured. Please restart the application and select a workspace."
    )
    SAVE_FAILED_TITLE = "Save Failed"
    SAVE_FAILED_MESSAGE = "Could not save campaign to file.\n\nError: {0}\n\nPlease check disk space and permissions."

    # Layout Constants
    MAIN_LAYOUT_MARGINS = (0, 0, 0, 0)
    MAIN_LAYOUT_SPACING = 0
    NAV_LAYOUT_MARGINS = (30, 20, 30, 20)
    NAV_LAYOUT_SPACING = 15

    def __init__(self, parent=None):
        # Initialize data before calling super() since BaseScreen calls _setup_screen()
        self.current_step = 0
        self.total_steps = 3
        self.workspace_path = None

        # Shared campaign data
        self.campaign = Campaign()
        self.campaign.workspace_path = self.workspace_path
        self.logger = logging.getLogger(__name__)

        super().__init__(parent)
        self.setWindowTitle(self.WINDOW_TITLE)

    def _setup_screen(self):
        """Setup the campaign wizard UI."""
        # Set central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(*self.MAIN_LAYOUT_MARGINS)
        main_layout.setSpacing(self.MAIN_LAYOUT_SPACING)

        # Create content area
        self._create_content_area(main_layout)

        # Create navigation
        self._create_navigation(main_layout)

        # Initialize display
        self._update_step_display()

    def _create_content_area(self, parent_layout):
        """Create main content area with step widgets."""
        self.stacked_widget = QStackedWidget()

        # Create step widgets
        self.step_widgets = [
            CampaignInfoStep(self.campaign),
            ParametersStep(self.campaign),
            DataImportStep(self.campaign),
        ]

        # Add to stacked widget
        for step_widget in self.step_widgets:
            self.stacked_widget.addWidget(step_widget)

        parent_layout.addWidget(self.stacked_widget)

    def _create_navigation(self, parent_layout):
        """Create navigation buttons."""
        # Navigation container
        nav_container = QWidget()
        nav_container.setObjectName("NavigationContainer")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(*self.NAV_LAYOUT_MARGINS)
        nav_layout.setSpacing(self.NAV_LAYOUT_SPACING)

        # Back button
        self.back_button = NavigationButton(self.BACK_BUTTON_TEXT, "back")
        self.back_button.clicked.connect(self._go_back)

        # Add stretch to push buttons apart
        nav_layout.addWidget(self.back_button)
        nav_layout.addStretch()

        # Next button
        self.next_button = NavigationButton(self.NEXT_BUTTON_TEXT, "next")
        self.next_button.clicked.connect(self._go_next)
        nav_layout.addWidget(self.next_button)

        parent_layout.addWidget(nav_container)

    def _go_back(self):
        """Navigate to previous step or start screen."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step_display()
        else:
            # Go back to start screen
            self.back_to_start_requested.emit()

    def _go_next(self):
        """Navigate to next step or create campaign."""
        # Get current step widget
        current_widget = self.stacked_widget.currentWidget()

        # Validate current step
        if not current_widget.validate():
            return  # Stay on current step if validation fails

        # Save current step data
        current_widget.save_data()

        if self.current_step < self.total_steps - 1:
            # Go to next step
            self.current_step += 1
            self._update_step_display()
        else:
            # Create campaign
            self._create_campaign()

    def _update_step_display(self):
        """Update current step display and navigation."""
        # Switch to current step
        self.stacked_widget.setCurrentIndex(self.current_step)

        # Update navigation buttons
        self.back_button.setEnabled(True)  # Always enabled (can go to start)

        # Update next button text
        if self.current_step == self.total_steps - 1:
            self.next_button.setText(self.CREATE_CAMPAIGN_BUTTON_TEXT)
        else:
            self.next_button.setText(self.NEXT_BUTTON_TEXT)

        # Load data into current step
        current_widget = self.stacked_widget.currentWidget()
        current_widget.load_data()

    def _create_campaign(self):
        """Create campaign with collected data."""
        self.logger.info("Creating campaign with data:")
        self.logger.info(f"Campaign Data: {self.campaign}")

        try:
            # Save campaign to file
            self._save_campaign_to_file()

            # Emit campaign created signal
            self.campaign_created.emit(self.campaign)

            # Go back to start screen
            self.back_to_start_requested.emit()
        except Exception as e:
            self.logger.error(f"Error occurred while creating the campaign: {e}")
            ErrorDialog.show_error(
                self.CAMPAIGN_CREATION_FAILED_TITLE,
                self.CAMPAIGN_CREATION_FAILED_MESSAGE,
                parent=self,
            )

    def _save_campaign_to_file(self):
        """Save the campaign data to a JSON file in the workspace."""
        if not self.workspace_path:
            ErrorDialog.show_error(
                self.CONFIGURATION_ERROR_TITLE,
                self.WORKSPACE_NOT_CONFIGURED_MESSAGE,
                parent=self,
            )
            return

        try:
            campaign_data = self.campaign.to_dict()
            campaign_id = campaign_data["id"]
            filename = f"{campaign_id}.json"

            # Correctly join paths to create the full file path
            campaigns_dir = os.path.join(self.workspace_path, WorkspaceConstants.CAMPAIGNS_DIRNAME)
            # os.makedirs(campaigns_dir, exist_ok=True)
            campaign_path = os.path.join(campaigns_dir, str(campaign_id))
            os.makedirs(campaign_path, exist_ok=True)

            file_path = os.path.join(campaign_path, filename)

            with open(file_path, "w") as f:
                json.dump(campaign_data, f, indent=4)
            self.logger.info(f"Campaign saved to {file_path}")

        except Exception as e:
            ErrorDialog.show_error(
                self.SAVE_FAILED_TITLE,
                self.SAVE_FAILED_MESSAGE.format(str(e)),
                parent=self,
            )

    def reset_wizard(self):
        """Reset wizard to initial state."""
        self.current_step = 0

        # Reset campaign data
        self.campaign.reset()

        # Reset all step widgets
        for step_widget in self.step_widgets:
            step_widget.reset()

        self._update_step_display()

    def _apply_styles(self):
        """Apply wizard-specific styles."""
        styles = get_widget_styles() + get_navigation_styles()
        self.setStyleSheet(styles)
