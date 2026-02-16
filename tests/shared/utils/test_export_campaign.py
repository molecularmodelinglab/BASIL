"""
Tests for the CampaignExporter, ParameterFormatter, and TargetFormatter functionality.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from app.models.enums import ParameterType
from app.shared.utils.export_campaign import CampaignExporter, ParameterFormatter, TargetFormatter


@pytest.fixture
def mock_campaign():
    """Create a mock campaign with parameters, targets, and experiments."""
    campaign = Mock()
    campaign.name = "Test Campaign"
    campaign.description = "A test campaign description"

    # Parameters
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

    param3 = Mock()
    param3.name = "pressure"
    param3.parameter_type = ParameterType.CONTINUOUS_NUMERICAL
    param3.min_val = 1.0
    param3.max_val = 10.0

    campaign.parameters = [param1, param2, param3]

    # Targets
    target1 = Mock()
    target1.name = "yield"
    target1.mode = "Max"
    target1.transformation = "log"
    target1.weight = 1.0
    target1.min_value = 0
    target1.max_value = 100

    target2 = Mock()
    target2.name = "cost"
    target2.mode = "Min"
    target2.transformation = None
    target2.weight = 0.5
    target2.min_value = None
    target2.max_value = None

    campaign.targets = [target1, target2]

    # Experiments
    exp1 = Mock()
    exp1.id = "exp-001"
    exp1.status = "completed"
    exp1.results = "Success"

    campaign.experiments = [exp1]

    return campaign


@pytest.fixture
def minimal_campaign():
    """Create a minimal campaign with no parameters, targets, or experiments."""
    campaign = Mock()
    campaign.name = "Minimal Campaign"
    campaign.description = "Minimal description"
    campaign.parameters = []
    campaign.targets = []
    campaign.experiments = []
    return campaign


class TestCampaignExporter:
    """Tests for CampaignExporter class."""

    @patch("app.shared.utils.export_campaign.QFileDialog.getSaveFileName")
    @patch("builtins.open", new_callable=mock_open)
    @patch("app.shared.utils.export_campaign.InfoDialog.show_info")
    def test_export_campaign_to_csv_success(self, mock_info, mock_file, mock_dialog, mock_campaign):
        """Test successful CSV export."""
        mock_dialog.return_value = ("test_campaign.csv", "CSV Files (*.csv)")

        result = CampaignExporter.export_campaign_to_csv(mock_campaign, parent_widget=Mock())

        assert result is True
        mock_dialog.assert_called_once()
        mock_file.assert_called_once_with("test_campaign.csv", "w", newline="", encoding="utf-8")
        mock_info.assert_called_once()

    @patch("app.shared.utils.export_campaign.QFileDialog.getSaveFileName")
    def test_export_campaign_to_csv_cancelled(self, mock_dialog, mock_campaign):
        """Test CSV export when user cancels file dialog."""
        mock_dialog.return_value = ("", "")

        result = CampaignExporter.export_campaign_to_csv(mock_campaign, parent_widget=Mock())

        assert result is False

    @patch("app.shared.utils.export_campaign.ErrorDialog.show_error")
    def test_export_campaign_to_csv_no_campaign(self, mock_error):
        """Test CSV export with no campaign."""
        parent_widget = Mock()

        result = CampaignExporter.export_campaign_to_csv(None, parent_widget=parent_widget)

        assert result is False
        mock_error.assert_called_once()

    @patch("app.shared.utils.export_campaign.QFileDialog.getSaveFileName")
    @patch("builtins.open", new_callable=mock_open)
    @patch("app.shared.utils.export_campaign.ErrorDialog.show_error")
    def test_export_campaign_to_csv_write_error(self, mock_error, mock_file, mock_dialog, mock_campaign):
        """Test CSV export when write fails."""
        mock_dialog.return_value = ("test_campaign.csv", "CSV Files (*.csv)")
        mock_file.side_effect = IOError("Write failed")

        parent_widget = Mock()
        result = CampaignExporter.export_campaign_to_csv(mock_campaign, parent_widget=parent_widget)

        assert result is False
        mock_error.assert_called_once()

    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.writer")
    def test_write_campaign_csv_with_all_data(self, mock_writer, mock_file, mock_campaign):
        """Test writing campaign CSV with all data."""
        mock_csv_writer = Mock()
        mock_writer.return_value = mock_csv_writer

        CampaignExporter._write_campaign_csv(mock_campaign, "test.csv")

        # Verify file was opened correctly
        mock_file.assert_called_once_with("test.csv", "w", newline="", encoding="utf-8")

        # Verify CSV writer was called with expected data
        assert mock_csv_writer.writerow.call_count > 0

        # Check that campaign info was written
        calls = [str(call) for call in mock_csv_writer.writerow.call_args_list]
        assert any("Campaign Information" in str(call) for call in calls)
        assert any("Parameters" in str(call) for call in calls)
        assert any("Targets" in str(call) for call in calls)
        assert any("Experiments" in str(call) for call in calls)

    @patch("builtins.open", new_callable=mock_open)
    @patch("csv.writer")
    def test_write_campaign_csv_minimal(self, mock_writer, mock_file, minimal_campaign):
        """Test writing campaign CSV with minimal data."""
        mock_csv_writer = Mock()
        mock_writer.return_value = mock_csv_writer

        CampaignExporter._write_campaign_csv(minimal_campaign, "test.csv")

        # Verify file was opened correctly
        mock_file.assert_called_once()

        # Check that only campaign info was written
        calls = [str(call) for call in mock_csv_writer.writerow.call_args_list]
        assert any("Campaign Information" in str(call) for call in calls)

    def test_format_parameter_type_discrete_regular(self):
        """Test formatting discrete numerical regular parameter type."""
        param = Mock()
        param.parameter_type = ParameterType.DISCRETE_NUMERICAL_REGULAR

        result = CampaignExporter._format_parameter_type(param)

        assert result == "Discrete Numerical Regular"

    def test_format_parameter_type_categorical(self):
        """Test formatting categorical parameter type."""
        param = Mock()
        param.parameter_type = ParameterType.CATEGORICAL

        result = CampaignExporter._format_parameter_type(param)

        assert result == "Categorical"

    def test_format_parameter_type_continuous(self):
        """Test formatting continuous numerical parameter type."""
        param = Mock()
        param.parameter_type = ParameterType.CONTINUOUS_NUMERICAL

        result = CampaignExporter._format_parameter_type(param)

        assert result == "Continuous Numerical"

    def test_format_parameter_type_fixed(self):
        """Test formatting fixed parameter type."""
        param = Mock()
        param.parameter_type = ParameterType.FIXED

        result = CampaignExporter._format_parameter_type(param)

        assert result == "Fixed"

    def test_format_parameter_type_unknown(self):
        """Test formatting unknown parameter type."""
        param = Mock()
        param.parameter_type = None

        result = CampaignExporter._format_parameter_type(param)

        assert result == "Unknown"

    def test_format_parameter_values_discrete_regular(self):
        """Test formatting discrete numerical regular parameter values."""
        param = Mock()
        param.parameter_type = Mock()
        param.parameter_type.value = "discrete_numerical_regular"
        param.min_val = 10
        param.max_val = 50
        param.step = 5

        result = CampaignExporter._format_parameter_values(param)

        assert "start: 10" in result
        assert "stop: 50" in result
        assert "step: 5" in result

    def test_format_parameter_values_discrete_irregular(self):
        """Test formatting discrete numerical irregular parameter values."""
        param = Mock()
        param.parameter_type = Mock()
        param.parameter_type.value = "discrete_numerical_irregular"
        param.values = [1, 5, 10, 20]

        result = CampaignExporter._format_parameter_values(param)

        assert "1, 5, 10, 20" == result

    def test_format_parameter_values_continuous(self):
        """Test formatting continuous numerical parameter values."""
        param = Mock()
        param.parameter_type = Mock()
        param.parameter_type.value = "continuous_numerical"
        param.min_val = 0.5
        param.max_val = 10.5

        result = CampaignExporter._format_parameter_values(param)

        assert "start: 0.5" in result
        assert "end: 10.5" in result

    def test_format_parameter_values_categorical(self):
        """Test formatting categorical parameter values."""
        param = Mock()
        param.parameter_type = Mock()
        param.parameter_type.value = "categorical"
        param.values = ["option1", "option2", "option3"]

        result = CampaignExporter._format_parameter_values(param)

        assert result == "option1, option2, option3"

    def test_format_parameter_values_fixed(self):
        """Test formatting fixed parameter values."""
        param = Mock()
        param.parameter_type = Mock()
        param.parameter_type.value = "fixed"
        param.value = 42

        result = CampaignExporter._format_parameter_values(param)

        assert "Value: 42" in result

    def test_format_parameter_values_substance(self):
        """Test formatting substance parameter values."""
        param = Mock()
        param.parameter_type = Mock()
        param.parameter_type.value = "substance"
        param.smiles = "CCO"

        result = CampaignExporter._format_parameter_values(param)

        assert "SMILES: CCO" in result

    def test_format_parameter_values_no_type(self):
        """Test formatting parameter values with no type."""
        param = Mock()
        param.parameter_type = None

        result = CampaignExporter._format_parameter_values(param)

        assert result == "No values defined"

    def test_format_target_mode_maximize(self):
        """Test formatting maximize target mode."""
        target = Mock()
        target.mode = "Max"

        result = CampaignExporter._format_target_mode(target)

        assert result == "Maximize"

    def test_format_target_mode_minimize(self):
        """Test formatting minimize target mode."""
        target = Mock()
        target.mode = "Min"

        result = CampaignExporter._format_target_mode(target)

        assert result == "Minimize"

    def test_format_target_mode_match(self):
        """Test formatting match target mode."""
        target = Mock()
        target.mode = "Match"

        result = CampaignExporter._format_target_mode(target)

        assert result == "Match"

    def test_format_target_mode_none(self):
        """Test formatting target mode when none."""
        target = Mock()
        target.mode = None

        result = CampaignExporter._format_target_mode(target)

        assert result == "N/A"

    def test_format_target_transform_with_value(self):
        """Test formatting target transform with value."""
        target = Mock()
        target.transformation = "log"

        result = CampaignExporter._format_target_transform(target)

        assert result == "log"

    def test_format_target_transform_none(self):
        """Test formatting target transform when none."""
        target = Mock()
        target.transformation = None

        result = CampaignExporter._format_target_transform(target)

        assert result == "N/A"

    def test_format_target_weight_with_value(self):
        """Test formatting target weight with value."""
        target = Mock()
        target.weight = 1.5

        result = CampaignExporter._format_target_weight(target)

        assert result == "1.5"

    def test_format_target_weight_none(self):
        """Test formatting target weight when none."""
        target = Mock()
        target.weight = None

        result = CampaignExporter._format_target_weight(target)

        assert result == "N/A"

    def test_format_target_values_with_min_max(self):
        """Test formatting target values with min and max."""
        target = Mock()
        target.min_value = 0
        target.max_value = 100

        result = CampaignExporter._format_target_values(target)

        assert "min: -inf" in result
        assert "max: 100" in result

    def test_format_target_values_no_limits(self):
        """Test formatting target values without limits."""
        target = Mock()
        target.min_value = None
        target.max_value = None

        result = CampaignExporter._format_target_values(target)

        assert "min: -inf" in result
        assert "max: +inf" in result

    def test_format_target_values_only_min(self):
        """Test formatting target values with only min."""
        target = Mock()
        target.min_value = 10
        target.max_value = None

        result = CampaignExporter._format_target_values(target)

        assert "min: 10" in result
        assert "max: +inf" in result


class TestParameterFormatter:
    """Tests for ParameterFormatter class."""

    def test_format_parameter_type(self):
        """Test that ParameterFormatter delegates to CampaignExporter."""
        param = Mock()
        param.parameter_type = ParameterType.CATEGORICAL

        result = ParameterFormatter.format_parameter_type(param)

        assert result == "Categorical"

    def test_format_parameter_values(self):
        """Test that ParameterFormatter delegates to CampaignExporter."""
        param = Mock()
        param.parameter_type = Mock()
        param.parameter_type.value = "categorical"
        param.values = ["A", "B", "C"]

        result = ParameterFormatter.format_parameter_values(param)

        assert result == "A, B, C"


class TestTargetFormatter:
    """Tests for TargetFormatter class."""

    def test_format_target_mode(self):
        """Test that TargetFormatter delegates to CampaignExporter."""
        target = Mock()
        target.mode = "Max"

        result = TargetFormatter.format_target_mode(target)

        assert result == "Maximize"

    def test_format_target_transform(self):
        """Test that TargetFormatter delegates to CampaignExporter."""
        target = Mock()
        target.transformation = "log"

        result = TargetFormatter.format_target_transform(target)

        assert result == "log"

    def test_format_target_weight(self):
        """Test that TargetFormatter delegates to CampaignExporter."""
        target = Mock()
        target.weight = 2.0

        result = TargetFormatter.format_target_weight(target)

        assert result == "2.0"

    def test_format_target_values(self):
        """Test that TargetFormatter delegates to CampaignExporter."""
        target = Mock()
        target.min_value = 5
        target.max_value = 50

        result = TargetFormatter.format_target_values(target)

        assert "min: 5" in result
        assert "max: 50" in result
