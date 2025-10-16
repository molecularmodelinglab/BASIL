"""
CSV Data Importer with validation against parameter constraints.

This module handles importing CSV files and validating the data against
the configured parameters from Step 2. It provides detailed error reporting
and data validation using the existing parameter validation methods.
"""

import csv
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.models.campaign import Campaign
from app.models.parameters.base import BaseParameter


class CSVValidationResult:
    """Container for CSV validation results with detailed error information."""

    # Error message templates
    VALIDATION_PASSED_MESSAGE = "Validation passed: {0}/{1} rows valid"
    VALIDATION_ISSUES_MESSAGE = "Validation found issues: {0} problems detected"
    FILE_ERROR_PREFIX = "File: {0}"
    CELL_ERROR_FORMAT = "Row {0}, Column '{1}': {2}"
    STRUCTURE_ERRORS_KEY = "structure_errors"
    CELL_ERRORS_KEY = "cell_errors"
    MISSING_COLUMNS_KEY = "missing_columns"
    WARNINGS_KEY = "warnings"

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.missing_columns: List[str] = []
        self.extra_columns: List[str] = []
        self.row_errors: Dict[int, List[str]] = {}
        self.cell_errors: Dict[int, Dict[str, str]] = {}  # {row_index: {column_name: error_msg}}
        self.total_rows: int = 0
        self.valid_rows: int = 0

    def add_error(self, message: str) -> None:
        """Add a general error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_row_error(self, row_index: int, message: str) -> None:
        """Add an error for a specific row."""
        if row_index not in self.row_errors:
            self.row_errors[row_index] = []
        self.row_errors[row_index].append(message)
        self.is_valid = False

    def add_cell_error(self, row_index: int, column_name: str, error_message: str) -> None:
        """Add an error for a specific cell."""
        if row_index not in self.cell_errors:
            self.cell_errors[row_index] = {}
        self.cell_errors[row_index][column_name] = error_message
        self.is_valid = False

    def get_cell_error(self, row_index: int, column_name: str) -> Optional[str]:
        """Get error message for specific cell."""
        return self.cell_errors.get(row_index, {}).get(column_name)

    def has_cell_error(self, row_index: int, column_name: str) -> bool:
        """Check if specific cell has an error."""
        return self.get_cell_error(row_index, column_name) is not None

    def is_row_valid(self, row_index: int) -> bool:
        """Check if entire row is valid (no cell errors)."""
        return row_index not in self.cell_errors or not self.cell_errors[row_index]

    def get_summary(self) -> str:
        """Get a summary of validation results."""
        if not self.errors and not self.cell_errors:
            return self.VALIDATION_PASSED_MESSAGE.format(self.valid_rows, self.total_rows)

        error_count = len(self.errors) + len(self.cell_errors)
        return self.VALIDATION_ISSUES_MESSAGE.format(error_count)

    def get_all_errors_formatted(self) -> str:
        """Get all errors formatted for display."""
        lines = []

        # General errors
        for error in self.errors:
            lines.append(self.FILE_ERROR_PREFIX.format(error))

        # Cell errors
        for row_idx, cell_errors in self.cell_errors.items():
            for column, error in cell_errors.items():
                lines.append(self.CELL_ERROR_FORMAT.format(row_idx + 1, column, error))

        return "\n".join(lines)

    def has_critical_errors(self) -> bool:
        """Check if there are critical errors that prevent data import."""
        return len(self.errors) > 0 or len(self.missing_columns) > 0

    def get_error_counts(self) -> Dict[str, int]:
        """Get counts of different error types."""
        return {
            self.STRUCTURE_ERRORS_KEY: len(self.errors),
            self.CELL_ERRORS_KEY: len(self.cell_errors),
            self.MISSING_COLUMNS_KEY: len(self.missing_columns),
            self.WARNINGS_KEY: len(self.warnings),
        }


class CSVDataImporter:
    """
    Imports and validates CSV data against configured parameters.

    Class Constants:
        TARGET_COLUMN_NAME: Name of the target column in CSV files
        CSV_SNIFFER_DELIMITERS: Delimiters used by csv.Sniffer to detect CSV format
        CSV_SAMPLE_SIZE: Number of bytes to read for CSV dialect detection
    """

    TARGET_COLUMN_NAME = "target_value"
    CSV_SNIFFER_DELIMITERS = ",;\t"
    CSV_SAMPLE_SIZE = 1024

    TARGET_COLUMN_NAME = "target_value"

    def __init__(
        self,
        parameters: List[BaseParameter],
        campaign: Campaign,
    ) -> None:
        """
        Initialize the CSV importer.

        Args:
            parameters: List of configured parameters from Step 2
            campaign: The campaign data model
        """
        self.parameters = parameters
        self.campaign = campaign
        self.logger = logging.getLogger(__name__)

    def import_csv(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], CSVValidationResult]:
        """
        Import and validate CSV file.

        Args:
            file_path: Path to the CSV file to import

        Returns:
            Tuple of (all_data, valid_data, validation_result)
            - all_data: All rows including invalid ones (for display)
            - valid_data: Only valid rows (for processing)
            - validation_result: Detailed validation information
        """
        result = CSVValidationResult()
        all_data: List[Dict[str, Any]] = []
        valid_data: List[Dict[str, Any]] = []

        try:
            raw_data, headers = self._parse_csv_file(file_path)
            result.total_rows = len(raw_data)

            self._validate_columns(headers, result)

            if result.errors or result.missing_columns:
                # Critical errors - cannot process data at all
                return all_data, valid_data, result

            data_as_dicts = self._convert_rows_to_dicts(raw_data, headers)
            all_data, valid_data = self._validate_data_rows(data_as_dicts, result)

            result.valid_rows = len(valid_data)

            # Update is_valid based on whether we have any valid data
            if valid_data:
                result.is_valid = True

            self.logger.info(f"CSV import completed: {len(valid_data)}/{len(all_data)} rows valid")

        except Exception as e:
            result.add_error(f"Failed to import CSV: {e}")

        return all_data, valid_data, result

    def validate_data(
        self, data: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], CSVValidationResult]:
        """
        Validate a list of data dictionaries without reading from a file.

        Args:
            data: A list of dictionaries, where each dictionary represents a row.

        Returns:
            Tuple of (all_data, valid_data, validation_result)
        """
        result = CSVValidationResult()
        if not data:
            return [], [], result

        headers = list(data[0].keys())
        self._validate_columns(headers, result)

        if result.errors or result.missing_columns:
            return [], [], result

        all_data, valid_data = self._validate_data_rows(data, result)
        result.total_rows = len(data)
        result.valid_rows = len(valid_data)

        return all_data, valid_data, result

    def _parse_csv_file(self, file_path: str) -> Tuple[List[List[str]], List[str]]:
        """
        Parse CSV file and extract headers and data rows.

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple of (data_rows, headers)
        """
        data_rows = []
        headers = []

        with open(file_path, "r", encoding="utf-8") as csvfile:
            # Read a small sample to detect CSV dialect (delimiter, quoting, etc.)
            # We need to detect if CSV uses comma, semicolon, tab, etc. as separator
            sample = csvfile.read(self.CSV_SAMPLE_SIZE)
            # Reset file pointer to beginning so we can read the full file
            # After read(1024), the pointer is at position 1024, but we need to start from 0
            csvfile.seek(0)

            # Use csv.Sniffer to detect delimiter
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=self.CSV_SNIFFER_DELIMITERS)
                reader = csv.reader(csvfile, dialect)
            except csv.Error:
                # Fallback to comma delimiter
                reader = csv.reader(csvfile)

            # Read headers (first row)
            headers = next(reader)
            headers = [header.strip() for header in headers]  # Clean whitespace

            for row_index, row in enumerate(reader):
                # Pad row with empty strings if it's shorter than headers
                while len(row) < len(headers):
                    row.append("")

                # Take only as many columns as headers
                row = row[: len(headers)]
                data_rows.append(row)

        return data_rows, headers

    def _convert_rows_to_dicts(self, data_rows: List[List[str]], headers: List[str]) -> List[Dict[str, Any]]:
        """Convert a list of raw string rows to a list of dictionaries."""
        dict_rows = []
        for row in data_rows:
            row_dict = {header: (row[i].strip() if i < len(row) else "") for i, header in enumerate(headers)}
            dict_rows.append(row_dict)
        return dict_rows

    def _validate_columns(self, headers: List[str], result: CSVValidationResult) -> None:
        """
        Validate that CSV headers match the configured parameters.

        Args:
            headers: List of column headers from CSV
            result: Validation result object to update
        """
        expected_columns = set(param.name for param in self.parameters)
        if self.campaign.targets:
            for target in self.campaign.targets:
                expected_columns.add(target.name)
        actual_columns = set(headers)

        missing = expected_columns - actual_columns
        if missing:
            result.missing_columns = list(missing)
            for col in missing:
                result.add_error(f"Missing required column: '{col}'")
                self.logger.error(f"Error: Required column '{col}' is missing from CSV")

        # Check for extra columns (not an error, just a warning)
        extra = actual_columns - expected_columns
        if extra:
            result.extra_columns = list(extra)
            for col in extra:
                result.add_warning(f"Extra column found: '{col}' (will be ignored)")
                self.logger.warning(f"Warning: Extra column '{col}' found in CSV (will be ignored)")

        # Check for duplicate headers
        if len(headers) != len(set(headers)):
            duplicates = [h for h in headers if headers.count(h) > 1]
            for dup in set(duplicates):
                result.add_error(f"Duplicate column header: '{dup}'")
                self.logger.info(f"CSV headers validated: {len(headers)} columns found")

    def _validate_data_rows(
        self,
        data_rows: List[Dict[str, Any]],
        result: CSVValidationResult,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate data in each row against parameter constraints.

        Returns both all rows (for display) and valid rows (for processing).

        Args:
            data_rows: A list of dictionaries representing the rows to validate.
            result: Validation result object to update.

        Returns:
            Tuple of (all_rows_with_validation, valid_rows_only)
        """
        all_rows = []  # All rows for display
        valid_rows = []  # Only valid rows for processing

        for row_index, row_dict in enumerate(data_rows):
            row_has_errors = False
            validated_row = row_dict.copy()

            # Validate each parameter column
            for param in self.parameters:
                if param.name in validated_row:
                    raw_value = str(validated_row[param.name])

                    is_valid, converted_value, error_msg = self._validate_parameter_value(param, raw_value, row_index)

                    if is_valid:
                        validated_row[param.name] = converted_value
                    else:
                        # Store cell-specific error
                        result.add_cell_error(row_index, param.name, error_msg)
                        row_has_errors = True
                        # Keep original value for display
                        validated_row[param.name] = raw_value
            
                if self.campaign.targets:
                    for target in self.campaign.targets:
                        if target.name in validated_row:
                            raw_target_value = validated_row[target.name]
                            
                            if raw_target_value is None or str(raw_target_value).strip() == "":
                                validated_row[target.name] = None
                                continue
                            
                            # Convert target value to float
                            try:
                                converted_target = float(str(raw_target_value).strip())
                                validated_row[target.name] = converted_target
                            except (ValueError, TypeError) as e:
                                result.add_cell_error(row_index, target.name, f"Invalid numeric value: {raw_target_value}")
                                row_has_errors = True
                                validated_row[target.name] = raw_target_value

            # Add to all rows (for display)
            all_rows.append(validated_row)

            # Add to valid rows only if no errors
            if not row_has_errors:
                valid_rows.append(validated_row)

        return all_rows, valid_rows

    def _validate_parameter_value(
        self, parameter: BaseParameter, raw_value: str, row_index: int
    ) -> Tuple[bool, Any, str]:
        """
        Validate a single value against a parameter's constraints.

        Args:
            parameter: The parameter to validate against
            raw_value: Raw string value from CSV
            row_index: Row index for error reporting

        Returns:
            Tuple of (is_valid, converted_value, error_message)
        """
        if not raw_value:
            return False, None, f"Empty value for parameter '{parameter.name}'"

        try:
            converted_value = parameter.convert_value(raw_value)

            is_valid, error_msg = parameter.validate_value(converted_value)

            if is_valid:
                return True, converted_value, ""
            else:
                return False, None, f"Parameter '{parameter.name}': {error_msg}"

        except (ValueError, TypeError) as e:
            return (
                False,
                None,
                f"Cannot convert value '{raw_value}' for parameter '{parameter.name}': {e}",
            )
