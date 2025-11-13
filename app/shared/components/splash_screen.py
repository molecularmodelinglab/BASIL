from PySide6.QtWidgets import QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor
import os

class SplashScreen(QSplashScreen):
    def __init__(self):
        logo_path = os.path.join(os.path.dirname(__file__), "../../../assets/logo.png")
        pixmap = QPixmap(logo_path) if os.path.exists(logo_path) else QPixmap(500, 400)
        
        if not pixmap.isNull():
            pixmap = pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.show_status("Initializing...")
    
    def show_status(self, message):
        """Update the splash screen message"""
        self.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()