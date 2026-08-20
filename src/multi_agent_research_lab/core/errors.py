"""Domain-specific errors."""


class LabError(Exception):
    """Base error for the lab package."""


class StudentTodoError(LabError):
    """Kept for starter compatibility; completed code should not raise this."""


class AgentExecutionError(LabError):
    """Raised when an agent fails after bounded retries/fallbacks."""


class ValidationError(LabError):
    """Raised when state or output validation fails."""
