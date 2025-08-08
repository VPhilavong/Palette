"""
Dependency Injection exceptions.
"""


class DIError(Exception):
    """Base exception for dependency injection errors."""
    pass


class ServiceNotFoundError(DIError):
    """Raised when a requested service is not registered."""
    def __init__(self, service_type: type, message: str = None):
        self.service_type = service_type
        if message is None:
            message = f"Service of type {service_type.__name__} not found in container"
        super().__init__(message)


class CircularDependencyError(DIError):
    """Raised when a circular dependency is detected."""
    def __init__(self, dependency_chain: list):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(t.__name__ for t in dependency_chain)
        message = f"Circular dependency detected: {chain_str}"
        super().__init__(message)


class InvalidServiceError(DIError):
    """Raised when a service registration is invalid."""
    pass