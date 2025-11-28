import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.bayesopt.baybe_service import BayBeService
from app.core.base import BaseWidget
from app.shared.components.buttons import PrimaryButton, SecondaryButton
from app.shared.components.dialogs import ErrorDialog


class VisualizationsPanel(BaseWidget):
    """Panel for the 'Visualizations' tab showing custom plots."""

    PANEL_TITLE = "Visualizations"
    MAIN_MARGINS = (30, 30, 30, 30)
    MAIN_LAYOUT_SPACING = 20
    GENERATE_BUTTON_TEXT = "Generate Plot"
    SAVE_BUTTON_TEXT = "Save Plot"

    def __init__(self, campaign, workspace_path, parent=None):
        self.campaign = campaign
        self.workspace_path = workspace_path
        self.current_figure = None
        self.canvas = None
        self.df = None
        super().__init__(parent)

    def _setup_widget(self):
        """Setup the visualizations panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*self.MAIN_MARGINS)
        main_layout.setSpacing(self.MAIN_LAYOUT_SPACING)

        # Controls Section
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(20)

        # Axes Grid (Left)
        axes_widget = QWidget()
        axes_layout = QGridLayout(axes_widget)
        axes_layout.setContentsMargins(0, 0, 0, 0)
        axes_layout.setSpacing(10)

        axes_layout.addWidget(QLabel("X Axis:"), 0, 0)
        self.x_combo = QComboBox()
        self.x_combo.setFixedWidth(150)
        axes_layout.addWidget(self.x_combo, 0, 1)

        axes_layout.addWidget(QLabel("Y Axis:"), 0, 2)
        self.y_combo = QComboBox()
        self.y_combo.setFixedWidth(150)
        axes_layout.addWidget(self.y_combo, 0, 3)

        axes_layout.addWidget(QLabel("Z Axis (Optional):"), 1, 0)
        self.z_combo = QComboBox()
        self.z_combo.setFixedWidth(150)
        axes_layout.addWidget(self.z_combo, 1, 1)

        axes_layout.addWidget(QLabel("Color (Optional):"), 1, 2)
        self.color_combo = QComboBox()
        self.color_combo.setFixedWidth(150)
        axes_layout.addWidget(self.color_combo, 1, 3)

        controls_layout.addWidget(axes_widget)

        # Spacer
        controls_layout.addStretch()

        # Buttons (Right)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.generate_button = PrimaryButton(self.GENERATE_BUTTON_TEXT)
        self.generate_button.clicked.connect(self._generate_plot)
        buttons_layout.addWidget(self.generate_button)

        self.download_button = SecondaryButton(self.SAVE_BUTTON_TEXT)
        self.download_button.clicked.connect(self._download_plot)
        self.download_button.setEnabled(False)
        buttons_layout.addWidget(self.download_button)

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)

        controls_layout.addWidget(buttons_widget, 0, Qt.AlignmentFlag.AlignBottom)

        main_layout.addWidget(controls_widget)

        self.plot_container = QWidget()
        self.plot_layout = QVBoxLayout(self.plot_container)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)

        self.info_label = QLabel("Select axes and click 'Generate Plot'.\nRequires experimental data.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #666; font-size: 14px;")
        self.plot_layout.addWidget(self.info_label)

        main_layout.addWidget(self.plot_container)
        main_layout.setStretchFactor(self.plot_container, 1)

        self._load_data()

    def _load_data(self):
        """Load experimental data and populate combo boxes."""
        try:
            service = BayBeService(self.campaign, self.workspace_path)
            self.df = service.get_experimental_data()

            if self.df is not None and not self.df.empty:
                columns = sorted(self.df.columns.tolist())

                # Populate combos
                self.x_combo.clear()
                self.x_combo.addItems(columns)

                self.y_combo.clear()
                self.y_combo.addItems(columns)
                if len(columns) > 1:
                    self.y_combo.setCurrentIndex(1)

                self.z_combo.clear()
                self.z_combo.addItem("None")
                self.z_combo.addItems(columns)

                self.color_combo.clear()
                self.color_combo.addItem("None")
                self.color_combo.addItems(columns)

                self.info_label.setText("Select axes and click 'Generate Plot'.")
                self.generate_button.setEnabled(True)
            else:
                self.info_label.setText("No experimental data found.")
                self.generate_button.setEnabled(False)

        except Exception as e:
            self.info_label.setText(f"Error loading data: {e}")
            self.generate_button.setEnabled(False)

    def _generate_plot(self):
        """Generate the plot based on selections."""
        if self.df is None or self.df.empty:
            return

        x_col = self.x_combo.currentText()
        y_col = self.y_combo.currentText()
        z_col = self.z_combo.currentText()
        color_col = self.color_combo.currentText()

        if not x_col or not y_col:
            return

        # Clear previous plot
        if self.canvas:
            self.plot_layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
            self.canvas = None

        if self.current_figure:
            plt.close(self.current_figure)
            self.current_figure = None

        try:
            fig = Figure(figsize=(6, 4))

            # Determine plot type
            is_3d = z_col != "None"
            has_color = color_col != "None"

            if is_3d:
                ax = fig.add_subplot(111, projection="3d")
                xs = self.df[x_col]
                ys = self.df[y_col]
                zs = self.df[z_col]

                c = self.df[color_col] if has_color else None

                sc = ax.scatter(xs, ys, zs, c=c, cmap="viridis" if has_color else None)

                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
                ax.set_zlabel(z_col)

                if has_color:
                    cbar = fig.colorbar(sc, ax=ax)
                    cbar.set_label(color_col)
            else:
                ax = fig.add_subplot(111)
                xs = self.df[x_col]
                ys = self.df[y_col]

                c = self.df[color_col] if has_color else None

                sc = ax.scatter(xs, ys, c=c, cmap="viridis" if has_color else None)

                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)

                if has_color:
                    cbar = fig.colorbar(sc, ax=ax)
                    cbar.set_label(color_col)

                ax.grid(True, linestyle="--", alpha=0.7)

            fig.tight_layout()

            self.current_figure = fig
            self.canvas = FigureCanvasQTAgg(fig)
            self.canvas.setFixedSize(650, 450)

            self.plot_layout.addWidget(self.canvas, 0, Qt.AlignmentFlag.AlignCenter)
            self.canvas.draw()

            self.download_button.setEnabled(True)
            self.info_label.setVisible(False)

        except Exception as e:
            ErrorDialog.show_error("Plot Error", str(e), parent=self)
            self.info_label.setVisible(True)
            self.info_label.setText(f"Error generating plot: {e}")

    def _download_plot(self):
        """Download the current plot."""
        if not self.current_figure:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", self.workspace_path, "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Image (*.svg)"
        )

        if file_path:
            try:
                self.current_figure.savefig(file_path)
            except Exception as e:
                ErrorDialog.show_error("Save Failed", f"Could not save plot: {e}", parent=self)

    def set_campaign(self, campaign):
        """Update the campaign and reload data."""
        self.campaign = campaign
        self._load_data()

    def set_workspace_path(self, workspace_path):
        self.workspace_path = workspace_path
        self._load_data()
