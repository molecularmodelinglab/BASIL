"""
Centralized styling and theming for the application.
"""

# Color palette
COLORS = {
    "primary": "#007BFF",
    "primary_dark": "#0056b3",
    "secondary": "#6c757d",
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8",
    "light": "#f8f9fa",
    "dark": "#343a40",
    "white": "#ffffff",
    "gray_100": "#f8f9fa",
    "gray_200": "#e9ecef",
    "gray_300": "#dee2e6",
    "gray_400": "#ced4da",
    "gray_500": "#adb5bd",
    "gray_600": "#6c757d",
    "gray_700": "#495057",
    "gray_800": "#343a40",
    "gray_900": "#212529",
    "border": "#e0e0e0",
    "text_primary": "#2c3e50",
    "text_secondary": "#555555",
    "text_muted": "#888888",
}

# Typography
FONTS = {
    "family": "Arial, sans-serif",
    "size_xs": "12px",
    "size_sm": "14px",
    "size_base": "16px",
    "size_lg": "18px",
    "size_xl": "20px",
    "size_2xl": "24px",
    "size_3xl": "28px",
    "weight_normal": "normal",
    "weight_bold": "bold",
}

# Spacing
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "base": "12px",
    "lg": "16px",
    "xl": "20px",
    "2xl": "24px",
    "3xl": "32px",
    "4xl": "40px",
}

# Border radius
RADIUS = {"sm": "4px", "base": "8px", "lg": "12px", "xl": "16px", "full": "50%"}


def get_base_styles() -> str:
    """Get base application styles."""
    return f"""
        /* Main window background */
        QMainWindow {{
            background-color: {COLORS["white"]};
            font-family: {FONTS["family"]};
        }}

        /* Main container widget */
        QWidget {{
            font-family: {FONTS["family"]};
            color: {COLORS["text_primary"]};
        }}
    """


def get_button_styles() -> str:
    """Get button component styles."""
    return f"""
        /* Primary Button */
        QPushButton[objectName="PrimaryButton"] {{
            background-color: {COLORS["primary"]};
            color: {COLORS["white"]};
            font-size: {FONTS["size_sm"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["2xl"]};
            border: none;
            border-radius: {RADIUS["base"]};
        }}
        QPushButton[objectName="PrimaryButton"]:hover {{
            background-color: {COLORS["primary_dark"]};
        }}
        QPushButton[objectName="PrimaryButton"]:pressed {{
            background-color: {COLORS["primary_dark"]};
        }}
        QPushButton[objectName="PrimaryButton"]:disabled {{
            background-color: {COLORS["gray_400"]};
            color: {COLORS["gray_600"]};
        }}

        /* Secondary Button */
        QPushButton[objectName="SecondaryButton"] {{
            background-color: {COLORS["white"]};
            color: {COLORS["text_primary"]};
            font-size: {FONTS["size_sm"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["2xl"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["base"]};
        }}
        QPushButton[objectName="SecondaryButton"]:hover {{
            background-color: {COLORS["gray_100"]};
        }}
        QPushButton[objectName="SecondaryButton"]:pressed {{
            background-color: {COLORS["gray_200"]};
        }}

        /* Danger Button */
        QPushButton[objectName="DangerButton"] {{
            background-color: {COLORS["danger"]};
            color: {COLORS["white"]};
            font-size: {FONTS["size_sm"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["2xl"]};
            border: none;
            border-radius: {RADIUS["base"]};
        }}
        QPushButton[objectName="DangerButton"]:hover {{
            background-color: #c82333;
        }}
    """


def get_header_styles() -> str:
    """Get header component styles."""
    return f"""
        /* Main Header */
        QLabel[objectName="MainHeader"] {{
            font-size: {FONTS["size_2xl"]};
            font-weight: {FONTS["weight_bold"]};
            color: {COLORS["text_primary"]};
            padding-bottom: {SPACING["base"]};
        }}

        /* Section Header */
        QLabel[objectName="SectionHeader"] {{
            font-size: {FONTS["size_lg"]};
            font-weight: {FONTS["weight_bold"]};
            color: {COLORS["text_primary"]};
            padding-top: {SPACING["lg"]};
        }}

        /* Subtitle */
        QLabel[objectName="Subtitle"] {{
            font-size: {FONTS["size_base"]};
            color: {COLORS["text_secondary"]};
        }}
    """


def get_card_styles() -> str:
    """Get card component styles."""
    return f"""
        /* Card Frame */
        QFrame[objectName="Card"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_200"]};
            border-radius: {RADIUS["base"]};
            padding: {SPACING["xl"]};
        }}

        /* Empty State Card */
        QFrame[objectName="EmptyStateCard"] {{
            background-color: {COLORS["gray_100"]};
            border: 1px dashed {COLORS["border"]};
            border-radius: {RADIUS["base"]};
            min-height: 250px;
        }}

        QFrame[objectName="EmptyStateCard"] QLabel {{
            background-color: transparent;
        }}
    """


def get_form_styles() -> str:
    """Get form component styles."""
    return f"""
        /* Campaign Info Scroll Area */
        QScrollArea#CampaignInfoScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea#CampaignInfoScrollArea > QWidget > QWidget#CampaignInfoScrollContainer {{
            background-color: transparent;
        }}

        /* Targets Section */
        QScrollArea#TargetsScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QWidget#TargetsContainer {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_200"]};
            border-radius: {RADIUS["base"]};
        }}

        /* Form Input */
        QLineEdit {{
            padding: {SPACING["base"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["base"]};
            font-size: {FONTS["size_sm"]};
            background-color: {COLORS["white"]};
        }}
        QLineEdit:focus {{
            border-color: {COLORS["primary"]};
            outline: none;
        }}

        /* Form Label */
        QLabel[objectName="FormLabel"] {{
            font-size: {FONTS["size_sm"]};
            font-weight: {FONTS["weight_bold"]};
            color: {COLORS["text_primary"]};
            margin-bottom: {SPACING["sm"]};
        }}

        /* Text Area */
        QTextEdit {{
            padding: {SPACING["base"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["base"]};
            font-size: {FONTS["size_sm"]};
            background-color: {COLORS["white"]};
        }}
        QTextEdit:focus {{
            border-color: {COLORS["primary"]};
        }}

        /* Combo Box */
        QComboBox {{
            padding: {SPACING["base"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["base"]};
            font-size: {FONTS["size_sm"]};
            background-color: {COLORS["white"]};
            color: {COLORS["text_primary"]};
            min-width: 120px;
        }}
        QComboBox:focus {{
            border-color: {COLORS["primary"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}
        /* Combo Box Dropdown List */
        QComboBox QAbstractItemView {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_300"]};
            color: {COLORS["text_primary"]};
            selection-background-color: {COLORS["primary"]};
            selection-color: {COLORS["white"]};
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: {SPACING["base"]};
            background-color: {COLORS["white"]};
            color: {COLORS["text_primary"]};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {COLORS["primary"]};
            color: {COLORS["white"]};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {COLORS["gray_100"]};
            color: {COLORS["text_primary"]};
        }}

        /* Specific styling for FormInput combo boxes */
        QComboBox[objectName="FormInput"] {{
            padding: {SPACING["base"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["base"]};
            font-size: {FONTS["size_sm"]};
            background-color: {COLORS["white"]};
            color: {COLORS["text_primary"]};
            min-width: 120px;
        }}
        QComboBox[objectName="FormInput"]:focus {{
            border-color: {COLORS["primary"]};
        }}
        QComboBox[objectName="FormInput"] QAbstractItemView {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_300"]};
            color: {COLORS["text_primary"]};
            selection-background-color: {COLORS["primary"]};
            selection-color: {COLORS["white"]};
        }}
        QComboBox[objectName="FormInput"] QAbstractItemView::item {{
            padding: {SPACING["base"]};
            background-color: {COLORS["white"]};
            color: {COLORS["text_primary"]};
            border: none;
        }}
        QComboBox[objectName="FormInput"] QAbstractItemView::item:selected {{
            background-color: {COLORS["primary"]};
            color: {COLORS["white"]};
        }}
        QComboBox[objectName="FormInput"] QAbstractItemView::item:hover {{
            background-color: {COLORS["gray_100"]};
            color: {COLORS["text_primary"]};
        }}
    """


def get_widget_styles() -> str:
    """Get combined widget styles."""
    return (
        get_base_styles()
        + get_button_styles()
        + get_header_styles()
        + get_card_styles()
        + get_form_styles()
        + get_table_styles()
        + get_tab_styles()
        + get_data_import_styles()
        + get_progress_styles()
        + get_dialog_form_styles()
    )


def get_table_styles() -> str:
    """Get table component styles."""
    return f"""
        /* Parameter Table */
        QTableWidget {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_200"]};
            border-radius: {RADIUS["base"]};
            gridline-color: {COLORS["gray_200"]};
            font-size: {FONTS["size_sm"]};
        }}

        QTableWidget::item {{
            padding: {SPACING["sm"]};
            border: none;
        }}

        QTableWidget::item:selected {{
            background-color: {COLORS["gray_100"]};
            color: {COLORS["text_primary"]};
        }}

        /* Table Headers */
        QHeaderView::section {{
            background-color: {COLORS["gray_100"]};
            color: {COLORS["text_primary"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]};
            border: 1px solid {COLORS["gray_200"]};
            border-radius: 0px;
        }}

        QHeaderView::section:first {{
            border-top-left-radius: {RADIUS["base"]};
        }}

        QHeaderView::section:last {{
            border-top-right-radius: {RADIUS["base"]};
        }}

        /* Parameter Name Input (in table) */
        QLineEdit[objectName="ParameterNameInput"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["sm"]};
            padding: {SPACING["base"]};
            font-size: {FONTS["size_sm"]};
            color: {COLORS["text_primary"]};
            min-width: 200px;
            max-width: 210px;
            min-height: 15px;
        }}

        QLineEdit[objectName="ParameterNameInput"]:focus {{
            border-color: {COLORS["primary"]};
        }}

        /* Parameter Type ComboBox (in table) */
        QComboBox[objectName="ParameterTypeCombo"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["sm"]};
            padding: {SPACING["base"]};
            font-size: {FONTS["size_sm"]};
            color: {COLORS["text_primary"]};
            min-width: 180px;
            max-width: 190px;
            min-height: 15px;
        }}

        QComboBox[objectName="ParameterTypeCombo"]:focus {{
            border-color: {COLORS["primary"]};
        }}

        QComboBox[objectName="ParameterTypeCombo"] QAbstractItemView {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_300"]};
            color: {COLORS["text_primary"]};
            selection-background-color: {COLORS["primary"]};
            selection-color: {COLORS["white"]};
        }}

        /* Constraints Widget (in table) */
        QTableWidget QWidget {{
            background-color: transparent;
        }}

        /* Constraint Labels */
        QTableWidget QLabel {{
            font-size: {FONTS["size_xs"]};
            color: {COLORS["text_secondary"]};
            font-weight: {FONTS["weight_bold"]};
            margin-right: {SPACING["xs"]};
        }}

        /* Constraint Spin Boxes */
        QDoubleSpinBox[objectName="ConstraintSpinBox"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["sm"]};
            padding: {SPACING["xs"]};
            font-size: {FONTS["size_sm"]};
            color: {COLORS["text_primary"]};
            min-width: 60px;
            max-width: 100px;
            min-height: 15px;
        }}

        QDoubleSpinBox[objectName="ConstraintSpinBox"]:focus {{
            border-color: {COLORS["primary"]};
        }}

        /* Spinbox buttons */
        QDoubleSpinBox[objectName="ConstraintSpinBox"]::up-button {{
            background-color: {COLORS["gray_100"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: 2px;
            width: 16px;
        }}

        QDoubleSpinBox[objectName="ConstraintSpinBox"]::up-button:hover {{
            background-color: {COLORS["gray_200"]};
        }}

        QDoubleSpinBox[objectName="ConstraintSpinBox"]::down-button {{
            background-color: {COLORS["gray_100"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: 2px;
            width: 16px;
        }}

        QDoubleSpinBox[objectName="ConstraintSpinBox"]::down-button:hover {{
            background-color: {COLORS["gray_200"]};
        }}

        /* Constraint Line Edit */
        QLineEdit[objectName="ConstraintLineEdit"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["sm"]};
            padding: {SPACING["xs"]} {SPACING["sm"]};
            font-size: {FONTS["size_xs"]};
            color: {COLORS["text_primary"]};
            min-width: 200px;
            max-width: 250px;
        }}

        QLineEdit[objectName="ConstraintLineEdit"]:focus {{
            border-color: {COLORS["primary"]};
        }}

        /* Values Text Edit */
        QTextEdit[objectName="ConstraintTextEdit"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["sm"]};
            padding: {SPACING["xs"]} {SPACING["sm"]};
            font-size: {FONTS["size_xs"]};
            color: {COLORS["text_primary"]};
            min-width: 200px;
            max-width: 250px;
        }}

        QTextEdit[objectName="ConstraintTextEdit"]:focus {{
            border-color: {COLORS["primary"]};
        }}

        /* Remove Button (in table) */
        QPushButton[objectName="ParameterRemoveButton"] {{
            background-color: {COLORS["danger"]};
            color: {COLORS["white"]};
            border: none;
            border-radius: {RADIUS["sm"]};
            font-size: {FONTS["size_base"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["sm"]};
            max-width: 20px;
            max-height: 20px;
            min-width: 10px;
            min-height: 10px;
        }}

        QPushButton[objectName="ParameterRemoveButton"]:hover {{
            background-color: #c82333;
        }}

        QPushButton[objectName="ParameterRemoveButton"]:pressed {{
            background-color: #bd2130;
        }}
    """


def get_data_import_styles() -> str:
    """Get data import screen styles."""
    return f"""
        /* Data Import Title */
        QLabel[objectName="DataImportTitle"] {{
            font-size: {FONTS["size_2xl"]};
            font-weight: {FONTS["weight_bold"]};
            color: {COLORS["text_primary"]};
           /* margin-bottom: {SPACING["lg"]}; */
        }}

        /* Data Import Description */
        QLabel[objectName="DataImportDescription"] {{
            font-size: {FONTS["size_base"]};
            color: {COLORS["text_secondary"]};
           /* margin-bottom: {SPACING["2xl"]}; */
            line-height: 1.4;
        }}

        /* Section Titles */
        QLabel[objectName="DataImportSectionTitle"] {{
            font-size: {FONTS["size_lg"]};
            font-weight: {FONTS["weight_bold"]};
            color: {COLORS["text_primary"]};
         /*   margin-bottom: {SPACING["base"]}; */
         /*   margin-top: {SPACING["xl"]}; */
        }}

        /* Drop Area */
        QWidget[objectName*="DragDrop"] {{
            background-color: {COLORS["gray_100"]};
            border: 2px dashed {COLORS["gray_300"]};
            border-radius: {RADIUS["lg"]};
            min-height: 120px;
          /*  margin: {SPACING["base"]}; */
        }}

        QWidget[objectName*="DragDrop"]:hover {{
            border-color: {COLORS["primary"]};
            background-color: {COLORS["gray_100"]};
        }}

        /* Drop Area Text */
        QLabel[objectName="DropAreaText"] {{
            font-size: {FONTS["size_base"]};
            color: {COLORS["text_secondary"]};
            margin-bottom: {SPACING["base"]};
        }}

        /* Data Import Buttons */
        QPushButton[objectName="DataImportBrowseButton"] {{
            background-color: {COLORS["primary"]};
            color: {COLORS["white"]};
            font-size: {FONTS["size_sm"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["2xl"]};
            border: none;
            border-radius: {RADIUS["base"]};
            min-width: 120px;
        }}

        QPushButton[objectName="DataImportBrowseButton"]:hover {{
            background-color: {COLORS["primary_dark"]};
        }}

        QPushButton[objectName="DataImportTemplateButton"] {{
            background-color: {COLORS["secondary"]};
            color: {COLORS["white"]};
            font-size: {FONTS["size_sm"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["xl"]};
            border: none;
            border-radius: {RADIUS["base"]};
            min-width: 120px;
        }}

        QPushButton[objectName="DataImportTemplateButton"]:hover {{
            background-color: #5a6268;
        }}

        /* Data Preview Table */
        QTableWidget[objectName="DataPreviewTable"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_200"]};
            border-radius: {RADIUS["base"]};
            gridline-color: {COLORS["gray_200"]};
            font-size: {FONTS["size_sm"]};
            min-height: 200px;
        }}

        QTableWidget[objectName="DataPreviewTable"]::item {{
            padding: {SPACING["sm"]};
            border: none;
        }}

        QTableWidget[objectName="DataPreviewTable"]::item:selected {{
            background-color: {COLORS["primary"]};
            color: {COLORS["white"]};
        }}

        /* Data Preview Headers */
        QTableWidget[objectName="DataPreviewTable"] QHeaderView::section {{
            background-color: {COLORS["gray_100"]};
            color: {COLORS["text_primary"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]};
            border: 1px solid {COLORS["gray_200"]};
        }}
    """


def get_tab_styles() -> str:
    """Get tab component styles."""
    return f"""
        /* Tab Buttons */
        QPushButton[objectName="InactiveTab"] {{
            background-color: transparent;
            color: {COLORS["text_secondary"]};
            border: none;
            border-bottom: 2px solid transparent;
            font-size: {FONTS["size_base"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["lg"]};
        }}
        QPushButton[objectName="InactiveTab"]:hover {{
            color: {COLORS["text_primary"]};
        }}
        QPushButton[objectName="ActiveTab"] {{
            background-color: transparent;
            color: {COLORS["primary"]};
            border: none;
            border-bottom: 2px solid {COLORS["primary"]};
            font-size: {FONTS["size_base"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["lg"]};
        }}
    """


def get_navigation_styles() -> str:
    """Get navigation component styles."""
    return f"""
        /* Navigation Container */
        QWidget[objectName="NavigationContainer"] {{
            background-color: {COLORS["white"]};
            border-top: 1px solid {COLORS["gray_200"]};
            padding: {SPACING["lg"]};
        }}

        /* Back Button */
        QPushButton[objectName="BackButton"] {{
            background-color: {COLORS["secondary"]};
            color: {COLORS["white"]};
            font-size: {FONTS["size_sm"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["2xl"]};
            border: none;
            border-radius: {RADIUS["base"]};
        }}
        QPushButton[objectName="BackButton"]:hover {{
            background-color: #5a6268;
        }}
        QPushButton[objectName="BackButton"]:disabled {{
            background-color: {COLORS["gray_400"]};
            color: {COLORS["gray_600"]};
        }}

        /* Next Button */
        QPushButton[objectName="NextButton"] {{
            background-color: {COLORS["primary"]};
            color: {COLORS["white"]};
            font-size: {FONTS["size_sm"]};
            font-weight: {FONTS["weight_bold"]};
            padding: {SPACING["base"]} {SPACING["2xl"]};
            border: none;
            border-radius: {RADIUS["base"]};
        }}
        QPushButton[objectName="NextButton"]:hover {{
            background-color: {COLORS["primary_dark"]};
        }}
    """


def get_confirmation_dialog_styles() -> str:
    """Get confirmation dialog styles."""
    return f"""
        QDialog#ConfirmationDialog, QDialog#GenerateExperimentsDialog {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_200"]};
            border-radius: {RADIUS["base"]};
        }}
        QLabel#ConfirmationDialogTitle, QLabel#DialogTitle {{
            font-size: {FONTS["size_lg"]};
            font-weight: {FONTS["weight_bold"]};
            color: {COLORS["text_primary"]};
            margin: {SPACING["base"]} 0;
        }}
        QLabel#ConfirmationDialogMessage, QLabel#DialogMessage {{
            font-size: {FONTS["size_sm"]};
            color: {COLORS["text_secondary"]};
            line-height: 1.4;
        }}
        QFrame#ConfirmationDialogSeparator, QFrame#DialogSeparator {{
            background-color: {COLORS["gray_200"]};
            border: none;
        }}
    """ + get_dialog_form_styles()


def get_info_dialog_styles() -> str:
    """Get info dialog styles."""
    return f"""
        QDialog#InfoDialog {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_200"]};
            border-radius: {RADIUS["base"]};
        }}
        QLabel#DialogTitle {{
            font-size: {FONTS["size_lg"]};
            font-weight: {FONTS["weight_bold"]};
            color: {COLORS["text_primary"]};
            margin: {SPACING["base"]} 0;
        }}
        QLabel#DialogMessage {{
            font-size: {FONTS["size_sm"]};
            color: {COLORS["text_secondary"]};
            line-height: 1.4;
        }}
        QFrame#DialogSeparator {{
            background-color: {COLORS["gray_200"]};
            border: none;
        }}
    """


def get_error_dialog_styles() -> str:
    """Get error dialog styles."""
    return f"""
        QDialog#InfoDialog {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["gray_200"]};
            border-radius: {RADIUS["base"]};
        }}
        QLabel#InfoDialogTitle {{
            font-size: {FONTS["size_lg"]};
            font-weight: {FONTS["weight_bold"]};
            color: #d32f2f;
            margin: {SPACING["base"]} 0;
        }}
        QLabel#DialogMessage {{
            font-size: {FONTS["size_sm"]};
            color: {COLORS["text_secondary"]};
            line-height: 1.4;
        }}
        QFrame#DialogSeparator {{
            background-color: #e57373;
            border: none;
        }}
    """


def get_dialog_form_styles() -> str:
    """Get styles for form elements in dialogs."""
    return f"""
        /* Dialog Spin Box */
        QSpinBox[objectName="DialogSpinBox"] {{
            padding: {SPACING["base"]};
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["base"]};
            font-size: {FONTS["size_sm"]};
            background-color: {COLORS["white"]};
            color: {COLORS["text_primary"]};
            min-width: 80px;
        }}
        QSpinBox[objectName="DialogSpinBox"]:focus {{
            border-color: {COLORS["primary"]};
        }}

        /* Dialog Label */
        QLabel[objectName="DialogLabel"] {{
            font-size: {FONTS["size_sm"]};
            color: {COLORS["text_primary"]};
            font-weight: {FONTS["weight_normal"]};
        }}
    """


def get_progress_styles() -> str:
    """Get styles for progress indicators."""
    return f"""
        /* Progress Bar */
        QProgressBar[objectName="GenerationProgress"] {{
            border: 1px solid {COLORS["gray_300"]};
            border-radius: {RADIUS["base"]};
            background-color: {COLORS["gray_100"]};
            height: 20px;
            text-align: center;
        }}
        QProgressBar[objectName="GenerationProgress"]::chunk {{
            background-color: {COLORS["primary"]};
            border-radius: {RADIUS["base"]};
        }}

        /* Status Labels */
        QLabel[objectName="GenerationTitle"] {{
            color: {COLORS["text_primary"]};
            font-weight: {FONTS["weight_bold"]};
        }}
        QLabel[objectName="GenerationSubtitle"] {{
            color: {COLORS["text_secondary"]};
        }}
        QLabel[objectName="GenerationStatus"] {{
            color: {COLORS["text_primary"]};
        }}
        QLabel[objectName="LastUpdateLabel"] {{
            color: {COLORS["text_secondary"]};
            font-style: italic;
        }}
    """
