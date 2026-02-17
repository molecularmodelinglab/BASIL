"""
Tests for the ParametersPanel functionality.
"""

from unittest.mock import Mock, patch

import pytest

from app.models.enums import ParameterType
from app.screens.campaign.panel.parameters_panel import ParametersPanel


@pytest.fixture
def mock_campaign():
    """Create a mock campaign with parameters and targets."""
    campaign = Mock()

    param1 = Mock()
    param1.name = "temperature"
    param1.parameter_type = ParameterType.DISCRETE_NUMERICAL_REGULAR
    param1.min_val = 20
    param1.max_val = 100
    param1.step = 5

    param2 = Mock()
    param2.name = "catalyst"
    param2.parameter_type = ParameterType.CATEGORICAL
    param2.values = ["A", "B", "C"]

    target1 = Mock()
    target1.name = "yield"
    target1.mode = Mock()
    target1.mode.value = "maximize"
    target1.transform = None
    target1.weight = 1.0
    target1.min_val = 0
    target1.max_val = 100

    target2 = Mock()
    target2.name = "cost"
    target2.mode = Mock()
    target2.mode.value = "minimize"
    target2.transform = Mock()
    target2.transform.value = "log"
    target2.weight = 0.5
    target2.min_val = 10
    target2.max_val = 1000

    campaign.parameters = [param1, param2]
    campaign.targets = [target1, target2]
    return campaign


@pytest.fixture
def mock_campaign_no_targets():
    """Create a mock campaign with parameters but no targets."""
    campaign = Mock()

    param1 = Mock()
    param1.name = "temperature"
    param1.parameter_type = ParameterType.DISCRETE_NUMERICAL_REGULAR
    param1.min_val = 20
    param1.max_val = 100
    param1.step = 5

    campaign.parameters = [param1]
    campaign.targets = []
    return campaign


@pytest.fixture
def parameters_panel(qtbot):
    """Create a ParametersPanel for testing."""
    panel = ParametersPanel()
    qtbot.addWidget(panel)
    return panel


@pytest.fixture
def parameters_panel_with_campaign(qtbot, mock_campaign):
    """Create a ParametersPanel with campaign data for testing."""
    with patch("app.screens.campaign.panel.parameters_panel.TargetFormatter") as mock_formatter:
        mock_formatter.format_target_mode.return_value = "Maximize"
        mock_formatter.format_target_transform.return_value = "None"
        mock_formatter.format_target_weight.return_value = "1.0"
        mock_formatter.format_target_values.return_value = "0 - 100"

        panel = ParametersPanel(campaign=mock_campaign)
        qtbot.addWidget(panel)
        return panel


def test_parameters_panel_creation(parameters_panel):
    """Test that the parameters panel is created correctly."""
    assert parameters_panel is not None
    assert hasattr(parameters_panel, "parameters_table")
    assert hasattr(parameters_panel, "targets_table")
    assert hasattr(parameters_panel, "info_label_parameters")
    assert hasattr(parameters_panel, "info_label_targets")


def test_parameters_panel_signal_exists(parameters_panel):
    """Test that the parameters panel has the required signal."""
    assert hasattr(parameters_panel, "data_exported")


def test_parameters_signal_emission(qtbot, parameters_panel):
    """Test that the parameters signal can be emitted."""
    with qtbot.waitSignal(parameters_panel.data_exported, timeout=1000):
        parameters_panel.data_exported.emit()


def test_get_panel_buttons_returns_export_button(parameters_panel):
    """Test that get_panel_buttons returns the Export Data button."""
    buttons = parameters_panel.get_panel_buttons()

    assert len(buttons) == 1
    assert buttons[0].text() == "Export Data"


def test_no_parameters_state(parameters_panel):
    """Test the panel shows correct state when no parameters are defined."""
    assert parameters_panel.info_label_parameters.text() == "No parameters defined for this campaign."
    assert parameters_panel.parameters_table.rowCount() == 0


def test_no_targets_state(parameters_panel):
    """Test the panel shows correct state when no targets are defined."""
    assert parameters_panel.info_label_targets.text() == "No targets defined for this campaign."
    assert parameters_panel.targets_table.rowCount() == 0


def test_parameters_table_creation(parameters_panel):
    """Test that the parameters table is created with correct structure."""
    table = parameters_panel.parameters_table

    assert table.columnCount() == 3
    assert table.horizontalHeaderItem(0).text() == "Parameter"
    assert table.horizontalHeaderItem(1).text() == "Type"
    assert table.horizontalHeaderItem(2).text() == "Values"


def test_targets_table_creation(parameters_panel):
    """Test that the targets table is created with correct structure."""
    table = parameters_panel.targets_table

    assert table.columnCount() == 5
    assert table.horizontalHeaderItem(0).text() == "Target"
    assert table.horizontalHeaderItem(1).text() == "Mode"
    assert table.horizontalHeaderItem(2).text() == "Transform"
    assert table.horizontalHeaderItem(3).text() == "Weight"
    assert table.horizontalHeaderItem(4).text() == "Values"


def test_load_parameters_data(parameters_panel_with_campaign):
    """Test loading parameters data into the table."""
    panel = parameters_panel_with_campaign

    assert panel.parameters_table.rowCount() == 2
    assert "Parameters (2)" in panel.info_label_parameters.text()

    assert panel.parameters_table.item(0, 0).text() == "temperature"
    assert panel.parameters_table.item(0, 1).text() == "Discrete Numerical (Regular)"

    assert panel.parameters_table.item(1, 0).text() == "catalyst"
    assert panel.parameters_table.item(1, 1).text() == "Categorical"


def test_load_targets_data(parameters_panel_with_campaign):
    """Test loading targets data into the table."""
    panel = parameters_panel_with_campaign

    assert panel.targets_table.rowCount() == 2
    assert "Targets (2)" in panel.info_label_targets.text()

    assert panel.targets_table.item(0, 0).text() == "yield"
    assert panel.targets_table.item(1, 0).text() == "cost"


def test_format_parameter_type(parameters_panel):
    """Test parameter type formatting."""
    panel = parameters_panel

    param = Mock()
    param.parameter_type = ParameterType.DISCRETE_NUMERICAL_REGULAR
    result = panel._format_parameter_type(param)
    assert result == ParameterType.DISCRETE_NUMERICAL_REGULAR.display_name

    param.parameter_type = ParameterType.CATEGORICAL
    result = panel._format_parameter_type(param)
    assert result == ParameterType.CATEGORICAL.display_name

    param.parameter_type = None
    result = panel._format_parameter_type(param)
    assert result == "Unknown"


def test_format_parameter_values_discrete_regular(parameters_panel):
    """Test parameter values formatting for discrete numerical regular."""
    panel = parameters_panel

    param = Mock()
    param.parameter_type = Mock()
    param.parameter_type = ParameterType.DISCRETE_NUMERICAL_REGULAR
    param.min_val = 10
    param.max_val = 50
    param.step = 2

    result = panel._format_parameter_values(param)
    assert "start: 10" in result
    assert "stop: 50" in result
    assert "step: 2" in result


def test_format_parameter_values_categorical(parameters_panel):
    """Test parameter values formatting for categorical."""
    panel = parameters_panel

    param = Mock()
    param.parameter_type = ParameterType.CATEGORICAL
    param.values = ["option1", "option2", "option3"]

    result = panel._format_parameter_values(param)
    assert result == "option1, option2, option3"


def test_format_target_mode(parameters_panel):
    """Test target mode formatting."""
    panel = parameters_panel

    with patch("app.screens.campaign.panel.parameters_panel.TargetFormatter.format_target_mode") as mock_format:
        mock_format.return_value = "Maximize"

        target = Mock()
        target.mode = Mock()
        target.mode.value = "maximize"

        result = panel._format_target_mode(target)
        assert result == "Maximize"
        mock_format.assert_called_once_with(target)


def test_format_target_transform(parameters_panel):
    """Test target transform formatting."""
    panel = parameters_panel

    with patch("app.screens.campaign.panel.parameters_panel.TargetFormatter.format_target_transform") as mock_format:
        mock_format.return_value = "Log"

        target = Mock()
        target.transform = Mock()
        target.transform.value = "log"

        result = panel._format_target_transform(target)
        assert result == "Log"
        mock_format.assert_called_once_with(target)


def test_format_target_weight(parameters_panel):
    """Test target weight formatting."""
    panel = parameters_panel

    with patch("app.screens.campaign.panel.parameters_panel.TargetFormatter.format_target_weight") as mock_format:
        mock_format.return_value = "1.5"

        target = Mock()
        target.weight = 1.5

        result = panel._format_target_weight(target)
        assert result == "1.5"
        mock_format.assert_called_once_with(target)


def test_format_target_values(parameters_panel):
    """Test target values formatting."""
    panel = parameters_panel

    with patch("app.screens.campaign.panel.parameters_panel.TargetFormatter.format_target_values") as mock_format:
        mock_format.return_value = "0 - 100"

        target = Mock()
        target.min_val = 0
        target.max_val = 100

        result = panel._format_target_values(target)
        assert result == "0 - 100"
        mock_format.assert_called_once_with(target)


def test_update_campaign_data(parameters_panel, mock_campaign):
    """Test updating campaign data."""
    panel = parameters_panel

    assert panel.parameters_table.rowCount() == 0
    assert panel.targets_table.rowCount() == 0

    with patch("app.screens.campaign.panel.parameters_panel.TargetFormatter") as mock_formatter:
        mock_formatter.format_target_mode.return_value = "Maximize"
        mock_formatter.format_target_transform.return_value = "None"
        mock_formatter.format_target_weight.return_value = "1.0"
        mock_formatter.format_target_values.return_value = "0 - 100"

        panel.set_campaign(mock_campaign)

    assert panel.parameters_table.rowCount() == 2
    assert panel.targets_table.rowCount() == 2
    assert "Parameters (2)" in panel.info_label_parameters.text()
    assert "Targets (2)" in panel.info_label_targets.text()


def test_set_campaign(parameters_panel, mock_campaign):
    """Test setting campaign."""
    panel = parameters_panel

    with patch("app.screens.campaign.panel.parameters_panel.TargetFormatter") as mock_formatter:
        mock_formatter.format_target_mode.return_value = "Maximize"
        mock_formatter.format_target_transform.return_value = "None"
        mock_formatter.format_target_weight.return_value = "1.0"
        mock_formatter.format_target_values.return_value = "0 - 100"

        panel.set_campaign(mock_campaign)

    assert panel.campaign == mock_campaign
    assert panel.parameters_table.rowCount() == 2
    assert panel.targets_table.rowCount() == 2


def test_set_campaign_no_targets(parameters_panel, mock_campaign_no_targets):
    """Test setting campaign with no targets."""
    panel = parameters_panel

    panel.set_campaign(mock_campaign_no_targets)

    assert panel.campaign == mock_campaign_no_targets
    assert panel.parameters_table.rowCount() == 1
    assert panel.targets_table.rowCount() == 0
    assert panel.info_label_targets.text() == "No targets defined for this campaign."


def test_set_workspace_path(parameters_panel):
    """Test setting workspace path."""
    panel = parameters_panel
    workspace_path = "/test/path"

    panel.set_workspace_path(workspace_path)

    assert panel.workspace_path == workspace_path
    assert panel.campaign_loader is not None


def test_handle_export_click(parameters_panel_with_campaign):
    """Test export button click handler."""
    panel = parameters_panel_with_campaign

    with patch("app.screens.campaign.panel.parameters_panel.CampaignExporter.export_campaign_to_csv") as mock_exporter:
        panel._handle_export_click()
        mock_exporter.assert_called_once_with(panel.campaign, panel)
