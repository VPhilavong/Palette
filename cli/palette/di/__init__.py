"""
Dependency Injection container for Palette.
Provides IoC (Inversion of Control) for better testability and flexibility.
"""

from .container import Container, Injectable, Singleton, Transient
from .registry import ServiceRegistry
from .exceptions import (
    DIError,
    ServiceNotFoundError,
    CircularDependencyError,
    InvalidServiceError
)

__all__ = [
    # Container
    "Container",
    "Injectable",
    "Singleton",
    "Transient",
    
    # Registry
    "ServiceRegistry",
    
    # Exceptions
    "DIError",
    "ServiceNotFoundError", 
    "CircularDependencyError",
    "InvalidServiceError",
]