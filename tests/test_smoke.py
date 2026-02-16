from PySide6.QtCore import Qt

from app.main_application import MainApplication
from app.screens.campaign.campaign_wizard import CampaignWizard
from app.screens.start.start_screen import StartScreen
from app.screens.workspace.select_workspace import SelectWorkspaceScreen


def test_main_application_creation(qapp):
    """Test if the main application window is created."""
    window = MainApplication()
    assert window is not None
    assert window.isVisible() is False  # Should not be visible until .show() is called


def test_initial_screen_is_select_worspace_screen(qapp):
    """Test if the initial screen is the StartScreen."""
    window = MainApplication()
    assert isinstance(window.stacked_widget.currentWidget(), SelectWorkspaceScreen)


def test_navigation_to_campaign_wizard(qtbot):
    """Test navigation from StartScreen to CampaignWizard."""
    window = MainApplication()
    qtbot.addWidget(window)
    window._on_workspace_selected("dummy_path")

    # Initially, we are on the start screen
    assert isinstance(window.stacked_widget.currentWidget(), StartScreen)

    # Simulate clicking the 'New Campaign' button
    start_screen = window.start_screen
    qtbot.mouseClick(start_screen.new_campaign_btn, Qt.LeftButton)

    # Now, we should be on the campaign wizard
    assert isinstance(window.stacked_widget.currentWidget(), CampaignWizard)


def test_navigation_back_to_start_screen(qtbot):
    """Test navigation from CampaignWizard back to StartScreen."""
    window = MainApplication()
    qtbot.addWidget(window)
    window._on_workspace_selected("dummy_path")
    window.show()

    # Go to campaign wizard first
    window.show_campaign_wizard()
    assert isinstance(window.stacked_widget.currentWidget(), CampaignWizard)

    # Simulate clicking the 'Back' button
    campaign_wizard = window.campaign_wizard
    campaign_wizard.back_to_start_requested.emit()

    # Now, we should be back on the start screen
    assert isinstance(window.stacked_widget.currentWidget(), StartScreen)


def test_campaign_panel_integration(qtbot):
    """Test integration of campaign panel with main application."""
    from app.models.campaign import Campaign, Target
    from app.screens.campaign.panel.campaign_panel import CampaignPanelScreen

    # Create a sample campaign
    campaign = Campaign()
    campaign.name = "Integration Test Campaign"
    campaign.description = "Test campaign for integration testing"
    campaign.targets = [Target(name="Accuracy", mode="Max")]

    # Create campaign panel
    panel = CampaignPanelScreen(campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)

    # Verify initial state
    assert panel.campaign == campaign
    assert "Runs" in panel.tabs
    assert "Parameters And Targets" in panel.tabs
    assert "Settings" in panel.tabs


def test_settings_panel_integration(qtbot):
    """Test settings panel integration with campaign data."""
    from app.models.campaign import Campaign, Target
    from app.screens.campaign.panel.settings_panel import SettingsPanel

    # Create a sample campaign
    campaign = Campaign()
    campaign.name = "Settings Test Campaign"
    campaign.description = "Test campaign for settings"
    campaign.targets = [Target(name="Performance", mode="Max")]

    # Create settings panel
    panel = SettingsPanel(campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)

    # Verify campaign data is loaded
    assert panel.name_input.text() == campaign.name
    assert panel.description_input.toPlainText() == campaign.description


def test_multiple_targets_workflow(qtbot):
    """Test the complete workflow with multiple targets."""
    from app.models.campaign import Campaign, Target
    from app.screens.campaign.setup.campaign_info_step import CampaignInfoStep

    # Create campaign with multiple targets
    campaign = Campaign()
    campaign.name = "Multi-Target Campaign"
    campaign.targets = [
        Target(name="Accuracy", mode="Max"),
        Target(name="Speed", mode="Min"),
        Target(name="Memory", mode="Min"),
    ]

    # Create campaign info step
    step = CampaignInfoStep(campaign)
    qtbot.addWidget(step)

    # Load the data
    step.load_data()

    # Verify all targets are loaded
    assert len(step.target_rows) == 3
    assert step.target_rows[0].name_input.text() == "Accuracy"
    assert step.target_rows[1].name_input.text() == "Speed"
    assert step.target_rows[2].name_input.text() == "Memory"
