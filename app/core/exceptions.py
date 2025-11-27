"""Custom exception classes for the application."""


class BaseballLeagueException(Exception):
    """Base exception for the application."""
    pass


class NotFoundError(BaseballLeagueException):
    """Raised when a resource is not found."""
    pass


class ValidationError(BaseballLeagueException):
    """Raised when validation fails."""
    pass


class OpenAIError(BaseballLeagueException):
    """Raised when OpenAI API calls fail."""
    pass

