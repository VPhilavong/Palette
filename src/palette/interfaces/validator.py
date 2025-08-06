"""
Validator interface and related data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationType(Enum):
    """Types of validation checks."""
    TYPESCRIPT = "typescript"
    IMPORTS = "imports"
    STYLING = "styling"
    NAMING = "naming"
    STRUCTURE = "structure"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class ValidationIssue:
    """A single validation issue found."""
    type: ValidationType
    severity: ValidationSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of component validation."""
    issues: List[ValidationIssue] = field(default_factory=list)
    passed: bool = True
    score: float = 1.0  # Quality score from 0 to 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue."""
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.ERROR:
            self.passed = False
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get all error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get all warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)
    
    def calculate_score(self) -> float:
        """Calculate quality score based on issues."""
        if not self.issues:
            return 1.0
        
        # Deduct points for issues
        score = 1.0
        for issue in self.issues:
            if issue.severity == ValidationSeverity.ERROR:
                score -= 0.2
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 0.1
            elif issue.severity == ValidationSeverity.INFO:
                score -= 0.05
        
        return max(0.0, score)


class IValidator(ABC):
    """
    Abstract interface for component validators.
    Validates generated components for quality and correctness.
    """
    
    @abstractmethod
    def validate(self, content: str, file_path: str) -> ValidationResult:
        """
        Validate a component file.
        
        Args:
            content: File content to validate
            file_path: Path where the file will be saved
            
        Returns:
            ValidationResult with any issues found
        """
        pass
    
    @abstractmethod
    def validate_typescript(self, content: str, file_path: str) -> ValidationResult:
        """
        Validate TypeScript types and syntax.
        
        Args:
            content: TypeScript content
            file_path: File path for context
            
        Returns:
            ValidationResult for TypeScript validation
        """
        pass
    
    @abstractmethod
    def validate_imports(self, content: str, project_path: str) -> ValidationResult:
        """
        Validate that all imports are valid and available.
        
        Args:
            content: File content with imports
            project_path: Project root for resolving imports
            
        Returns:
            ValidationResult for import validation
        """
        pass
    
    @abstractmethod
    def validate_styling(self, content: str, styling_approach: str) -> ValidationResult:
        """
        Validate styling consistency.
        
        Args:
            content: Component content
            styling_approach: Expected styling approach (tailwind, css, etc.)
            
        Returns:
            ValidationResult for styling validation
        """
        pass
    
    @abstractmethod
    def supports_validation_type(self, validation_type: ValidationType) -> bool:
        """
        Check if the validator supports a specific validation type.
        
        Args:
            validation_type: Type of validation
            
        Returns:
            True if the validation type is supported
        """
        pass