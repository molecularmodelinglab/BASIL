"""
Tests for the ExperimentsTableScreen service.
"""

from unittest.mock import Mock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from app.models.campaign import Campaign, Target
from app.models.parameters.types import Categorical, ContinuousNumerical
from app.screens.campaign.panel.services.experiments_table import ExperimentsTableScreen, TargetInputDelegate


@pytest.fixture
def sample_campaign():
    """Create a sample campaign for testing."""
    campaign = Campaign()
    campaign.id = "test_campaign_123"
    campaign.name = "Test Campaign"
    campaign.description = "A test campaign"

    param1 = ContinuousNumerical("temperature", 20.0, 100.0)
    param2 = Categorical("solvent", ["water", "ethanol", "methanol"])

    campaign.parameters = [param1, param2]

    target1 = Target()
    target1.name = "yield"
    target1.mode = "MAX"

    target2 = Target()
    target2.name = "purity"
    target2.mode = "MAX"

    campaign.targets = [target1, target2]

    return campaign


@pytest.fixture
def sample_experiments():
    """Create sample experiments data."""
    return [
        {"temperature": 25.0, "solvent": "water", "yield": None, "purity": None},
        {"temperature": 50.0, "solvent": "ethanol", "yield": 0.8, "purity": None},
        {"temperature": 75.0, "solvent": "methanol", "yield": None, "purity": 0.95},
    ]


@pytest.fixture
def experiments_table_screen(qtbot, sample_experiments, sample_campaign):
    """Create an ExperimentsTableScreen for testing."""
    screen = ExperimentsTableScreen(sample_experiments, sample_campaign, 1)
    qtbot.addWidget(screen)
    return screen


class TestExperimentsTableScreen:
    """Tests for ExperimentsTableScreen class."""

    def test_initialization(self, experiments_table_screen, sample_experiments, sample_campaign):
        """Test that the screen initializes correctly."""
        assert experiments_table_screen.experiments == sample_experiments
        assert experiments_table_screen.campaign == sample_campaign
        assert experiments_table_screen.run_number == 1
        assert hasattr(experiments_table_screen, "back_to_runs_requested")
        assert hasattr(experiments_table_screen, "save_results_requested")

    def test_screen_has_table(self, experiments_table_screen):
        """Test that the screen has a table widget."""
        assert hasattr(experiments_table_screen, "table")
        assert experiments_table_screen.table is not None

    def test_column_separation(self, experiments_table_screen):
        """Test that parameters and targets are properly separated into columns."""
        # Should have stored column lists
        assert hasattr(experiments_table_screen, "_param_columns")
        assert hasattr(experiments_table_screen, "_target_columns")
        assert "temperature" in experiments_table_screen._param_columns
        assert "solvent" in experiments_table_screen._param_columns
        assert "yield" in experiments_table_screen._target_columns
        assert "purity" in experiments_table_screen._target_columns

    def test_table_setup(self, experiments_table_screen, sample_experiments, sample_campaign):
        """Test that the table is set up correctly."""
        table = experiments_table_screen.table

        # Should have correct number of rows and columns
        assert table.rowCount() == len(sample_experiments)
        expected_columns = len(experiments_table_screen._param_columns) + len(experiments_table_screen._target_columns)
        assert table.columnCount() == expected_columns

    def test_parameter_columns_editable(self, experiments_table_screen):
        """Test that parameter columns are editable."""
        table = experiments_table_screen.table

        # Parameter columns should be editable
        for param_col_idx in range(len(experiments_table_screen._param_columns)):
            for row in range(table.rowCount()):
                item = table.item(row, param_col_idx)
                if item:
                    assert item.flags() & Qt.ItemFlag.ItemIsEditable

    def test_target_columns_editable(self, experiments_table_screen):
        """Test that target columns are editable."""
        table = experiments_table_screen.table
        param_count = len(experiments_table_screen._param_columns)

        # Target columns should be editable
        for target_col_idx in range(len(experiments_table_screen._target_columns)):
            col_idx = param_count + target_col_idx
            for row in range(table.rowCount()):
                item = table.item(row, col_idx)
                if item:
                    assert item.flags() & Qt.ItemFlag.ItemIsEditable

    def test_save_results_signal(self, qtbot, experiments_table_screen):
        """Test that save results emits the correct signal."""
        with qtbot.waitSignal(experiments_table_screen.save_results_requested, timeout=1000):
            experiments_table_screen._handle_save_results()

    def test_back_to_runs_signal(self, qtbot, experiments_table_screen):
        """Test that back to runs emits the correct signal."""
        with qtbot.waitSignal(experiments_table_screen.back_to_runs_requested, timeout=1000):
            experiments_table_screen.back_to_runs_requested.emit()

    def test_save_results_with_changes(self, experiments_table_screen):
        """Test saving results with target value changes."""
        table = experiments_table_screen.table
        param_count = len(experiments_table_screen._param_columns)

        # Modify a target value in the table
        assert "yield" in experiments_table_screen._target_columns
        yield_col_idx = param_count + experiments_table_screen._target_columns.index("yield")

        new_item = QTableWidgetItem("0.95")
        table.setItem(0, yield_col_idx, new_item)

        # Save results
        experiments_table_screen._handle_save_results()

        # Check that the value was updated in experiments
        assert experiments_table_screen.experiments[0]["yield"] == 0.95

    def test_has_unsaved_changes_false(self, experiments_table_screen):
        """Test has_unsaved_changes returns False when no changes."""
        result = experiments_table_screen.has_unsaved_changes()
        assert result is False

    def test_has_unsaved_changes_true(self, experiments_table_screen):
        """Test has_unsaved_changes returns True when there are changes."""
        table = experiments_table_screen.table
        param_count = len(experiments_table_screen._param_columns)

        # Modify a target value
        yield_col_idx = param_count + experiments_table_screen._target_columns.index("yield")
        new_item = QTableWidgetItem("0.95")
        table.setItem(0, yield_col_idx, new_item)

        result = experiments_table_screen.has_unsaved_changes()
        assert result is True

    def test_numeric_conversion_in_save(self, experiments_table_screen):
        """Test that numeric values are properly converted during save."""
        table = experiments_table_screen.table
        param_count = len(experiments_table_screen._param_columns)

        # Set numeric value as string for yield target
        assert "yield" in experiments_table_screen._target_columns
        yield_col_idx = param_count + experiments_table_screen._target_columns.index("yield")

        new_item = QTableWidgetItem("0.85")
        table.setItem(0, yield_col_idx, new_item)

        experiments_table_screen._handle_save_results()

        # Should convert to float
        assert isinstance(experiments_table_screen.experiments[0]["yield"], float)
        assert experiments_table_screen.experiments[0]["yield"] == 0.85

    def test_rejects_non_numeric_on_save(self, experiments_table_screen, monkeypatch):
        """Non-numeric inputs should be rejected with an error popup and save aborted."""
        from app.shared.components.dialogs import ErrorDialog

        # Spy for error dialog
        errors = []
        monkeypatch.setattr(ErrorDialog, "show_error", lambda title, msg, parent=None: errors.append((title, msg)))

        table = experiments_table_screen.table
        param_count = len(experiments_table_screen._param_columns)

        yield_col_idx = param_count + experiments_table_screen._target_columns.index("yield")
        new_item = QTableWidgetItem("pending")
        table.setItem(0, yield_col_idx, new_item)

        # Spy for save signal; should not emit
        emitted = []
        experiments_table_screen.save_results_requested.connect(lambda data: emitted.append(data))

        experiments_table_screen._handle_save_results()

        assert len(errors) == 1
        assert "Invalid Input" in errors[0][0]
        assert "Please enter a number" in errors[0][1]
        assert len(emitted) == 0

    def test_empty_values_converted_to_none(self, experiments_table_screen):
        """Test that empty values are converted to None."""
        table = experiments_table_screen.table
        param_count = len(experiments_table_screen._param_columns)

        # Set empty value
        yield_col_idx = param_count + experiments_table_screen._target_columns.index("yield")
        new_item = QTableWidgetItem("")
        table.setItem(0, yield_col_idx, new_item)

        experiments_table_screen._handle_save_results()

        # Should convert to None
        assert experiments_table_screen.experiments[0]["yield"] is None

    def test_rejects_nan_on_save(self, experiments_table_screen, monkeypatch):
        """'NaN' should be rejected as non-finite."""
        from app.shared.components.dialogs import ErrorDialog

        errors = []
        monkeypatch.setattr(ErrorDialog, "show_error", lambda title, msg, parent=None: errors.append((title, msg)))

        table = experiments_table_screen.table
        param_count = len(experiments_table_screen._param_columns)
        col_idx = param_count + experiments_table_screen._target_columns.index("yield")
        table.setItem(0, col_idx, QTableWidgetItem("NaN"))

        emitted = []
        experiments_table_screen.save_results_requested.connect(lambda data: emitted.append(data))
        experiments_table_screen._handle_save_results()

        assert errors, "Expected an error dialog for NaN"
        assert len(emitted) == 0

    def test_rejects_infinite_on_save(self, experiments_table_screen, monkeypatch):
        """'inf' should be rejected as non-finite."""
        from app.shared.components.dialogs import ErrorDialog

        errors = []
        monkeypatch.setattr(ErrorDialog, "show_error", lambda title, msg, parent=None: errors.append((title, msg)))

        table = experiments_table_screen.table
        param_count = len(experiments_table_screen._param_columns)
        col_idx = param_count + experiments_table_screen._target_columns.index("yield")
        table.setItem(0, col_idx, QTableWidgetItem("inf"))

        emitted = []
        experiments_table_screen.save_results_requested.connect(lambda data: emitted.append(data))
        experiments_table_screen._handle_save_results()

        assert errors, "Expected an error dialog for inf"
        assert len(emitted) == 0

    def test_existing_target_values_displayed(self, qtbot, sample_campaign):
        """Test that existing target values are displayed in the table."""
        # Update campaign to have multiple targets for this test
        sample_campaign.targets = []

        from app.models.campaign import Target

        yield_target = Target()
        yield_target.name = "yield"
        yield_target.mode = "MAX"
        sample_campaign.targets.append(yield_target)

        purity_target = Target()
        purity_target.name = "purity"
        purity_target.mode = "MAX"
        sample_campaign.targets.append(purity_target)

        experiments_with_values = [{"temperature": 25.0, "solvent": "water", "yield": 0.8, "purity": 0.95}]

        screen = ExperimentsTableScreen(experiments_with_values, sample_campaign, 1)
        qtbot.addWidget(screen)

        table = screen.table
        param_count = len(screen._param_columns)

        # Check that existing values are displayed
        yield_col_idx = param_count + screen._target_columns.index("yield")
        purity_col_idx = param_count + screen._target_columns.index("purity")

        yield_item = table.item(0, yield_col_idx)
        purity_item = table.item(0, purity_col_idx)

        assert yield_item.text() == "0.8"
        assert purity_item.text() == "0.95"

    def test_empty_experiments_list(self, qtbot, sample_campaign):
        """Test screen behavior with empty experiments list."""
        screen = ExperimentsTableScreen([], sample_campaign, 1)
        qtbot.addWidget(screen)

        # Should handle empty list gracefully
        assert screen.experiments == []
        assert screen.table.rowCount() == 0

    def test_missing_target_columns_added(self, qtbot, sample_campaign):
        """Test that missing target columns are added to the table."""
        # Experiments missing some target columns
        incomplete_experiments = [
            {
                "temperature": 25.0,
                "solvent": "water",
                "yield": 0.8,
                # Missing 'purity' column
            }
        ]

        screen = ExperimentsTableScreen(incomplete_experiments, sample_campaign, 1)
        qtbot.addWidget(screen)

        # Should still have columns for all campaign targets
        assert "yield" in screen._target_columns
        assert "purity" in screen._target_columns

        # Table should have correct number of columns
        expected_columns = len(screen._param_columns) + len(sample_campaign.targets)
        assert screen.table.columnCount() == expected_columns


class TestLargeInputDelegate:
    """Tests for LargeInputDelegate class."""

    @pytest.fixture
    def delegate(self):
        """Create a TargetInputDelegate for testing."""
        return TargetInputDelegate()

    def test_delegate_creation(self, delegate):
        """Test that the delegate can be created."""
        assert delegate is not None
        assert hasattr(delegate, "createEditor")
        assert hasattr(delegate, "setEditorData")
        assert hasattr(delegate, "setModelData")

    def test_create_editor(self, delegate, qtbot):
        """Test that the delegate creates an editor."""
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        qtbot.addWidget(parent)

        option = Mock()
        index = Mock()

        editor = delegate.createEditor(parent, option, index)

        # Should return some kind of editor widget
        assert editor is not None

    def test_set_editor_data(self, delegate, qtbot):
        """Test setting data in the editor."""
        from unittest.mock import Mock

        from PySide6.QtCore import QAbstractTableModel, QModelIndex
        from PySide6.QtWidgets import QLineEdit

        editor = QLineEdit()
        qtbot.addWidget(editor)

        # Create a proper mock model and index
        mock_model = Mock(spec=QAbstractTableModel)
        mock_model.data.return_value = "test_value"

        index = Mock(spec=QModelIndex)
        index.model.return_value = mock_model

        delegate.setEditorData(editor, index)

        # Should have set the editor text
        assert editor.text() == "test_value"

    def test_set_model_data_accepts_numeric(self, delegate, qtbot):
        """Delegate should set model data when input is numeric."""
        from PySide6.QtWidgets import QLineEdit

        editor = QLineEdit()
        editor.setText("123.45")
        qtbot.addWidget(editor)

        model = Mock()
        index = Mock()

        delegate.setModelData(editor, model, index)

        model.setData.assert_called_with(index, "123.45", Qt.ItemDataRole.EditRole)

    def test_set_model_data_rejects_non_numeric(self, delegate, qtbot, monkeypatch):
        """Delegate should reject non-numeric input and not update the model."""
        from PySide6.QtWidgets import QLineEdit

        # Patch the ErrorDialog used inside the module under test
        import app.screens.campaign.panel.services.experiments_table as et

        errors = []
        monkeypatch.setattr(et.ErrorDialog, "show_error", lambda title, msg, parent=None: errors.append((title, msg)))
        editor = QLineEdit()
        editor.setText("abc")
        qtbot.addWidget(editor)
        model = Mock()
        index = Mock()
        delegate.setModelData(editor, model, index)
        # Should not have updated the model
        assert model.setData.call_count == 0
        assert errors, "Expected an error dialog for non-numeric input"
