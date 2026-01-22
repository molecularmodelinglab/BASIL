"""
Campaign information step for campaign creation wizard.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.base import BaseStep
from app.models.campaign import Campaign, Target
from app.models.enums import (
    BOAcquisitionFunction,
    BOSurrogateModel,
    MultiObjectiveStrategy,
    ObjectiveScope,
    TargetMode,
    TargetTransformation,
)
from app.shared.components.buttons import DangerButton, PrimaryButton
from app.shared.components.dialogs import ErrorDialog
from app.shared.components.headers import MainHeader, SectionHeader

COLUMN_STRETCH = (3, 3, 2, 2, 2, 2, 0)


class TargetRow(QWidget):
    """Individual target row widget."""

    # UI Constants
    TARGET_NAME_PLACEHOLDER = "Enter target name"
    MIN_VALUE_PLACEHOLDER = "Min (optional)"
    MAX_VALUE_PLACEHOLDER = "Max (optional)"
    WEIGHT_PLACEHOLDER = "Weight (optional)"
    REMOVE_BUTTON_TEXT = "X"
    REMOVE_BUTTON_TOOLTIP = "Remove this target"

    def __init__(self, target: Target, on_remove_callback, parent=None):
        super().__init__(parent)
        self.target = target
        self.on_remove_callback = on_remove_callback
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Target name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.TARGET_NAME_PLACEHOLDER)
        self.name_input.setObjectName("FormInput")
        self.name_input.setText(self.target.name)
        self.name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.name_input)

        # Target mode combo
        self.mode_combo = QComboBox()
        self.mode_combo.setObjectName("FormInput")
        for mode in TargetMode:
            self.mode_combo.addItem(mode.value)

        # Set current mode
        index = self.mode_combo.findText(self.target.mode or TargetMode.MAX.value)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)
        self.mode_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.mode_combo)

        self.min_input = QLineEdit()
        self.min_input.setPlaceholderText(self.MIN_VALUE_PLACEHOLDER)
        self.min_input.setObjectName("FormInput")
        if self.target.min_value is not None:
            self.min_input.setText(str(self.target.min_value))
        self.min_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.min_input)

        # Max value input
        self.max_input = QLineEdit()
        self.max_input.setPlaceholderText(self.MAX_VALUE_PLACEHOLDER)
        self.max_input.setObjectName("FormInput")
        if self.target.max_value is not None:
            self.max_input.setText(str(self.target.max_value))
        self.max_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.max_input)

        # Transformation combo
        self.transformation_combo = QComboBox()
        self.transformation_combo.setObjectName("FormInput")
        for transformation in TargetTransformation:
            self.transformation_combo.addItem(transformation.value)
        transformation_index = self.transformation_combo.findText(
            self.target.transformation or TargetTransformation.LINEAR.value
        )
        if transformation_index >= 0:
            self.transformation_combo.setCurrentIndex(transformation_index)
        self.transformation_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.transformation_combo)

        # Weight input
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText(self.WEIGHT_PLACEHOLDER)
        self.weight_input.setObjectName("FormInput")
        self.weight_input.setMinimumWidth(80)
        if self.target.weight is not None:
            self.weight_input.setText(str(self.target.weight))
        self.weight_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.weight_input)

        # Remove button
        self.remove_btn = DangerButton(self.REMOVE_BUTTON_TEXT)
        self.remove_btn.setToolTip(self.REMOVE_BUTTON_TOOLTIP)
        self.remove_btn.clicked.connect(lambda: self.on_remove_callback(self))
        self.remove_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.remove_btn)

        for idx, stretch in enumerate(COLUMN_STRETCH):
            layout.setStretch(idx, stretch)

    def get_target_data(self) -> Target:
        """Get target data from this row."""
        self.target.name = self.name_input.text().strip()
        self.target.mode = self.mode_combo.currentText()

        min_value_str = self.min_input.text().strip()
        max_value_str = self.max_input.text().strip()

        weight_str = self.weight_input.text().strip()

        self.target.transformation = self.transformation_combo.currentText()

        try:
            self.target.min_value = float(min_value_str) if min_value_str else None
        except ValueError:
            self.target.min_value = None

        try:
            self.target.max_value = float(max_value_str) if max_value_str else None
        except ValueError:
            self.target.max_value = None

        try:
            self.target.weight = float(weight_str) if weight_str else None
        except ValueError:
            self.target.weight = None

        return self.target

    def set_weight_visible(self, visible: bool) -> None:
        """Show or hide the weight input for this row."""
        self.weight_input.setVisible(visible)

    def is_valid(self) -> bool:
        """Check if this target row has valid data."""
        if not self.name_input.text().strip():
            return False

        min_text = self.min_input.text().strip()
        max_text = self.max_input.text().strip()

        if min_text or max_text:
            try:
                min_text = float(min_text) if min_text else None
                max_text = float(max_text) if max_text else None

                if min_text is not None and max_text is not None:
                    if min_text >= max_text:
                        return False

            except ValueError:
                return False

        weight_text = self.weight_input.text().strip()

        if weight_text:
            try:
                weight_text = float(weight_text) if weight_text else None
                if weight_text is not None:
                    if weight_text <= 0:
                        return False
            except ValueError:
                return False

        return True

    def get_validation_errors(self) -> list[str]:
        """Get list of validation errors for this target row."""
        errors = []

        if not self.name_input.text().strip():
            errors.append("Target name is required")

        min_text = self.min_input.text().strip()
        max_text = self.max_input.text().strip()
        weight_text = self.weight_input.text().strip()

        # Validate bounds
        if min_text:
            try:
                min_val = float(min_text)
            except ValueError:
                errors.append("Min value must be a valid number")
                min_val = None
        else:
            min_val = None

        if max_text:
            try:
                max_val = float(max_text)
            except ValueError:
                errors.append("Max value must be a valid number")
                max_val = None
        else:
            max_val = None

        if min_val is not None and max_val is not None and min_val >= max_val:
            errors.append("Min value must be less than max value")

        if weight_text:
            try:
                weight = float(weight_text)
                if weight <= 0:
                    errors.append("Weight must be a positive number")
            except ValueError:
                errors.append("Weight must be a valid number")

        return errors


class CampaignInfoStep(BaseStep):
    """
    First step of campaign creation wizard.

    Collects basic campaign information: name, description, and target configuration.
    """

    # UI Text Constants
    TITLE = "Campaign Information"
    NAME_LABEL = "Campaign Name:"
    NAME_PLACEHOLDER = "Enter campaign name"
    DESCRIPTION_LABEL = "Description:"
    DESCRIPTION_PLACEHOLDER = "Enter campaign description"
    OBJECTIVE_SCOPE_LABEL = "Objective Type:"
    MULTI_OBJECTIVE_STRATEGY_LABEL = "Multi-Objective Strategy:"
    TARGETS_LABEL = "Targets/Objectives:"
    ADD_TARGET_BUTTON_TEXT = "Add Another Target"
    ADD_TARGET_BUTTON_TOOLTIP = "Add a new target to the campaign"
    SURROGATE_MODEL_LABEL = "Surrogate Model:"
    ACQUISITION_FUNCTION_LABEL = "Acquisition Function:"

    # Object Name Constants
    FORM_INPUT_OBJECT_NAME = "FormInput"
    FORM_LABEL_OBJECT_NAME = "FormLabel"

    # Validation Error Constants
    VALIDATION_ERROR_TITLE = "Validation Error"
    CAMPAIGN_NAME_REQUIRED_MESSAGE = "Campaign name is required."
    TARGET_REQUIRED_MESSAGE = "At least one target is required."
    MIN_VALUE_TARGET_MESSAGE = "Min value must be a number."
    MAX_VALUE_TARGET_MESSAGE = "Max value must be a number."
    WEIGHT_TARGET_MESSAGE = "Weight must be a number."
    TARGET_NAME_REQUIRED_MESSAGE = "At least one target must have a name"
    SINGLE_TARGET_REQUIRED_MESSAGE = "Single-objective optimization requires exactly one target."
    MULTI_TARGET_MINIMUM_MESSAGE = "Multi-objective optimization requires at least two targets."
    MULTI_TARGET_BOUNDS_REQUIRED_MESSAGE = "Bounds (min/max values) are required for multi-target campaigns."
    MULTI_TARGET_WEIGHT_REQUIRED_MESSAGE = "Weights are required for multi-target campaigns."
    INVALID_BOUNDS_MESSAGE = "Min value must be less than max value for target: {}"

    # Layout Constants
    MARGINS = (30, 30, 30, 30)
    MAIN_SPACING = 25
    FORM_SPACING = 15
    TARGET_SPACING = 10
    DESCRIPTION_HEIGHT = 100

    def __init__(self, wizard_data: Campaign, parent=None):
        self.target_rows: list[TargetRow] = []
        super().__init__(wizard_data, parent)
        self.campaign: Campaign = self.wizard_data

    def _setup_widget(self):
        """Setup the campaign info step UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*self.MARGINS)
        main_layout.setSpacing(self.MAIN_SPACING)

        # Title
        title = MainHeader(self.TITLE)
        main_layout.addWidget(title)

        # Form
        self._create_form(main_layout)

        # Add stretch
        main_layout.addStretch()

    def _create_form(self, parent_layout):
        """Create form with all input fields."""
        form_layout = QFormLayout()
        form_layout.setSpacing(self.FORM_SPACING)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        parent_layout.addLayout(form_layout)

        # Campaign name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.NAME_PLACEHOLDER)
        self.name_input.setObjectName(self.FORM_INPUT_OBJECT_NAME)
        form_label = SectionHeader(self.NAME_LABEL)
        form_label.setObjectName(self.FORM_LABEL_OBJECT_NAME)
        form_layout.addRow(form_label, self.name_input)

        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(self.DESCRIPTION_PLACEHOLDER)
        self.description_input.setFixedHeight(self.DESCRIPTION_HEIGHT)
        self.description_input.setObjectName(self.FORM_INPUT_OBJECT_NAME)
        desc_label = SectionHeader(self.DESCRIPTION_LABEL)
        desc_label.setObjectName(self.FORM_LABEL_OBJECT_NAME)
        form_layout.addRow(desc_label, self.description_input)

        # Objective selection
        self._create_objective_selection(form_layout)

        # Target section
        self._create_targets_section(form_layout)

        # Surrogate model section
        self.surrogate_combo = QComboBox()
        self.surrogate_combo.setObjectName("FormInput")
        for model in BOSurrogateModel:
            self.surrogate_combo.addItem(model.display_name, model.value)
        surrogate_label = SectionHeader(self.SURROGATE_MODEL_LABEL)
        surrogate_label.setObjectName(self.FORM_LABEL_OBJECT_NAME)
        form_layout.addRow(surrogate_label, self.surrogate_combo)

        # Acquisition function section
        self.acquisition_combo = QComboBox()
        self.acquisition_combo.setObjectName("FormInput")
        for func in BOAcquisitionFunction:
            self.acquisition_combo.addItem(func.display_name, func.value)
        acquisition_label = SectionHeader(self.ACQUISITION_FUNCTION_LABEL)
        acquisition_label.setObjectName(self.FORM_LABEL_OBJECT_NAME)
        form_layout.addRow(acquisition_label, self.acquisition_combo)

    def _create_objective_selection(self, form_layout):
        """Create objective scope and strategy selection controls."""
        self.objective_scope_combo = QComboBox()
        self.objective_scope_combo.setObjectName(self.FORM_INPUT_OBJECT_NAME)
        for scope in ObjectiveScope:
            self.objective_scope_combo.addItem(scope.display_name, scope.value)

        objective_scope_label = SectionHeader(self.OBJECTIVE_SCOPE_LABEL)
        objective_scope_label.setObjectName(self.FORM_LABEL_OBJECT_NAME)
        form_layout.addRow(objective_scope_label, self.objective_scope_combo)

        self.multi_objective_combo = QComboBox()
        self.multi_objective_combo.setObjectName(self.FORM_INPUT_OBJECT_NAME)
        for strategy in MultiObjectiveStrategy:
            self.multi_objective_combo.addItem(strategy.display_name, strategy.value)

        self.multi_objective_label = SectionHeader(self.MULTI_OBJECTIVE_STRATEGY_LABEL)
        self.multi_objective_label.setObjectName(self.FORM_LABEL_OBJECT_NAME)
        form_layout.addRow(self.multi_objective_label, self.multi_objective_combo)

        self.objective_scope_combo.currentIndexChanged.connect(self._handle_objective_scope_changed)
        self.multi_objective_combo.currentIndexChanged.connect(self._handle_multi_objective_changed)

        self._apply_objective_selection()

    def _create_targets_section(self, form_layout):
        """Create targets configuration section."""
        targets_widget = QWidget()
        targets_widget.setObjectName("TargetsWidget")
        targets_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        targets_layout = QVBoxLayout(targets_widget)
        targets_layout.setContentsMargins(0, 0, 0, 0)
        targets_layout.setSpacing(self.TARGET_SPACING)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        scroll_area.setMinimumHeight(200)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setObjectName("TargetsScrollArea")

        self.targets_container = QWidget()
        self.targets_layout = QVBoxLayout(self.targets_container)
        self.targets_container.setObjectName("TargetsContainer")
        self.targets_container.setStyleSheet("""
            QWidget#TargetsContainer {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 0px;
            }
        """)
        # self.targets_layout = QVBoxLayout(self.targets_container)
        self.targets_layout.setContentsMargins(10, 10, 10, 10)
        self.targets_layout.setSpacing(5)

        self._add_targets_header()

        scroll_area.setWidget(self.targets_container)
        targets_layout.addWidget(scroll_area)

        self.add_target_btn = PrimaryButton(self.ADD_TARGET_BUTTON_TEXT)
        self.add_target_btn.setObjectName("PrimaryButton")
        self.add_target_btn.setFixedWidth(250)
        self.add_target_btn.setToolTip(self.ADD_TARGET_BUTTON_TOOLTIP)
        self.add_target_btn.clicked.connect(self._handle_add_target_click)
        targets_layout.addWidget(self.add_target_btn)

        targets_label = SectionHeader(self.TARGETS_LABEL)
        targets_label.setObjectName(self.FORM_LABEL_OBJECT_NAME)
        form_layout.addRow(targets_label, targets_widget)

    def _handle_objective_scope_changed(self):
        """Update UI when objective scope changes."""
        self._apply_objective_selection()

    def _handle_multi_objective_changed(self):
        """Update UI when multi-objective strategy changes."""
        self._apply_objective_selection()

    def _apply_objective_selection(self):
        """Apply objective scope/strategy selections to the UI."""
        scope = self._get_objective_scope()
        is_multi = scope == ObjectiveScope.MULTI.value

        self.multi_objective_label.setVisible(is_multi)
        self.multi_objective_combo.setVisible(is_multi)

        if hasattr(self, "add_target_btn"):
            if is_multi:
                self.add_target_btn.setVisible(True)
            else:
                self.add_target_btn.setVisible(False)
                self._ensure_single_target_row()

        strategy = self._get_multi_objective_strategy()
        show_weights = is_multi and strategy == MultiObjectiveStrategy.DESIRABILITY.value
        self._set_weight_column_visible(show_weights)
        self._update_remove_buttons()

    def _get_objective_scope(self) -> str:
        """Get the selected objective scope value."""
        return self.objective_scope_combo.currentData() or ObjectiveScope.SINGLE.value

    def _get_multi_objective_strategy(self) -> str:
        """Get the selected multi-objective strategy value."""
        return self.multi_objective_combo.currentData() or MultiObjectiveStrategy.DESIRABILITY.value

    def _ensure_single_target_row(self):
        """Ensure exactly one target row exists."""
        if not self.target_rows:
            self._add_target_row()
            return

        while len(self.target_rows) > 1:
            self._remove_target_row(self.target_rows[-1])

    def _set_weight_column_visible(self, visible: bool):
        """Show or hide weight column and inputs."""
        if hasattr(self, "targets_header_labels") and len(self.targets_header_labels) > 5:
            self.targets_header_labels[5].setVisible(visible)
        for row in self.target_rows:
            row.set_weight_visible(visible)

    def _add_targets_header(self):
        """Add header row for targets table."""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 5)
        header_layout.setSpacing(5)

        headers = ["Name", "Mode", "Min", "Max", "Transform", "Weight", ""]

        self.targets_header_labels = []

        for header in headers:
            label = QLabel(header)
            label.setStyleSheet("font-weight: bold; color: #666; font-size: 11px;")
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            header_layout.addWidget(label)
            self.targets_header_labels.append(label)

        for idx, stretch in enumerate(COLUMN_STRETCH):
            header_layout.setStretch(idx, stretch)

        self.targets_layout.addWidget(header_widget)

    def _handle_add_target_click(self):
        """Slot for the 'Add Target' button. Calls _add_target_row with no target."""
        self._add_target_row()

    def _add_target_row(self, target: Target | None = None):
        """Add a new target row."""
        if target is None:
            target = Target()

        target_row = TargetRow(target, self._remove_target_row)
        show_weights = (
            self._get_objective_scope() == ObjectiveScope.MULTI.value
            and self._get_multi_objective_strategy() == MultiObjectiveStrategy.DESIRABILITY.value
        )
        target_row.set_weight_visible(show_weights)
        self.target_rows.append(target_row)
        self.targets_layout.addWidget(target_row)

        # Update remove button visibility
        self._update_remove_buttons()

    def _remove_target_row(self, target_row: TargetRow):
        """Remove a target row."""
        if target_row in self.target_rows:
            self.target_rows.remove(target_row)
            self.targets_layout.removeWidget(target_row)
            target_row.deleteLater()
            self._update_remove_buttons()

    def _update_remove_buttons(self):
        """Update remove button visibility based on number of targets."""
        if self._get_objective_scope() == ObjectiveScope.SINGLE.value:
            show_remove = False
        else:
            show_remove = len(self.target_rows) > 1
        for row in self.target_rows:
            row.remove_btn.setVisible(show_remove)

    def validate(self) -> bool:
        """Validate form data."""
        if not self.name_input.text().strip():
            ErrorDialog.show_error(self.VALIDATION_ERROR_TITLE, self.CAMPAIGN_NAME_REQUIRED_MESSAGE, parent=self)
            return False

        if not self.target_rows:
            ErrorDialog.show_error(self.VALIDATION_ERROR_TITLE, self.TARGET_REQUIRED_MESSAGE, parent=self)
            return False

        validation_errors = []
        valid_targets = []

        for i, row in enumerate(self.target_rows, 1):
            row_errors = row.get_validation_errors()
            if row_errors:
                for error in row_errors:
                    validation_errors.append(f"Target {i}: {error}")
            else:
                if row.name_input.text().strip():
                    valid_targets.append(row)

        if validation_errors:
            error_message = "Please fix the following errors:\n\n" + "\n".join(validation_errors)
            ErrorDialog.show_error(self.VALIDATION_ERROR_TITLE, error_message, parent=self)
            return False

        if not valid_targets:
            ErrorDialog.show_error(self.VALIDATION_ERROR_TITLE, self.TARGET_NAME_REQUIRED_MESSAGE, parent=self)
            return False

        scope = self._get_objective_scope()
        strategy = self._get_multi_objective_strategy()

        if scope == ObjectiveScope.SINGLE.value:
            if len(valid_targets) != 1:
                ErrorDialog.show_error(self.VALIDATION_ERROR_TITLE, self.SINGLE_TARGET_REQUIRED_MESSAGE, parent=self)
                return False

        if scope == ObjectiveScope.MULTI.value:
            if len(valid_targets) < 2:
                ErrorDialog.show_error(self.VALIDATION_ERROR_TITLE, self.MULTI_TARGET_MINIMUM_MESSAGE, parent=self)
                return False

            if strategy == MultiObjectiveStrategy.DESIRABILITY.value:
                multi_target_errors = []

                for i, row in enumerate(valid_targets, 1):
                    target_data = row.get_target_data()

                    # Bounds are required for desirability multi-target
                    if target_data.min_value is None or target_data.max_value is None:
                        multi_target_errors.append(
                            f"Target {i} ({target_data.name}): {self.MULTI_TARGET_BOUNDS_REQUIRED_MESSAGE}"
                        )

                    # Weights are required for desirability multi-target
                    if target_data.weight is None:
                        multi_target_errors.append(
                            f"Target {i} ({target_data.name}): {self.MULTI_TARGET_WEIGHT_REQUIRED_MESSAGE}"
                        )

                if multi_target_errors:
                    error_message = "Multi-target validation errors:\n\n" + "\n".join(multi_target_errors)
                    ErrorDialog.show_error(self.VALIDATION_ERROR_TITLE, error_message, parent=self)
                    return False

        return True

    def save_data(self):
        """Save form data to shared data."""
        self.campaign.name = self.name_input.text().strip()
        self.campaign.description = self.description_input.toPlainText().strip()
        self.campaign.objective_scope = self._get_objective_scope()
        self.campaign.multi_objective_strategy = self._get_multi_objective_strategy()

        self.campaign.targets = []
        for row in self.target_rows:
            if row.is_valid():
                self.campaign.targets.append(row.get_target_data())

    def load_data(self):
        """Load data from shared data into form."""
        self.name_input.setText(self.campaign.name)
        self.description_input.setPlainText(self.campaign.description)

        self._resolve_objective_defaults()
        self._set_combo_value(self.objective_scope_combo, self.campaign.objective_scope)
        self._set_combo_value(self.multi_objective_combo, self.campaign.multi_objective_strategy)

        # Clear existing target rows
        for row in self.target_rows[:]:
            self._remove_target_row(row)

        # Load targets or add one empty target if none exist
        if self.campaign.targets:
            for target in self.campaign.targets:
                self._add_target_row(target)
        else:
            self._add_target_row()

        self._apply_objective_selection()

    def reset(self):
        """Reset form to initial state."""
        self.name_input.clear()
        self.description_input.clear()

        self._set_combo_value(self.objective_scope_combo, ObjectiveScope.SINGLE.value)
        self._set_combo_value(self.multi_objective_combo, MultiObjectiveStrategy.DESIRABILITY.value)

        for row in self.target_rows[:]:
            self._remove_target_row(row)
        self._add_target_row()
        self._apply_objective_selection()

    def _set_combo_value(self, combo: QComboBox, value: str) -> None:
        """Set a combo box current index based on item data value."""
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _resolve_objective_defaults(self) -> None:
        """Ensure objective scope/strategy are consistent with current targets."""
        if not self.campaign.objective_scope:
            self.campaign.objective_scope = ObjectiveScope.SINGLE.value

        if len(self.campaign.targets) > 1:
            self.campaign.objective_scope = ObjectiveScope.MULTI.value

        if self.campaign.objective_scope == ObjectiveScope.MULTI.value and not self.campaign.multi_objective_strategy:
            self.campaign.multi_objective_strategy = MultiObjectiveStrategy.DESIRABILITY.value

        if len(self.campaign.targets) <= 1 and self.campaign.objective_scope == ObjectiveScope.MULTI.value:
            self.campaign.objective_scope = ObjectiveScope.SINGLE.value
