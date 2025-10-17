"""
Base classes for BASIL application screens and widgets.
"""

from typing import Optional

from PySide6.QtWidgets import QMainWindow, QWidget

from app.shared.constants import ScreenName


class BaseScreen(QMainWindow):
    """
    Base class for all main application screens.

    Provides common functionality for screen management,
    navigation, and styling.
    """

    DEFAULT_WINDOW_TITLE = "BASIL"

    GEOMETRY = (100, 100, 1200, 700)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.DEFAULT_WINDOW_TITLE)
        self.setGeometry(*self.GEOMETRY)
        self._setup_screen()
        self._apply_styles()

    def _setup_screen(self):
        """Setup the screen UI. Should be implemented by subclasses."""
        pass

    def _apply_styles(self):
        """Apply base styles. Can be overridden by subclasses."""
        from app.shared.styles.theme import get_base_styles

        self.setStyleSheet(get_base_styles())

    def navigate_to(self, screen_name: ScreenName, data: Optional[dict] = None):
        """Navigate to another screen with optional data."""
        if hasattr(self.parent(), "navigate_to"):
            self.parent().navigate_to(screen_name, data)


class BaseWidget(QWidget):
    """
    Base class for reusable widgets.

    Provides common functionality for validation,
    data handling, and styling.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_widget()
        self._apply_styles()

    def _setup_widget(self):
        """Setup the widget UI. Should be implemented by subclasses."""
        pass

    def _apply_styles(self):
        """Apply base styles. Can be overridden by subclasses."""
        from app.shared.styles.theme import get_widget_styles

        self.setStyleSheet(get_widget_styles())

    def validate(self) -> bool:
        """Validate widget data. Override in subclasses as needed."""
        return True

    def get_data(self) -> dict:
        """Get widget data. Override in subclasses as needed."""
        return {}

    def set_data(self, data: dict):
        """Set widget data. Override in subclasses as needed."""
        pass


class BaseStep(BaseWidget):
    """
    Base class for wizard steps in multi-step processes.

    Extends BaseWidget with step-specific functionality.
    """

    def __init__(self, wizard_data, parent=None):
        self.wizard_data = wizard_data
        super().__init__(parent)

    def save_data(self):
        """Save step data to shared data. Override in subclasses."""
        pass

    def load_data(self):
        """Load data from shared data into step. Override in subclasses."""
        pass
