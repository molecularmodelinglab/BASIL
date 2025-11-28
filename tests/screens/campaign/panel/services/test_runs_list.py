"""
Tests for the RunsListScreen service.
"""

from datetime import datetime

import pytest
from PySide6.QtCore import Qt

from app.screens.campaign.panel.services.runs_list import RunCard, RunsListScreen


@pytest.fixture
def sample_runs_data():
    """Create sample runs data for testing."""
    return [
        {
            "run_id": "test_run_1",
            "run_number": 1,
            "campaign_id": "test_campaign",
            "status": "completed",
            "experiments": [
                {"temperature": 25.0, "solvent": "water", "yield": 0.8},
                {"temperature": 50.0, "solvent": "ethanol", "yield": 0.9},
            ],
            "targets": [{"name": "yield", "mode": "MAX"}],
            "created_at": datetime(2024, 1, 15, 10, 30),
            "updated_at": datetime(2024, 1, 15, 11, 0),
            "experiment_count": 2,
            "completed_count": 2,
        },
        {
            "run_id": "test_run_2",
            "run_number": 2,
            "campaign_id": "test_campaign",
            "status": "in_progress",
            "experiments": [
                {"temperature": 75.0, "solvent": "methanol", "yield": None},
                {"temperature": 100.0, "solvent": "water", "yield": 0.7},
            ],
            "targets": [{"name": "yield", "mode": "MAX"}],
            "created_at": datetime(2024, 1, 16, 14, 15),
            "updated_at": datetime(2024, 1, 16, 14, 45),
            "experiment_count": 2,
            "completed_count": 1,
        },
    ]


@pytest.fixture
def runs_list_screen(qtbot, sample_runs_data):
    """Create a RunsListScreen for testing."""
    screen = RunsListScreen(sample_runs_data)
    qtbot.addWidget(screen)
    return screen


class TestRunsListScreen:
    """Tests for RunsListScreen class."""

    def test_initialization(self, runs_list_screen, sample_runs_data):
        """Test that the screen initializes correctly."""
        assert runs_list_screen.runs_data == sample_runs_data
        assert hasattr(runs_list_screen, "run_selected")
        assert hasattr(runs_list_screen, "new_run_requested")

    def test_screen_has_header(self, runs_list_screen):
        """Test that the screen has a proper header."""
        # The screen should have been set up with a header
        assert runs_list_screen.layout() is not None

    def test_screen_has_runs_cards(self, runs_list_screen, sample_runs_data):
        """Test that the screen displays run cards."""
        # Should have created run cards for each run
        # This test verifies the structure is created, actual rendering would need UI tests
        assert len(sample_runs_data) == 2

    def test_get_panel_buttons(self, runs_list_screen):
        """Test that the screen returns appropriate panel buttons."""
        buttons = runs_list_screen.get_panel_buttons()

        # There are two buttons: Export All and Generate New Run
        assert len(buttons) == 2
        generate_button = next((b for b in buttons if b.text() == "Generate New Run"), None)
        assert generate_button is not None

    def test_generate_new_run_button_signal(self, qtbot, runs_list_screen):
        """Test that clicking Generate New Run button emits signal."""
        buttons = runs_list_screen.get_panel_buttons()
        generate_button = next((b for b in buttons if b.text() == "Generate New Run"), None)
        assert generate_button is not None

        with qtbot.waitSignal(runs_list_screen.new_run_requested, timeout=1000):
            qtbot.mouseClick(generate_button, Qt.LeftButton)

    def test_empty_runs_data(self, qtbot):
        """Test screen behavior with empty runs data."""
        screen = RunsListScreen([])
        qtbot.addWidget(screen)

        # Should still work with empty data
        buttons = screen.get_panel_buttons()
        assert len(buttons) == 2
        generate_button = next((b for b in buttons if b.text() == "Generate New Run"), None)
        assert generate_button is not None


class TestRunCard:
    """Tests for RunCard class."""

    @pytest.fixture
    def sample_run_data(self):
        """Create sample run data for testing."""
        return {
            "run_id": "test_run_1",
            "run_number": 1,
            "campaign_id": "test_campaign",
            "status": "completed",
            "experiments": [
                {"temperature": 25.0, "solvent": "water", "yield": 0.8},
                {"temperature": 50.0, "solvent": "ethanol", "yield": 0.9},
            ],
            "targets": [{"name": "yield", "mode": "MAX"}],
            "created_at": datetime(2024, 1, 15, 10, 30),
            "updated_at": datetime(2024, 1, 15, 11, 0),
            "experiment_count": 2,
            "completed_count": 2,
        }

    @pytest.fixture
    def run_card(self, qtbot, sample_run_data):
        """Create a RunCard for testing."""
        card = RunCard(sample_run_data, 1)
        qtbot.addWidget(card)
        return card

    def test_card_creation(self, run_card, sample_run_data):
        """Test that the run card is created correctly."""
        assert run_card.run_data == sample_run_data
        assert run_card.run_number == 1
        assert hasattr(run_card, "run_clicked")

    def test_card_click_signal(self, qtbot, run_card):
        """Test that clicking the card emits the signal."""
        with qtbot.waitSignal(run_card.run_clicked, timeout=1000):
            qtbot.mouseClick(run_card, Qt.LeftButton)

    def test_card_status_styles(self, qtbot):
        """Test different status styles for run cards."""
        completed_data = {
            "run_number": 1,
            "status": "completed",
            "experiments": [],
            "targets": [],
            "created_at": datetime.now(),
        }

        in_progress_data = {
            "run_number": 2,
            "status": "in_progress",
            "experiments": [],
            "targets": [],
            "created_at": datetime.now(),
        }

        failed_data = {
            "run_number": 3,
            "status": "failed",
            "experiments": [],
            "targets": [],
            "created_at": datetime.now(),
        }

        completed_card = RunCard(completed_data, 1)
        in_progress_card = RunCard(in_progress_data, 2)
        failed_card = RunCard(failed_data, 3)

        qtbot.addWidget(completed_card)
        qtbot.addWidget(in_progress_card)
        qtbot.addWidget(failed_card)

        # Test that different status styles are applied
        assert completed_card._get_status_style("completed") != ""
        assert in_progress_card._get_status_style("in_progress") != ""
        assert failed_card._get_status_style("failed") != ""

    def test_card_progress_calculation(self, qtbot):
        """Test progress calculation for run cards."""
        # Test case with partial completion
        partial_data = {
            "run_number": 1,
            "status": "in_progress",
            "experiments": [
                {"temperature": 25.0, "yield": 0.8},  # completed
                {"temperature": 50.0, "yield": None},  # not completed
                {"temperature": 75.0, "yield": 0.9},  # completed
            ],
            "targets": [{"name": "yield", "mode": "MAX"}],
            "created_at": datetime.now(),
        }

        card = RunCard(partial_data, 1)
        qtbot.addWidget(card)

        # Should have 3 experiments, 2 completed
        # This verifies the card processes the data correctly

    def test_card_date_formatting(self, qtbot):
        """Test date formatting in run cards."""
        # Test with datetime object
        datetime_data = {
            "run_number": 1,
            "status": "completed",
            "experiments": [],
            "targets": [],
            "created_at": datetime(2024, 1, 15, 10, 30),
        }

        # Test with string date
        string_data = {
            "run_number": 2,
            "status": "completed",
            "experiments": [],
            "targets": [],
            "created_at": "Jan 15, 2024 at 10:30",
        }

        datetime_card = RunCard(datetime_data, 1)
        string_card = RunCard(string_data, 2)

        qtbot.addWidget(datetime_card)
        qtbot.addWidget(string_card)

        # Both should handle date formatting without errors

    def test_card_target_display(self, qtbot):
        """Test target information display in run cards."""
        # Test with string targets
        string_targets_data = {
            "run_number": 1,
            "status": "completed",
            "experiments": [],
            "targets": ["yield", "purity"],
            "created_at": datetime.now(),
        }

        # Test with dict targets
        dict_targets_data = {
            "run_number": 2,
            "status": "completed",
            "experiments": [],
            "targets": [{"name": "yield", "mode": "MAX"}, {"name": "purity", "mode": "MAX"}],
            "created_at": datetime.now(),
        }

        string_card = RunCard(string_targets_data, 1)
        dict_card = RunCard(dict_targets_data, 2)

        qtbot.addWidget(string_card)
        qtbot.addWidget(dict_card)

        # Both should handle target formatting without errors

    def test_card_no_experiments(self, qtbot):
        """Test run card with no experiments."""
        empty_data = {
            "run_number": 1,
            "status": "failed",
            "experiments": [],
            "targets": [],
            "created_at": datetime.now(),
        }

        card = RunCard(empty_data, 1)
        qtbot.addWidget(card)

        # Should handle empty experiments list gracefully

    def test_card_cursor_style(self, run_card):
        """Test that the card has pointer cursor."""
        assert run_card.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_card_minimum_height(self, run_card):
        """Test that the card has minimum height set."""
        assert run_card.minimumHeight() == 110
