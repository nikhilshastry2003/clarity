class TaskContextValidationError(Exception):
    """Raised when task context validation fails."""
    pass


class TaskContext:
    """Structured task context model produced by an LLM."""

    REQUIRED_KEYS = {"task", "owner", "explicit_goals", "unknowns", "constraints", "assumptions"}
    SCHEMA = {
        "task": str,
        "owner": str,
        "explicit_goals": list,
        "unknowns": list,
        "constraints": list,
        "assumptions": list,
    }

    def __init__(
        self,
        task: str,
        owner: str,
        explicit_goals: list,
        unknowns: list,
        constraints: list,
        assumptions: list,
    ):
        self.task = task
        self.owner = owner
        self.explicit_goals = explicit_goals
        self.unknowns = unknowns
        self.constraints = constraints
        self.assumptions = assumptions

    @classmethod
    def from_dict(cls, data: dict) -> "TaskContext":
        """Create a TaskContext from a dictionary with full validation."""
        cls._validate(data)
        return cls(
            task=data["task"],
            owner=data["owner"],
            explicit_goals=data["explicit_goals"],
            unknowns=data["unknowns"],
            constraints=data["constraints"],
            assumptions=data["assumptions"],
        )

    @classmethod
    def _validate(cls, data: dict) -> None:
        """Validate the input data against the schema."""
        if not isinstance(data, dict):
            raise TaskContextValidationError(
                f"Expected a dictionary, got {type(data).__name__}"
            )

        provided_keys = set(data.keys())

        missing_keys = cls.REQUIRED_KEYS - provided_keys
        if missing_keys:
            raise TaskContextValidationError(
                f"Missing required keys: {', '.join(sorted(missing_keys))}"
            )

        unexpected_keys = provided_keys - cls.REQUIRED_KEYS
        if unexpected_keys:
            raise TaskContextValidationError(
                f"Unexpected keys: {', '.join(sorted(unexpected_keys))}"
            )

        for key, expected_type in cls.SCHEMA.items():
            value = data[key]
            if not isinstance(value, expected_type):
                raise TaskContextValidationError(
                    f"Invalid type for '{key}': expected {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

        list_fields = ["explicit_goals", "unknowns", "constraints", "assumptions"]
        for field in list_fields:
            for i, item in enumerate(data[field]):
                if not isinstance(item, str):
                    raise TaskContextValidationError(
                        f"Invalid type for '{field}[{i}]': expected str, "
                        f"got {type(item).__name__}"
                    )

    def to_dict(self) -> dict:
        """Convert the TaskContext to a dictionary."""
        return {
            "task": self.task,
            "owner": self.owner,
            "explicit_goals": self.explicit_goals,
            "unknowns": self.unknowns,
            "constraints": self.constraints,
            "assumptions": self.assumptions,
        }

    def __repr__(self) -> str:
        return (
            f"TaskContext(task={self.task!r}, owner={self.owner!r}, "
            f"explicit_goals={self.explicit_goals!r}, unknowns={self.unknowns!r}, "
            f"constraints={self.constraints!r}, assumptions={self.assumptions!r})"
        )
