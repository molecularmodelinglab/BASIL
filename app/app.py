import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

APPLICATION_NAME = "BASIL"


def get_icon_path() -> str | None:
    """Get platform-specific icon path from bundled resources."""
    if sys.platform == "darwin":
        icon_name = "icon.icns"
    elif sys.platform.startswith("win"):
        icon_name = "icon.ico"
    else:
        icon_name = "icon.png"

    # Check if running as PyInstaller bundle
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)  # type: ignore
        icon_path = base_path / "assets" / "icons" / icon_name
    else:
        base_path = Path(__file__).parent.parent
        icon_path = base_path / "assets" / "icons" / icon_name

    if icon_path.exists():
        return str(icon_path)
    else:
        return None


def main():
    try:
        # Windows-specific for proper taskbar icon
        if sys.platform.startswith("win"):
            try:
                import ctypes

                myappid = "mml.unc.basil.0.0.1"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except Exception:
                pass

        app = QApplication(sys.argv)

        from app.shared.components.splash_screen import SplashScreen

        splash = SplashScreen()
        splash.show()
        splash.show_status("Starting BASIL...")

        splash.show_status("Loading modules...")
        from PySide6 import QtGui

        from app.logging_config import setup_application_logging
        from app.main_application import MainApplication

        setup_application_logging(app_name=APPLICATION_NAME)
        logger = logging.getLogger(__name__)
        logger.info("BASIL Starting")

        splash.show_status("Loading resources...")
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

        splash.show_status("Initializing application...")
        window = MainApplication()

        if icon and not icon.isNull():
            window.setWindowIcon(icon)

        splash.show_status("Loading workspace...")
        window.show()
        logger.info("Main application window initialized and shown")

        splash.finish(window)
        sys.exit(app.exec())

    except Exception as e:
        # Logger might not be initialized yet
        try:
            logger = logging.getLogger(__name__)
            logger.critical("Critical startup error", exc_info=True)
        except Exception:
            print(f"Critical startup error: {e}", file=sys.stderr)
        sys.exit(1)
