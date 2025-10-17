"""
Runs panel managing the complete experiment workflow.
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QFont, QPainter, QPixmap
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget

from app.bayesopt.baybe_service import BayBeService
from app.core.base import BaseWidget
from app.models.campaign import Campaign
from app.screens.campaign.panel.services.experiments_table import ExperimentsTableScreen
from app.screens.campaign.panel.services.generation_progress import GenerationProgressScreen
from app.screens.campaign.panel.services.runs_data_manager import RunsDataManager
from app.screens.campaign.panel.services.runs_list import RunsListScreen
from app.shared.components.buttons import PrimaryButton
from app.shared.components.cards import EmptyStateCard
from app.shared.components.dialogs import GenerateExperimentsDialog


class ExperimentGenerationWorker(QObject):
    """Worker thread for generating experiments."""

    progress_updated = Signal(str)
    generation_completed = Signal(list)
    generation_failed = Signal(str)

    def __init__(self, campaign: Campaign, workspace_path: str, num_experiments: int, has_previous_data: bool):
        super().__init__()
        self.campaign = campaign
        self.workspace_path = workspace_path
        self.num_experiments = num_experiments
        self.has_previous_data = has_previous_data
        self.should_cancel = False

    def run(self):
        """Run the experiment generation process."""
        try:
            self.progress_updated.emit("Initializing BayBe service...")

            baybe_service = BayBeService(self.campaign, self.workspace_path)

            if self.should_cancel:
                return

            self.progress_updated.emit("Generating experiments...")

            # Generate experiments
            experiments = baybe_service.generate_experiments(self.num_experiments, self.has_previous_data)

            if self.should_cancel:
                return

            self.progress_updated.emit("Experiments generated successfully!")
            self.generation_completed.emit(experiments)

        except Exception as e:
            self.generation_failed.emit(str(e))

    def cancel(self):
        """Cancel the generation process."""
        self.should_cancel = True


class RunsPanel(BaseWidget):
    """Enhanced panel for the 'Runs' tab managing the complete workflow."""

    PRIMARY_MESSAGE = "No runs yet"
    SECONDARY_MESSAGE = "Generate your first run to start experimenting"
    PIXMAP_FONT = QFont("Segoe UI Emoji", 25)
    NEW_RUNS_BUTTON_TEXT = "Generate New Run"

    # Panel states
    EMPTY_STATE = "empty"
    RUNS_LIST_STATE = "runs_list"
    GENERATION_PROGRESS_STATE = "generation_progress"
    EXPERIMENTS_TABLE_STATE = "experiments_table"

    new_run_requested = Signal()

    def __init__(self, campaign: Campaign, workspace_path: str, parent=None):
        self.campaign = campaign
        self.workspace_path = workspace_path
        self.current_state = self.EMPTY_STATE

        # Initialize data manager
        self.runs_manager = RunsDataManager(workspace_path, campaign.id)

        self.current_experiments: List[Dict[str, Any]] = []
        self.current_run_number = 0

        # Generation worker
        self.generation_worker: Optional[ExperimentGenerationWorker] = None
        self.generation_thread: Optional[QThread] = None

        super().__init__(parent)

        self._load_and_set_initial_state()

    def _setup_widget(self):
        """Setup the panel's UI with a stacked widget for different states."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # Create all the different state widgets
        self._create_state_widgets()

    def _create_state_widgets(self):
        """Create widgets for all possible states."""
        self.empty_state_widget = self._create_empty_state_widget()
        self.stacked_widget.addWidget(self.empty_state_widget)

        # Runs list state (will be created when needed)
        self.runs_list_widget = None

        self.generation_progress_widget = None

        self.experiments_table_widget = None

    def _create_empty_state_widget(self) -> QWidget:
        """Create the empty state widget."""
        icon_pixmap = self._get_clock_icon_pixmap()
        empty_state = EmptyStateCard(
            primary_message=self.PRIMARY_MESSAGE,
            secondary_message=self.SECONDARY_MESSAGE,
            icon_pixmap=icon_pixmap,
        )
        return empty_state

    def _load_and_set_initial_state(self):
        """Load runs data and set the appropriate initial state."""
        runs_data = self.runs_manager.load_runs()

        if runs_data:
            self._switch_to_runs_list_state(runs_data)
        else:
            self._switch_to_empty_state()

    def _switch_to_empty_state(self):
        """Switch to the empty state."""
        self.current_state = self.EMPTY_STATE
        self.stacked_widget.setCurrentWidget(self.empty_state_widget)

    def _switch_to_runs_list_state(self, runs_data: List[Dict[str, Any]]):
        """Switch to the runs list state."""
        self.current_state = self.RUNS_LIST_STATE

        # Create or update runs list widget
        if self.runs_list_widget is None:
            self.runs_list_widget = RunsListScreen(runs_data)
            self.runs_list_widget.run_selected.connect(self._handle_run_selected)
            self.runs_list_widget.new_run_requested.connect(self._handle_generate_new_run)
            self.stacked_widget.addWidget(self.runs_list_widget)
        else:
            self.runs_list_widget.update_runs_data(runs_data)

        self.stacked_widget.setCurrentWidget(self.runs_list_widget)

    def _switch_to_generation_progress_state(self, experiment_count: int, is_first_run: bool):
        """Switch to the generation progress state."""
        self.current_state = self.GENERATION_PROGRESS_STATE

        # Create generation progress widget
        if self.generation_progress_widget:
            self.stacked_widget.removeWidget(self.generation_progress_widget)
            self.generation_progress_widget.setParent(None)

        self.generation_progress_widget = GenerationProgressScreen(experiment_count, is_first_run)
        self.generation_progress_widget.back_to_runs_requested.connect(self._handle_back_to_runs)
        self.generation_progress_widget.cancel_run_requested.connect(self._handle_cancel_generation)
        self.generation_progress_widget.generation_completed.connect(self._handle_generation_completed)

        self.stacked_widget.addWidget(self.generation_progress_widget)
        self.stacked_widget.setCurrentWidget(self.generation_progress_widget)

    def _switch_to_experiments_table_state(self, experiments: List[Dict[str, Any]], run_number: int):
        """Switch to the experiments table state."""
        self.current_state = self.EXPERIMENTS_TABLE_STATE

        # Create experiments table widget
        if self.experiments_table_widget:
            self.stacked_widget.removeWidget(self.experiments_table_widget)
            self.experiments_table_widget.setParent(None)

        self.experiments_table_widget = ExperimentsTableScreen(experiments, self.campaign, run_number)
        self.experiments_table_widget.back_to_runs_requested.connect(self._handle_back_to_runs)
        self.experiments_table_widget.save_results_requested.connect(self._handle_save_results)

        self.stacked_widget.addWidget(self.experiments_table_widget)
        self.stacked_widget.setCurrentWidget(self.experiments_table_widget)

    def _handle_generate_new_run(self):
        """Handle request to generate new run."""
        # Show dialog to get experiment count
        accepted, count = GenerateExperimentsDialog.get_experiment_count_from_user(self)

        if accepted and count > 0:
            # Check if this is the first run
            is_first_run = self.runs_manager.get_run_count() == 0

            self._switch_to_generation_progress_state(count, is_first_run)

            # Start generation in background
            self._start_experiment_generation(count, self.runs_manager.has_previous_data())

    def _start_experiment_generation(self, num_experiments: int, has_previous_data: bool):
        """Start the experiment generation process in a background thread."""
        self.generation_worker = ExperimentGenerationWorker(
            self.campaign, self.workspace_path, num_experiments, has_previous_data
        )
        self.generation_thread = QThread()

        self.generation_worker.moveToThread(self.generation_thread)

        self.generation_thread.started.connect(self.generation_worker.run)
        self.generation_worker.progress_updated.connect(self._handle_generation_progress)
        self.generation_worker.generation_completed.connect(self._handle_generation_completed)
        self.generation_worker.generation_failed.connect(self._handle_generation_failed)

        self.generation_thread.start()

    def _handle_generation_progress(self, status: str):
        """Handle progress updates from generation worker."""
        if self.generation_progress_widget:
            self.generation_progress_widget.update_status(status)

    def _handle_generation_completed(self, experiments: List[Dict[str, Any]]):
        """Handle successful completion of experiment generation."""
        # Stop the thread
        if self.generation_thread:
            self.generation_thread.quit()
            self.generation_thread.wait()

        run_number = self.runs_manager.add_run(experiments, self.campaign)
        self.current_run_number = run_number

        self._switch_to_experiments_table_state(experiments, run_number)

    def _handle_generation_failed(self, error_message: str):
        """Handle failed experiment generation."""
        if self.generation_thread:
            self.generation_thread.quit()
            self.generation_thread.wait()

        from app.shared.components.dialogs import ErrorDialog

        ErrorDialog.show_error("Generation Failed", f"Failed to generate experiments: {error_message}", parent=self)

        runs_data = self.runs_manager.load_runs()
        if runs_data:
            self._switch_to_runs_list_state(runs_data)
        else:
            self._switch_to_empty_state()

    def _handle_cancel_generation(self):
        """Handle cancellation of experiment generation."""
        if self.generation_worker:
            self.generation_worker.cancel()

        # Stop the thread
        if self.generation_thread:
            self.generation_thread.quit()
            self.generation_thread.wait()

        # Go back to previous state
        runs_data = self.runs_manager.load_runs()
        if runs_data:
            self._switch_to_runs_list_state(runs_data)
        else:
            self._switch_to_empty_state()

    def _handle_run_selected(self, run_number: int):
        """Handle selection of a specific run from the list."""
        run_data = self.runs_manager.get_run(run_number)
        if run_data:
            self.current_run_number = run_number
            experiments = run_data.get("experiments", [])
            self._switch_to_experiments_table_state(experiments, run_number)

    def _handle_back_to_runs(self):
        """Handle request to go back to runs list."""
        runs_data = self.runs_manager.load_runs()
        if runs_data:
            self._switch_to_runs_list_state(runs_data)
        else:
            self._switch_to_empty_state()

    def _handle_save_results(self, experiments: List[Dict[str, Any]]):
        """Handle saving of experiment results."""
        run_number = getattr(self, "current_run_number", None)
        if not run_number:
            # Fallback to the most recent run
            runs_data = self.runs_manager.load_runs()
            run_number = len(runs_data) if runs_data else 1

        # Save the updated experiments
        self.runs_manager.update_run_experiments(self.current_run_number, experiments)

        from app.shared.components.dialogs import InfoDialog

        InfoDialog.show_info("Results Saved", "Experiment results have been saved successfully.", parent=self)

    def _get_clock_icon_pixmap(self) -> QPixmap:
        """Get a clock icon pixmap."""
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(self.PIXMAP_FONT)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🕐")
        painter.end()

        return pixmap

    def get_panel_buttons(self):
        """Return buttons specific to this panel based on current state."""
        if self.current_state == self.EMPTY_STATE:
            generate_button = PrimaryButton(self.NEW_RUNS_BUTTON_TEXT)
            generate_button.clicked.connect(self._handle_generate_new_run)
            return [generate_button]

        elif self.current_state == self.RUNS_LIST_STATE and self.runs_list_widget:
            return self.runs_list_widget.get_panel_buttons()

        elif self.current_state == self.GENERATION_PROGRESS_STATE and self.generation_progress_widget:
            return self.generation_progress_widget.get_panel_buttons()

        elif self.current_state == self.EXPERIMENTS_TABLE_STATE and self.experiments_table_widget:
            generate_button = PrimaryButton(self.NEW_RUNS_BUTTON_TEXT)
            generate_button.clicked.connect(self._handle_generate_new_run)
            return [generate_button]

        return []
