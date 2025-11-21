import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from app.bayesopt.baybe_service import BayBeService
from app.core.base import BaseWidget
from app.shared.components.buttons import PrimaryButton, SecondaryButton
from app.shared.components.dialogs import ErrorDialog


class ExplanationWorker(QThread):
    """Worker thread for generating SHAP explanations."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, campaign, workspace_path):
        super().__init__()
        self.campaign = campaign
        self.workspace_path = workspace_path

    def run(self):
        try:
            service = BayBeService(self.campaign, self.workspace_path)
            insight = service.get_shap_insight()
            self.finished.emit(insight)
        except Exception as e:
            self.error.emit(str(e))


class ExplanationsPanel(BaseWidget):
    """Panel for the 'Explanations' tab showing SHAP plots."""

    PANEL_TITLE = "Explanations"
    MAIN_MARGINS = (30, 30, 30, 30)
    MAIN_LAYOUT_SPACING = 20
    ALLOWED_PLOT_TYPES = ["bar", "beeswarm", "heatmap", "scatter"]

    def __init__(self, campaign, workspace_path, parent=None):
        self.campaign = campaign
        self.workspace_path = workspace_path
        self.current_figure = None
        self.canvas = None
        self.worker = None
        super().__init__(parent)

    def _setup_widget(self):
        """Setup the explanations panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*self.MAIN_MARGINS)
        main_layout.setSpacing(self.MAIN_LAYOUT_SPACING)

        header_layout = QHBoxLayout()

        title_label = QLabel(self.PANEL_TITLE)
        title_label.setObjectName("PanelTitle")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(self.ALLOWED_PLOT_TYPES)
        self.plot_type_combo.setFixedWidth(150)
        header_layout.addWidget(QLabel("Plot Type:"))
        header_layout.addWidget(self.plot_type_combo)

        self.target_combo = QComboBox()
        if self.campaign and self.campaign.targets:
            self.target_combo.addItems([t.name for t in self.campaign.targets])
        self.target_combo.setFixedWidth(150)
        self.target_combo.setVisible(len(self.campaign.targets) > 1)
        if len(self.campaign.targets) > 1:
            header_layout.addWidget(QLabel("Target:"))
            header_layout.addWidget(self.target_combo)

        self.generate_button = PrimaryButton("Generate Plot")
        self.generate_button.clicked.connect(self._generate_plot)
        header_layout.addWidget(self.generate_button)

        self.download_button = SecondaryButton("Download Plot")
        self.download_button.clicked.connect(self._download_plot)
        self.download_button.setEnabled(False)
        header_layout.addWidget(self.download_button)

        main_layout.addLayout(header_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)

        self.info_label = QLabel(
            "Select options and click 'Generate Plot' to see explanations.\nRequires at least 2 completed runs."
        )
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #666; font-size: 14px;")
        self.plot_layout.addWidget(self.info_label)

        main_layout.addWidget(self.plot_container)
        main_layout.setStretchFactor(self.plot_container, 1)

    def _generate_plot(self):
        """Start the plot generation worker."""
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.info_label.setVisible(False)

        if self.canvas:
            self.plot_layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
            self.canvas = None
            if self.current_figure:
                plt.close(self.current_figure)
                self.current_figure = None

        self.worker = ExplanationWorker(self.campaign, self.workspace_path)
        self.worker.finished.connect(self._handle_plot_finished)
        self.worker.error.connect(self._handle_plot_error)
        self.worker.start()

    def _handle_plot_finished(self, insight):
        """Handle successful insight generation and create plot."""
        try:
            plot_type = self.plot_type_combo.currentText()
            target_index = self.target_combo.currentIndex()

            plt.close("all")  # - close all existing figures

            original_show = plt.show  # override to prevent blocking
            plt.show = lambda *args, **kwargs: None

            try:
                result = insight.plot(plot_type, target_index=target_index)
            finally:
                plt.show = original_show

            if hasattr(result, "figure"):
                fig = result.figure
            elif isinstance(result, Figure):
                fig = result
            else:
                fig = plt.gcf()

            fig.set_size_inches(6, 4)
            fig.tight_layout()

            self.current_figure = fig
            self.canvas = FigureCanvasQTAgg(fig)

            self.canvas.setFixedSize(650, 450)

            self.plot_layout.addWidget(self.canvas, 0, Qt.AlignmentFlag.AlignCenter)
            self.canvas.draw()

            self.generate_button.setEnabled(True)
            self.download_button.setEnabled(True)
            self.progress_bar.setVisible(False)

        except Exception as e:
            self._handle_plot_error(str(e))

    def _download_plot(self):
        """Download the current plot."""
        if not self.current_figure:
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save Plot", self.workspace_path, "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Image (*.svg)"
        )

        if file_path:
            try:
                self.current_figure.savefig(file_path)
            except Exception as e:
                ErrorDialog.show_error("Save Failed", f"Could not save plot: {e}", parent=self)

    def _handle_plot_error(self, error_msg):
        """Handle plot generation error."""
        self.generate_button.setEnabled(True)
        self.download_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.info_label.setVisible(True)
        self.info_label.setText(f"Error generating plot:\n{error_msg}")

        ErrorDialog.show_error("Plot Generation Failed", error_msg, parent=self)

    def set_campaign(self, campaign):
        """Update the campaign."""
        self.campaign = campaign
        self.target_combo.clear()
        if self.campaign and self.campaign.targets:
            self.target_combo.addItems([t.name for t in self.campaign.targets])
        self.target_combo.setVisible(len(self.campaign.targets) > 1)

    def set_workspace_path(self, workspace_path):
        self.workspace_path = workspace_path
