import csv

from PySide6.QtWidgets import QFileDialog

from app.models.enums import ParameterType
from app.shared.components.dialogs import ErrorDialog, InfoDialog


class CampaignExporter:
    """Utility class for exporting campaign data to various formats."""

    @staticmethod
    def export_campaign_to_csv(campaign, parent_widget=None):
        """Export campaign data to CSV file with file dialog."""
        if not campaign:
            if parent_widget:
                ErrorDialog.show_error("Export Error", "No campaign data to export.", parent=parent_widget)
            return False

        campaign_name = campaign.name or "campaign"
        safe_name = "".join(c for c in campaign_name if c.isalnum() or c in (" ", "-", "_")).rstrip()
        default_filename = f"{safe_name}.csv"

        filename, _ = QFileDialog.getSaveFileName(
            parent_widget, "Export Campaign Data", default_filename, "CSV Files (*.csv);;All Files (*)"
        )

        if filename:
            try:
                CampaignExporter._write_campaign_csv(campaign, filename)
                if parent_widget:
                    InfoDialog.show_info(
                        "Export Successful", f"Campaign data exported to:\n{filename}", parent=parent_widget
                    )
                return True
            except Exception as e:
                if parent_widget:
                    ErrorDialog.show_error(
                        "Export Error", f"Failed to export campaign data:\n{str(e)}", parent=parent_widget
                    )
                return False

        return False

    @staticmethod
    def _write_campaign_csv(campaign, filename: str):
        """Write campaign data to CSV file."""
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(["Campaign Information"])
            writer.writerow(["Name", campaign.name or ""])
            writer.writerow(["Description", campaign.description or ""])
            writer.writerow([])

            if hasattr(campaign, "parameters") and campaign.parameters:
                writer.writerow(["Parameters"])
                writer.writerow(["Parameter Name", "Type", "Values"])

                for param in campaign.parameters:
                    param_name = param.name or ""
                    param_type = CampaignExporter._format_parameter_type(param)
                    param_values = CampaignExporter._format_parameter_values(param)
                    writer.writerow([param_name, param_type, param_values])

                writer.writerow([])

            if hasattr(campaign, "targets") and campaign.targets:
                writer.writerow(["Targets"])
                writer.writerow(["Target Name", "Mode", "Transform", "Weight", "Values"])  # To add new columns

                for target in campaign.targets:
                    target_name = target.name or ""
                    target_mode = CampaignExporter._format_target_mode(target)
                    target_transform = CampaignExporter._format_target_transform(target)
                    target_weight = CampaignExporter._format_target_weight(target)
                    target_values = CampaignExporter._format_target_values(target)
                    writer.writerow([target_name, target_mode, target_transform, target_weight, target_values])

                writer.writerow([])

            if hasattr(campaign, "experiments") and campaign.experiments:
                writer.writerow(["Experiments"])
                writer.writerow(["Experiment ID", "Status", "Results"])

                for exp in campaign.experiments:
                    exp_id = getattr(exp, "id", "N/A")
                    exp_status = getattr(exp, "status", "N/A")
                    exp_results = getattr(exp, "results", "N/A")
                    writer.writerow([exp_id, exp_status, exp_results])

    @staticmethod
    def _format_parameter_type(param) -> str:
        """Format parameter type for display."""
        if not hasattr(param, "parameter_type") or not param.parameter_type:
            return "Unknown"

        param_type = param.parameter_type

        if param_type == ParameterType.DISCRETE_NUMERICAL_REGULAR:
            return "Discrete Numerical Regular"
        elif param_type == ParameterType.DISCRETE_NUMERICAL_IRREGULAR:
            return "Discrete Numerical Irregular"
        elif param_type == ParameterType.CONTINUOUS_NUMERICAL:
            return "Continuous Numerical"
        elif param_type == ParameterType.CATEGORICAL:
            return "Categorical"
        elif param_type == ParameterType.FIXED:
            return "Fixed"
        elif param_type == ParameterType.SUBSTANCE:
            return "Substance"
        else:
            return param_type.name.replace("_", " ").title()

    @staticmethod
    def _format_parameter_values(param) -> str:
        """Format parameter values for display."""
        if not hasattr(param, "parameter_type") or not param.parameter_type:
            return "No values defined"

        param_type = param.parameter_type.value

        try:
            if param_type == "discrete_numerical_regular":
                start = getattr(param, "min_val", "N/A")
                stop = getattr(param, "max_val", "N/A")
                step = getattr(param, "step", "N/A")
                return f"start: {start}, stop: {stop}, step: {step}"

            elif param_type == "discrete_numerical_irregular":
                values = getattr(param, "values", [])
                if isinstance(values, list) and values:
                    return ", ".join(map(str, values))
                return "No values"

            elif param_type == "continuous_numerical":
                start = getattr(param, "min_val", "N/A")
                end = getattr(param, "max_val", "N/A")
                return f"start: {start}, end: {end}"

            elif param_type == "fixed":
                value = getattr(param, "value", "N/A")
                return f"Value: {value}"

            elif param_type == "categorical":
                values = getattr(param, "values", [])
                if isinstance(values, list) and values:
                    return ", ".join(map(str, values))
                return "No values"

            elif param_type == "substance":
                smiles = getattr(param, "smiles", "N/A")
                return f"SMILES: {smiles}"

            else:
                if hasattr(param, "values"):
                    values = param.values
                    if isinstance(values, list) and values:
                        return ", ".join(map(str, values))
                return "No values defined"

        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def _format_target_mode(target) -> str:
        """Format target mode for display."""
        if not hasattr(target, "mode") or not target.mode:
            return "N/A"

        target_mode = target.mode
        try:
            if target_mode == "Min":
                return "Minimize"
            elif target_mode == "Max":
                return "Maximize"
            elif target_mode == "Match":
                return "Match"
            else:
                return target_mode.replace("_", " ")
        except Exception:
            return "N/A"

    @staticmethod
    def _format_target_transform(target) -> str:
        """Format target transform for display."""
        if not hasattr(target, "transformation") or not target.transformation:
            return "N/A"
        target_transformation = target.transformation
        try:
            return target_transformation
        except Exception:
            return "N/A"

    @staticmethod
    def _format_target_weight(target) -> str:
        """Format target weight for display."""
        if not hasattr(target, "weight") or not target.weight:
            return "N/A"
        target_weight = target.weight
        try:
            return str(target_weight)
        except Exception:
            return "N/A"

    @staticmethod
    def _format_target_values(target) -> str:
        """Format target values for display."""
        min_value = "-inf"
        max_value = "+inf"
        if hasattr(target, "min_value") and target.min_value:
            min_value = str(target.min_value)
        if hasattr(target, "max_value") and target.max_value:
            max_value = str(target.max_value)

        return f"min: {min_value}, max: {max_value}"


class ParameterFormatter:
    """Utility class for formatting parameter data for display."""

    @staticmethod
    def format_parameter_type(param) -> str:
        """Format parameter type for display."""
        return CampaignExporter._format_parameter_type(param)

    @staticmethod
    def format_parameter_values(param) -> str:
        """Format parameter values for display."""
        return CampaignExporter._format_parameter_values(param)


class TargetFormatter:
    """Utility class for formatting target data for display."""

    @staticmethod
    def format_target_mode(target) -> str:
        """Format target mode for display."""
        return CampaignExporter._format_target_mode(target)

    @staticmethod
    def format_target_transform(target) -> str:
        """Format target transform for display."""
        return CampaignExporter._format_target_transform(target)

    @staticmethod
    def format_target_weight(target) -> str:
        """Format target weight for display."""
        return CampaignExporter._format_target_weight(target)

    @staticmethod
    def format_target_values(target) -> str:
        """Format target values for display."""
        return CampaignExporter._format_target_values(target)
