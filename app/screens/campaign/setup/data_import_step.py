"""
Data import step for campaign creation wizard.
"""

import logging
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QFileDialog, QVBoxLayout

from app.bayesopt.baybe_service import BayBeService
from app.core.base import BaseStep
from app.models.campaign import Campaign
from app.models.parameters import ParameterSerializer
from app.models.parameters.base import BaseParameter
from app.screens.campaign.panel.services.runs_data_manager import RunsDataManager
from app.shared.components.dialogs import ErrorDialog, InfoDialog
from app.shared.components.headers import MainHeader, SectionHeader

from .components.csv_data_importer import CSVDataImporter, CSVValidationResult
from .components.csv_template_generator import CSVTemplateGenerator
from .components.data_import_widgets import (
    DataPreviewWidget,
    PageHeaderWidget,
    TemplateSectionWidget,
    UploadSectionWidget,
)


class DataImportStep(BaseStep):
    """
    Third step of campaign creation wizard.

    This step coordinates multiple specialized widgets:
    - PageHeaderWidget: Title and description
    - UploadSectionWidget: File upload functionality
    - TemplateSectionWidget: Template generation
    - DataPreviewWidget: Data preview and validation

    The step follows the same pattern as other wizard steps:
    - validate(): Check if data is properly imported and valid
    - save_data(): Save imported data to shared_data
    - load_data(): Load previously imported data (if any)
    """

    # UI Text Constants
    TITLE = "Data Import"
    DESCRIPTION = "Import historical data to help optimize your campaign parameters."
    SAVE_TEMPLATE_DIALOG_TITLE = "Save CSV Template"
    DEFAULT_TEMPLATE_FILENAME = "campaign_data_template.csv"
    CSV_FILE_FILTER = "CSV Files (*.csv);;All Files (*)"

    # Error Dialog Constants
    CONFIGURE_ERROR_TITLE = "Configure Error"
    CONFIGURE_PARAMETERS_MESSAGE = "Please configure parameters in Step 2 before importing data."
    IMPORT_ERROR_TITLE = "Import Error"
    IMPORT_ERROR_MESSAGE = "Error importing CSV file: {0}"
    CONFIGURATION_ERROR_TITLE = "Configuration Error"
    NO_PARAMETERS_MESSAGE = "No parameters configured - cannot generate template"
    TEMPLATE_ERROR_TITLE = "Error"
    TEMPLATE_ERROR_MESSAGE = "Error generating template: {0}"
    VALIDATION_ERROR_TITLE = "Data Validation Failed"
    NO_VALID_DATA_MESSAGE = "No valid data rows found. Please fix the errors in your CSV file before proceeding."
    FILE_STRUCTURE_ERROR_TITLE = "File Structure Error"
    FILE_STRUCTURE_ERROR_MESSAGE = "Cannot process CSV file due to structure issues. See details in the table below."
    IMPORT_WARNINGS_TITLE = "Import Warnings"
    IMPORT_WARNINGS_MESSAGE = "Found {0} warning(s): extra columns will be ignored during processing"
    SAVE_ERROR_MESSAGE = "Error saving import data: {0}"
    LOAD_ERROR_MESSAGE = "Error loading import data: {0}"

    # Layout Constants
    MAIN_LAYOUT_SPACING = 30
    MAIN_LAYOUT_MARGINS = (40, 40, 40, 40)

    def __init__(self, wizard_data: Campaign, parent=None):
        """
        Initialize the data import step.

        Args:
            wizard_data: The campaign data model
        """
        # Initialize data before calling super()
        self.all_imported_data: List[Dict[str, Any]] = []  # All rows including invalid
        self.valid_imported_data: List[Dict[str, Any]] = []  # Only valid rows
        self.parameters: List[BaseParameter] = []
        self.selected_file_path: Optional[str] = None
        self.validation_result: Optional[CSVValidationResult] = None
        self.serializer = ParameterSerializer()

        self.logger = logging.getLogger(__name__)

        super().__init__(wizard_data, parent)
        self.campaign: Campaign = self.wizard_data

        # Connect signals after UI is setup
        self._connect_signals()

    def _setup_widget(self):
        """Setup the data import step UI."""
        layout = self._create_main_layout()

        # Create title and description
        title = MainHeader(self.TITLE)
        layout.addWidget(title)

        description = SectionHeader(self.DESCRIPTION)
        layout.addWidget(description)

        # Create specialized widgets
        self.header_widget = PageHeaderWidget()
        self.upload_widget = UploadSectionWidget()
        self.template_widget = TemplateSectionWidget()
        self.preview_widget = DataPreviewWidget()

        layout.addWidget(self.header_widget)
        layout.addWidget(self.upload_widget)
        layout.addWidget(self.template_widget)
        layout.addWidget(self.preview_widget)
        layout.addStretch()

    def _create_main_layout(self) -> QVBoxLayout:
        """Create and configure the main layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(self.MAIN_LAYOUT_SPACING)
        layout.setContentsMargins(*self.MAIN_LAYOUT_MARGINS)
        return layout

    def _connect_signals(self) -> None:
        """Connect signals from child widgets."""
        if hasattr(self, "upload_widget"):
            self.upload_widget.file_selected.connect(self._on_file_selected)
        if hasattr(self, "template_widget"):
            self.template_widget.template_requested.connect(self._on_template_requested)

    def _on_file_selected(self, file_path: str) -> None:
        """Handle file selection from upload widget."""
        self.logger.info(f"File selected: {file_path}")

        self.selected_file_path = file_path

        self._import_and_validate_csv(file_path)

    def _import_and_validate_csv(self, file_path: str) -> None:
        """
        Import CSV file and validate data against configured parameters.

        Args:
            file_path: Path to the CSV file to import
        """
        if not self.parameters:
            ErrorDialog.show_error(self.CONFIGURE_ERROR_TITLE, self.CONFIGURE_PARAMETERS_MESSAGE, parent=self)
            return

        try:
            csv_importer = CSVDataImporter(self.parameters, self.campaign)
            self.all_imported_data, self.valid_imported_data, self.validation_result = csv_importer.import_csv(
                file_path
            )
            self._update_preview()

        except Exception as e:
            ErrorDialog.show_error(self.IMPORT_ERROR_TITLE, self.IMPORT_ERROR_MESSAGE.format(e), parent=self)

    def _on_template_requested(self) -> None:
        """Handle template download request."""
        if not self.parameters:
            ErrorDialog.show_error(self.CONFIGURATION_ERROR_TITLE, self.NO_PARAMETERS_MESSAGE, parent=self)
            return

        # Show file save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.SAVE_TEMPLATE_DIALOG_TITLE,
            self.DEFAULT_TEMPLATE_FILENAME,
            self.CSV_FILE_FILTER,
        )

        if file_path:
            try:
                generator = CSVTemplateGenerator(self.parameters, self.campaign)
                generator.generate_template(file_path)
                self.logger.info(f"Template saved to: {file_path}")

            except Exception as e:
                ErrorDialog.show_error(self.TEMPLATE_ERROR_TITLE, self.TEMPLATE_ERROR_MESSAGE.format(e), parent=self)

    def _update_preview(self) -> None:
        """Update the preview widget with the current data and validation results."""
        if not hasattr(self, "preview_widget"):
            return

        # Check for critical errors (missing columns, file structure issues)
        if self.validation_result and (self.validation_result.errors or self.validation_result.missing_columns):
            # Critical errors - show error summary table
            self.preview_widget.display_validation_errors(self.validation_result)

            # Show simple error dialog for critical issues
            ErrorDialog.show_error(
                self.FILE_STRUCTURE_ERROR_TITLE,
                self.FILE_STRUCTURE_ERROR_MESSAGE,
                parent=self,
            )
            return

        # No critical errors - show data (valid + invalid with highlighting)
        if self.all_imported_data:
            self.logger.info(
                f"Displaying {len(self.all_imported_data)} total rows ({len(self.valid_imported_data)} valid)"
            )
            self.preview_widget.display_data(self.all_imported_data, self.valid_imported_data, self.validation_result)
        else:
            self.logger.info("No data to display")
            self.preview_widget.clear_data()

        if self.validation_result and self.validation_result.warnings and len(self.all_imported_data) > 0:
            warning_count = len(self.validation_result.warnings)
            InfoDialog.show_info(
                self.IMPORT_WARNINGS_TITLE,
                self.IMPORT_WARNINGS_MESSAGE.format(warning_count),
                parent=self,
            )

    def validate(self) -> bool:
        """
        Validate that data import is complete and valid.

        Data import is optional, so this step passes validation even without data.
        If data is imported, we only proceed if we have some valid rows.

        Returns:
            bool: True if no data imported or some valid data exists
        """
        if not self.all_imported_data:
            self.logger.info("No data imported - proceeding without historical data")
            return True

        if not self.valid_imported_data:
            # No valid data at all
            ErrorDialog.show_error(
                self.VALIDATION_ERROR_TITLE,
                self.NO_VALID_DATA_MESSAGE,
                parent=self,
            )
            return False

        self.logger.info(f"Data import validation passed - {len(self.valid_imported_data)} valid rows imported")
        return True

    def save_data(self) -> None:
        """Save only valid imported data to campaign."""
        try:
            # Save only valid data for processing
            self.campaign.initial_dataset = self.valid_imported_data.copy()

            self.logger.info(f"Successfully saved {len(self.valid_imported_data)} valid rows to campaign")

            self._seed_initial_run()
        except Exception as e:
            ErrorDialog.show_error(self.VALIDATION_ERROR_TITLE, self.SAVE_ERROR_MESSAGE.format(e), parent=self)

    def load_data(self) -> None:
        """Load previously imported data from the campaign model."""
        try:
            self.parameters = self.campaign.parameters
            self.valid_imported_data = self.campaign.initial_dataset.copy()

            # When loading, we only have valid data, so all_data = valid_data
            self.all_imported_data = self.valid_imported_data.copy()

            if self.valid_imported_data:
                # Create a validation result for display
                self.validation_result = CSVValidationResult()
                self.validation_result.total_rows = len(self.valid_imported_data)
                self.validation_result.valid_rows = len(self.valid_imported_data)
                self.validation_result.is_valid = True

                self._update_preview()
                self.logger.info(f"Loaded {len(self.valid_imported_data)} rows of valid data")

                self._seed_initial_run()

        except Exception as e:
            ErrorDialog.show_error(self.IMPORT_ERROR_TITLE, self.LOAD_ERROR_MESSAGE.format(e), parent=self)

    def _seed_initial_run(self) -> None:
        """
        Seed Run 1 from the imported valid data if there are no runs yet.
        Also initializes the BayBe campaign with the imported data.
        """
        try:
            if not self.valid_imported_data:
                self.logger.info("No valid imported data available to seed runs")
                return

            workspace_path = self.campaign.workspace_path
            campaign_id = self.campaign.id

            if not workspace_path or not campaign_id:
                self.logger.warning("Cannot seed runs: missing workspace_path or campaign_id on Campaign")
                return

            manager = RunsDataManager(workspace_path, campaign_id)

            if manager.get_run_count() == 0:
                manager.add_run(experiments=self.valid_imported_data, campaign=self.campaign)
                self.logger.info("Seeded initial Run 1 from imported data")

                self._initialize_baybe_with_imported_data(workspace_path)
            else:
                self.logger.info("Runs already exist; skipping seed")

        except Exception as e:
            # Non-fatal: log and show error, but do not block workflow
            self.logger.exception("Failed to seed initial run from imported data")
            ErrorDialog.show_error(self.IMPORT_ERROR_TITLE, f"Failed to seed initial run: {e}", parent=self)

    def _initialize_baybe_with_imported_data(self, workspace_path: str) -> None:
        """
        Initialize BayBe campaign and add imported data as measurements.
        This ensures the BayBe campaign is ready for future run generation.
        """
        try:
            self.logger.info("Initializing BayBe campaign with imported data")

            baybe_service = BayBeService(campaign=self.campaign, workspace_path=workspace_path)

            baybe_service._initialize_baybe_campaign()

            # Add imported data to the BayBe campaign
            if baybe_service.baybe_campaign is not None:
                import pandas as pd

                df = pd.DataFrame(self.valid_imported_data)
                print(df)
                print(df.dtypes)

                # Add measurements to BayBe campaign
                baybe_service.baybe_campaign.add_measurements(df, numerical_measurements_must_be_within_tolerance=False)
                self.logger.info(f"Added {len(df)} measurements to BayBe campaign")

                baybe_service._save_baybe_campaign_state()
                self.logger.info("Saved initialized BayBe campaign state")
            else:
                self.logger.warning("BayBe campaign was not properly initialized")

        except Exception as e:
            self.logger.warning(f"Failed to initialize BayBe campaign with imported data: {e}")

    def _validate_data(self) -> None:
        """Re-validate the current imported data."""
        if not self.parameters:
            self.logger.info("No parameters configured - cannot validate CSV data")
            return

        csv_importer = CSVDataImporter(self.parameters, self.campaign)
        self.all_imported_data, self.valid_imported_data, self.validation_result = csv_importer.validate_data(
            self.valid_imported_data
        )

    def reset(self):
        """Reset import step to initial state."""
        self.selected_file_path = None
        self.all_imported_data = []
        self.valid_imported_data = []
        self.validation_result = None

        # Reset UI widgets
        if hasattr(self, "preview_widget"):
            self.preview_widget.clear_data()
