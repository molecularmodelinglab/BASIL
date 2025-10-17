"""
Reusable button components for the application.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton


class PrimaryButton(QPushButton):
    """Primary action button with consistent styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("PrimaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class SecondaryButton(QPushButton):
    """Secondary action button with consistent styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("SecondaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class DangerButton(QPushButton):
    """Danger/destructive action button with consistent styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("DangerButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class NavigationButton(QPushButton):
    """Navigation button for wizard-style interfaces."""

    def __init__(self, text: str, button_type: str = "next", parent=None):
        super().__init__(text, parent)

        if button_type == "back":
            self.setObjectName("BackButton")
        else:
            self.setObjectName("NextButton")

        self.setCursor(Qt.CursorShape.PointingHandCursor)
