"""
Tests for the SettingsPanel functionality.
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from app.models.campaign import Campaign
from app.screens.campaign.panel.settings_panel import SettingsPanel


@pytest.fixture
def sample_campaign():
    """Create a sample campaign for testing."""
    campaign = Campaign()
    campaign.id = "test-campaign-123"
    campaign.name = "Test Campaign"
    campaign.description = "A test campaign for unit testing"
    campaign.objective_scope = "single"
    campaign.multi_objective_strategy = None
    campaign.surrogate_model = "gp"
    campaign.acquisition_function = "ei"
    return campaign


@pytest.fixture
def settings_panel(qtbot, sample_campaign):
    """Create a SettingsPanel for testing."""
    panel = SettingsPanel(sample_campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)
    return panel


def test_settings_panel_creation(settings_panel, sample_campaign):
    """Test that the settings panel is created correctly."""
    assert settings_panel.campaign == sample_campaign
    assert settings_panel.workspace_path == "test_workspace"
    assert hasattr(settings_panel, "name_input")
    assert hasattr(settings_panel, "description_input")
    assert hasattr(settings_panel, "rename_button")
    assert hasattr(settings_panel, "edit_button")


def test_campaign_data_loaded_correctly(settings_panel, sample_campaign):
    """Test that campaign data is loaded into the form fields."""
    assert settings_panel.name_input.text() == sample_campaign.name
    assert settings_panel.description_input.toPlainText() == sample_campaign.description


def test_initial_form_state_is_readonly(settings_panel):
    """Test that form fields are initially read-only."""
    assert settings_panel.name_input.isReadOnly() is True
    assert settings_panel.description_input.isReadOnly() is True
    assert settings_panel.rename_button.text() == "Rename"
    assert settings_panel.edit_button.text() == "Edit"


def test_name_edit_mode_toggle(qtbot, settings_panel):
    """Test toggling name field edit mode."""
    assert settings_panel.name_input.isReadOnly() is True
    assert settings_panel.rename_button.text() == "Rename"

    qtbot.mouseClick(settings_panel.rename_button, Qt.LeftButton)

    assert settings_panel.name_input.isReadOnly() is False
    assert settings_panel.rename_button.text() == "Save"


def test_description_edit_mode_toggle(qtbot, settings_panel):
    """Test toggling description field edit mode."""
    assert settings_panel.description_input.isReadOnly() is True
    assert settings_panel.edit_button.text() == "Edit"

    qtbot.mouseClick(settings_panel.edit_button, Qt.LeftButton)

    assert settings_panel.description_input.isReadOnly() is False
    assert settings_panel.edit_button.text() == "Save"


def test_successful_name_save(qtbot, settings_panel, sample_campaign):
    """Test successful campaign name saving."""
    mock_loader_instance = Mock()
    settings_panel.campaign_loader = mock_loader_instance

    qtbot.mouseClick(settings_panel.rename_button, Qt.LeftButton)

    settings_panel.name_input.clear()
    qtbot.keyClicks(settings_panel.name_input, "New Campaign Name")

    with qtbot.waitSignal(settings_panel.campaign_renamed, timeout=1000):
        qtbot.mouseClick(settings_panel.rename_button, Qt.LeftButton)

    assert settings_panel.campaign.name == "New Campaign Name"
    assert settings_panel.name_input.isReadOnly() is True
    assert settings_panel.rename_button.text() == "Rename"
    mock_loader_instance.update_campaign.assert_called_once()


def test_successful_description_save(qtbot, settings_panel, sample_campaign):
    """Test successful campaign description saving."""
    mock_loader_instance = Mock()
    settings_panel.campaign_loader = mock_loader_instance

    qtbot.mouseClick(settings_panel.edit_button, Qt.LeftButton)

    settings_panel.description_input.clear()
    qtbot.keyClicks(settings_panel.description_input, "New campaign description")

    with qtbot.waitSignal(settings_panel.campaign_description_updated, timeout=1000):
        qtbot.mouseClick(settings_panel.edit_button, Qt.LeftButton)

    assert settings_panel.campaign.description == "New campaign description"
    assert settings_panel.description_input.isReadOnly() is True
    assert settings_panel.edit_button.text() == "Edit"
    mock_loader_instance.update_campaign.assert_called_once()


@patch("app.screens.campaign.panel.settings_panel.ErrorDialog")
def test_save_failure_reverts_changes(mock_error_dialog, qtbot, settings_panel, sample_campaign):
    """Test that save failure reverts changes."""
    mock_loader_instance = Mock()
    mock_loader_instance.update_campaign.side_effect = Exception("Save failed")
    settings_panel.campaign_loader = mock_loader_instance

    original_name = sample_campaign.name

    qtbot.mouseClick(settings_panel.rename_button, Qt.LeftButton)

    settings_panel.name_input.clear()
    qtbot.keyClicks(settings_panel.name_input, "Failed Name Change")

    qtbot.mouseClick(settings_panel.rename_button, Qt.LeftButton)

    assert settings_panel.campaign.name == original_name
    assert settings_panel.name_input.text() == original_name
    assert settings_panel.name_input.isReadOnly() is True
    mock_error_dialog.show_error.assert_called_once()


def test_get_panel_buttons_returns_correct_buttons(settings_panel):
    """Test that get_panel_buttons returns the expected buttons."""
    buttons = settings_panel.get_panel_buttons()

    assert len(buttons) == 2

    button_texts = [button.text() for button in buttons]
    assert "Delete Campaign" in button_texts
    assert "Export Data" in button_texts


def test_campaign_data_update(settings_panel):
    """Test updating campaign data programmatically."""
    new_campaign = Campaign()
    new_campaign.id = "new-campaign-456"
    new_campaign.name = "Updated Campaign"
    new_campaign.description = "Updated description"

    settings_panel.update_campaign_data(new_campaign)

    assert settings_panel.campaign == new_campaign
    assert settings_panel.name_input.text() == "Updated Campaign"
    assert settings_panel.description_input.toPlainText() == "Updated description"


def test_set_campaign(settings_panel):
    """Test setting campaign."""
    new_campaign = Campaign()
    new_campaign.id = "another-campaign-789"
    new_campaign.name = "Another Campaign"
    new_campaign.description = "Another description"

    settings_panel.set_campaign(new_campaign)

    assert settings_panel.campaign == new_campaign
    assert settings_panel.name_input.text() == "Another Campaign"
    assert settings_panel.description_input.toPlainText() == "Another description"


def test_workspace_path_update(settings_panel):
    """Test updating workspace path."""
    new_workspace_path = "new_test_workspace"
    settings_panel.set_workspace_path(new_workspace_path)

    assert settings_panel.workspace_path == new_workspace_path
    assert settings_panel.campaign_loader is not None


def test_panel_without_campaign_loader():
    """Test panel behavior when no campaign loader is available."""
    panel = SettingsPanel()

    result = panel._save_campaign_changes()
    assert result is False


def test_save_without_campaign(settings_panel):
    """Test save behavior when no campaign is set."""
    settings_panel.campaign = None

    result = settings_panel._save_campaign_changes()
    assert result is False


def test_save_campaign_changes_success(settings_panel):
    """Test successful campaign save."""
    mock_loader = Mock()
    settings_panel.campaign_loader = mock_loader

    result = settings_panel._save_campaign_changes()

    assert result is True
    mock_loader.update_campaign.assert_called_once_with(settings_panel.campaign)


def test_save_campaign_changes_failure(settings_panel):
    """Test failed campaign save."""
    mock_loader = Mock()
    mock_loader.update_campaign.side_effect = Exception("Save error")
    settings_panel.campaign_loader = mock_loader

    result = settings_panel._save_campaign_changes()

    assert result is False


@patch("app.screens.campaign.panel.settings_panel.CampaignExporter")
def test_export_button_functionality(mock_exporter, qtbot, settings_panel):
    """Test that the export button calls the exporter correctly."""
    mock_exporter.export_campaign_to_csv.return_value = True

    buttons = settings_panel.get_panel_buttons()
    export_button = next(btn for btn in buttons if btn.text() == "Export Data")

    qtbot.mouseClick(export_button, Qt.LeftButton)

    mock_exporter.export_campaign_to_csv.assert_called_once_with(settings_panel.campaign, settings_panel)


def test_export_button_emits_signal_on_success(qtbot, settings_panel):
    """Test that export button emits signal on successful export."""
    with patch("app.screens.campaign.panel.settings_panel.CampaignExporter") as mock_exporter:
        mock_exporter.export_campaign_to_csv.return_value = True

        buttons = settings_panel.get_panel_buttons()
        export_button = next(btn for btn in buttons if btn.text() == "Export Data")

        with qtbot.waitSignal(settings_panel.data_exported, timeout=1000):
            qtbot.mouseClick(export_button, Qt.LeftButton)


@patch("app.screens.campaign.panel.settings_panel.ConfirmationDialog")
def test_delete_button_shows_confirmation_dialog(mock_dialog, qtbot, settings_panel):
    """Test that the delete button shows confirmation dialog."""
    mock_dialog.show_confirmation.return_value = False

    buttons = settings_panel.get_panel_buttons()
    delete_button = next(btn for btn in buttons if btn.text() == "Delete Campaign")

    qtbot.mouseClick(delete_button, Qt.LeftButton)

    mock_dialog.show_confirmation.assert_called_once()


@patch("app.screens.campaign.panel.settings_panel.ConfirmationDialog")
@patch("app.screens.campaign.panel.settings_panel.InfoDialog")
def test_delete_campaign_success_emits_signal(mock_info_dialog, mock_confirmation, qtbot, settings_panel):
    """Test that successful campaign deletion emits the signal."""
    mock_confirmation.show_confirmation.return_value = True

    with patch.object(settings_panel, "_delete_campaign_files", return_value=True):
        buttons = settings_panel.get_panel_buttons()
        delete_button = next(btn for btn in buttons if btn.text() == "Delete Campaign")

        with qtbot.waitSignal(settings_panel.campaign_deleted, timeout=1000):
            qtbot.mouseClick(delete_button, Qt.LeftButton)

    mock_info_dialog.show_info.assert_called_once()


@patch("app.screens.campaign.panel.settings_panel.ConfirmationDialog")
@patch("app.screens.campaign.panel.settings_panel.ErrorDialog")
def test_delete_campaign_failure_shows_error(mock_error_dialog, mock_confirmation, qtbot, settings_panel):
    """Test that failed campaign deletion shows error dialog."""
    mock_confirmation.show_confirmation.return_value = True

    with patch.object(settings_panel, "_delete_campaign_files", return_value=False):
        buttons = settings_panel.get_panel_buttons()
        delete_button = next(btn for btn in buttons if btn.text() == "Delete Campaign")

        qtbot.mouseClick(delete_button, Qt.LeftButton)

    mock_error_dialog.show_error.assert_called_once()


@patch("app.screens.campaign.panel.settings_panel.ErrorDialog")
def test_delete_campaign_with_no_campaign(mock_error_dialog, qtbot):
    """Test delete button behavior when no campaign is set."""
    panel = SettingsPanel(campaign=None, workspace_path="test_workspace")

    buttons = panel.get_panel_buttons()
    delete_button = next(btn for btn in buttons if btn.text() == "Delete Campaign")

    delete_button.click()

    mock_error_dialog.show_error.assert_called_once()


def test_delete_campaign_files_success(settings_panel, tmp_path):
    """Test successful deletion of campaign files."""
    campaigns_dir = tmp_path / "campaigns"
    campaigns_dir.mkdir()
    campaign_folder = campaigns_dir / settings_panel.campaign.id
    campaign_folder.mkdir()

    (campaign_folder / "data.json").write_text("{}")

    settings_panel.workspace_path = str(tmp_path)
    mock_loader = Mock()
    settings_panel.campaign_loader = mock_loader

    result = settings_panel._delete_campaign_files()

    assert result is True
    assert not campaign_folder.exists()
    mock_loader.delete_campaign.assert_called_once_with(settings_panel.campaign)


def test_delete_campaign_files_no_campaign(settings_panel):
    """Test delete files when no campaign is set."""
    settings_panel.campaign = None

    result = settings_panel._delete_campaign_files()

    assert result is False


def test_delete_campaign_files_no_workspace(settings_panel):
    """Test delete files when no workspace path is set."""
    settings_panel.workspace_path = None

    result = settings_panel._delete_campaign_files()

    assert result is False


def test_get_enum_display_name_success(settings_panel):
    """Test getting enum display name successfully."""
    from app.models.enums import BOSurrogateModel

    result = SettingsPanel._get_enum_display_name(BOSurrogateModel, "gp")

    assert result is not None


def test_get_enum_display_name_fallback(settings_panel):
    """Test getting enum display name with fallback to raw value."""
    from app.models.enums import BOSurrogateModel

    result = SettingsPanel._get_enum_display_name(BOSurrogateModel, "invalid_value")

    assert result == "invalid_value"


def test_panel_displays_campaign_id(settings_panel, sample_campaign):
    """Test that the panel displays the campaign ID."""
    assert settings_panel.campaign.id == sample_campaign.id


def test_panel_with_minimal_campaign(qtbot):
    """Test panel creation with minimal campaign data."""
    minimal_campaign = Campaign()
    minimal_campaign.id = "minimal-id"
    minimal_campaign.name = None
    minimal_campaign.description = None
    minimal_campaign.objective_scope = "single"
    minimal_campaign.multi_objective_strategy = None
    minimal_campaign.surrogate_model = None
    minimal_campaign.acquisition_function = None

    panel = SettingsPanel(minimal_campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)

    assert panel.name_input.text() == ""
    assert panel.description_input.toPlainText() == ""


def test_panel_single_objective_strategy_display(qtbot):
    """Test that single objective strategy label displays correctly."""
    campaign = Campaign()
    campaign.id = "test-id"
    campaign.name = "Test"
    campaign.description = ""
    campaign.objective_scope = "single"
    campaign.multi_objective_strategy = None
    campaign.surrogate_model = "gp"
    campaign.acquisition_function = "ei"

    panel = SettingsPanel(campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)

    label_texts = [label.text() for label in panel.findChildren(QLabel)]
    assert "Single Objective" in label_texts


def test_panel_multi_objective_pareto_display(qtbot):
    """Test that multi objective pareto strategy label displays correctly."""
    campaign = Campaign()
    campaign.id = "test-id"
    campaign.name = "Test"
    campaign.description = ""
    campaign.objective_scope = "multi"
    campaign.multi_objective_strategy = "pareto"
    campaign.surrogate_model = "gp"
    campaign.acquisition_function = "ei"

    panel = SettingsPanel(campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)

    label_texts = [label.text() for label in panel.findChildren(QLabel)]
    assert "Multi Objective, Pareto (Frontier)" in label_texts


def test_panel_multi_objective_desirability_display(qtbot):
    """Test that multi objective desirability strategy label displays correctly."""
    campaign = Campaign()
    campaign.id = "test-id"
    campaign.name = "Test"
    campaign.description = ""
    campaign.objective_scope = "multi"
    campaign.multi_objective_strategy = "desirability"
    campaign.surrogate_model = "gp"
    campaign.acquisition_function = "ei"

    panel = SettingsPanel(campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)

    label_texts = [label.text() for label in panel.findChildren(QLabel)]
    assert "Multi Objective, Desirability (Weighted)" in label_texts


def test_panel_unknown_objective_scope_display(qtbot):
    """Test that unknown objective scope shows 'Unknown' label."""
    campaign = Campaign()
    campaign.id = "test-id"
    campaign.name = "Test"
    campaign.description = ""
    campaign.objective_scope = "something_unexpected"
    campaign.multi_objective_strategy = None
    campaign.surrogate_model = "gp"
    campaign.acquisition_function = "ei"

    panel = SettingsPanel(campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)

    label_texts = [label.text() for label in panel.findChildren(QLabel)]
    assert "Unknown" in label_texts
