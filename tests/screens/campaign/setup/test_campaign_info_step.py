"""
Tests for the multiple targets functionality in CampaignInfoStep.
"""

from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt

from app.models.campaign import Campaign, Target
from app.models.enums import MultiObjectiveStrategy, ObjectiveScope
from app.screens.campaign.setup.campaign_info_step import CampaignInfoStep, TargetRow


@pytest.fixture
def sample_campaign():
    """Create a sample campaign for testing."""
    campaign = Campaign()
    campaign.name = "Test Campaign"
    campaign.description = "A test campaign"
    campaign.targets = [Target(name="Yield", mode="Max"), Target(name="Purity", mode="Min")]
    campaign.objective_scope = ObjectiveScope.MULTI.value
    campaign.multi_objective_strategy = MultiObjectiveStrategy.DESIRABILITY.value
    return campaign


@pytest.fixture
def campaign_info_step(qtbot, sample_campaign):
    """Create a CampaignInfoStep for testing."""
    step = CampaignInfoStep(sample_campaign)
    qtbot.addWidget(step)
    return step


def test_campaign_info_step_creation(campaign_info_step):
    """Test that the campaign info step is created correctly."""
    assert campaign_info_step is not None
    assert hasattr(campaign_info_step, "target_rows")
    assert hasattr(campaign_info_step, "add_target_btn")


def test_initial_target_row_added(campaign_info_step):
    """Test that at least one target row is added initially."""
    # After load_data or reset, there should be at least one target row
    campaign_info_step.load_data()
    assert len(campaign_info_step.target_rows) >= 1


def test_add_target_button_functionality(qtbot, campaign_info_step):
    """Test that clicking add target button creates a new target row."""
    campaign_info_step.objective_scope_combo.setCurrentIndex(
        campaign_info_step.objective_scope_combo.findData(ObjectiveScope.MULTI.value)
    )
    campaign_info_step.multi_objective_combo.setCurrentIndex(
        campaign_info_step.multi_objective_combo.findData(MultiObjectiveStrategy.DESIRABILITY.value)
    )
    campaign_info_step._apply_objective_selection()
    initial_count = len(campaign_info_step.target_rows)

    # Click the add target button
    qtbot.mouseClick(campaign_info_step.add_target_btn, Qt.LeftButton)

    # Should have one more target row
    assert len(campaign_info_step.target_rows) == initial_count + 1


def test_remove_target_functionality(qtbot, campaign_info_step):
    """Test removing a target row."""
    campaign_info_step.objective_scope_combo.setCurrentIndex(
        campaign_info_step.objective_scope_combo.findData(ObjectiveScope.MULTI.value)
    )
    campaign_info_step.multi_objective_combo.setCurrentIndex(
        campaign_info_step.multi_objective_combo.findData(MultiObjectiveStrategy.DESIRABILITY.value)
    )
    campaign_info_step._apply_objective_selection()
    # Add multiple targets first
    campaign_info_step._add_target_row()
    campaign_info_step._add_target_row()

    initial_count = len(campaign_info_step.target_rows)
    assert initial_count >= 2

    # Remove one target
    target_row_to_remove = campaign_info_step.target_rows[0]
    campaign_info_step._remove_target_row(target_row_to_remove)

    # Should have one fewer target row
    assert len(campaign_info_step.target_rows) == initial_count - 1


def test_remove_button_visibility(qtbot, campaign_info_step):
    """Test that remove buttons are only visible when there are multiple targets."""
    # With only one target, remove button should be hidden
    campaign_info_step.load_data()

    for row in campaign_info_step.target_rows[:]:
        campaign_info_step._remove_target_row(row)

    campaign_info_step._add_target_row()

    assert len(campaign_info_step.target_rows) == 1
    assert not campaign_info_step.target_rows[0].remove_btn.isVisible()

    campaign_info_step._add_target_row()
    campaign_info_step._update_remove_buttons()

    assert len(campaign_info_step.target_rows) == 2
    for row in campaign_info_step.target_rows:
        assert row.remove_btn.isEnabled()

    campaign_info_step._remove_target_row(campaign_info_step.target_rows[0])
    assert len(campaign_info_step.target_rows) == 1
    assert not campaign_info_step.target_rows[0].remove_btn.isVisible()


def test_load_existing_targets(campaign_info_step, sample_campaign):
    """Test loading existing targets from campaign data."""
    # Load the campaign data which has 2 targets
    campaign_info_step.load_data()

    # Should have the same number of target rows as targets in the campaign
    assert len(campaign_info_step.target_rows) == len(sample_campaign.targets)

    # Check that target data is loaded correctly
    for i, target_row in enumerate(campaign_info_step.target_rows):
        expected_target = sample_campaign.targets[i]
        assert target_row.name_input.text() == expected_target.name
        assert target_row.mode_combo.currentText() == expected_target.mode


def test_save_target_data(campaign_info_step, sample_campaign):
    """Test saving target data to the campaign."""
    # Load data first
    campaign_info_step.load_data()

    # Modify some target data
    if campaign_info_step.target_rows:
        campaign_info_step.target_rows[0].name_input.setText("Modified Target")
        campaign_info_step.target_rows[0].mode_combo.setCurrentText("Min")

    # Save the data
    campaign_info_step.save_data()

    # Check that the campaign was updated
    if campaign_info_step.campaign.targets:
        assert campaign_info_step.campaign.targets[0].name == "Modified Target"
        assert campaign_info_step.campaign.targets[0].mode == "Min"


@patch("app.shared.components.dialogs.ErrorDialog.show_error")
def test_validation_with_empty_targets(_, campaign_info_step):
    """Test validation when no targets are provided."""
    # Clear all targets
    for row in campaign_info_step.target_rows[:]:
        campaign_info_step._remove_target_row(row)

    # Validation should fail
    assert not campaign_info_step.validate()


@patch("app.shared.components.dialogs.ErrorDialog.show_error")
def test_validation_with_invalid_targets(_, campaign_info_step):
    """Test validation when targets have empty names."""
    # Add a target with empty name
    campaign_info_step.objective_scope_combo.setCurrentIndex(
        campaign_info_step.objective_scope_combo.findData(ObjectiveScope.MULTI.value)
    )
    campaign_info_step.multi_objective_combo.setCurrentIndex(
        campaign_info_step.multi_objective_combo.findData(MultiObjectiveStrategy.DESIRABILITY.value)
    )
    campaign_info_step._apply_objective_selection()
    campaign_info_step._add_target_row()
    if campaign_info_step.target_rows:
        campaign_info_step.target_rows[0].name_input.setText("")

    # Validation should fail
    assert not campaign_info_step.validate()


def test_validation_with_valid_targets(campaign_info_step):
    """Test validation when targets are valid."""
    # Add a target with proper data
    campaign_info_step.objective_scope_combo.setCurrentIndex(
        campaign_info_step.objective_scope_combo.findData(ObjectiveScope.SINGLE.value)
    )
    campaign_info_step._apply_objective_selection()
    if campaign_info_step.target_rows:
        campaign_info_step.target_rows[0].name_input.setText("Valid Target")

    # Also need campaign name for validation to pass
    campaign_info_step.name_input.setText("Valid Campaign")

    # Validation should pass
    assert campaign_info_step.validate()


def test_target_row_creation():
    """Test TargetRow creation and functionality."""
    target = Target(name="Test Target", mode="Max")

    # Mock remove callback
    def mock_remove_callback(row):
        pass

    target_row = TargetRow(target, mock_remove_callback)

    assert target_row.target == target
    assert target_row.name_input.text() == "Test Target"
    assert target_row.mode_combo.currentText() == "Max"


def test_target_row_get_data():
    """Test getting data from a TargetRow."""
    target = Target(name="Original", mode="Min")

    def mock_remove_callback(row):
        pass

    target_row = TargetRow(target, mock_remove_callback)

    # Modify the row data
    target_row.name_input.setText("Modified")
    target_row.mode_combo.setCurrentText("Max")

    # Get the updated data
    updated_target = target_row.get_target_data()

    assert updated_target.name == "Modified"
    assert updated_target.mode == "Max"


def test_target_row_validation():
    """Test TargetRow validation."""
    target = Target()

    def mock_remove_callback(row):
        pass

    target_row = TargetRow(target, mock_remove_callback)

    # Empty name should be invalid
    target_row.name_input.setText("")
    assert not target_row.is_valid()

    # Non-empty name should be valid
    target_row.name_input.setText("Valid Target")
    assert target_row.is_valid()
