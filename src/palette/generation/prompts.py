# Complete UI/UX AI Copilot System
# This is a comprehensive system for prompt-to-production UI/UX code generation

from typing import Dict, List, Tuple, Optional, Union
import re
from dataclasses import dataclass
from enum import Enum


class FrameworkType(Enum):
    """Supported frontend frameworks"""
    REACT = "react"
    NEXTJS = "next.js"
    REMIX = "remix"
    VITE_REACT = "vite"


class StylingLibrary(Enum):
    """Supported styling libraries"""
    TAILWIND = "tailwind"
    STYLED_COMPONENTS = "styled-components"
    EMOTION = "emotion"
    CSS_MODULES = "css-modules"
    SASS = "sass"
    VANILLA_CSS = "css"
    STITCHES = "stitches"
    PANDA_CSS = "panda-css"
    UNO_CSS = "uno-css"


class ComponentLibrary(Enum):
    """Supported component libraries"""
    SHADCN_UI = "shadcn/ui"
    MATERIAL_UI = "material-ui"
    CHAKRA_UI = "chakra-ui"
    ANT_DESIGN = "ant-design"
    HEADLESS_UI = "headless-ui"
    RADIX_UI = "radix-ui"
    MANTINE = "mantine"
    NONE = "none"


class GenerationType(Enum):
    """Types of generation modes"""
    SINGLE_COMPONENT = "single"
    MULTI_FILE_COMPONENT = "multi"
    PAGE = "page"
    FULL_FEATURE = "feature"
    EDIT_FILE = "edit"
    UTILS = "utils"
    HOOKS = "hooks"
    CONTEXT = "context"
    STORE = "store"


@dataclass
class GenerationRequest:
    """Represents a UI/UX generation request"""
    prompt: str
    generation_type: GenerationType
    framework: FrameworkType
    styling: StylingLibrary
    component_library: ComponentLibrary
    target_files: Optional[List[str]] = None
    edit_mode: Optional[str] = None  # 'add', 'modify', 'refactor', 'enhance'
    include_tests: bool = True
    include_storybook: bool = False
    responsive: bool = True
    accessibility_level: str = "aa"  # 'a', 'aa', 'aaa'


class UIUXCopilotPromptBuilder:
    """Advanced prompt builder for comprehensive UI/UX code generation"""
    
    def __init__(self):
        self.styling_patterns = self._load_styling_patterns()
        self.framework_patterns = self._load_framework_patterns()
        self.utility_patterns = self._load_utility_patterns()
    
    def build_generation_prompt(self, request: GenerationRequest, context: Dict) -> str:
        """Build a comprehensive prompt based on the generation request"""
        
        # Extract design tokens and project info
        design_tokens = context.get("design_tokens", {})
        project_structure = context.get("project_structure", {})
        available_imports = context.get("available_imports", {})
        ast_analysis = context.get("ast_analysis", {})
        
        # Build the base system prompt
        base_prompt = self._build_base_prompt(request, design_tokens)
        
        # Add framework-specific instructions
        framework_prompt = self._build_framework_instructions(request.framework, project_structure)
        
        # Add styling-specific instructions
        styling_prompt = self._build_styling_instructions(request.styling, design_tokens)
        
        # Add component library instructions
        library_prompt = self._build_library_instructions(request.component_library, available_imports)
        
        # Add generation type specific instructions
        generation_prompt = self._build_generation_instructions(request.generation_type, request)
        
        # Add utility instructions
        utility_prompt = self._build_utility_instructions(request)
        
        # Combine all prompts
        full_prompt = f"""{base_prompt}

{framework_prompt}

{styling_prompt}

{library_prompt}

{generation_prompt}

{utility_prompt}

PROJECT CONTEXT:
{self._format_project_context(context, ast_analysis)}

USER REQUEST: {request.prompt}

CRITICAL REQUIREMENTS:
1. Generate ONLY production-ready code that needs ZERO manual fixes
2. Follow ALL project conventions and patterns detected
3. Include ALL necessary imports and type definitions
4. Ensure full compatibility with the project's tech stack
5. Generate complete files, not fragments

OUTPUT RULES:
- For single files: Return complete, runnable code
- For multiple files: Use the === FILE: path/to/file.ext === format
- Include all necessary configuration updates
- Provide clear file paths following project structure"""
        
        return full_prompt
    
    def _build_base_prompt(self, request: GenerationRequest, design_tokens: Dict) -> str:
        """Build the base system prompt"""
        return f"""You are an expert UI/UX AI Copilot that generates production-ready frontend code.

CORE CAPABILITIES:
- Generate complete, working components with ZERO manual fixes needed
- Support multiple frameworks: React, Next.js, Remix, Vite
- Support multiple styling solutions: Tailwind, Styled Components, Emotion, CSS Modules, etc.
- Create accessible, responsive, performant UI components
- Follow established design patterns and best practices
- Generate multi-file architectures when appropriate

CRITICAL: PROJECT DESIGN SYSTEM
{self._format_design_tokens_enhanced(design_tokens)}

DESIGN TOKEN USAGE RULES:
- MUST use project-specific colors over generic ones (e.g., use 'blue' or 'emerald' instead of 'gray')
- MUST incorporate detected design tokens in every component
- For gradients, use project colors (e.g., 'from-blue-500 to-emerald-500')
- Maintain consistency with the existing design system

QUALITY STANDARDS:
- TypeScript by default with comprehensive type safety
- {request.accessibility_level.upper()}-level WCAG accessibility compliance
- Mobile-first responsive design
- Performance optimized (lazy loading, memoization where appropriate)
- SEO-friendly markup when applicable
- Comprehensive error handling
- Loading and empty states"""
    
    def _build_framework_instructions(self, framework: FrameworkType, structure: Dict) -> str:
        """Build framework-specific instructions"""
        
        instructions = {
            FrameworkType.NEXTJS: """
NEXT.JS 14+ APP ROUTER REQUIREMENTS:
- Use App Router patterns (not Pages Router)
- Server Components by default, 'use client' only when needed
- Proper data fetching patterns (server-side when possible)
- Dynamic imports for code splitting
- Image optimization with next/image
- Font optimization with next/font
- Metadata API for SEO
- Proper error.tsx and loading.tsx patterns
- Parallel routes and intercepting routes when beneficial

File Structure:
- app/ directory for pages and layouts
- components/ for reusable components
- lib/ or utils/ for utilities
- hooks/ for custom hooks
- types/ for TypeScript definitions""",
            
            FrameworkType.REACT: """
REACT 18+ REQUIREMENTS:
- Use latest React features (Suspense, concurrent features)
- Proper hook usage and rules
- Component composition patterns
- Error boundaries for error handling
- React.memo for performance where beneficial
- useCallback/useMemo for expensive operations
- Portals for modals/tooltips
- Context API for state management when needed""",
            
            FrameworkType.REMIX: """
REMIX REQUIREMENTS:
- Use Remix data loading patterns (loader/action)
- Proper form handling with Form component
- Progressive enhancement approach
- Nested routing patterns
- Error and catch boundaries
- Meta exports for SEO
- Optimistic UI patterns
- Resource routes when needed""",
            
            FrameworkType.VITE_REACT: """
VITE + REACT REQUIREMENTS:
- Fast HMR compatible code
- Proper module imports
- Environment variable handling
- Code splitting with React.lazy
- Vite-specific optimizations
- CSS modules or PostCSS setup
- Proper build optimization patterns"""
        }
        
        return f"""FRAMEWORK: {framework.value.upper()}
{instructions.get(framework, "Use modern React patterns and best practices")}

Project Structure Detected:
- Components: {structure.get('components_dir', 'src/components')}
- Pages/Routes: {structure.get('pages_dir', 'src/pages')}
- Utilities: {structure.get('utils_dir', 'src/utils')}"""
    
    def _build_styling_instructions(self, styling: StylingLibrary, tokens: Dict) -> str:
        """Build styling-specific instructions"""
        
        instructions = {
            StylingLibrary.TAILWIND: f"""
TAILWIND CSS REQUIREMENTS:
- Use utility-first approach
- Follow project's color palette: {', '.join(tokens.get('colors', [])[:5])}
- Use spacing scale: {', '.join(tokens.get('spacing', [])[:5])}
- Typography scale: {', '.join(tokens.get('typography', [])[:5])}
- Responsive modifiers: sm:, md:, lg:, xl:, 2xl:
- Dark mode with dark: modifier if enabled
- Custom utilities via @apply sparingly
- Component variants with cn() or clsx()
- Avoid arbitrary values when possible""",
            
            StylingLibrary.STYLED_COMPONENTS: """
STYLED COMPONENTS REQUIREMENTS:
- Use styled-components v5+ patterns
- Theme provider integration
- Proper TypeScript types for theme
- Use css prop when beneficial
- Transient props ($prop) for non-DOM props
- Global styles setup
- Server-side rendering compatibility
- Animation with keyframes helper""",
            
            StylingLibrary.EMOTION: """
EMOTION REQUIREMENTS:
- Use @emotion/react and @emotion/styled
- css prop for inline styles
- styled API for component styles
- Theme integration with ThemeProvider
- Proper TypeScript setup
- Server-side rendering with extractCritical
- Use composition patterns""",
            
            StylingLibrary.CSS_MODULES: """
CSS MODULES REQUIREMENTS:
- Use .module.css or .module.scss files
- camelCase class names
- Composition with composes
- Global styles with :global()
- Proper TypeScript declarations
- PostCSS integration if available
- BEM-like naming for clarity""",
            
            StylingLibrary.PANDA_CSS: """
PANDA CSS REQUIREMENTS:
- Use Panda's css() function
- Recipe patterns for variants
- Slot recipes for compound components
- Token-based design system
- Proper layer organization
- Pattern functions
- Responsive arrays and objects"""
        }
        
        return f"""STYLING: {styling.value.upper()}
{instructions.get(styling, "Use appropriate styling patterns for the library")}"""
    
    def _build_library_instructions(self, library: ComponentLibrary, imports: Dict) -> str:
        """Build component library instructions"""
        
        if library == ComponentLibrary.NONE:
            return """
COMPONENT APPROACH:
- Build custom components from scratch
- Use semantic HTML elements
- Implement proper ARIA attributes
- Create reusable, composable components
- Follow atomic design principles where appropriate"""
        
        available_components = imports.get("ui_components", {}).get(library.value, [])
        
        instructions = {
            ComponentLibrary.SHADCN_UI: f"""
SHADCN/UI INTEGRATION:
Available components: {', '.join(available_components[:10])}
- Import from @/components/ui/
- Use cn() utility from @/lib/utils
- Extend with custom variants
- Follow shadcn/ui patterns
- Compose primitives for complex components
- Use Radix UI primitives underneath""",
            
            ComponentLibrary.MATERIAL_UI: """
MUI INTEGRATION:
- Use MUI v5 components and sx prop
- Theme integration with createTheme
- Proper TypeScript augmentation
- Use MUI system props
- Icon integration with @mui/icons-material
- Follow Material Design principles""",
            
            ComponentLibrary.CHAKRA_UI: """
CHAKRA UI INTEGRATION:
- Use Chakra component primitives
- Theme integration and customization
- Responsive array/object syntax
- Use style props system
- Compose with Box, Flex, Grid
- Color mode support""",
        }
        
        return instructions.get(library, f"Use {library.value} components appropriately")
    
    def _build_generation_instructions(self, gen_type: GenerationType, request: GenerationRequest) -> str:
        """Build generation type specific instructions"""
        
        if gen_type == GenerationType.MULTI_FILE_COMPONENT:
            return self._build_multifile_component_instructions(request)
        elif gen_type == GenerationType.PAGE:
            return self._build_page_generation_instructions(request)
        elif gen_type == GenerationType.FULL_FEATURE:
            return self._build_feature_generation_instructions(request)
        elif gen_type == GenerationType.EDIT_FILE:
            return self._build_edit_instructions(request)
        elif gen_type == GenerationType.UTILS:
            return self._build_utils_instructions()
        elif gen_type == GenerationType.HOOKS:
            return self._build_hooks_instructions()
        elif gen_type == GenerationType.CONTEXT:
            return self._build_context_instructions()
        elif gen_type == GenerationType.STORE:
            return self._build_store_instructions()
        else:
            return self._build_single_component_instructions()
    
    def _build_multifile_component_instructions(self, request: GenerationRequest) -> str:
        """Instructions for multi-file component generation"""
        files = ["index.ts", "Component.tsx", "Component.types.ts"]
        
        if request.include_tests:
            files.append("Component.test.tsx")
        if request.include_storybook:
            files.append("Component.stories.tsx")
        if request.styling == StylingLibrary.CSS_MODULES:
            files.append("Component.module.css")
        
        return f"""
MULTI-FILE COMPONENT GENERATION:
Generate a complete component package with proper separation of concerns.

REQUIRED FILES:
{chr(10).join(f"- {file}" for file in files)}

STRUCTURE EXAMPLE:
```
components/
  └── ComponentName/
      ├── index.ts              # Barrel export
      ├── ComponentName.tsx     # Main component
      ├── ComponentName.types.ts # TypeScript types
      ├── ComponentName.test.tsx # Unit tests
      ├── ComponentName.stories.tsx # Storybook stories
      └── ComponentName.module.css # Styles (if CSS modules)
```

ARCHITECTURAL PATTERNS:
- Separate types into dedicated file
- Use barrel exports for clean imports
- Colocate tests with components
- Extract complex logic to hooks
- Create sub-components in same directory
- Use composition for flexibility"""
    
    def _build_feature_generation_instructions(self, request: GenerationRequest) -> str:
        """Instructions for full feature generation"""
        return """
FULL FEATURE GENERATION:
Generate a complete feature with all necessary files and infrastructure.

FEATURE STRUCTURE:
```
features/
  └── FeatureName/
      ├── index.ts              # Public API
      ├── components/           # Feature-specific components
      │   ├── FeatureMain/
      │   └── FeatureItem/
      ├── hooks/                # Feature-specific hooks
      │   ├── useFeatureData.ts
      │   └── useFeatureLogic.ts
      ├── utils/                # Feature utilities
      │   └── featureHelpers.ts
      ├── types/                # Feature types
      │   └── feature.types.ts
      ├── services/             # API/data services
      │   └── featureService.ts
      ├── store/                # Feature state (if needed)
      │   └── featureStore.ts
      └── __tests__/            # Feature tests
```

PATTERNS:
- Feature-first architecture
- Encapsulation of feature logic
- Clear public API via index.ts
- Dependency injection where appropriate
- Feature-level error boundaries
- Lazy loading for performance"""
    
    def _build_page_generation_instructions(self, request: GenerationRequest) -> str:
        """Page generation instructions based on framework"""
        if request.framework == FrameworkType.NEXTJS:
            return """
NEXT.JS PAGE GENERATION:
Create complete page with proper App Router patterns.

REQUIRED FILES:
- app/[route]/page.tsx       # Main page component
- app/[route]/layout.tsx     # Layout (if custom needed)
- app/[route]/loading.tsx    # Loading state
- app/[route]/error.tsx      # Error boundary
- app/[route]/metadata.ts    # SEO metadata

PAGE PATTERNS:
1. Server Components for data fetching
2. Streaming with Suspense boundaries
3. Parallel data fetching
4. Proper cache directives
5. generateStaticParams for SSG
6. generateMetadata for dynamic SEO

EXAMPLE STRUCTURE:
```tsx
// page.tsx
export default async function PageName({ params, searchParams }) {
  const data = await fetchData();
  return <PageComponent data={data} />;
}

// loading.tsx
export default function Loading() {
  return <PageSkeleton />;
}

// error.tsx
'use client';
export default function Error({ error, reset }) {
  return <ErrorComponent error={error} reset={reset} />;
}
```"""
        else:
            return """
PAGE GENERATION:
Create complete page component with routing integration."""
    
    def _build_edit_instructions(self, request: GenerationRequest) -> str:
        """Instructions for editing existing files"""
        edit_modes = {
            'add': 'Add new functionality while preserving existing code',
            'modify': 'Modify existing functionality with minimal changes',
            'refactor': 'Improve code quality without changing functionality',
            'enhance': 'Add improvements and new features'
        }
        
        return f"""
FILE EDITING MODE: {request.edit_mode}
{edit_modes.get(request.edit_mode, 'Modify the file as requested')}

EDITING RULES:
1. Preserve ALL existing functionality unless explicitly asked to change
2. Maintain consistent code style
3. Update all affected imports
4. Update types/interfaces as needed
5. Add proper documentation for changes
6. Ensure backward compatibility
7. Run through the same quality checks as new code

TARGET FILES:
{chr(10).join(request.target_files or ['No specific files targeted'])}

OUTPUT FORMAT:
Show the COMPLETE updated file(s), not just the changes."""
    
    def _build_utils_instructions(self) -> str:
        """Instructions for utility generation"""
        return """
UTILITY GENERATION:
Create well-organized, reusable utility functions.

UTILITY PATTERNS:
- Pure functions when possible
- Proper TypeScript generics
- Comprehensive JSDoc comments
- Unit tests for each utility
- Group related utilities
- Export from index file

EXAMPLE STRUCTURE:
```
utils/
  ├── index.ts          # Public exports
  ├── string.ts         # String utilities
  ├── array.ts          # Array utilities
  ├── date.ts           # Date utilities
  ├── validation.ts     # Validation utilities
  └── __tests__/        # Utility tests
```"""
    
    def _build_hooks_instructions(self) -> str:
        """Instructions for custom hooks generation"""
        return """
CUSTOM HOOKS GENERATION:
Create reusable React hooks following best practices.

HOOK PATTERNS:
- Start with 'use' prefix
- Return consistent value types
- Handle cleanup properly
- Memoize expensive operations
- Support SSR when needed
- Comprehensive TypeScript types
- Include usage examples

COMMON PATTERNS:
- Data fetching hooks
- State management hooks
- Event listener hooks
- Animation hooks
- Form handling hooks
- LocalStorage/SessionStorage hooks"""
    
    def _build_context_instructions(self) -> str:
        """Instructions for React Context generation"""
        return """
CONTEXT GENERATION:
Create properly structured React Context with TypeScript.

CONTEXT STRUCTURE:
```
contexts/
  └── FeatureContext/
      ├── index.tsx              # Main context file
      ├── FeatureContext.types.ts # Types
      ├── FeatureProvider.tsx     # Provider component
      ├── useFeature.ts          # Hook for consuming
      └── __tests__/             # Context tests
```

PATTERNS:
- Separate Provider component
- Custom hook for consumption
- Proper TypeScript types
- Default values
- Error handling for missing provider
- Performance optimization
- Split contexts when needed"""
    
    def _build_store_instructions(self) -> str:
        """Instructions for state management generation"""
        return """
STATE MANAGEMENT GENERATION:
Create state management solution (Zustand/Redux Toolkit/Jotai/Valtio).

STORE PATTERNS:
- Modular store structure
- TypeScript types for state
- Async actions support
- Devtools integration
- Persistence when needed
- Proper selectors
- Performance optimizations

Choose the most appropriate based on project needs."""
    
    def _build_single_component_instructions(self) -> str:
        """Default single component instructions"""
        return """
SINGLE COMPONENT GENERATION:
Create a complete, self-contained React component.

REQUIREMENTS:
- Full TypeScript interfaces
- Proper prop validation
- Error boundaries if needed
- Loading/error states
- Responsive design
- Accessibility features
- Performance optimizations
- Clean, maintainable code"""
    
    def _build_utility_instructions(self, request: GenerationRequest) -> str:
        """Build utility-specific instructions"""
        utilities = []
        
        if request.responsive:
            utilities.append("""
RESPONSIVE DESIGN:
- Mobile-first approach
- Breakpoints: 640px (sm), 768px (md), 1024px (lg), 1280px (xl)
- Fluid typography and spacing
- Touch-friendly interactive elements
- Proper viewport handling""")
        
        if request.accessibility_level:
            utilities.append(f"""
ACCESSIBILITY ({request.accessibility_level.upper()}-level):
- Semantic HTML elements
- ARIA labels and descriptions
- Keyboard navigation support
- Focus management
- Screen reader compatibility
- Color contrast compliance
- Error announcements
- Loading state announcements""")
        
        return "\n\n".join(utilities)
    
    def _format_design_tokens(self, tokens: Dict) -> str:
        """Format design tokens for the prompt"""
        sections = []
        
        if tokens.get('colors'):
            colors = tokens['colors']
            if isinstance(colors, dict):
                color_list = list(colors.keys())[:8]
            else:
                color_list = colors[:8]
            sections.append(f"Colors: {', '.join(color_list)}")
        
        if tokens.get('spacing'):
            spacing_list = tokens['spacing'][:8] if isinstance(tokens['spacing'], list) else list(tokens['spacing'].keys())[:8]
            sections.append(f"Spacing: {', '.join(str(s) for s in spacing_list)}")
        
        if tokens.get('typography'):
            type_list = tokens['typography'][:6] if isinstance(tokens['typography'], list) else list(tokens['typography'].keys())[:6]
            sections.append(f"Typography: {', '.join(str(t) for t in type_list)}")
        
        return "\n".join(sections) if sections else "No specific design tokens detected"
    
    def _format_design_tokens_enhanced(self, tokens: Dict) -> str:
        """Format design tokens with emphasis for better adherence"""
        sections = []
        
        if tokens.get('colors'):
            colors = tokens['colors']
            if isinstance(colors, dict):
                color_list = list(colors.keys())[:10]
            else:
                color_list = colors[:10]
            
            # Exclude generic colors and emphasize project-specific ones
            project_colors = [c for c in color_list if c not in ['black', 'white', 'gray']]
            
            sections.append(f"PROJECT COLORS (USE THESE!): {', '.join(project_colors)}")
            sections.append(f"Available shades: {'-'.join([f'{c}-500' for c in project_colors[:3]])}")
            
            # Add gradient examples
            if len(project_colors) >= 2:
                sections.append(f"Gradient examples: from-{project_colors[0]}-400 to-{project_colors[1]}-600")
        
        if tokens.get('spacing'):
            spacing_list = tokens['spacing'][:8] if isinstance(tokens['spacing'], list) else list(tokens['spacing'].keys())[:8]
            sections.append(f"Spacing scale: {', '.join(str(s) for s in spacing_list)}")
        
        if tokens.get('typography'):
            type_list = tokens['typography'][:6] if isinstance(tokens['typography'], list) else list(tokens['typography'].keys())[:6]
            sections.append(f"Typography scale: {', '.join(str(t) for t in type_list)}")
        
        if not sections:
            return "No specific design tokens detected - use standard Tailwind classes"
        
        return "\n".join(sections)
    
    def _format_project_context(self, context: Dict, ast_analysis: Dict) -> str:
        """Format project context for the prompt"""
        sections = []
        
        # Add detected patterns
        if ast_analysis and 'common_patterns' in ast_analysis:
            patterns = ast_analysis['common_patterns']
            if patterns.get('common_props'):
                sections.append(f"Common props: {', '.join(list(patterns['common_props'].keys())[:5])}")
            if patterns.get('common_imports'):
                sections.append(f"Common imports: {', '.join(list(patterns['common_imports'].keys())[:5])}")
        
        # Add project structure
        structure = context.get('project_structure', {})
        if structure:
            sections.append(f"Component directory: {structure.get('components_dir', 'unknown')}")
        
        return "\n".join(sections) if sections else "Standard React project structure"
    
    def _load_styling_patterns(self) -> Dict:
        """Load styling-specific patterns"""
        return {
            StylingLibrary.TAILWIND: {
                'utility_examples': ['flex items-center justify-between', 'grid grid-cols-1 md:grid-cols-2'],
                'responsive_pattern': 'sm:px-6 md:px-8 lg:px-10',
                'state_pattern': 'hover:bg-blue-600 focus:ring-2 active:scale-95'
            },
            StylingLibrary.STYLED_COMPONENTS: {
                'component_pattern': 'const Button = styled.button`...`',
                'props_pattern': '${props => props.primary && css`...`}',
                'theme_pattern': '${({ theme }) => theme.colors.primary}'
            }
        }
    
    def _load_framework_patterns(self) -> Dict:
        """Load framework-specific patterns"""
        return {
            FrameworkType.NEXTJS: {
                'data_fetching': 'async function with fetch',
                'routing': 'file-based with app directory',
                'api_routes': 'route.ts files'
            },
            FrameworkType.REACT: {
                'routing': 'react-router-dom',
                'state': 'useState, useReducer, Context',
                'data_fetching': 'useEffect, react-query, SWR'
            }
        }
    
    def _load_utility_patterns(self) -> Dict:
        """Load utility patterns"""
        return {
            'form_validation': {
                'libraries': ['react-hook-form', 'formik', 'react-final-form'],
                'patterns': ['yup', 'zod', 'joi']
            },
            'animation': {
                'libraries': ['framer-motion', 'react-spring', 'auto-animate'],
                'css': ['transitions', 'animations', 'transforms']
            },
            'data_fetching': {
                'libraries': ['swr', 'react-query', 'apollo-client'],
                'patterns': ['suspense', 'error boundaries', 'loading states']
            }
        }
    
    def build_ui_system_prompt(self, context: Dict) -> str:
        """Build a focused system prompt for clean component generation."""
        
        return f"""You are a senior React developer. Generate clean, production-ready React components.

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY the raw TypeScript React component code
- NO markdown code blocks (```tsx, ```, etc.)
- NO explanations, feature lists, or usage examples
- NO extra text before or after the code
- Start directly with imports and end with export

TECHNICAL SPECIFICATIONS:
- Framework: {context.get('framework', 'React')}
- Styling: {context.get('styling', 'Tailwind CSS')}
- Component Library: {context.get('component_library', 'none')}
- Use TypeScript with proper interfaces
- Make components accessible (ARIA labels, semantic HTML)
- Include responsive design patterns
- Follow React best practices

Generate only the component code, nothing else."""
    
    def build_user_prompt(self, prompt: str, context: Dict) -> str:
        """Build a focused user prompt."""
        return f"""Create a React component: {prompt}

Requirements:
- Complete, working TypeScript component
- Responsive and accessible
- Follow project conventions
- Output code only, no explanations"""


# Example usage function
def create_generation_request(
    prompt: str,
    framework: str = "next.js",
    styling: str = "tailwind",
    component_library: str = "shadcn/ui",
    generation_type: str = "single"
) -> GenerationRequest:
    """Helper function to create a generation request"""
    
    # Map strings to enums
    framework_map = {
        "react": FrameworkType.REACT,
        "next.js": FrameworkType.NEXTJS,
        "remix": FrameworkType.REMIX,
        "vite": FrameworkType.VITE_REACT
    }
    
    styling_map = {
        "tailwind": StylingLibrary.TAILWIND,
        "styled-components": StylingLibrary.STYLED_COMPONENTS,
        "emotion": StylingLibrary.EMOTION,
        "css-modules": StylingLibrary.CSS_MODULES,
        "sass": StylingLibrary.SASS,
        "css": StylingLibrary.VANILLA_CSS,
        "panda-css": StylingLibrary.PANDA_CSS
    }
    
    library_map = {
        "shadcn/ui": ComponentLibrary.SHADCN_UI,
        "material-ui": ComponentLibrary.MATERIAL_UI,
        "chakra-ui": ComponentLibrary.CHAKRA_UI,
        "ant-design": ComponentLibrary.ANT_DESIGN,
        "headless-ui": ComponentLibrary.HEADLESS_UI,
        "none": ComponentLibrary.NONE
    }
    
    type_map = {
        "single": GenerationType.SINGLE_COMPONENT,
        "multi": GenerationType.MULTI_FILE_COMPONENT,
        "page": GenerationType.PAGE,
        "feature": GenerationType.FULL_FEATURE,
        "edit": GenerationType.EDIT_FILE,
        "utils": GenerationType.UTILS,
        "hooks": GenerationType.HOOKS,
        "context": GenerationType.CONTEXT,
        "store": GenerationType.STORE
    }
    
    return GenerationRequest(
        prompt=prompt,
        generation_type=type_map.get(generation_type, GenerationType.SINGLE_COMPONENT),
        framework=framework_map.get(framework, FrameworkType.REACT),
        styling=styling_map.get(styling, StylingLibrary.TAILWIND),
        component_library=library_map.get(component_library, ComponentLibrary.NONE),
        include_tests=True,
        include_storybook=False,
        responsive=True,
        accessibility_level="aa"
    )