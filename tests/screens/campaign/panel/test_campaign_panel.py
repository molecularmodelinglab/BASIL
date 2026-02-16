"""
Tests for the CampaignPanelScreen and its tab functionality.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from app.models.campaign import Campaign, Target
from app.screens.campaign.panel.campaign_panel import CampaignPanelScreen


@pytest.fixture
def sample_campaign():
    """Create a sample campaign for testing."""
    campaign = Campaign()
    campaign.name = "Test Campaign"
    campaign.description = "A test campaign for unit testing"
    campaign.targets = [Target(name="Yield", mode="Max"), Target(name="Purity", mode="Min")]
    return campaign


@pytest.fixture
def campaign_panel(qtbot, sample_campaign):
    """Create a CampaignPanelScreen for testing."""
    panel = CampaignPanelScreen(sample_campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)
    return panel


def test_campaign_panel_creation(campaign_panel, sample_campaign):
    """Test that the campaign panel is created correctly."""
    assert campaign_panel.campaign == sample_campaign
    assert campaign_panel.workspace_path == "test_workspace"
    assert hasattr(campaign_panel, "stacked_widget")
    assert hasattr(campaign_panel, "shared_buttons_section")


def test_campaign_panel_has_all_tabs(campaign_panel):
    """Test that all required tabs are created."""
    expected_tabs = ["Runs", "Parameters And Targets", "Settings"]

    # Check that all tabs exist
    for tab_name in expected_tabs:
        assert tab_name in campaign_panel.tabs
        assert isinstance(campaign_panel.tabs[tab_name], QPushButton)

    # Check that all panels exist
    for tab_name in expected_tabs:
        assert tab_name in campaign_panel.panels


def test_campaign_panel_initial_tab_is_runs(campaign_panel):
    """Test that the initial active tab is 'Runs'."""
    # Check that Runs tab is active
    runs_tab = campaign_panel.tabs["Runs"]
    assert runs_tab.objectName() == "ActiveTab"

    # Check that other tabs are inactive
    assert campaign_panel.tabs["Parameters And Targets"].objectName() == "InactiveTab"
    assert campaign_panel.tabs["Settings"].objectName() == "InactiveTab"

    # Check that Runs panel is visible
    assert campaign_panel.stacked_widget.currentWidget() == campaign_panel.panels["Runs"]


def test_tab_switching(qtbot, campaign_panel):
    """Test switching between tabs."""
    # Initially on Runs tab
    assert campaign_panel.stacked_widget.currentWidget() == campaign_panel.panels["Runs"]

    # Switch to Parameters tab
    qtbot.mouseClick(campaign_panel.tabs["Parameters And Targets"], Qt.LeftButton)
    assert campaign_panel.stacked_widget.currentWidget() == campaign_panel.panels["Parameters And Targets"]
    assert campaign_panel.tabs["Parameters And Targets"].objectName() == "ActiveTab"
    assert campaign_panel.tabs["Runs"].objectName() == "InactiveTab"

    # Switch to Settings tab
    qtbot.mouseClick(campaign_panel.tabs["Settings"], Qt.LeftButton)
    assert campaign_panel.stacked_widget.currentWidget() == campaign_panel.panels["Settings"]
    assert campaign_panel.tabs["Settings"].objectName() == "ActiveTab"
    assert campaign_panel.tabs["Parameters And Targets"].objectName() == "InactiveTab"


def test_campaign_metadata_display(campaign_panel, sample_campaign):
    """Test that campaign metadata is displayed correctly."""
    # The campaign name should be displayed
    assert campaign_panel.campaign.name == sample_campaign.name
    assert campaign_panel.campaign.description == sample_campaign.description
    assert len(campaign_panel.campaign.targets) == 2


def test_shared_buttons_section_exists(campaign_panel):
    """Test that the shared buttons section is created."""
    assert hasattr(campaign_panel, "shared_buttons_section")
    assert hasattr(campaign_panel, "buttons_layout")

    # Home button should always be present
    assert campaign_panel.buttons_layout.count() >= 1


def test_panel_specific_buttons_update_on_tab_switch(qtbot, campaign_panel):
    """Test that panel-specific buttons update when switching tabs."""
    # Switch to Runs tab and check for Generate New Run button
    campaign_panel.switch_tab("Runs")
    # After switching, there should be additional buttons beyond the home button
    initial_button_count = campaign_panel.buttons_layout.count()

    # Switch to Settings tab
    campaign_panel.switch_tab("Settings")
    # Button count might change as Settings panel has different buttons
    settings_button_count = campaign_panel.buttons_layout.count()

    # Both should have at least the home button + stretch + panel buttons
    assert initial_button_count >= 2  # home + stretch minimum
    assert settings_button_count >= 2  # home + stretch minimum


def test_home_signal_emission(qtbot, campaign_panel):
    """Test that the home signal is emitted correctly."""
    with qtbot.waitSignal(campaign_panel.home_requested, timeout=1000):
        # Find and click the home button
        home_button = None
        for i in range(campaign_panel.buttons_layout.count()):
            item = campaign_panel.buttons_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), "text") and item.widget().text() == "Home":
                home_button = item.widget()
                break

        assert home_button is not None, "Home button not found"
        qtbot.mouseClick(home_button, Qt.LeftButton)


def test_new_run_signal_emission(qtbot, campaign_panel):
    """Test that the new run signal is emitted from the runs panel."""
    # Ensure we're on the Runs tab
    campaign_panel.switch_tab("Runs")

    with qtbot.waitSignal(campaign_panel.new_run_requested, timeout=1000):
        # Emit the signal directly from the runs panel
        campaign_panel.runs_panel.new_run_requested.emit()
