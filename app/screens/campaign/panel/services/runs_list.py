"""
Screen for displaying the list of all runs for a campaign.
"""

from datetime import datetime
from typing import Any, Dict, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from app.core.base import BaseWidget
from app.shared.components.buttons import PrimaryButton
from app.shared.components.cards import Card, EmptyStateCard


class RunCard(Card):
    """Card representing a single run in the runs list."""

    CARD_MARGIN = (10, 5, 10, 5)
    CARD_SPACING = 6
    RUN_NUM_FONT_SIZE = 12

    run_clicked = Signal(int)

    def __init__(self, run_data: Dict[str, Any], run_number: int, parent=None):
        self.run_data = run_data
        self.run_number = run_number
        super().__init__(parent)
        self._setup_card()

    def _setup_card(self):
        """Setup the run card UI."""
        self.setMinimumHeight(110)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.CARD_MARGIN)
        layout.setSpacing(self.CARD_SPACING)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        run_title = QLabel(f"Run {self.run_number}")
        run_font = QFont()
        run_font.setPointSize(self.RUN_NUM_FONT_SIZE)
        run_font.setBold(True)
        run_title.setFont(run_font)
        header_layout.addWidget(run_title)

        # Compute completion to infer status
        experiments_count = len(self.run_data.get("experiments", []))
        completed_count = sum(
            1
            for exp in self.run_data.get("experiments", [])
            if any(
                target["name"] in exp and exp[target["name"]] is not None for target in self.run_data.get("targets", [])
            )
        )
        completion_percentage = (completed_count / experiments_count) * 100 if experiments_count > 0 else 0

        # Derive status from completion progress
        status = "pending" if completion_percentage < 100 else "completed"
        status_label = QLabel(status.title())
        status_label.setObjectName(f"RunStatus{status.title()}")
        status_label.setStyleSheet(self._get_status_style(status))
        header_layout.addWidget(status_label)

        header_layout.addStretch()

        created_date = self.run_data.get("created_at", datetime.now())
        if isinstance(created_date, str):
            date_text = created_date
        else:
            date_text = created_date.strftime("%b %d, %Y at %H:%M")

        date_label = QLabel(date_text)
        date_label.setStyleSheet("color: #666; font-size: 11px;")
        header_layout.addWidget(date_label)

        layout.addLayout(header_layout)

        details_text = f"{experiments_count} experiments"
        if completed_count > 0:
            details_text += f" • {completed_count} completed"

        if self.run_data.get("targets"):
            target_names = [
                t.get("name", t) if isinstance(t, dict) else str(t) for t in self.run_data.get("targets", [])
            ]
            details_text += f" • Targets: {', '.join(target_names)}"

        details_label = QLabel(details_text)
        details_label.setStyleSheet("color: #555; font-size: 12px;")
        layout.addWidget(details_label)

        # Progress bar (visual representation of completion)
        if experiments_count > 0:
            progress_layout = QHBoxLayout()
            progress_layout.setSpacing(5)

            progress_label = QLabel("Progress:")
            progress_label.setStyleSheet("color: #666; font-size: 11px;")
            progress_layout.addWidget(progress_label)

            progress_text = f"{completion_percentage:.0f}% ({completed_count}/{experiments_count})"
            progress_value = QLabel(progress_text)
            progress_value.setStyleSheet("color: #444; font-size: 11px; font-weight: bold;")
            progress_layout.addWidget(progress_value)

            progress_layout.addStretch()
            layout.addLayout(progress_layout)

    def _get_status_style(self, status: str) -> str:
        """Get styling for status badge."""
        common = "padding: 2px 4px; border-radius: 4px; font-size: 10px; font-weight: bold;"
        status_styles = {
            "completed": f"background-color: #d4edda; color: #155724; {common}",
            "running": f"background-color: #fff3cd; color: #856404; {common}",
            "failed": f"background-color: #f8d7da; color: #721c24; {common}",
            "pending": f"background-color: #e2e3e5; color: #383d41; {common}",
        }
        return status_styles.get(status, status_styles["completed"])

    def mousePressEvent(self, event):
        """Handle mouse press to emit run clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.run_clicked.emit(self.run_number)
        super().mousePressEvent(event)


class RunsListScreen(BaseWidget):
    """Screen displaying the list of all runs."""

    TITLE_TEXT = "All Runs"
    SUBTITLE_TEXT = "View and manage your experiment runs"
    GENERATE_NEW_RUN_TEXT = "Generate New Run"
    EMPTY_MESSAGE = "No runs yet"
    EMPTY_SECONDARY = "Generate your first run to start experimenting"
    RUNS_LIST_STYLE = """QScrollArea {
                        background: transparent;
                        border: none;
                    }
                    QScrollArea > QWidget > QWidget {
                        background: transparent;
                    }"""
    RUNS_SCREEN_STYLE = """#RunsListScreen {
        background-color: #f8f9fb;
    }"""
    LAYOUT_MARGIN = (20, 20, 20, 20)
    LAYOUT_SPACING = 20

    run_selected = Signal(int)
    new_run_requested = Signal()

    def __init__(self, runs_data: List[Dict[str, Any]], parent=None):
        self.runs_data = runs_data or []
        super().__init__(parent)

    def _setup_widget(self):
        """Setup the runs list screen UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(*self.LAYOUT_MARGIN)
        main_layout.setSpacing(self.LAYOUT_SPACING)

        self.setObjectName("RunsListScreen")
        self.setStyleSheet(self.RUNS_SCREEN_STYLE)

        header_widget = self._create_header()
        main_layout.addWidget(header_widget)

        content_holder = QWidget()
        self.content_layout = QVBoxLayout(content_holder)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        main_layout.addWidget(content_holder)

        self._refresh_view()

    def _create_header(self) -> QWidget:
        """Create the header section."""
        header_widget = QWidget()
        layout = QHBoxLayout(header_widget)
        layout.setSpacing(15)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)

        title_label = QLabel(self.TITLE_TEXT)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)

        self.subtitle_label = QLabel(self._build_subtitle())
        self.subtitle_label.setStyleSheet("color: #666; font-size: 14px;")
        title_layout.addWidget(self.subtitle_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        return header_widget

    def _create_runs_list(self) -> QWidget:
        """Create the scrollable list of runs."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_area.setStyleSheet(self.RUNS_LIST_STYLE)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Add run cards (in reverse order - newest first)
        for i, run_data in enumerate(reversed(self.runs_data)):
            run_number = len(self.runs_data) - i
            run_card = RunCard(run_data, run_number)
            run_card.run_clicked.connect(self.run_selected.emit)
            container_layout.addWidget(run_card)

        container_layout.addStretch()
        scroll_area.setWidget(container)

        return scroll_area

    def _create_empty_state(self) -> QWidget:
        """Create empty state when no runs exist."""
        empty_widget = QWidget()
        layout = QVBoxLayout(empty_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Empty state card
        icon_pixmap = self._get_empty_runs_icon()
        empty_state = EmptyStateCard(
            primary_message=self.EMPTY_MESSAGE, secondary_message=self.EMPTY_SECONDARY, icon_pixmap=icon_pixmap
        )
        layout.addWidget(empty_state)

        return empty_widget

    def _get_empty_runs_icon(self) -> QPixmap:
        """Get icon for empty runs state."""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.black)
        font = QFont("Segoe UI Emoji", 25)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "📊")
        painter.end()

        return pixmap
    
    def _build_subtitle(self) -> str:
        """Return subtitle including run count when available."""
        if self.runs_data:
            return f"{self.SUBTITLE_TEXT} ({len(self.runs_data)} runs)"
        return self.SUBTITLE_TEXT
    
    def _refresh_view(self):
        """Refresh the runs list view."""
        if self.subtitle_label:
            self.subtitle_label.setText(self._build_subtitle())

        if not self.content_layout:
            return

        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if widget := item.widget():
                widget.setParent(None)
                #Could be widget.deleteLater()

        if self.runs_data:
            self.content_layout.addWidget(self._create_runs_list())
        else:
            self.content_layout.addWidget(self._create_empty_state())


    def update_runs_data(self, runs_data: List[Dict[str, Any]]):
        """Update the runs data and refresh the display."""
        self.runs_data = runs_data or []
        self._refresh_view()

    def get_panel_buttons(self):
        """Return the panel-specific buttons."""
        generate_button = PrimaryButton(self.GENERATE_NEW_RUN_TEXT)
        generate_button.clicked.connect(self.new_run_requested.emit)
        return [generate_button]
