import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QSplashScreen


class SplashScreen(QSplashScreen):
    def __init__(self):
        logo_path = self._get_logo_path()
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap(500, 400)

        if not pixmap.isNull():
            pixmap = pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        super().__init__(pixmap, Qt.WindowStaysOnTopHint)

        self.setWindowFlag(Qt.FramelessWindowHint)
        self.show_status("Initializing...")

    def _get_logo_path(self) -> Path:
        """Get logo path for both bundled and development environments."""
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)  # type: ignore
        else:
            base_path = Path(__file__).parent.parent.parent.parent
        return base_path / "assets" / "logo.png"

    def show_status(self, message):
        """Update the splash screen message"""
        self.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()
