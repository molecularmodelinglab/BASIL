from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.core.base import BaseWidget
from app.screens.start.components.campaign_loader import CampaignLoader
from app.shared.components.buttons import PrimaryButton
from app.shared.utils.export_campaign import CampaignExporter, ParameterFormatter


class ParametersPanel(BaseWidget):
    """Panel for the 'Parameters' tab."""

    data_exported = Signal()

    NO_PARAMETERS_MESSAGE = "No parameters defined for this campaign."

    EXPORT_DATA_BUTTON_TEXT = "Export Data"

    PARAMETER_HEADER = "Parameter"
    TYPE_HEADER = "Type"
    VALUES_HEADER = "Values"

    MAIN_MARGINS = (30, 30, 30, 30)
    MAIN_LAYOUT_SPACING = 25
    MIN_TABLE_HEIGHT = 300
    HEADER_FONT_SIZE = 18

    def __init__(self, campaign=None, workspace_path=None, parent=None):
        self.campaign = campaign
        self.workspace_path = workspace_path
        self.campaign_loader = CampaignLoader(workspace_path) if workspace_path else None
        self.is_editing = False
        super().__init__(parent)

    def _setup_widget(self):
        """Setup the parameters panel UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*self.MAIN_MARGINS)
        main_layout.setSpacing(self.MAIN_LAYOUT_SPACING)

        self.info_label = QLabel()
        self.info_label.setObjectName("ParametersInfo")
        self.info_label.setStyleSheet("color: #666; font-size: 14px; margin-bottom: 10px;")
        main_layout.addWidget(self.info_label)

        self.parameters_table = self._create_parameters_table()
        main_layout.addWidget(self.parameters_table)

        main_layout.addStretch()
        self._load_parameters_data()

    def _create_parameters_table(self) -> QTableWidget:
        """Create the parameters table widget."""
        table = QTableWidget()
        table.setObjectName("ParametersTable")
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([self.PARAMETER_HEADER, self.TYPE_HEADER, self.VALUES_HEADER])

        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        table.setAlternatingRowColors(True)

        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        vertical_header = table.verticalHeader()
        vertical_header.setVisible(True)
        vertical_header.setDefaultSectionSize(40)

        table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)

        return table

    def _load_parameters_data(self):
        """Load parameters data into the table."""
        if not self.campaign or not self.campaign.parameters:
            self._show_no_parameters_state()
            return

        parameters = self.campaign.parameters
        self.parameters_table.setRowCount(len(parameters))

        param_count = len(parameters)
        self.info_label.setText(f"Parameters ({param_count})")

        for row, param in enumerate(parameters):
            name_item = QTableWidgetItem(param.name or "")
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.parameters_table.setItem(row, 0, name_item)

            type_text = self._format_parameter_type(param)
            type_item = QTableWidgetItem(type_text)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.parameters_table.setItem(row, 1, type_item)

            values_text = self._format_parameter_values(param)
            values_item = QTableWidgetItem(values_text)
            values_item.setFlags(values_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.parameters_table.setItem(row, 2, values_item)

    def _format_parameter_type(self, param) -> str:
        """Format parameter type for display."""
        return ParameterFormatter.format_parameter_type(param)

    def _format_parameter_values(self, param) -> str:
        """Format parameter values for display."""
        return ParameterFormatter.format_parameter_values(param)

    def _handle_export_click(self):
        """Handle export button click - export campaign data to CSV."""
        CampaignExporter.export_campaign_to_csv(self.campaign, self)

    def _show_no_parameters_state(self):
        """Show state when no parameters are defined."""
        self.parameters_table.setRowCount(0)
        self.info_label.setText(self.NO_PARAMETERS_MESSAGE)

    def get_panel_buttons(self):
        """Return buttons specific to this panel."""
        buttons = []

        export_button = PrimaryButton(self.EXPORT_DATA_BUTTON_TEXT)
        export_button.clicked.connect(self._handle_export_click)
        buttons.append(export_button)

        return buttons

    def set_campaign(self, campaign):
        """Set the campaign and update the parameters display."""
        self.campaign = campaign
        self._load_parameters_data()

    def set_workspace_path(self, workspace_path: str):
        """Set the workspace path and update the campaign loader."""
        self.workspace_path = workspace_path
        self.campaign_loader = CampaignLoader(workspace_path) if workspace_path else None
