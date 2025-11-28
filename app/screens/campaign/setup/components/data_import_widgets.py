"""
Specialized widgets for the data import step.

This module contains all UI components for the data import functionality:
- PageHeaderWidget: Page title and description
- FileValidator: File validation logic
- DragDropArea: Drag & drop functionality
- UploadSectionWidget: File upload coordination
- TemplateSectionWidget: Template generation buttons
- DataPreviewWidget: Display imported data with validation status

"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.shared.components.dialogs import ErrorDialog

from .csv_data_importer import CSVValidationResult


class PageHeaderWidget(QWidget):
    """Widget for displaying page title and description."""

    TITLE_TEXT = "Import Existing Data"
    DESCRIPTION_TEXT = (
        "Add existing/historical experimental data from CSV files. This step is optional - "
        "you can skip it and create campaigns without historical data."
        " Click 'Download CSV' to get a template file matching your campaign parameters."
    )

    NO_MARGINS = (0, 0, 0, 0)

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create and arrange header components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.NO_MARGINS)

        self.title_label = QLabel(self.TITLE_TEXT)
        self.title_label.setObjectName("DataImportTitle")
        self.description_label = QLabel(self.DESCRIPTION_TEXT)
        self.description_label.setObjectName("DataImportDescription")

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)


class FileValidator:
    """Handles file validation logic for CSV uploads."""

    # Error Messages
    FILE_NOT_EXIST_MESSAGE = "File does not exist: {0}"
    NOT_A_FILE_MESSAGE = "Path is not a file: {0}"
    NOT_CSV_MESSAGE = "File is not a CSV: {0}"
    CANNOT_READ_MESSAGE = "Cannot read file: {0}"
    VALIDATION_ERROR_MESSAGE = "Error validating file: {0}"

    @staticmethod
    def validate_file(file_path: str) -> tuple[bool, str]:
        """
        Validate that the selected file is accessible and appears to be a CSV.

        Args:
            file_path: Path to the file to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return False, FileValidator.FILE_NOT_EXIST_MESSAGE.format(file_path)

            if not path.is_file():
                return False, FileValidator.NOT_A_FILE_MESSAGE.format(file_path)

            if path.suffix.lower() != ".csv":
                return False, FileValidator.NOT_CSV_MESSAGE.format(file_path)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    f.readline()
            except (PermissionError, UnicodeDecodeError) as e:
                return False, FileValidator.CANNOT_READ_MESSAGE.format(e)

            return True, ""

        except Exception as e:
            return False, FileValidator.VALIDATION_ERROR_MESSAGE.format(e)


class DragDropArea(QFrame):
    """Frame widget that handles drag & drop functionality for CSV files."""

    file_dropped = Signal(str)  # Emitted when valid file is dropped

    DROP_AREA_TEXT = "Drop CSV file here or"
    BROWSE_BUTTON_TEXT = "Browse CSV file"

    IMPORT_ERROR_TITLE = "Import Error"

    MIN_HEIGHT = 120
    LAYOUT_SPACING = 10
    NO_MARGINS = (0, 0, 0, 0)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("DragDropArea")
        self.file_validator = FileValidator()
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._setup_drag_drop()

    def _setup_ui(self) -> None:
        """Create and arrange the drop area UI."""
        self.setMinimumHeight(self.MIN_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(self.LAYOUT_SPACING)
        layout.setContentsMargins(*self.NO_MARGINS)

        self.drop_text = QLabel(self.DROP_AREA_TEXT)
        self.drop_text.setObjectName("DropAreaText")
        self.drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.drop_text)

        self.browse_button = QPushButton(self.BROWSE_BUTTON_TEXT)
        self.browse_button.setObjectName("DataImportBrowseButton")
        layout.addWidget(self.browse_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def _setup_drag_drop(self) -> None:
        """Enable drag & drop functionality."""
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event."""
        if self._is_valid_drag(event):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag move event."""
        if self._is_valid_drag(event):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event."""
        if self._is_valid_drag(event):
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                is_valid, error_msg = self.file_validator.validate_file(file_path)

                if is_valid:
                    self.logger.info(f"File dropped: {file_path}")
                    self.file_dropped.emit(file_path)
                    event.accept()
                    return
                else:
                    ErrorDialog.show_error(self.IMPORT_ERROR_TITLE, error_msg, parent=self)

        self.logger.warning("Invalid file dropped")
        event.ignore()

    def _is_valid_drag(self, event) -> bool:
        """Check if the drag event contains valid files."""
        if not event.mimeData().hasUrls():
            return False

        urls = event.mimeData().urls()
        if not urls:
            return False

        # Check if first file is a CSV
        file_path = urls[0].toLocalFile()
        return file_path.lower().endswith(".csv")


class UploadSectionWidget(QWidget):
    """Main widget for file upload functionality with drag&drop and browse button."""

    file_selected = Signal(str)  # Emitted when user selects a file

    SECTION_TITLE = "Upload experimental data"
    DIALOG_TITLE = "Select CSV File"
    FILE_FILTER = "CSV files (*.csv);;All files (*.*)"

    IMPORT_ERROR_TITLE = "Import Error"
    INVALID_FILE_MESSAGE = "Invalid file selected: {0}"

    NO_MARGINS = (0, 0, 0, 0)

    def __init__(self) -> None:
        super().__init__()
        self.file_validator = FileValidator()
        self.logger = logging.getLogger(__name__)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Create and arrange upload components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.NO_MARGINS)

        # Section title
        self.section_title = QLabel(self.SECTION_TITLE)
        self.section_title.setObjectName("DataImportSectionTitle")
        layout.addWidget(self.section_title)

        # Drag & drop area
        self.drop_area = DragDropArea()
        layout.addWidget(self.drop_area)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.drop_area.browse_button.clicked.connect(self._on_browse_clicked)
        self.drop_area.file_dropped.connect(self._on_file_dropped)

    def _on_browse_clicked(self) -> None:
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(self, self.DIALOG_TITLE, "", self.FILE_FILTER)

        if file_path:
            is_valid, error_msg = self.file_validator.validate_file(file_path)

            if is_valid:
                self.logger.info(f"Valid CSV file selected: {file_path}")
                self.file_selected.emit(file_path)
            else:
                ErrorDialog.show_error(
                    self.IMPORT_ERROR_TITLE, self.INVALID_FILE_MESSAGE.format(error_msg), parent=self
                )
        else:
            self.logger.info("File selection cancelled by user")

    def _on_file_dropped(self, file_path: str) -> None:
        """Handle file dropped from drag & drop area."""
        self.file_selected.emit(file_path)


class TemplateSectionWidget(QWidget):
    """Widget for template generation functionality."""

    template_requested = Signal(str)  # Emitted with format type (csv, xlsx)

    SECTION_TITLE = "Generate a template"
    DOWNLOAD_CSV_BUTTON_TEXT = "Download CSV"

    NO_MARGINS = (0, 0, 0, 0)

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Create and arrange template components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.NO_MARGINS)

        self.section_title = QLabel(self.SECTION_TITLE)
        self.section_title.setObjectName("DataImportSectionTitle")
        layout.addWidget(self.section_title)

        self.download_csv_button = QPushButton(self.DOWNLOAD_CSV_BUTTON_TEXT)
        self.download_csv_button.setObjectName("DataImportTemplateButton")
        layout.addWidget(self.download_csv_button)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.download_csv_button.clicked.connect(self._on_download_csv_clicked)

    def _on_download_csv_clicked(self) -> None:
        """Handle CSV template download."""
        self.template_requested.emit("csv")


class DataPreviewWidget(QWidget):
    """
    Widget for displaying imported CSV data with validation status.

    Shows all imported data in a table with proper headers and provides
    visual feedback about validation errors through cell highlighting.
    """

    # UI Text Constants
    SECTION_TITLE = "Data Preview"
    NO_DATA_TEXT = "No data imported yet"
    EMPTY_DATA_TEXT = "No valid data to display"
    ERROR_DATA_TEXT = "Data contains validation errors - see details below"
    STATUS_HEADER = "Status"
    ERROR_HEADER = "Validation Issues"
    DESCRIPTION_HEADER = "Description"
    FILE_STRUCTURE_ERROR = "File Structure"
    MISSING_COLUMN_ERROR = "Missing Column"
    MISSING_COLUMN_ERROR_MESSAGE = "Required column '{0}' not found"
    CELL_ERRORS_HEADER = "Cell Errors"
    MORE_CELL_ERRORS_MESSAGE = "... and {0} more rows with errors"
    CELL_ERROR_HEADER = "Cell Error"
    CELL_ERROR_MESSAGE = "Row {0}, '{1}': {2}"
    EXTRA_COLUMN_TOOLTIP = "Extra column '{0}' - will be ignored during processing"
    ERROR_TOOLTIP_PREFIX = "Error: {0}"
    DISPLAYING_ALL_ROWS_MESSAGE = "Displaying all {0} rows (no errors)"
    DISPLAYING_ROWS_WITH_ERRORS_MESSAGE = "Displaying {0} rows ({1} valid, {2} with errors)"

    # Status Messages
    NO_DATA_DISPLAYED = "No data displayed"

    # Layout constants
    NO_MARGINS = (0, 0, 0, 0)
    TABLE_MIN_HEIGHT = 200

    def __init__(self) -> None:
        super().__init__()
        self.all_data: List[Dict[str, Any]] = []  # All rows including invalid
        self.valid_data: List[Dict[str, Any]] = []  # Only valid rows
        self.validation_result: Optional["CSVValidationResult"] = None
        self.logger = logging.getLogger(__name__)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Create and arrange preview components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.NO_MARGINS)

        # Section title
        self.section_title = QLabel(self.SECTION_TITLE)
        self.section_title.setObjectName("DataImportSectionTitle")
        layout.addWidget(self.section_title)

        # Status label
        self.status_label = QLabel()
        self.status_label.setObjectName("DataImportStatusLabel")
        layout.addWidget(self.status_label)

        # Preview table
        self.table = self._create_preview_table()
        self.table.setObjectName("DataPreviewTable")
        layout.addWidget(self.table)

        # Initially show no data message
        self._show_no_data_message()

    def _create_preview_table(self) -> QTableWidget:
        """Create and configure the data preview table."""
        table = QTableWidget()
        table.setMinimumHeight(self.TABLE_MIN_HEIGHT)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True)

        # Configure headers
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setDefaultSectionSize(40)

        return table

    def display_data(
        self,
        all_data: List[Dict[str, Any]],
        valid_data: List[Dict[str, Any]],
        validation_result: "CSVValidationResult",
    ) -> None:
        """
        Display all data with validation status highlighting.

        Args:
            all_data: All rows including invalid ones
            valid_data: Only valid rows
            validation_result: Validation results with error information
        """
        self.all_data = all_data
        self.valid_data = valid_data
        self.validation_result = validation_result

        if not all_data:
            self._show_empty_data_message()
            return

        self._update_status_label()
        self._populate_table_with_validation()
        self.logger.info(f"Displaying {len(all_data)} rows ({len(valid_data)} valid) in preview table")

    def _populate_table_with_validation(self) -> None:
        """Populate the table with all data, highlighting invalid cells."""
        if not self.all_data:
            return

        # Get column headers from first row
        headers = list(self.all_data[0].keys())

        self.table.setRowCount(len(self.all_data))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Populate table data with validation highlighting
        for row_index, row_data in enumerate(self.all_data):
            for col_index, header in enumerate(headers):
                value = row_data.get(header, "")
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # Check if this cell has an error
                if self.validation_result and self.validation_result.has_cell_error(row_index, header):
                    # Highlight cells with errors:
                    item.setData(Qt.ItemDataRole.ForegroundRole, QColor("#f44336"))

                    # Add tooltip with error message
                    error_msg = self.validation_result.get_cell_error(row_index, header)
                    item.setToolTip(self.ERROR_TOOLTIP_PREFIX.format(error_msg))
                elif self.validation_result and header in getattr(self.validation_result, "extra_columns", []):
                    # Highlight cells of the extra columns:
                    font = item.font()
                    font.setItalic(True)
                    item.setFont(font)
                    item.setData(Qt.ItemDataRole.ForegroundRole, QColor("#757575"))  # Gray
                    item.setToolTip(self.EXTRA_COLUMN_TOOLTIP.format(header))

                self.table.setItem(row_index, col_index, item)

        # Auto-resize columns to content
        self.table.resizeColumnsToContents()

    def _update_status_label(self) -> None:
        """Update the status label with current data information."""
        if not self.validation_result:
            self.status_label.setText("")
            return

        total_rows = len(self.all_data) if self.all_data else 0
        valid_rows = len(self.valid_data) if self.valid_data else 0
        invalid_rows = total_rows - valid_rows

        if invalid_rows == 0:
            status_text = f"All {total_rows} rows are valid"
        else:
            status_text = f"{valid_rows}/{total_rows} rows valid - hover over red values for error details"

        self.status_label.setText(status_text)

    def display_validation_errors(self, validation_result: "CSVValidationResult") -> None:
        """
        Display validation errors when no data could be loaded.

        Args:
            validation_result: Validation results with error information
        """
        self.validation_result = validation_result
        self.all_data = []
        self.valid_data = []

        self._update_status_label()
        self._show_error_summary_table()
        self.logger.info(f"Displaying validation errors: {validation_result.get_summary()}")

    def _show_error_summary_table(self) -> None:
        """Show a summary of validation errors when no valid data exists."""
        if not self.validation_result:
            return

        # Create a simple table showing error summary
        errors_list = []

        # Add general errors
        for error in self.validation_result.errors:
            errors_list.append(("File Structure", error))

        # Add missing columns
        for col in self.validation_result.missing_columns:
            errors_list.append((self.MISSING_COLUMN_ERROR, self.MISSING_COLUMN_ERROR_MESSAGE.format(col)))

        # Add cell errors (first 10)
        cell_count = 0
        for row_idx, cell_errors in self.validation_result.cell_errors.items():
            if cell_count >= 10:
                remaining = len(self.validation_result.cell_errors) - 10
                errors_list.append((self.CELL_ERRORS_HEADER, self.MORE_CELL_ERRORS_MESSAGE.format(remaining)))
                break
            for column, error in cell_errors.items():
                errors_list.append((self.CELL_ERROR_HEADER, self.CELL_ERROR_MESSAGE.format(row_idx + 1, column, error)))
            cell_count += 1

        if not errors_list:
            self._show_empty_data_message()
            return

        self.table.setRowCount(len(errors_list))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([self.ERROR_HEADER, self.DESCRIPTION_HEADER])

        for row_index, (error_type, description) in enumerate(errors_list):
            type_item = QTableWidgetItem(error_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            desc_item = QTableWidgetItem(description)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            desc_item.setToolTip(description)  # Show full text on hover

            self.table.setItem(row_index, 0, type_item)
            self.table.setItem(row_index, 1, desc_item)

        # Auto-resize columns
        self.table.resizeColumnsToContents()

    def _show_no_data_message(self) -> None:
        """Show message when no data has been imported."""
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels([self.STATUS_HEADER])

        item = QTableWidgetItem(self.NO_DATA_TEXT)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 0, item)

        self.status_label.setText("")

    def _show_empty_data_message(self) -> None:
        """Show message when no valid data to display."""
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels([self.STATUS_HEADER])

        item = QTableWidgetItem(self.EMPTY_DATA_TEXT)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(0, 0, item)

    def clear_data(self) -> None:
        """Clear the preview table and reset to initial state."""
        self.all_data = []
        self.valid_data = []
        self.validation_result = None
        self._show_no_data_message()

    def get_display_summary(self) -> str:
        """
        Get a summary of the displayed data for status reporting.

        Returns:
            String summary of what's currently displayed
        """
        if not self.all_data:
            return self.NO_DATA_DISPLAYED

        total_rows = len(self.all_data)
        valid_rows = len(self.valid_data)
        invalid_rows = total_rows - valid_rows

        if invalid_rows == 0:
            return self.DISPLAYING_ALL_ROWS_MESSAGE.format(total_rows)
        else:
            return self.DISPLAYING_ROWS_WITH_ERRORS_MESSAGE.format(total_rows, valid_rows, invalid_rows)
