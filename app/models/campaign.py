"""
Data models for the campaign.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.models.enums import BOAcquisitionFunction, TargetTransformation
from app.models.parameters import ParameterSerializer
from app.models.parameters.base import BaseParameter


@dataclass
class Target:
    """Data model for the campaign target."""

    name: str = ""
    mode: str = "Max"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    transformation: Optional[str] = TargetTransformation.NONE.value
    weight: Optional[float] = None


@dataclass
class Campaign:
    """Data model for a campaign."""

    name: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    targets: List[Target] = field(default_factory=list)
    parameters: List[BaseParameter] = field(default_factory=list)
    initial_dataset: List[Dict[str, Any]] = field(default_factory=list)
    acquisition_function: str = BOAcquisitionFunction.QLOGEI.value
    surrogate_model: str = "GaussianProcess"
    workspace_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)

    def reset(self):
        """Reset all campaign data to its initial state."""

        self.name = ""
        self.description = ""
        self.targets = []
        self.parameters.clear()
        self.initial_dataset.clear()
        self.acquisition_function = BOAcquisitionFunction.QLOGEI.value
        self.surrogate_model = "GaussianProcess"
        self.workspace_path = None 
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.accessed_at = datetime.now()
        self.id = str(uuid4())

    def get_parameter_data(self) -> List[Dict[str, Any]]:
        """Serialize parameters to a list of dictionaries."""
        serializer = ParameterSerializer()
        return serializer.serialize_parameters(self.parameters)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Campaign":
        """Create a Campaign instance from a dictionary."""
        serializer = ParameterSerializer()
        parameters = serializer.deserialize_parameters(data.get("parameters", []))

        targets_data = data.get("targets", [])
        targets = [
            Target(
                name=target.get("name", ""),
                mode=target.get("mode", "Max"),
                min_value=target.get("min_value"),
                max_value=target.get("max_value"),
                transformation=target.get("transformation"),
                weight=target.get("weight"),
            )
            for target in targets_data
        ]

        created_at = data.get("created_at", datetime.now())
        updated_at = data.get("updated_at", datetime.now())
        # Access at is a new field. For consistency, let's read updated_at of it's not there.
        # We'll need to delete it later.
        accessed_at = data.get("accessed_at", updated_at)

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        if isinstance(accessed_at, str):
            accessed_at = datetime.fromisoformat(accessed_at)

        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            targets=targets,
            parameters=parameters,
            initial_dataset=data.get("initial_dataset", []),
            acquisition_function=data.get("acquisition_function", BOAcquisitionFunction.QLOGEI.value),
            surrogate_model=data.get("surrogate_model", "GaussianProcess"),
            workspace_path=data.get("workspace_path"),
            created_at=created_at,
            updated_at=updated_at,
            accessed_at=accessed_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Campaign instance to a dictionary."""
        serializer = ParameterSerializer()
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "targets": [
                {
                    "name": target.name,
                    "mode": target.mode,
                    "min_value": target.min_value,
                    "max_value": target.max_value,
                    "transformation": target.transformation,
                    "weight": target.weight,
                }
                for target in self.targets
            ],
            "parameters": serializer.serialize_parameters(self.parameters),
            "initial_dataset": self.initial_dataset,
            "acquisition_function": self.acquisition_function,
            "surrogate_model": self.surrogate_model,
            "workspace_path": self.workspace_path,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "accessed_at": self.accessed_at.isoformat() if isinstance(self.accessed_at, datetime) else self.accessed_at,
        }
