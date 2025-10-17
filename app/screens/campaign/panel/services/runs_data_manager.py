"""
Data manager for handling runs data and persistence.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.models.campaign import Campaign
from app.shared.components.dialogs import ErrorDialog
from app.shared.constants import WorkspaceConstants


class RunsDataManager:
    """Manages runs data storage and retrieval."""

    RUNS_FOLDERNAME = "runs"

    def __init__(self, workspace_path: str, campaign_id: str):
        self.workspace_path = Path(workspace_path)
        self.campaign_id = campaign_id
        self.campaign_folder = self.workspace_path / WorkspaceConstants.CAMPAIGNS_DIRNAME / f"{self.campaign_id}"
        self.runs_dir = self.campaign_folder / self.RUNS_FOLDERNAME
        self.runs_file = self.runs_dir / f"runs_{campaign_id}.json"

        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def load_runs(self) -> List[Dict[str, Any]]:
        """Load all runs for the campaign."""
        if not self.runs_file.exists():
            return []

        try:
            with open(self.runs_file, "r", encoding="utf-8") as f:
                runs_data = json.load(f)

            # Convert date strings back to datetime objects
            for run in runs_data:
                if "created_at" in run:
                    run["created_at"] = datetime.fromisoformat(run["created_at"])
                if "updated_at" in run:
                    run["updated_at"] = datetime.fromisoformat(run["updated_at"])

            return runs_data
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            ErrorDialog.show_error("Error loading runs data", str(e), parent=None)
            return []

    def save_runs(self, runs_data: List[Dict[str, Any]]):
        """Save all runs data."""
        # Convert datetime objects to strings for JSON serialization
        serializable_runs = []
        for run in runs_data:
            run_copy = run.copy()
            if "created_at" in run_copy and isinstance(run_copy["created_at"], datetime):
                run_copy["created_at"] = run_copy["created_at"].isoformat()
            if "updated_at" in run_copy and isinstance(run_copy["updated_at"], datetime):
                run_copy["updated_at"] = run_copy["updated_at"].isoformat()
            serializable_runs.append(run_copy)

        try:
            with open(self.runs_file, "w", encoding="utf-8") as f:
                json.dump(serializable_runs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            ErrorDialog.show_error("Error saving runs data", str(e), parent=None)

    def add_run(self, experiments: List[Dict[str, Any]], campaign: Campaign) -> int:
        """Add a new run and return its run number."""
        runs_data = self.load_runs()

        # Create new run
        run_number = len(runs_data) + 1

        # Calculate completed count
        target_names = [target.name for target in campaign.targets]
        completed_count = sum(
            1 for exp in experiments if any(exp.get(target_name) is not None for target_name in target_names)
        )

        status = "completed" if completed_count == len(experiments) and len(experiments) > 0 else "pending"

        new_run = {
            "run_id": str(uuid4()),
            "run_number": run_number,
            "campaign_id": self.campaign_id,
            "status": status,
            "experiments": experiments,
            "targets": [{"name": target.name, "mode": target.mode} for target in campaign.targets],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "experiment_count": len(experiments),
            "completed_count": completed_count,
            "csv_file": str(self._get_run_csv_path(run_number)),
        }

        try:
            self._write_run_csv(new_run)
        except Exception as e:
            ErrorDialog.show_error("Error writing run CSV", str(e), parent=None)

        runs_data.append(new_run)
        self.save_runs(runs_data)

        return run_number

    def update_run_experiments(self, run_number: int, experiments: List[Dict[str, Any]]):
        """Update experiments data for a specific run."""
        runs_data = self.load_runs()

        for run in runs_data:
            if run.get("run_number") == run_number:
                run["experiments"] = experiments
                run["updated_at"] = datetime.now()

                target_names = [t["name"] for t in run.get("targets", [])]
                completed_count = sum(
                    1 for exp in experiments if any(exp.get(target_name) is not None for target_name in target_names)
                )
                run["completed_count"] = completed_count

                try:
                    self._write_run_csv(run)
                except Exception as e:
                    ErrorDialog.show_error("Error updating run CSV", str(e), parent=None)

                break

        self.save_runs(runs_data)

    def get_run(self, run_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific run by number."""
        runs_data = self.load_runs()

        for run in runs_data:
            if run.get("run_number") == run_number:
                return run

        return None

    def delete_run(self, run_number: int):
        """Delete a specific run."""
        runs_data = self.load_runs()
        runs_data = [run for run in runs_data if run.get("run_number") != run_number]

        for i, run in enumerate(runs_data, 1):
            run["run_number"] = i

        self.save_runs(runs_data)

    def get_run_count(self) -> int:
        """Get the total number of runs."""
        return len(self.load_runs())

    def has_previous_data(self) -> bool:
        """Check if there are any completed runs with target data."""
        runs_data = self.load_runs()

        for run in runs_data:
            if run.get("completed_count", 0) > 0:
                return True

        return False

    def _get_run_csv_path(self, run_number: int) -> Path:
        """Compute the CSV path for a given run number."""
        return self.runs_dir / f"run_{run_number}.csv"

    def _write_run_csv(self, run: Dict[str, Any]) -> None:
        """Write the run data to its CSV file."""
        experiments: List[Dict[str, Any]] = run.get("experiments", []) or []
        targets = run.get("targets", []) or []
        target_names = [t["name"] for t in targets]

        csv_path = Path(run.get("csv_file") or self._get_run_csv_path(run.get("run_number", 0)))
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine columns: parameters first (preserve insertion order from the first experiment), then targets
        param_columns: List[str] = []
        if experiments:
            first = experiments[0]
            param_columns = [k for k in first.keys() if k not in target_names]
            # Include any extra param keys appearing in later experiments
            seen = set(param_columns)
            for exp in experiments[1:]:
                for k in exp.keys():
                    if k not in seen and k not in target_names:
                        param_columns.append(k)
                        seen.add(k)

        # Ensure targets are all present and ordered by `targets`
        all_columns = param_columns + target_names

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(all_columns)
                for exp in experiments:
                    row = []
                    for col in all_columns:
                        v = exp.get(col, "")
                        row.append("" if v is None else v)
                    writer.writerow(row)
        except Exception as e:
            ErrorDialog.show_error("Error writing run CSV", str(e), parent=None)
            raise e
