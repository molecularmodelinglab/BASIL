"""
Base panel screen for a campaign, managing different views via tabs.
"""

from typing import Dict

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from app.core.base import BaseScreen, BaseWidget
from app.models.campaign import Campaign
from app.screens.campaign.panel.parameters_panel import ParametersPanel
from app.screens.campaign.panel.runs_panel import RunsPanel
from app.screens.campaign.panel.settings_panel import SettingsPanel
from app.shared.components.buttons import PrimaryButton, SecondaryButton
from app.shared.styles.theme import get_navigation_styles, get_tab_styles, get_widget_styles


class CampaignPanelScreen(BaseScreen):
    """
    Base screen for the campaign panel.
    Manages navigation between Runs, Parameters, and Settings tabs.
    """

    APP_TITLE = "BASIL"
    HOME_BUTTON_TEXT = "Home"
    RUNS_TAB_TEXT = "Runs"
    PARAMETERS_TAB_TEXT = "Parameters"
    SETTINGS_TAB_TEXT = "Settings"
    DEFAULT_CAMPAIGN_NAME = "My Cool Campaign 1"

    HEADER_HEIGHT = 60
    TAB_SECTION_SPACING = 15
    HOME_BUTTON_SECTION_SPACING = 15
    HEADER_MARGINS = (20, 15, 20, 15)
    MAIN_LAYOUT_MARGINS = (0, 0, 0, 0)
    TAB_SECTION_MARGINS = (20, 20, 20, 0)
    TAB_LAYOUT_MARGINS = (0, 10, 0, 0)
    HOME_BUTTON_SECTION_MARGINS = (20, 20, 20, 20)
    # Signals
    home_requested = Signal()
    new_run_requested = Signal()

    def __init__(self, campaign: Campaign, workspace_path: str, parent=None):
        self.campaign = campaign
        self.workspace_path = workspace_path
        self.tabs: Dict[str, PrimaryButton] = {}
        self.panels: Dict[str, BaseWidget] = {}
        super().__init__(parent)

    def _setup_screen(self):
        """Setup the default campaign screen UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(*self.MAIN_LAYOUT_MARGINS)

        main_layout.addWidget(self._create_header())
        main_layout.addWidget(self._create_tab_section())

        # Stacked widget for tab content
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.shared_buttons_section = self._create_shared_buttons_section()
        main_layout.addWidget(self.shared_buttons_section)

        self._create_panels()

    def _create_header(self) -> QWidget:
        """Create the campaign header section."""
        header_widget = QWidget()
        header_widget.setObjectName("CampaignHeader")
        header_widget.setFixedHeight(self.HEADER_HEIGHT)

        layout = QHBoxLayout(header_widget)
        layout.setContentsMargins(*self.HEADER_MARGINS)

        # BASIL title
        title_label = QLabel(self.APP_TITLE)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setObjectName("AppTitle")

        layout.addWidget(title_label)
        layout.addStretch()

        return header_widget

    def _create_tab_section(self) -> QWidget:
        """Create the tab navigation section."""
        tab_widget = QWidget()
        tab_widget.setObjectName("TabSection")

        layout = QVBoxLayout(tab_widget)
        layout.setContentsMargins(*self.TAB_SECTION_MARGINS)
        layout.setSpacing(self.TAB_SECTION_SPACING)
        # Campaign name and metadata
        campaign_name = QLabel(self.campaign.name or self.DEFAULT_CAMPAIGN_NAME)
        campaign_name.setObjectName("CampaignName")
        campaign_font = QFont()
        campaign_font.setPointSize(18)
        campaign_font.setBold(True)
        campaign_name.setFont(campaign_font)

        # Campaign metadata
        param_count = len(self.campaign.parameters) if self.campaign.parameters else "Nan"
        target_names = ", ".join([t.name for t in self.campaign.targets]) or "None"
        if self.campaign.created_at == self.campaign.updated_at:
            metadata_text = (
                f"Created on {self.campaign.created_at} • {param_count} Parameters • Targets: {target_names}"
            )
        else:
            metadata_text = (
                f"Updated on {self.campaign.updated_at} • {param_count} Parameters • Targets: {target_names}"
            )

        metadata_label = QLabel(metadata_text)
        metadata_label.setObjectName("CampaignMetadata")
        metadata_label.setStyleSheet("color: #666; font-size: 12px;")

        tab_container = self._create_tab_buttons()

        layout.addWidget(campaign_name)
        layout.addWidget(metadata_label)
        layout.addWidget(tab_container)

        return tab_widget

    def _create_tab_buttons(self) -> QWidget:
        """Create the interactive tab buttons."""
        tab_container = QWidget()
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(*self.TAB_LAYOUT_MARGINS)
        tab_layout.setSpacing(0)

        self.tabs[self.RUNS_TAB_TEXT] = self._create_tab_button(self.RUNS_TAB_TEXT)
        self.tabs[self.PARAMETERS_TAB_TEXT] = self._create_tab_button(self.PARAMETERS_TAB_TEXT)
        self.tabs[self.SETTINGS_TAB_TEXT] = self._create_tab_button(self.SETTINGS_TAB_TEXT)

        for name, button in self.tabs.items():
            button.clicked.connect(self._create_tab_button_handler(name))
            tab_layout.addWidget(button)

        tab_layout.addStretch()
        return tab_container

    def _create_tab_button_handler(self, name: str):
        """Create a click handler for tab buttons."""

        def handler():
            self.switch_tab(name)

        return handler

    def _create_tab_button(self, text: str) -> PrimaryButton:
        """Helper to create a single tab button."""
        button = PrimaryButton(text)
        button.setCheckable(True)
        button.setFlat(True)
        button.setObjectName("InactiveTab")
        return button

    def _create_panels(self):
        """Create panels and connect their signals."""
        self.runs_panel = RunsPanel(self.campaign, self.workspace_path)
        self.parameters_panel = ParametersPanel(self.campaign, self.workspace_path)
        self.settings_panel = SettingsPanel(self.campaign, self.workspace_path)

        self.panels = {
            self.RUNS_TAB_TEXT: self.runs_panel,
            self.PARAMETERS_TAB_TEXT: self.parameters_panel,
            self.SETTINGS_TAB_TEXT: self.settings_panel,
        }

        self.runs_panel.new_run_requested.connect(self.new_run_requested.emit)
        self.settings_panel.campaign_renamed.connect(self._handle_campaign_renamed)
        self.settings_panel.campaign_deleted.connect(self._handle_campaign_deleted)

        self.stacked_widget.addWidget(self.runs_panel)
        self.stacked_widget.addWidget(self.parameters_panel)
        self.stacked_widget.addWidget(self.settings_panel)

        self.switch_tab("Runs")

    def switch_tab(self, name: str):
        """Switch the visible tab and update button styles."""
        for tab_name, button in self.tabs.items():
            is_active = tab_name == name
            button.setObjectName("ActiveTab" if is_active else "InactiveTab")
            self.style().unpolish(button)
            self.style().polish(button)

        self.stacked_widget.setCurrentWidget(self.panels[name])

        active_panel = self.panels[name]
        if hasattr(active_panel, "get_panel_buttons"):
            panel_buttons = active_panel.get_panel_buttons()
            self._add_panel_buttons(panel_buttons)
        else:
            # Clear panel buttons if panel doesn't provide any
            self._clear_panel_buttons()

    def _create_shared_buttons_section(self) -> QWidget:
        """Create the bottom buttons section."""
        self.buttons_widget = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setContentsMargins(*self.HOME_BUTTON_SECTION_MARGINS)
        self.buttons_layout.setSpacing(self.HOME_BUTTON_SECTION_SPACING)

        home_button = SecondaryButton(self.HOME_BUTTON_TEXT)
        home_button.clicked.connect(self.home_requested.emit)
        self.buttons_layout.addWidget(home_button)

        self.buttons_layout.addStretch()

        return self.buttons_widget

    def _add_panel_buttons(self, buttons_list):
        """Add panel-specific buttons to the shared button section."""
        self._clear_panel_buttons()

        # Add new panel buttons
        for button in buttons_list:
            self.buttons_layout.addWidget(button)

    def _clear_panel_buttons(self):
        """Remove panel-specific buttons, keeping only home button and stretch."""
        if not hasattr(self, "buttons_layout"):
            return

        while self.buttons_layout.count() > 2:
            item = self.buttons_layout.takeAt(self.buttons_layout.count() - 1)
            if item.widget():
                item.widget().setParent(None)

    def _handle_campaign_renamed(self, new_name: str):
        """Handle campaign rename - update the UI display."""
        # Update the campaign name display in the tab section
        self._refresh_campaign_metadata()

    def _handle_campaign_deleted(self):
        """Handle campaign deletion - navigate back to home."""
        self.home_requested.emit()

    def _refresh_campaign_metadata(self):
        """Refresh the campaign metadata display in the tab section."""
        campaign_name = self.campaign.name or self.DEFAULT_CAMPAIGN_NAME
        campaign_name_label = self.findChild(QLabel, "CampaignName")
        if campaign_name_label:
            campaign_name_label.setText(campaign_name)

    def _apply_styles(self):
        """Apply wizard-specific styles."""
        styles = get_widget_styles() + get_navigation_styles() + get_tab_styles()
        self.setStyleSheet(styles)
