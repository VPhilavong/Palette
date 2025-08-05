"""
Lightweight dependency injection container implementation.
"""

import inspect
from typing import TypeVar, Type, Callable, Dict, Any, Optional, Union, Set
from functools import wraps
from enum import Enum

from .exceptions import ServiceNotFoundError, CircularDependencyError, InvalidServiceError


T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime options."""
    SINGLETON = "singleton"      # Single instance for entire application
    TRANSIENT = "transient"      # New instance every time
    SCOPED = "scoped"           # Single instance per scope (future enhancement)


class ServiceDescriptor:
    """Describes a registered service."""
    
    def __init__(
        self,
        service_type: Type,
        implementation: Union[Type, Callable, Any],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory: Optional[Callable] = None
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance = None  # For singleton storage


class Container:
    """
    Lightweight dependency injection container.
    Supports constructor injection with automatic resolution.
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._resolving: Set[Type] = set()  # Track resolution chain
    
    def register(
        self,
        service_type: Type[T],
        implementation: Union[Type[T], Callable[..., T], T] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory: Optional[Callable[..., T]] = None
    ) -> None:
        """
        Register a service in the container.
        
        Args:
            service_type: The interface/base type
            implementation: The concrete implementation (class, instance, or factory)
            lifetime: Service lifetime (singleton, transient, etc.)
            factory: Optional factory function for complex construction
        """
        if implementation is None:
            implementation = service_type
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            lifetime=lifetime,
            factory=factory
        )
        
        self._services[service_type] = descriptor
    
    def register_singleton(self, service_type: Type[T], implementation: Union[Type[T], T] = None) -> None:
        """Register a singleton service."""
        self.register(service_type, implementation, ServiceLifetime.SINGLETON)
    
    def register_transient(self, service_type: Type[T], implementation: Type[T] = None) -> None:
        """Register a transient service."""
        self.register(service_type, implementation, ServiceLifetime.TRANSIENT)
    
    def register_factory(self, service_type: Type[T], factory: Callable[..., T]) -> None:
        """Register a service with a factory function."""
        self.register(service_type, factory=factory)
    
    def resolve(self, service_type: Type[T]) -> T:
        """
        Resolve a service and its dependencies.
        
        Args:
            service_type: The type to resolve
            
        Returns:
            An instance of the requested type
            
        Raises:
            ServiceNotFoundError: If the service is not registered
            CircularDependencyError: If circular dependencies are detected
        """
        # Check for circular dependencies
        if service_type in self._resolving:
            chain = list(self._resolving) + [service_type]
            raise CircularDependencyError(chain)
        
        # Get service descriptor
        if service_type not in self._services:
            raise ServiceNotFoundError(service_type)
        
        descriptor = self._services[service_type]
        
        # Return existing singleton if available
        if descriptor.lifetime == ServiceLifetime.SINGLETON and descriptor.instance is not None:
            return descriptor.instance
        
        # Track resolution
        self._resolving.add(service_type)
        
        try:
            # Create instance
            instance = self._create_instance(descriptor)
            
            # Store singleton
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                descriptor.instance = instance
            
            return instance
            
        finally:
            self._resolving.remove(service_type)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create an instance of a service."""
        # Use factory if provided
        if descriptor.factory:
            return self._invoke_factory(descriptor.factory)
        
        implementation = descriptor.implementation
        
        # If already an instance, return it
        if not inspect.isclass(implementation):
            return implementation
        
        # Get constructor parameters
        init_signature = inspect.signature(implementation.__init__)
        dependencies = {}
        
        for param_name, param in init_signature.parameters.items():
            if param_name == 'self':
                continue
            
            # Get type annotation
            if param.annotation == inspect.Parameter.empty:
                continue
            
            param_type = param.annotation
            
            # Skip optional parameters if not registered
            if param.default != inspect.Parameter.empty and param_type not in self._services:
                continue
            
            # Resolve dependency
            try:
                dependencies[param_name] = self.resolve(param_type)
            except ServiceNotFoundError:
                if param.default == inspect.Parameter.empty:
                    raise
        
        # Create instance with resolved dependencies
        return implementation(**dependencies)
    
    def _invoke_factory(self, factory: Callable) -> Any:
        """Invoke a factory function with dependency injection."""
        signature = inspect.signature(factory)
        dependencies = {}
        
        for param_name, param in signature.parameters.items():
            if param.annotation == inspect.Parameter.empty:
                continue
            
            param_type = param.annotation
            
            # Skip optional parameters if not registered
            if param.default != inspect.Parameter.empty and param_type not in self._services:
                continue
            
            # Resolve dependency
            try:
                dependencies[param_name] = self.resolve(param_type)
            except ServiceNotFoundError:
                if param.default == inspect.Parameter.empty:
                    raise
        
        return factory(**dependencies)
    
    def clear(self) -> None:
        """Clear all service registrations."""
        self._services.clear()
        self._resolving.clear()
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services
    
    def get_all_registrations(self) -> Dict[Type, ServiceDescriptor]:
        """Get all service registrations."""
        return self._services.copy()


# Decorators for marking services
def Injectable(lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """Decorator to mark a class as injectable with specified lifetime."""
    def decorator(cls):
        cls._injectable_lifetime = lifetime
        return cls
    return decorator


def Singleton(cls):
    """Decorator to mark a class as a singleton service."""
    cls._injectable_lifetime = ServiceLifetime.SINGLETON
    return cls


def Transient(cls):
    """Decorator to mark a class as a transient service."""
    cls._injectable_lifetime = ServiceLifetime.TRANSIENT
    return cls