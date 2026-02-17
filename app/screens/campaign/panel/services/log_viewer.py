"""
Live log viewer dialog for streaming log files.
"""

from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QTextEdit, QVBoxLayout

from app.shared.components.buttons import PrimaryButton, SecondaryButton


class LogViewerDialog(QDialog):
    """Dialog for viewing live log stream (tail -f behavior)."""

    # Dialog dimensions
    DIALOG_WIDTH = 900
    DIALOG_HEIGHT = 650

    # Layout spacing and margins
    LAYOUT_MARGINS = (30, 30, 30, 30)
    LAYOUT_SPACING = 20

    # Object names for styling
    DIALOG_OBJECT_NAME = "LogViewerDialog"
    TITLE_OBJECT_NAME = "DialogTitle"
    SEPARATOR_OBJECT_NAME = "DialogSeparator"
    INFO_OBJECT_NAME = "DialogMessage"
    LOG_TEXT_OBJECT_NAME = "LogTextArea"

    # Text constants
    WINDOW_TITLE = "View Logs"
    TITLE_TEXT = "BayBe Generation Logs"
    INFO_TEXT = "Live stream of experiment generation logs"
    FOLLOW_LOGS_TEXT = "Follow logs"
    CLEAR_BUTTON_TEXT = "Clear"
    CLOSE_BUTTON_TEXT = "Close"

    # Button dimensions
    CLEAR_BUTTON_WIDTH = 100
    CLOSE_BUTTON_WIDTH = 100

    # Log messages
    LOG_FILE_NOT_FOUND_MSG = "[Log file not found yet. Waiting for logs...]"
    LOG_FILE_EMPTY_MSG = "[Log file is empty. Waiting for logs...]"
    LOG_READ_ERROR_FORMAT = "[Error reading log file: {error}]"
    LOG_UPDATE_ERROR_FORMAT = "\n[Error reading log: {error}]\n"

    # Styling
    INFO_LABEL_STYLE = "color: #666; font-size: 13px;"

    DIALOG_STYLES = """
        QDialog#LogViewerDialog {
            background-color: white;
        }

        QLabel#DialogTitle {
            font-size: 18px;
            font-weight: bold;
            color: #1a1a1a;
        }

        QFrame#DialogSeparator {
            background-color: #e5e7eb;
        }

        QLabel#DialogMessage {
            font-size: 14px;
            color: #4b5563;
        }

        QTextEdit#LogTextArea {
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 12px;
        }
    """

    def __init__(self, log_file_path: Path, parent=None):
        super().__init__(parent)
        self.log_file_path = log_file_path
        self.last_position = 0
        self.auto_scroll_enabled = True

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setModal(False)  # Non-modal: you can open/close
        self.resize(self.DIALOG_WIDTH, self.DIALOG_HEIGHT)

        self._setup_ui()
        self._setup_file_watcher()
        self._load_initial_logs()

        # Apply consistent styling
        self.setObjectName(self.DIALOG_OBJECT_NAME)
        self.setStyleSheet(self.DIALOG_STYLES)

    def _setup_ui(self):
        """Setup the dialog UI elements."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.LAYOUT_MARGINS)
        layout.setSpacing(self.LAYOUT_SPACING)

        # Title
        title_label = QLabel(self.TITLE_TEXT)
        title_label.setObjectName(self.TITLE_OBJECT_NAME)
        layout.addWidget(title_label)

        # Separator
        separator = QFrame()
        separator.setObjectName(self.SEPARATOR_OBJECT_NAME)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Info label
        info_label = QLabel(self.INFO_TEXT)
        info_label.setObjectName(self.INFO_OBJECT_NAME)
        info_label.setStyleSheet(self.INFO_LABEL_STYLE)
        layout.addWidget(info_label)

        # Text area for logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName(self.LOG_TEXT_OBJECT_NAME)
        layout.addWidget(self.log_text)

        # Buttons
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)

    def _create_button_layout(self) -> QHBoxLayout:
        """Create and configure button layout."""
        button_layout = QHBoxLayout()

        # Auto-scroll
        self.follow_checkbox = QCheckBox(self.FOLLOW_LOGS_TEXT)
        self.follow_checkbox.setChecked(True)
        self.follow_checkbox.stateChanged.connect(self._on_follow_changed)

        button_layout.addWidget(self.follow_checkbox)

        # Clear button
        clear_btn = SecondaryButton(self.CLEAR_BUTTON_TEXT)
        clear_btn.clicked.connect(self.log_text.clear)
        clear_btn.setFixedWidth(self.CLEAR_BUTTON_WIDTH)

        button_layout.addWidget(clear_btn)
        button_layout.addStretch()

        # Close button
        close_btn = PrimaryButton(self.CLOSE_BUTTON_TEXT)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedWidth(self.CLOSE_BUTTON_WIDTH)
        button_layout.addWidget(close_btn)

        return button_layout

    def _setup_file_watcher(self):
        """Setup file system watcher for real-time updates."""
        if self.log_file_path.exists():
            self.file_watcher = QFileSystemWatcher([str(self.log_file_path)])
            self.file_watcher.fileChanged.connect(self._on_file_changed)
        else:
            self.file_watcher = None

    def _load_initial_logs(self):
        """Load initial log content."""
        if not self.log_file_path.exists():
            self.log_text.append(self.LOG_FILE_NOT_FOUND_MSG)
            return

        try:
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.last_position = f.tell()
                if content:
                    self.log_text.setPlainText(content)
                    if self.auto_scroll_enabled:
                        self._scroll_to_bottom()
                else:
                    self.log_text.append(self.LOG_FILE_EMPTY_MSG)
        except Exception as e:
            self.log_text.append(self.LOG_READ_ERROR_FORMAT.format(error=e))

    def _load_new_logs(self):
        """Load new log content (tail -f behavior)."""
        if not self.log_file_path.exists():
            return

        try:
            with open(self.log_file_path, "r", encoding="utf-8") as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = f.tell()

                if new_content:
                    self.log_text.append(new_content.rstrip())
                    if self.auto_scroll_enabled:
                        self._scroll_to_bottom()
        except Exception as e:
            self.log_text.append(self.LOG_UPDATE_ERROR_FORMAT.format(error=e))

    def _on_file_changed(self, path):
        """Handle file change event."""
        self._load_new_logs()
        if self.file_watcher and str(self.log_file_path) not in self.file_watcher.files():
            self.file_watcher.addPath(str(self.log_file_path))

    def _on_follow_changed(self, state):
        """Handle follow checkbox state change."""
        self.auto_scroll_enabled = bool(state)

    def _scroll_to_bottom(self):
        """Scroll text area to bottom."""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    @staticmethod
    def show_logs(log_file_path: Path, parent=None):
        """Show the log viewer dialog (non-blocking)."""
        dialog = LogViewerDialog(log_file_path, parent)
        dialog.show()
