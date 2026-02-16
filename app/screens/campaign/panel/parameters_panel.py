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
from app.shared.utils.export_campaign import CampaignExporter, ParameterFormatter, TargetFormatter


class ParametersPanel(BaseWidget):
    """Panel for the 'Parameters' tab."""

    data_exported = Signal()

    NO_PARAMETERS_MESSAGE = "No parameters defined for this campaign."
    NO_TARGETS_MESSAGE = "No targets defined for this campaign."

    EXPORT_DATA_BUTTON_TEXT = "Export Data"

    PARAMETER_HEADER = "Parameter"
    TYPE_HEADER = "Type"
    VALUES_HEADER = "Values"

    TARGET_HEADER = "Target"
    MODE_HEADER = "Mode"
    TARGET_TRANSFORM = "Transform"
    TARGET_WEIGHT = "Weight"
    TARGET_VALUES = "Values"

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

        self.info_label_parameters = QLabel()
        self.info_label_parameters.setObjectName("ParametersInfo")
        self.info_label_parameters.setStyleSheet("color: #666; font-size: 14px; margin-bottom: 10px;")
        main_layout.addWidget(self.info_label_parameters)

        self.parameters_table = self._create_parameters_table()
        main_layout.addWidget(self.parameters_table)

        self.info_label_targets = QLabel()
        self.info_label_targets.setObjectName("TargetsInfo")
        self.info_label_targets.setStyleSheet("color: #666; font-size: 14px; margin-bottom: 10px;")
        main_layout.addWidget(self.info_label_targets)

        self.targets_table = self._create_targets_table()
        main_layout.addWidget(self.targets_table)

        main_layout.addStretch()
        self._load_parameters_data()
        self._load_targets_data()

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

    def _create_targets_table(self) -> QTableWidget:
        """Create the targets table widget."""
        table = QTableWidget()
        table.setObjectName("TargetsTable")
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(
            [self.TARGET_HEADER, self.MODE_HEADER, self.TARGET_TRANSFORM, self.TARGET_WEIGHT, self.TARGET_VALUES]
        )

        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        table.setAlternatingRowColors(True)

        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

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
        self.info_label_parameters.setText(f"Parameters ({param_count})")

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

    def _load_targets_data(self):
        """Load targets data into the table."""
        if not self.campaign or not self.campaign.targets:
            self._show_no_targets_state()
            return

        targets = self.campaign.targets
        self.targets_table.setRowCount(len(targets))

        targets_count = len(targets)
        self.info_label_targets.setText(f"Targets ({targets_count})")

        for row, target in enumerate(targets):
            name_item = QTableWidgetItem(target.name or "")
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.targets_table.setItem(row, 0, name_item)

            mode_text = self._format_target_mode(target)
            mode_item = QTableWidgetItem(mode_text)
            mode_item.setFlags(mode_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.targets_table.setItem(row, 1, mode_item)

            transform_text = self._format_target_transform(target)
            transform_item = QTableWidgetItem(transform_text)
            transform_item.setFlags(transform_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.targets_table.setItem(row, 2, transform_item)

            weight_text = self._format_target_weight(target)
            weight_item = QTableWidgetItem(weight_text)
            weight_item.setFlags(weight_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.targets_table.setItem(row, 3, weight_item)

            target_values_text = self._format_target_values(target)
            target_values_item = QTableWidgetItem(target_values_text)
            target_values_item.setFlags(target_values_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.targets_table.setItem(row, 4, target_values_item)

    def _format_parameter_type(self, param) -> str:
        """Format parameter type for display."""
        return ParameterFormatter.format_parameter_type(param)

    def _format_parameter_values(self, param) -> str:
        """Format parameter values for display."""
        return ParameterFormatter.format_parameter_values(param)

    def _format_target_mode(self, target) -> str:
        """Format target mode for display."""
        return TargetFormatter.format_target_mode(target)

    def _format_target_transform(self, target) -> str:
        """Format target transform for display."""
        return TargetFormatter.format_target_transform(target)

    def _format_target_weight(self, target) -> str:
        """Format target weight for display."""
        return TargetFormatter.format_target_weight(target)

    def _format_target_values(self, target) -> str:
        """Format target values for display."""
        return TargetFormatter.format_target_values(target)

    def _handle_export_click(self):
        """Handle export button click - export campaign data to CSV."""
        CampaignExporter.export_campaign_to_csv(self.campaign, self)

    def _show_no_parameters_state(self):
        """Show state when no parameters are defined."""
        self.parameters_table.setRowCount(0)
        self.info_label_parameters.setText(self.NO_PARAMETERS_MESSAGE)

    def _show_no_targets_state(self):
        """Show state when no targets are defined."""
        self.targets_table.setRowCount(0)
        self.info_label_targets.setText(self.NO_TARGETS_MESSAGE)

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
        self._load_targets_data()

    def set_workspace_path(self, workspace_path: str):
        """Set the workspace path and update the campaign loader."""
        self.workspace_path = workspace_path
        self.campaign_loader = CampaignLoader(workspace_path) if workspace_path else None
