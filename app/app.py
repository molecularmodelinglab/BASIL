import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6 import QtGui

from app.logging_config import setup_application_logging
from app.main_application import MainApplication

APPLICATION_NAME = "BASIL"

def get_icon_path() -> str:
    """Get platform-specific icon path from bundled resources."""
    if sys.platform == "darwin":
        icon_name = "icon.icns"
    elif sys.platform.startswith("win"):
        icon_name = "icon.ico"
    else:
        icon_name = "icon.png"
    
    # Check if running as PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        icon_path = base_path / "assets" / "icons" / icon_name
    else:
        base_path = Path(__file__).parent.parent
        icon_path = base_path / "assets" / "icons" / icon_name
    
    if icon_path.exists():
        return str(icon_path)
    else:
        return None

def main():
    setup_application_logging(app_name=APPLICATION_NAME)

    logger = logging.getLogger(__name__)
    logger.info("BASIL Starting")

    try:

        # Windows-specific for proper taskbar icon
        if sys.platform.startswith("win"):
            try:
                import ctypes
                myappid = 'mml.unc.basil.0.0.1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception as e:
                logger.warning(f"Could not set AppUserModelID: {e}")
        app = QApplication(sys.argv)

        icon_path = get_icon_path()
        icon = None
        if icon_path:
            icon = QtGui.QIcon(str(icon_path))
            if icon and not icon.isNull():
                app.setWindowIcon(icon)
                logger.info(f"Icon loaded from: {icon_path}")
            else:
                logger.warning(f"Failed to load icon from: {icon_path}")
        else:
            logger.warning("No valid icon found; using default.")

        # Set application properties
        app.setApplicationName(APPLICATION_NAME)
        app.setOrganizationName("MML - UNC")

        logger.info("Qt Application created successfully")

        window = MainApplication()

        if icon and not icon.isNull():
            window.setWindowIcon(icon)

        window.show()
        logger.info("Main application window initialized and shown")
        sys.exit(app.exec())

    except Exception:
        logger.critical("Critical startup error", exc_info=True)
        sys.exit(1)
