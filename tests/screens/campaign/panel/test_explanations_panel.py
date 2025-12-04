"""
Tests for the ExplanationsPanel.
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLabel, QProgressBar

from app.models.campaign import Campaign, Target
from app.screens.campaign.panel.explanations_panel import ExplanationsPanel, ExplanationWorker
from app.shared.components.buttons import PrimaryButton, SecondaryButton


@pytest.fixture
def sample_campaign():
    """Create a sample campaign for testing."""
    campaign = Campaign()
    campaign.name = "Test Campaign"
    campaign.targets = [Target(name="Yield", mode="Max"), Target(name="Purity", mode="Min")]
    return campaign


@pytest.fixture
def explanations_panel(qtbot, sample_campaign):
    """Create an ExplanationsPanel for testing."""
    panel = ExplanationsPanel(sample_campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)
    panel.show()
    qtbot.waitExposed(panel)
    return panel


def test_panel_initialization(explanations_panel):
    """Test that the panel is initialized correctly."""
    assert explanations_panel.PANEL_TITLE == "Explanations"
    assert isinstance(explanations_panel.plot_type_combo, QComboBox)
    assert isinstance(explanations_panel.target_combo, QComboBox)
    assert isinstance(explanations_panel.generate_button, PrimaryButton)
    assert isinstance(explanations_panel.download_button, SecondaryButton)
    assert isinstance(explanations_panel.progress_bar, QProgressBar)
    assert isinstance(explanations_panel.info_label, QLabel)

    assert explanations_panel.generate_button.isEnabled()
    assert not explanations_panel.download_button.isEnabled()
    assert not explanations_panel.progress_bar.isVisible()
    assert explanations_panel.info_label.isVisible()


def test_plot_type_combo_items(explanations_panel):
    """Test that the plot type combo box has the correct items."""
    expected_items = ["bar", "beeswarm", "heatmap", "scatter"]
    items = [explanations_panel.plot_type_combo.itemText(i) for i in range(explanations_panel.plot_type_combo.count())]
    assert items == expected_items


def test_target_combo_items(explanations_panel, sample_campaign):
    """Test that the target combo box has the correct items."""
    expected_items = [t.name for t in sample_campaign.targets]
    items = [explanations_panel.target_combo.itemText(i) for i in range(explanations_panel.target_combo.count())]
    assert items == expected_items
    assert explanations_panel.target_combo.isVisible()


def test_target_combo_visibility_single_target(qtbot):
    """Test that the target combo box is hidden for single-target campaigns."""
    campaign = Campaign()
    campaign.targets = [Target(name="Yield", mode="Max")]
    panel = ExplanationsPanel(campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)

    assert not panel.target_combo.isVisible()


@patch("app.screens.campaign.panel.explanations_panel.ExplanationWorker")
def test_generate_plot_starts_worker(mock_worker_class, explanations_panel, qtbot):
    """Test that clicking generate button starts the worker."""
    mock_worker = MagicMock()
    mock_worker_class.return_value = mock_worker

    qtbot.mouseClick(explanations_panel.generate_button, Qt.LeftButton)

    assert not explanations_panel.generate_button.isEnabled()
    assert explanations_panel.progress_bar.isVisible()
    assert not explanations_panel.info_label.isVisible()

    mock_worker_class.assert_called_with(explanations_panel.campaign, "test_workspace")
    mock_worker.start.assert_called_once()

    # we can't easily check signal connections on mocks, but we can verify the flow


@patch("app.screens.campaign.panel.explanations_panel.plt")
@patch("app.screens.campaign.panel.explanations_panel.FigureCanvasQTAgg")
def test_handle_plot_finished(mock_canvas_class, mock_plt, explanations_panel):
    """Test handling of finished plot generation."""
    mock_insight = MagicMock()
    mock_figure = MagicMock()
    mock_insight.plot.return_value.figure = mock_figure

    mock_canvas = MagicMock()
    mock_canvas_class.return_value = mock_canvas

    explanations_panel.plot_layout = MagicMock()

    explanations_panel._handle_plot_finished(mock_insight)

    mock_insight.plot.assert_called_once()

    mock_figure.set_size_inches.assert_called_with(6, 4)
    mock_figure.tight_layout.assert_called_once()

    mock_canvas_class.assert_called_with(mock_figure)
    mock_canvas.setFixedSize.assert_called_with(650, 450)
    mock_canvas.draw.assert_called_once()

    assert explanations_panel.generate_button.isEnabled()
    assert explanations_panel.download_button.isEnabled()
    assert not explanations_panel.progress_bar.isVisible()
    assert explanations_panel.current_figure == mock_figure


@patch("app.screens.campaign.panel.explanations_panel.ErrorDialog")
def test_handle_plot_error(mock_error_dialog, explanations_panel):
    """Test handling of plot generation error."""
    error_msg = "Test error"
    explanations_panel._handle_plot_error(error_msg)

    assert explanations_panel.generate_button.isEnabled()
    assert not explanations_panel.download_button.isEnabled()
    assert not explanations_panel.progress_bar.isVisible()
    assert explanations_panel.info_label.isVisible()
    assert error_msg in explanations_panel.info_label.text()

    mock_error_dialog.show_error.assert_called_once()


@patch("app.screens.campaign.panel.explanations_panel.QFileDialog.getSaveFileName")
def test_download_plot(mock_get_save_file_name, explanations_panel):
    """Test downloading the plot."""
    mock_figure = MagicMock()
    explanations_panel.current_figure = mock_figure

    mock_get_save_file_name.return_value = ("test_plot.png", "PNG Image (*.png)")

    explanations_panel._download_plot()

    mock_figure.savefig.assert_called_with("test_plot.png")


@patch("app.screens.campaign.panel.explanations_panel.QFileDialog.getSaveFileName")
def test_download_plot_cancel(mock_get_save_file_name, explanations_panel):
    """Test cancelling download."""
    mock_figure = MagicMock()
    explanations_panel.current_figure = mock_figure

    mock_get_save_file_name.return_value = ("", "")

    explanations_panel._download_plot()

    mock_figure.savefig.assert_not_called()


def test_set_campaign_updates_targets(explanations_panel):
    """Test that set_campaign updates the target combo box."""
    new_campaign = Campaign()
    new_campaign.targets = [Target(name="New Target", mode="Max")]

    explanations_panel.set_campaign(new_campaign)

    assert explanations_panel.campaign == new_campaign
    assert explanations_panel.target_combo.count() == 1
    assert explanations_panel.target_combo.itemText(0) == "New Target"
    assert not explanations_panel.target_combo.isVisible()


@patch("app.screens.campaign.panel.explanations_panel.BayBeService")
def test_worker_run(mock_service_class):
    """Test the ExplanationWorker run method."""
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_insight = MagicMock()
    mock_service.get_shap_insight.return_value = mock_insight

    worker = ExplanationWorker(MagicMock(), "test_path")

    worker.finished = MagicMock()
    worker.error = MagicMock()

    worker.run()

    mock_service.get_shap_insight.assert_called_once()
    worker.finished.emit.assert_called_once_with(mock_insight)
    worker.error.emit.assert_not_called()


@patch("app.screens.campaign.panel.explanations_panel.BayBeService")
def test_worker_run_error(mock_service_class):
    """Test the ExplanationWorker run method with error."""
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    mock_service.get_shap_insight.side_effect = Exception("Service error")

    worker = ExplanationWorker(MagicMock(), "test_path")

    worker.finished = MagicMock()
    worker.error = MagicMock()

    worker.run()

    worker.finished.emit.assert_not_called()
    worker.error.emit.assert_called_once_with("Service error")
