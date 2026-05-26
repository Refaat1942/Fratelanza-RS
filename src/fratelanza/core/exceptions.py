"""Application-specific exception hierarchy."""


class FratelanzaError(Exception):
    """Base exception for expected application failures."""


class ConfigurationError(FratelanzaError):
    """Raised when runtime configuration is invalid."""


class DatabaseConnectionError(FratelanzaError):
    """Raised when SQL Server cannot be reached or initialized."""


class AuthenticationError(FratelanzaError):
    """Raised when user credentials cannot be authenticated."""


class PermissionDeniedError(FratelanzaError):
    """Raised when a user does not have a required permission."""


class RepositoryError(FratelanzaError):
    """Raised for expected data-access errors."""
