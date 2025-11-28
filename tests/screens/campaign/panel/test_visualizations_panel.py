"""
Tests for the VisualizationsPanel.
"""

from unittest.mock import MagicMock, patch

import pytest
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from app.models.campaign import Campaign, Target
from app.screens.campaign.panel.visualizations_panel import VisualizationsPanel
from app.shared.components.buttons import PrimaryButton, SecondaryButton


@pytest.fixture
def sample_campaign():
    campaign = Campaign()
    campaign.name = "Test Campaign"
    campaign.targets = [Target(name="Yield", mode="Max")]
    return campaign


@pytest.fixture
def visualizations_panel(qtbot, sample_campaign):
    panel = VisualizationsPanel(sample_campaign, workspace_path="test_workspace")
    qtbot.addWidget(panel)
    panel.show()
    qtbot.waitExposed(panel)
    return panel


def test_panel_initialization(visualizations_panel):
    assert visualizations_panel.PANEL_TITLE == "Visualizations"
    assert hasattr(visualizations_panel, "x_combo")
    assert hasattr(visualizations_panel, "y_combo")
    assert hasattr(visualizations_panel, "z_combo")
    assert hasattr(visualizations_panel, "color_combo")
    assert isinstance(visualizations_panel.generate_button, PrimaryButton)
    assert isinstance(visualizations_panel.download_button, SecondaryButton)
    assert isinstance(visualizations_panel.info_label, QLabel)


@patch("app.screens.campaign.panel.visualizations_panel.BayBeService")
def test_load_data_populates_combos(mock_service_class, visualizations_panel):
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
    mock_service = MagicMock()
    mock_service.get_experimental_data.return_value = df
    mock_service_class.return_value = mock_service

    # Force reload
    visualizations_panel._load_data()

    # Combos should be populated
    x_items = [visualizations_panel.x_combo.itemText(i) for i in range(visualizations_panel.x_combo.count())]
    y_items = [visualizations_panel.y_combo.itemText(i) for i in range(visualizations_panel.y_combo.count())]
    z_items = [visualizations_panel.z_combo.itemText(i) for i in range(visualizations_panel.z_combo.count())]
    color_items = [visualizations_panel.color_combo.itemText(i) for i in range(visualizations_panel.color_combo.count())]

    expected_columns = sorted(df.columns.tolist())

    assert x_items == expected_columns
    assert y_items == expected_columns
    # z and color include a leading 'None'
    assert z_items[0] == "None"
    assert color_items[0] == "None"
    assert visualizations_panel.generate_button.isEnabled()


@patch("app.screens.campaign.panel.visualizations_panel.BayBeService")
def test_no_data_disables_generate(mock_service_class, visualizations_panel):
    mock_service = MagicMock()
    mock_service.get_experimental_data.return_value = None
    mock_service_class.return_value = mock_service

    visualizations_panel._load_data()

    assert not visualizations_panel.generate_button.isEnabled()
    assert "No experimental data" in visualizations_panel.info_label.text()


@patch("app.screens.campaign.panel.visualizations_panel.FigureCanvasQTAgg")
@patch("app.screens.campaign.panel.visualizations_panel.BayBeService")
def test_generate_plot_creates_figure(mock_service_class, mock_canvas_class, visualizations_panel):
    df = pd.DataFrame({"X": [1, 2, 3], "Y": [4, 5, 6]})
    mock_service = MagicMock()
    mock_service.get_experimental_data.return_value = df
    mock_service_class.return_value = mock_service

    visualizations_panel._load_data()

    visualizations_panel.x_combo.setCurrentIndex(0)
    visualizations_panel.y_combo.setCurrentIndex(0)

    mock_canvas = MagicMock()
    mock_canvas_class.return_value = mock_canvas

    visualizations_panel.plot_layout = MagicMock()

    visualizations_panel._generate_plot()

    assert visualizations_panel.current_figure is not None
    mock_canvas_class.assert_called()
    assert visualizations_panel.download_button.isEnabled()
    assert not visualizations_panel.info_label.isVisible()


@patch("app.screens.campaign.panel.visualizations_panel.FigureCanvasQTAgg")
@patch("app.screens.campaign.panel.visualizations_panel.BayBeService")
def test_generate_plot_3d_and_color(mock_service_class, mock_canvas_class, visualizations_panel):
    df = pd.DataFrame({"X": [1, 2, 3], "Y": [4, 5, 6], "Z": [7, 8, 9], "C": [0.1, 0.5, 0.9]})
    mock_service = MagicMock()
    mock_service.get_experimental_data.return_value = df
    mock_service_class.return_value = mock_service

    visualizations_panel._load_data()

    visualizations_panel.x_combo.setCurrentIndex(0)
    visualizations_panel.y_combo.setCurrentIndex(1)
    z_index = [visualizations_panel.z_combo.itemText(i) for i in range(visualizations_panel.z_combo.count())].index("Z")
    color_index = [visualizations_panel.color_combo.itemText(i) for i in range(visualizations_panel.color_combo.count())].index("C")
    visualizations_panel.z_combo.setCurrentIndex(z_index)
    visualizations_panel.color_combo.setCurrentIndex(color_index)

    mock_canvas = MagicMock()
    mock_canvas_class.return_value = mock_canvas

    visualizations_panel.plot_layout = MagicMock()

    visualizations_panel._generate_plot()

    assert visualizations_panel.current_figure is not None
    mock_canvas.draw.assert_called()
    assert visualizations_panel.download_button.isEnabled()


@patch("app.screens.campaign.panel.visualizations_panel.QFileDialog.getSaveFileName")
def test_download_plot(mock_get_save_file_name, visualizations_panel):
    mock_figure = MagicMock()
    visualizations_panel.current_figure = mock_figure

    mock_get_save_file_name.return_value = ("test_plot.png", "PNG Image (*.png)")

    visualizations_panel._download_plot()

    mock_figure.savefig.assert_called_with("test_plot.png")


@patch("app.screens.campaign.panel.visualizations_panel.QFileDialog.getSaveFileName")
def test_download_plot_cancel(mock_get_save_file_name, visualizations_panel):
    mock_figure = MagicMock()
    visualizations_panel.current_figure = mock_figure

    mock_get_save_file_name.return_value = ("", "")

    visualizations_panel._download_plot()

    mock_figure.savefig.assert_not_called()


@patch("app.screens.campaign.panel.visualizations_panel.BayBeService")
def test_load_data_error_shows_message(mock_service_class, visualizations_panel):
    mock_service = MagicMock()
    mock_service.get_experimental_data.side_effect = Exception("boom")
    mock_service_class.return_value = mock_service

    visualizations_panel._load_data()

    assert "Error loading data" in visualizations_panel.info_label.text()
    assert not visualizations_panel.generate_button.isEnabled()


@patch("app.screens.campaign.panel.visualizations_panel.BayBeService")
def test_set_campaign_triggers_reload(mock_service_class, visualizations_panel):
    mock_service = MagicMock()
    mock_service.get_experimental_data.return_value = None
    mock_service_class.return_value = mock_service

    visualizations_panel.set_campaign(Campaign())

    assert not visualizations_panel.generate_button.isEnabled()
