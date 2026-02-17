import csv

from PySide6.QtWidgets import QFileDialog

from app.models.enums import ParameterType, TargetMode
from app.shared.components.dialogs import ErrorDialog, InfoDialog


class CampaignExporter:
    """Utility class for exporting campaign data to various formats."""

    # Export dialog
    EXPORT_ERROR_TITLE = "Export Error"
    EXPORT_NO_DATA_MESSAGE = "No campaign data to export."
    EXPORT_DIALOG_TITLE = "Export Campaign Data"
    EXPORT_FILE_FILTER = "CSV Files (*.csv);;All Files (*)"
    EXPORT_SUCCESS_TITLE = "Export Successful"
    EXPORT_SUCCESS_MESSAGE = "Campaign data exported to:\n{0}"
    EXPORT_FAILED_MESSAGE = "Failed to export campaign data:\n{0}"
    DEFAULT_FILENAME = "campaign"

    # CSV section headers
    CSV_SECTION_CAMPAIGN = "Campaign Information"
    CSV_SECTION_PARAMETERS = "Parameters"
    CSV_SECTION_TARGETS = "Targets"
    CSV_SECTION_EXPERIMENTS = "Experiments"

    # CSV column headers
    CSV_COL_NAME = "Name"
    CSV_COL_DESCRIPTION = "Description"
    CSV_COL_PARAM_NAME = "Parameter Name"
    CSV_COL_PARAM_TYPE = "Type"
    CSV_COL_PARAM_VALUES = "Values"
    CSV_COL_TARGET_NAME = "Target Name"
    CSV_COL_TARGET_MODE = "Mode"
    CSV_COL_TARGET_TRANSFORM = "Transform"
    CSV_COL_TARGET_WEIGHT = "Weight"
    CSV_COL_TARGET_VALUES = "Values"
    CSV_COL_EXP_ID = "Experiment ID"
    CSV_COL_EXP_STATUS = "Status"
    CSV_COL_EXP_RESULTS = "Results"

    # Fallback values
    NO_VALUE = "N/A"
    NO_VALUES = "No values"
    NO_VALUES_DEFINED = "No values defined"
    UNKNOWN_TYPE = "Unknown"
    MIN_INF = "-inf"
    MAX_INF = "+inf"

    @staticmethod
    def export_campaign_to_csv(campaign, parent_widget=None):
        """Export campaign data to CSV file with file dialog."""
        if not campaign:
            if parent_widget:
                ErrorDialog.show_error(
                    CampaignExporter.EXPORT_ERROR_TITLE,
                    CampaignExporter.EXPORT_NO_DATA_MESSAGE,
                    parent=parent_widget,
                )
            return False

        campaign_name = campaign.name or CampaignExporter.DEFAULT_FILENAME
        safe_name = "".join(c for c in campaign_name if c.isalnum() or c in (" ", "-", "_")).rstrip()
        default_filename = f"{safe_name}.csv"

        filename, _ = QFileDialog.getSaveFileName(
            parent_widget,
            CampaignExporter.EXPORT_DIALOG_TITLE,
            default_filename,
            CampaignExporter.EXPORT_FILE_FILTER,
        )

        if filename:
            try:
                CampaignExporter._write_campaign_csv(campaign, filename)
                if parent_widget:
                    InfoDialog.show_info(
                        CampaignExporter.EXPORT_SUCCESS_TITLE,
                        CampaignExporter.EXPORT_SUCCESS_MESSAGE.format(filename),
                        parent=parent_widget,
                    )
                return True
            except Exception as e:
                if parent_widget:
                    ErrorDialog.show_error(
                        CampaignExporter.EXPORT_ERROR_TITLE,
                        CampaignExporter.EXPORT_FAILED_MESSAGE.format(str(e)),
                        parent=parent_widget,
                    )
                return False

        return False

    @staticmethod
    def _write_campaign_csv(campaign, filename: str):
        """Write campaign data to CSV file."""
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow([CampaignExporter.CSV_SECTION_CAMPAIGN])
            writer.writerow([CampaignExporter.CSV_COL_NAME, campaign.name or ""])
            writer.writerow([CampaignExporter.CSV_COL_DESCRIPTION, campaign.description or ""])
            writer.writerow([])

            if hasattr(campaign, "parameters") and campaign.parameters:
                writer.writerow([CampaignExporter.CSV_SECTION_PARAMETERS])
                writer.writerow(
                    [
                        CampaignExporter.CSV_COL_PARAM_NAME,
                        CampaignExporter.CSV_COL_PARAM_TYPE,
                        CampaignExporter.CSV_COL_PARAM_VALUES,
                    ]
                )

                for param in campaign.parameters:
                    writer.writerow(
                        [
                            param.name or "",
                            CampaignExporter._format_parameter_type(param),
                            CampaignExporter._format_parameter_values(param),
                        ]
                    )

                writer.writerow([])

            if hasattr(campaign, "targets") and campaign.targets:
                writer.writerow([CampaignExporter.CSV_SECTION_TARGETS])
                writer.writerow(
                    [
                        CampaignExporter.CSV_COL_TARGET_NAME,
                        CampaignExporter.CSV_COL_TARGET_MODE,
                        CampaignExporter.CSV_COL_TARGET_TRANSFORM,
                        CampaignExporter.CSV_COL_TARGET_WEIGHT,
                        CampaignExporter.CSV_COL_TARGET_VALUES,
                    ]
                )

                for target in campaign.targets:
                    writer.writerow(
                        [
                            target.name or "",
                            CampaignExporter._format_target_mode(target),
                            CampaignExporter._format_target_transform(target),
                            CampaignExporter._format_target_weight(target),
                            CampaignExporter._format_target_values(target),
                        ]
                    )

                writer.writerow([])

            if hasattr(campaign, "experiments") and campaign.experiments:
                writer.writerow([CampaignExporter.CSV_SECTION_EXPERIMENTS])
                writer.writerow(
                    [
                        CampaignExporter.CSV_COL_EXP_ID,
                        CampaignExporter.CSV_COL_EXP_STATUS,
                        CampaignExporter.CSV_COL_EXP_RESULTS,
                    ]
                )

                for exp in campaign.experiments:
                    writer.writerow(
                        [
                            getattr(exp, "id", CampaignExporter.NO_VALUE),
                            getattr(exp, "status", CampaignExporter.NO_VALUE),
                            getattr(exp, "results", CampaignExporter.NO_VALUE),
                        ]
                    )

    @staticmethod
    def _format_parameter_type(param) -> str:
        """Format parameter type for display."""
        if not hasattr(param, "parameter_type") or not param.parameter_type:
            return CampaignExporter.UNKNOWN_TYPE
        try:
            return param.parameter_type.display_name
        except AttributeError:
            return param.parameter_type.name.replace("_", " ").title()

    @staticmethod
    def _format_parameter_values(param) -> str:
        """Format parameter values for display."""
        if not hasattr(param, "parameter_type") or not param.parameter_type:
            return CampaignExporter.NO_VALUES_DEFINED

        try:
            param_type = param.parameter_type

            if param_type == ParameterType.DISCRETE_NUMERICAL_REGULAR:
                start = getattr(param, "min_val", CampaignExporter.NO_VALUE)
                stop = getattr(param, "max_val", CampaignExporter.NO_VALUE)
                step = getattr(param, "step", CampaignExporter.NO_VALUE)
                return f"start: {start}, stop: {stop}, step: {step}"

            elif param_type == ParameterType.DISCRETE_NUMERICAL_IRREGULAR:
                values = getattr(param, "values", [])
                if isinstance(values, list) and values:
                    return ", ".join(map(str, values))
                return CampaignExporter.NO_VALUES

            elif param_type == ParameterType.CONTINUOUS_NUMERICAL:
                start = getattr(param, "min_val", CampaignExporter.NO_VALUE)
                end = getattr(param, "max_val", CampaignExporter.NO_VALUE)
                return f"start: {start}, end: {end}"

            elif param_type == ParameterType.FIXED:
                value = getattr(param, "value", CampaignExporter.NO_VALUE)
                return f"Value: {value}"

            elif param_type == ParameterType.CATEGORICAL:
                values = getattr(param, "values", [])
                if isinstance(values, list) and values:
                    return ", ".join(map(str, values))
                return CampaignExporter.NO_VALUES

            elif param_type == ParameterType.SUBSTANCE:
                smiles = getattr(param, "smiles", CampaignExporter.NO_VALUE)
                return f"SMILES: {smiles}"

            else:
                if hasattr(param, "values") and isinstance(param.values, list) and param.values:
                    return ", ".join(map(str, param.values))
                return CampaignExporter.NO_VALUES_DEFINED

        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def _format_target_mode(target) -> str:
        """Format target mode for display."""
        if not hasattr(target, "mode") or not target.mode:
            return CampaignExporter.NO_VALUE
        try:
            return TargetMode.get_display_name(target.mode)
        except (ValueError, AttributeError):
            return str(target.mode).replace("_", " ")

    @staticmethod
    def _format_target_transform(target) -> str:
        """Format target transform for display."""
        if not hasattr(target, "transformation") or not target.transformation:
            return CampaignExporter.NO_VALUE
        return str(target.transformation)

    @staticmethod
    def _format_target_weight(target) -> str:
        """Format target weight for display."""
        if not hasattr(target, "weight") or target.weight is None:
            return CampaignExporter.NO_VALUE
        return str(target.weight)

    @staticmethod
    def _format_target_values(target) -> str:
        """Format target values for display."""
        min_value = CampaignExporter.MIN_INF
        max_value = CampaignExporter.MAX_INF
        if hasattr(target, "min_value") and target.min_value is not None:
            min_value = str(target.min_value)
        if hasattr(target, "max_value") and target.max_value is not None:
            max_value = str(target.max_value)
        return f"min: {min_value}, max: {max_value}"


class ParameterFormatter:
    """Utility class for formatting parameter data for display."""

    @staticmethod
    def format_parameter_type(param) -> str:
        return CampaignExporter._format_parameter_type(param)

    @staticmethod
    def format_parameter_values(param) -> str:
        return CampaignExporter._format_parameter_values(param)


class TargetFormatter:
    """Utility class for formatting target data for display."""

    @staticmethod
    def format_target_mode(target) -> str:
        return CampaignExporter._format_target_mode(target)

    @staticmethod
    def format_target_transform(target) -> str:
        return CampaignExporter._format_target_transform(target)

    @staticmethod
    def format_target_weight(target) -> str:
        return CampaignExporter._format_target_weight(target)

    @staticmethod
    def format_target_values(target) -> str:
        return CampaignExporter._format_target_values(target)
