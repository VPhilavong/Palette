"""
Framework Pattern Library with modular knowledge system.

Provides centralized framework-specific patterns, best practices, and examples
with intelligent pattern matching and contextual recommendations.
"""

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path

from ..intelligence.framework_detector import Framework
from ..intelligence.styling_analyzer import StylingSystem
from ..errors.decorators import handle_errors


class PatternType(Enum):
    """Types of framework patterns."""
    COMPONENT = "component"
    HOOK = "hook"
    LAYOUT = "layout"
    ROUTING = "routing"
    STATE_MANAGEMENT = "state_management"
    STYLING = "styling"
    FORM = "form"
    DATA_FETCHING = "data_fetching"
    ANIMATION = "animation"
    UTILITY = "utility"


class PatternComplexity(Enum):
    """Pattern complexity levels."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class PatternExample:
    """Framework pattern example with context."""
    
    code: str
    description: str
    use_cases: List[str]
    dependencies: List[str] = field(default_factory=list)
    props_interface: Optional[str] = None
    styling_notes: Optional[str] = None
    accessibility_notes: Optional[str] = None
    performance_notes: Optional[str] = None


@dataclass
class FrameworkPattern:
    """Complete framework pattern definition."""
    
    id: str
    name: str
    pattern_type: PatternType
    complexity: PatternComplexity
    framework: Framework
    styling_system: Optional[StylingSystem] = None
    description: str = ""
    examples: List[PatternExample] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    version_requirements: Dict[str, str] = field(default_factory=dict)
    last_updated: Optional[str] = None


@dataclass
class PatternSearchQuery:
    """Pattern search and filtering criteria."""
    
    framework: Optional[Framework] = None
    styling_system: Optional[StylingSystem] = None
    pattern_types: Optional[List[PatternType]] = None
    complexity_levels: Optional[List[PatternComplexity]] = None
    tags: Optional[Set[str]] = None
    keywords: Optional[List[str]] = None
    use_case: Optional[str] = None


class FrameworkPatternLibrary:
    """
    Modular framework pattern library with intelligent pattern matching.
    
    Features:
    1. Hierarchical pattern organization by framework and styling system  
    2. Contextual pattern recommendations based on user request
    3. Pattern validation and quality scoring
    4. Dynamic pattern loading and caching
    5. Extensible pattern definitions via JSON/YAML
    """
    
    def __init__(self, patterns_dir: Optional[str] = None):
        self.patterns_dir = patterns_dir or self._get_default_patterns_dir()
        self.patterns: Dict[str, FrameworkPattern] = {}
        self.pattern_index: Dict[str, Set[str]] = {}  # Tag -> Pattern IDs
        self.framework_index: Dict[Framework, Set[str]] = {}  # Framework -> Pattern IDs
        self.styling_index: Dict[StylingSystem, Set[str]] = {}  # Styling -> Pattern IDs
        
        self._initialize_pattern_library()
    
    def _get_default_patterns_dir(self) -> str:
        """Get default patterns directory path."""
        current_dir = Path(__file__).parent
        return str(current_dir / "patterns")
    
    @handle_errors(fallback_return={}, reraise=False)
    def _initialize_pattern_library(self) -> None:
        """Initialize pattern library with built-in and external patterns."""
        
        # Load built-in patterns
        self._load_builtin_patterns()
        
        # Load external patterns if directory exists
        if os.path.exists(self.patterns_dir):
            self._load_external_patterns()
        
        # Build search indices
        self._build_search_indices()
        
        print(f"🔍 Loaded {len(self.patterns)} framework patterns across {len(self.framework_index)} frameworks")
    
    def _load_builtin_patterns(self) -> None:
        """Load built-in framework patterns."""
        
        # React + Chakra UI patterns
        self._add_react_chakra_patterns()
        
        # React + Tailwind patterns  
        self._add_react_tailwind_patterns()
        
        # Next.js patterns
        self._add_nextjs_patterns()
        
        # General React patterns
        self._add_react_patterns()
    
    def _add_react_chakra_patterns(self) -> None:
        """Add React + Chakra UI specific patterns."""
        
        # Button Component Pattern
        button_example = PatternExample(
            code='''import { Button, ButtonGroup } from '@chakra-ui/react'

interface ButtonProps {
  children: React.ReactNode
  variant?: 'solid' | 'outline' | 'ghost' | 'link'
  colorScheme?: string
  size?: 'xs' | 'sm' | 'md' | 'lg'
  isLoading?: boolean
  onClick?: () => void
}

const CustomButton: React.FC<ButtonProps> = ({
  children,
  variant = 'solid',
  colorScheme = 'blue',
  size = 'md',
  isLoading = false,
  onClick
}) => {
  return (
    <Button
      variant={variant}
      colorScheme={colorScheme}
      size={size}
      isLoading={isLoading}
      onClick={onClick}
    >
      {children}
    </Button>
  )
}''',
            description="Chakra UI button component with proper TypeScript typing",
            use_cases=["Form submissions", "Navigation actions", "Modal triggers"],
            dependencies=["@chakra-ui/react"],
            styling_notes="Uses Chakra's built-in color schemes and variants",
            accessibility_notes="Inherits Chakra's built-in accessibility features"
        )
        
        button_pattern = FrameworkPattern(
            id="react_chakra_button",
            name="Chakra UI Button Component",
            pattern_type=PatternType.COMPONENT,
            complexity=PatternComplexity.BASIC,
            framework=Framework.REACT,
            styling_system=StylingSystem.CHAKRA_UI,
            description="Standard button component using Chakra UI design system",
            examples=[button_example],
            best_practices=[
                "Use colorScheme prop instead of custom colors",
                "Leverage built-in size variants",
                "Include loading states for async actions",
                "Use ButtonGroup for related actions"
            ],
            common_mistakes=[
                "Adding custom CSS classes instead of using props",
                "Not using TypeScript interfaces",
                "Ignoring built-in accessibility features"
            ],
            tags={"button", "component", "chakra", "ui", "interactive"}
        )
        
        self.patterns[button_pattern.id] = button_pattern
        
        # Form Pattern
        form_example = PatternExample(
            code='''import {
  Box,
  Button,
  FormControl,
  FormLabel,
  FormErrorMessage,
  Input,
  Stack,
  useToast
} from '@chakra-ui/react'
import { useForm } from 'react-hook-form'

interface FormData {
  email: string
  password: string
}

const LoginForm: React.FC = () => {
  const toast = useToast()
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<FormData>()

  const onSubmit = async (data: FormData) => {
    try {
      // Handle form submission
      console.log(data)
      toast({
        title: 'Success',
        description: 'Login successful',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Login failed',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    }
  }

  return (
    <Box maxW="md" mx="auto" p={6}>
      <form onSubmit={handleSubmit(onSubmit)}>
        <Stack spacing={4}>
          <FormControl isInvalid={!!errors.email}>
            <FormLabel>Email</FormLabel>
            <Input
              type="email"
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}$/i,
                  message: 'Invalid email address'
                }
              })}
            />
            <FormErrorMessage>
              {errors.email && errors.email.message}
            </FormErrorMessage>
          </FormControl>

          <FormControl isInvalid={!!errors.password}>
            <FormLabel>Password</FormLabel>
            <Input
              type="password"
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 6,
                  message: 'Password must be at least 6 characters'
                }
              })}
            />
            <FormErrorMessage>
              {errors.password && errors.password.message}
            </FormErrorMessage>
          </FormControl>

          <Button
            type="submit"
            colorScheme="blue"
            isLoading={isSubmitting}
            loadingText="Signing in..."
          >
            Sign In
          </Button>
        </Stack>
      </form>
    </Box>
  )
}''',
            description="Complete form with validation using Chakra UI and React Hook Form",
            use_cases=["Login forms", "Registration forms", "Contact forms"],
            dependencies=["@chakra-ui/react", "react-hook-form"],
            styling_notes="Uses Chakra's form components with consistent spacing",
            accessibility_notes="Proper form labels and error announcements"
        )
        
        form_pattern = FrameworkPattern(
            id="react_chakra_form",
            name="Chakra UI Form with Validation",
            pattern_type=PatternType.FORM,
            complexity=PatternComplexity.INTERMEDIATE,
            framework=Framework.REACT,
            styling_system=StylingSystem.CHAKRA_UI,
            description="Form pattern with validation and error handling using Chakra UI",
            examples=[form_example],
            best_practices=[
                "Use react-hook-form for form state management",
                "Implement proper validation with helpful error messages",
                "Use Chakra's toast for user feedback",
                "Include loading states for submission"
            ],
            common_mistakes=[
                "Not handling form validation properly",
                "Missing error states in FormControl",
                "Not using semantic HTML form elements"
            ],
            tags={"form", "validation", "chakra", "react-hook-form", "accessibility"}
        )
        
        self.patterns[form_pattern.id] = form_pattern
    
    def _add_react_tailwind_patterns(self) -> None:
        """Add React + Tailwind CSS specific patterns."""
        
        # Card Component Pattern
        card_example = PatternExample(
            code='''interface CardProps {
  title: string
  description?: string
  children?: React.ReactNode
  className?: string
  onClick?: () => void
}

const Card: React.FC<CardProps> = ({
  title,
  description,
  children,
  className = "",
  onClick
}) => {
  return (
    <div
      className={`
        bg-white rounded-lg shadow-md border border-gray-200 
        hover:shadow-lg transition-shadow duration-200
        ${onClick ? 'cursor-pointer hover:border-gray-300' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {title}
        </h3>
        {description && (
          <p className="text-gray-600 text-sm mb-4">
            {description}
          </p>
        )}
        {children}
      </div>
    </div>
  )
}''',
            description="Reusable card component with Tailwind CSS styling",
            use_cases=["Product cards", "Content previews", "Dashboard widgets"],
            dependencies=["tailwindcss"],
            styling_notes="Uses Tailwind's utility classes for responsive design",
            accessibility_notes="Proper heading hierarchy and interactive states"
        )
        
        card_pattern = FrameworkPattern(
            id="react_tailwind_card",
            name="Tailwind CSS Card Component",
            pattern_type=PatternType.COMPONENT,
            complexity=PatternComplexity.BASIC,
            framework=Framework.REACT,
            styling_system=StylingSystem.TAILWIND,
            description="Card component built with Tailwind CSS utilities",
            examples=[card_example],
            best_practices=[
                "Use consistent spacing with Tailwind's spacing scale",
                "Implement hover states for interactive elements",
                "Use semantic color names from Tailwind palette",
                "Apply responsive design with Tailwind breakpoints"
            ],
            common_mistakes=[
                "Overusing arbitrary values instead of design tokens",
                "Not considering dark mode variants",
                "Missing focus states for keyboard navigation"
            ],
            tags={"card", "tailwind", "component", "responsive"}
        )
        
        self.patterns[card_pattern.id] = card_pattern
    
    def _add_nextjs_patterns(self) -> None:
        """Add Next.js specific patterns."""
        
        # API Route Pattern
        api_example = PatternExample(
            code='''// pages/api/users/[id].ts
import type { NextApiRequest, NextApiResponse } from 'next'

interface User {
  id: string
  name: string
  email: string
}

interface ApiError {
  error: string
  message?: string
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<User | User[] | ApiError>
) {
  const { id } = req.query

  // Validate request method
  if (!['GET', 'PUT', 'DELETE'].includes(req.method || '')) {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    switch (req.method) {
      case 'GET':
        if (id) {
          // Get single user
          const user = await getUserById(id as string)
          if (!user) {
            return res.status(404).json({ error: 'User not found' })
          }
          return res.status(200).json(user)
        } else {
          // Get all users
          const users = await getAllUsers()
          return res.status(200).json(users)
        }

      case 'PUT':
        const updatedUser = await updateUser(id as string, req.body)
        return res.status(200).json(updatedUser)

      case 'DELETE':
        await deleteUser(id as string)
        return res.status(204).end()

      default:
        return res.status(405).json({ error: 'Method not allowed' })
    }
  } catch (error) {
    console.error('API Error:', error)
    return res.status(500).json({ 
      error: 'Internal server error',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    })
  }
}

// Helper functions (implement based on your data layer)
async function getUserById(id: string): Promise<User | null> {
  // Implementation
  return null
}

async function getAllUsers(): Promise<User[]> {
  // Implementation
  return []
}

async function updateUser(id: string, data: Partial<User>): Promise<User> {
  // Implementation
  throw new Error('Not implemented')
}

async function deleteUser(id: string): Promise<void> {
  // Implementation
}''',
            description="RESTful API route with proper error handling and TypeScript",
            use_cases=["CRUD operations", "User management", "Data APIs"],
            dependencies=["next"],
            performance_notes="Consider implementing caching and rate limiting"
        )
        
        api_pattern = FrameworkPattern(
            id="nextjs_api_route",
            name="Next.js API Route",
            pattern_type=PatternType.ROUTING,
            complexity=PatternComplexity.INTERMEDIATE,
            framework=Framework.NEXT_JS,
            description="RESTful API route pattern with error handling",
            examples=[api_example],
            best_practices=[
                "Use proper HTTP status codes",
                "Implement comprehensive error handling",
                "Validate request methods and data",
                "Use TypeScript for type safety",
                "Handle edge cases gracefully"
            ],
            common_mistakes=[
                "Not validating request methods",
                "Exposing sensitive error details in production",
                "Missing error handling for database operations",
                "Not using proper HTTP status codes"
            ],
            tags={"api", "nextjs", "routing", "typescript", "rest"}
        )
        
        self.patterns[api_pattern.id] = api_pattern
    
    def _add_react_patterns(self) -> None:
        """Add general React patterns."""
        
        # Custom Hook Pattern
        hook_example = PatternExample(
            code='''import { useState, useEffect, useCallback } from 'react'

interface UseFetchResult<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => void
}

interface UseFetchOptions {
  skip?: boolean
  onSuccess?: (data: any) => void
  onError?: (error: string) => void
}

function useFetch<T>(
  url: string, 
  options: UseFetchOptions = {}
): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState<boolean>(!options.skip)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (options.skip) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      setData(result)
      
      if (options.onSuccess) {
        options.onSuccess(result)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      
      if (options.onError) {
        options.onError(errorMessage)  
      }
    } finally {
      setLoading(false)
    }
  }, [url, options.skip, options.onSuccess, options.onError])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const refetch = useCallback(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch }
}

// Usage example:
const UserProfile: React.FC<{ userId: string }> = ({ userId }) => {
  const { data: user, loading, error, refetch } = useFetch<User>(
    `/api/users/${userId}`,
    {
      onSuccess: (user) => console.log('User loaded:', user.name),
      onError: (error) => console.error('Failed to load user:', error)
    }
  )

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>
  if (!user) return <div>No user found</div>

  return (
    <div>
      <h1>{user.name}</h1>
      <button onClick={refetch}>Refresh</button>
    </div>
  )
}''',
            description="Custom hook for data fetching with error handling",
            use_cases=["API data fetching", "Async operations", "Data management"],
            dependencies=["react"],
            performance_notes="Uses useCallback to prevent unnecessary re-renders"
        )
        
        hook_pattern = FrameworkPattern(
            id="react_fetch_hook",
            name="Custom Fetch Hook",
            pattern_type=PatternType.HOOK,
            complexity=PatternComplexity.INTERMEDIATE,
            framework=Framework.REACT,
            description="Reusable custom hook for data fetching with TypeScript",
            examples=[hook_example],
            best_practices=[
                "Use TypeScript generics for type safety",
                "Implement proper error handling",
                "Provide loading and error states",
                "Use useCallback to optimize performance",
                "Support conditional fetching with skip option"
            ],
            common_mistakes=[
                "Not handling loading and error states",
                "Missing dependency arrays in useEffect/useCallback",
                "Not cleaning up on component unmount",
                "Over-fetching data unnecessarily"
            ],
            tags={"hook", "fetch", "async", "typescript", "react"}
        )
        
        self.patterns[hook_pattern.id] = hook_pattern
    
    def _load_external_patterns(self) -> None:
        """Load patterns from external JSON/YAML files."""
        patterns_path = Path(self.patterns_dir)
        
        for pattern_file in patterns_path.glob("*.json"):
            try:
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    pattern_data = json.load(f)
                    pattern = self._deserialize_pattern(pattern_data)
                    if pattern:
                        self.patterns[pattern.id] = pattern
            except Exception as e:
                print(f"⚠️ Failed to load pattern from {pattern_file}: {e}")
    
    def _deserialize_pattern(self, data: Dict[str, Any]) -> Optional[FrameworkPattern]:
        """Convert JSON data to FrameworkPattern object."""
        try:
            examples = [
                PatternExample(**example) for example in data.get('examples', [])
            ]
            
            return FrameworkPattern(
                id=data['id'],
                name=data['name'],
                pattern_type=PatternType(data['pattern_type']),
                complexity=PatternComplexity(data['complexity']),
                framework=Framework(data['framework']),
                styling_system=StylingSystem(data['styling_system']) if data.get('styling_system') else None,
                description=data.get('description', ''),
                examples=examples,
                best_practices=data.get('best_practices', []),
                common_mistakes=data.get('common_mistakes', []),
                related_patterns=data.get('related_patterns', []),
                tags=set(data.get('tags', [])),
                version_requirements=data.get('version_requirements', {}),
                last_updated=data.get('last_updated')
            )
        except Exception as e:
            print(f"⚠️ Failed to deserialize pattern: {e}")
            return None
    
    def _build_search_indices(self) -> None:
        """Build search indices for efficient pattern lookup."""
        
        for pattern_id, pattern in self.patterns.items():
            # Framework index
            if pattern.framework not in self.framework_index:
                self.framework_index[pattern.framework] = set()
            self.framework_index[pattern.framework].add(pattern_id)
            
            # Styling system index
            if pattern.styling_system:
                if pattern.styling_system not in self.styling_index:
                    self.styling_index[pattern.styling_system] = set()
                self.styling_index[pattern.styling_system].add(pattern_id)
            
            # Tag index
            for tag in pattern.tags:
                if tag not in self.pattern_index:
                    self.pattern_index[tag] = set()
                self.pattern_index[tag].add(pattern_id)
    
    def search_patterns(self, query: PatternSearchQuery) -> List[FrameworkPattern]:
        """Search patterns based on query criteria."""
        
        matching_patterns = set(self.patterns.keys())
        
        # Filter by framework
        if query.framework:
            framework_patterns = self.framework_index.get(query.framework, set())
            matching_patterns = matching_patterns.intersection(framework_patterns)
        
        # Filter by styling system
        if query.styling_system:
            styling_patterns = self.styling_index.get(query.styling_system, set())
            matching_patterns = matching_patterns.intersection(styling_patterns)
        
        # Filter by pattern types
        if query.pattern_types:
            type_patterns = {
                pid for pid, pattern in self.patterns.items()
                if pattern.pattern_type in query.pattern_types
            }
            matching_patterns = matching_patterns.intersection(type_patterns)
        
        # Filter by complexity levels
        if query.complexity_levels:
            complexity_patterns = {
                pid for pid, pattern in self.patterns.items()
                if pattern.complexity in query.complexity_levels
            }
            matching_patterns = matching_patterns.intersection(complexity_patterns)
        
        # Filter by tags
        if query.tags:
            tag_patterns = set()
            for tag in query.tags:
                tag_patterns.update(self.pattern_index.get(tag, set()))
            matching_patterns = matching_patterns.intersection(tag_patterns)
        
        # Filter by keywords
        if query.keywords:
            keyword_patterns = set()
            for pattern_id, pattern in self.patterns.items():
                pattern_text = f"{pattern.name} {pattern.description} {' '.join(pattern.tags)}"
                if any(keyword.lower() in pattern_text.lower() for keyword in query.keywords):
                    keyword_patterns.add(pattern_id)
            matching_patterns = matching_patterns.intersection(keyword_patterns)
        
        # Convert to pattern objects and sort by relevance
        results = [self.patterns[pid] for pid in matching_patterns]
        return self._sort_patterns_by_relevance(results, query)
    
    def _sort_patterns_by_relevance(
        self, 
        patterns: List[FrameworkPattern], 
        query: PatternSearchQuery
    ) -> List[FrameworkPattern]:
        """Sort patterns by relevance to the query."""
        
        def relevance_score(pattern: FrameworkPattern) -> float:
            score = 0.0
            
            # Framework match bonus
            if query.framework and pattern.framework == query.framework:
                score += 2.0
            
            # Styling system match bonus
            if query.styling_system and pattern.styling_system == query.styling_system:
                score += 1.5
            
            # Pattern type match bonus
            if query.pattern_types and pattern.pattern_type in query.pattern_types:
                score += 1.0
            
            # Tag match bonus
            if query.tags:
                tag_matches = len(query.tags.intersection(pattern.tags))
                score += tag_matches * 0.5
            
            # Keyword match bonus
            if query.keywords:
                pattern_text = f"{pattern.name} {pattern.description}".lower()
                keyword_matches = sum(
                    1 for keyword in query.keywords 
                    if keyword.lower() in pattern_text
                )
                score += keyword_matches * 0.3
            
            # Complexity preference (intermediate patterns slightly favored)
            if pattern.complexity == PatternComplexity.INTERMEDIATE:
                score += 0.1
            
            return score
        
        return sorted(patterns, key=relevance_score, reverse=True)
    
    def get_recommended_patterns(
        self,
        user_request: str,
        framework: Framework,
        styling_system: Optional[StylingSystem] = None,
        max_results: int = 5
    ) -> List[FrameworkPattern]:
        """Get pattern recommendations based on user request context."""
        
        # Extract keywords and intent from user request
        keywords = self._extract_keywords_from_request(user_request)
        pattern_types = self._infer_pattern_types_from_request(user_request)
        
        # Build search query
        query = PatternSearchQuery(
            framework=framework,
            styling_system=styling_system,
            pattern_types=pattern_types,
            keywords=keywords
        )
        
        # Search and return top results
        results = self.search_patterns(query)
        return results[:max_results]
    
    def _extract_keywords_from_request(self, request: str) -> List[str]:
        """Extract relevant keywords from user request."""
        # Simple keyword extraction - could be enhanced with NLP
        keywords = []
        
        # Component-related keywords
        component_keywords = {
            'button', 'card', 'form', 'input', 'modal', 'dropdown', 'navigation',
            'header', 'footer', 'sidebar', 'table', 'list', 'grid', 'layout'
        }
        
        # Feature-related keywords
        feature_keywords = {
            'validation', 'authentication', 'routing', 'api', 'fetch', 'state',
            'hook', 'animation', 'responsive', 'accessibility', 'loading'
        }
        
        request_lower = request.lower()
        all_keywords = component_keywords.union(feature_keywords)
        
        for keyword in all_keywords:
            if keyword in request_lower:
                keywords.append(keyword)
        
        return keywords
    
    def _infer_pattern_types_from_request(self, request: str) -> List[PatternType]:
        """Infer pattern types from user request."""
        request_lower = request.lower()
        pattern_types = []
        
        # Pattern type inference rules
        if any(word in request_lower for word in ['button', 'card', 'input', 'modal']):
            pattern_types.append(PatternType.COMPONENT)
        
        if any(word in request_lower for word in ['form', 'validation', 'submit']):
            pattern_types.append(PatternType.FORM)
            
        if any(word in request_lower for word in ['hook', 'custom hook', 'use']):
            pattern_types.append(PatternType.HOOK)
            
        if any(word in request_lower for word in ['layout', 'grid', 'responsive']):
            pattern_types.append(PatternType.LAYOUT)
            
        if any(word in request_lower for word in ['api', 'fetch', 'data']):
            pattern_types.append(PatternType.DATA_FETCHING)
        
        if any(word in request_lower for word in ['route', 'navigation', 'page']):
            pattern_types.append(PatternType.ROUTING)
        
        return pattern_types if pattern_types else [PatternType.COMPONENT]
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[FrameworkPattern]:
        """Get a specific pattern by ID."""
        return self.patterns.get(pattern_id)
    
    def get_patterns_by_framework(self, framework: Framework) -> List[FrameworkPattern]:
        """Get all patterns for a specific framework."""
        pattern_ids = self.framework_index.get(framework, set())
        return [self.patterns[pid] for pid in pattern_ids]
    
    def get_patterns_by_styling_system(self, styling_system: StylingSystem) -> List[FrameworkPattern]:
        """Get all patterns for a specific styling system."""
        pattern_ids = self.styling_index.get(styling_system, set())
        return [self.patterns[pid] for pid in pattern_ids]
    
    def add_pattern(self, pattern: FrameworkPattern) -> None:
        """Add a new pattern to the library."""
        self.patterns[pattern.id] = pattern
        self._update_indices_for_pattern(pattern)
    
    def _update_indices_for_pattern(self, pattern: FrameworkPattern) -> None:
        """Update search indices for a new pattern."""
        # Update framework index
        if pattern.framework not in self.framework_index:
            self.framework_index[pattern.framework] = set()
        self.framework_index[pattern.framework].add(pattern.id)
        
        # Update styling system index
        if pattern.styling_system:
            if pattern.styling_system not in self.styling_index:
                self.styling_index[pattern.styling_system] = set()
            self.styling_index[pattern.styling_system].add(pattern.id)
        
        # Update tag index
        for tag in pattern.tags:
            if tag not in self.pattern_index:
                self.pattern_index[tag] = set()
            self.pattern_index[tag].add(pattern.id)
    
    def export_pattern(self, pattern_id: str, output_path: str) -> bool:
        """Export a pattern to JSON file."""
        pattern = self.patterns.get(pattern_id)
        if not pattern:
            return False
        
        try:
            pattern_data = self._serialize_pattern(pattern)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(pattern_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️ Failed to export pattern {pattern_id}: {e}")
            return False
    
    def _serialize_pattern(self, pattern: FrameworkPattern) -> Dict[str, Any]:
        """Convert FrameworkPattern to JSON-serializable dict."""
        return {
            'id': pattern.id,
            'name': pattern.name,
            'pattern_type': pattern.pattern_type.value,
            'complexity': pattern.complexity.value,
            'framework': pattern.framework.value,
            'styling_system': pattern.styling_system.value if pattern.styling_system else None,
            'description': pattern.description,
            'examples': [
                {
                    'code': example.code,
                    'description': example.description,
                    'use_cases': example.use_cases,
                    'dependencies': example.dependencies,
                    'props_interface': example.props_interface,
                    'styling_notes': example.styling_notes,
                    'accessibility_notes': example.accessibility_notes,
                    'performance_notes': example.performance_notes
                }
                for example in pattern.examples
            ],
            'best_practices': pattern.best_practices,
            'common_mistakes': pattern.common_mistakes,
            'related_patterns': pattern.related_patterns,
            'tags': list(pattern.tags),
            'version_requirements': pattern.version_requirements,
            'last_updated': pattern.last_updated
        }
    
    def get_library_stats(self) -> Dict[str, Any]:
        """Get statistics about the pattern library."""
        
        framework_counts = {
            framework.value: len(pattern_ids) 
            for framework, pattern_ids in self.framework_index.items()
        }
        
        styling_counts = {
            styling.value: len(pattern_ids)
            for styling, pattern_ids in self.styling_index.items()
        }
        
        type_counts = {}
        complexity_counts = {}
        
        for pattern in self.patterns.values():
            # Count by pattern type
            type_name = pattern.pattern_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            # Count by complexity
            complexity_name = pattern.complexity.value
            complexity_counts[complexity_name] = complexity_counts.get(complexity_name, 0) + 1
        
        return {
            'total_patterns': len(self.patterns),
            'frameworks': framework_counts,
            'styling_systems': styling_counts,
            'pattern_types': type_counts,
            'complexity_levels': complexity_counts,
            'total_tags': len(self.pattern_index)
        }