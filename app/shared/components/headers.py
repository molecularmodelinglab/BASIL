"""
Reusable header components for the application.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class MainHeader(QLabel):
    """Main page header with consistent styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("MainHeader")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)


class SectionHeader(QLabel):
    """Section header with consistent styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("SectionHeader")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)


class Subtitle(QLabel):
    """Subtitle text with consistent styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("Subtitle")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
