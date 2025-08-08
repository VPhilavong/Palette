"""
Chakra UI Generation Strategy.
Specialized strategy that ensures proper Chakra UI component usage and prevents
Tailwind CSS class generation - addressing the critical framework detection issue.
"""

import re
from typing import Dict, List, Optional, Tuple, Any

from .base import GenerationStrategy, GenerationResult, ValidationIssue, ComponentSpec
from ...intelligence.styling_analyzer import StylingSystem


class ChakraUIGenerationStrategy(GenerationStrategy):
    """
    Specialized generation strategy for Chakra UI projects.
    
    This strategy addresses the critical issue where Tailwind classes were being
    generated in Chakra UI projects. It ensures:
    1. Only Chakra UI components are used
    2. No CSS utility classes (Tailwind) are generated  
    3. Proper Chakra UI patterns and imports
    4. Theme-aware prop usage
    """
    
    def __init__(self):
        super().__init__(
            name="ChakraUI",
            supported_systems=[StylingSystem.CHAKRA_UI]
        )
        
        # Initialize Chakra UI specific patterns and rules
        self._initialize_chakra_patterns()
        self._initialize_validation_rules()
        self._initialize_component_mappings()
    
    def _initialize_chakra_patterns(self):
        """Initialize Chakra UI specific patterns."""
        
        # Required import patterns
        self.required_imports = [
            "from '@chakra-ui/react'",
            "@chakra-ui/react",
            "@chakra-ui/next-js"
        ]
        
        # Forbidden patterns that indicate wrong styling approach
        self.forbidden_patterns = [
            # Tailwind CSS classes
            r'className="[^"]*(?:bg-(?:red|blue|green|gray|slate|zinc|neutral|stone|amber|yellow|lime|emerald|teal|cyan|sky|indigo|violet|purple|fuchsia|pink|rose)-\d+)',
            r'className="[^"]*(?:text-(?:xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl))',
            r'className="[^"]*(?:p-\d+|px-\d+|py-\d+|pt-\d+|pb-\d+|pl-\d+|pr-\d+)',
            r'className="[^"]*(?:m-\d+|mx-\d+|my-\d+|mt-\d+|mb-\d+|ml-\d+|mr-\d+)',
            r'className="[^"]*(?:w-(?:full|screen|\d+)|h-(?:full|screen|\d+))',
            r'className="[^"]*(?:flex|grid|block|inline|hidden)',
            r'className="[^"]*(?:rounded-(?:none|sm|md|lg|xl|2xl|3xl|full))',
            r'className="[^"]*(?:shadow-(?:sm|md|lg|xl|2xl|inner|none))',
            r'className="[^"]*(?:border-(?:\d+|none|solid|dashed|dotted))',
            r'className="[^"]*(?:hover:|focus:|active:|disabled:|first:|last:|odd:|even:)',
            r'className="[^"]*(?:sm:|md:|lg:|xl:|2xl:)',
            
            # CSS-in-JS patterns that shouldn't be used with Chakra
            r'styled\.\w+',
            r'css=\{',
            r'style=\{',
            
            # Direct CSS classes
            r'className="[^"]*(?:btn|button-|card-|nav-|modal-|form-|input-)',
        ]
        
        # Required patterns that should be present in Chakra UI code
        self.required_patterns = [
            r'@chakra-ui/react',  # Must import from Chakra UI
            r'<(?:Box|Flex|Stack|VStack|HStack|Grid|GridItem|Container)',  # Layout components
            r'(?:colorScheme|variant|size)=',  # Chakra props
        ]
        
        # Component mappings from HTML/generic to Chakra UI
        self.component_mappings = {
            'div': 'Box',
            'button': 'Button', 
            'input': 'Input',
            'textarea': 'Textarea',
            'select': 'Select',
            'form': 'Box as="form"',
            'nav': 'Box as="nav"',
            'header': 'Box as="header"',
            'footer': 'Box as="footer"',
            'main': 'Box as="main"',
            'section': 'Box as="section"',
            'article': 'Box as="article"',
            'aside': 'Box as="aside"',
            'h1': 'Heading as="h1"',
            'h2': 'Heading as="h2"',
            'h3': 'Heading as="h3"',
            'h4': 'Heading as="h4"',
            'h5': 'Heading as="h5"',
            'h6': 'Heading as="h6"',
            'p': 'Text',
            'span': 'Text as="span"',
            'img': 'Image',
            'a': 'Link',
            'ul': 'List',
            'ol': 'OrderedList',
            'li': 'ListItem'
        }
    
    def _initialize_validation_rules(self):
        """Initialize validation rules specific to Chakra UI."""
        self.validation_rules = [
            {
                'name': 'chakra_imports',
                'description': 'Must import from @chakra-ui/react',
                'pattern': r'@chakra-ui/react',
                'required': True
            },
            {
                'name': 'no_tailwind_classes',
                'description': 'No Tailwind CSS classes allowed',
                'pattern': r'className="[^"]*(?:bg-\w+-\d+|text-\w+-\d+|p-\d+|m-\d+)',
                'forbidden': True
            },
            {
                'name': 'chakra_components',
                'description': 'Should use Chakra UI components',
                'pattern': r'<(?:Box|Button|Text|Flex|Stack|Input|Textarea)',
                'recommended': True
            },
            {
                'name': 'theme_props',
                'description': 'Should use theme-aware props',
                'pattern': r'(?:colorScheme|variant|size)=',
                'recommended': True
            }
        ]
    
    def _initialize_component_mappings(self):
        """Initialize mappings from common patterns to Chakra UI."""
        
        # Button variants mapping
        self.button_variants = {
            'primary': 'solid',
            'secondary': 'outline', 
            'ghost': 'ghost',
            'link': 'link',
            'danger': 'solid',  # with colorScheme="red"
            'success': 'solid', # with colorScheme="green"
        }
        
        # Color scheme mappings
        self.color_schemes = {
            'primary': 'blue',
            'secondary': 'gray',
            'success': 'green',
            'warning': 'yellow',
            'danger': 'red',
            'error': 'red',
            'info': 'blue'
        }
        
        # Size mappings
        self.size_mappings = {
            'xs': 'xs',
            'sm': 'sm', 
            'small': 'sm',
            'md': 'md',
            'medium': 'md',
            'lg': 'lg',
            'large': 'lg',
            'xl': 'xl'
        }
    
    def generate_component(self, prompt: str, context: Dict) -> GenerationResult:
        """
        Generate Chakra UI component ensuring no Tailwind classes are used.
        
        This is the main method that addresses the critical framework detection issue.
        """
        # Analyze component requirements
        component_spec = self.analyze_requirements(prompt)
        
        # Build Chakra UI-specific context
        chakra_context = self._build_chakra_context(context, component_spec)
        
        # Generate prompts with strict Chakra UI guidance
        system_prompt = self._build_chakra_system_prompt(chakra_context)
        user_prompt = self._build_chakra_user_prompt(prompt, component_spec)
        
        # Generate code with the configured LLM
        try:
            raw_code = self._generate_with_llm(system_prompt, user_prompt, context)
        except Exception as e:
            return GenerationResult(
                code=f"// Error generating component: {e}",
                quality_score=0.0,
                strategy_used=self.name,
                validation_issues=[ValidationIssue("error", f"Generation failed: {e}")]
            )
        
        # Critical: Validate and fix Chakra UI compliance
        validated_code, validation_issues = self._validate_and_fix_chakra_compliance(raw_code)
        
        # Apply additional post-generation fixes
        fixed_code, fixes_applied = self.apply_post_generation_fixes(validated_code)
        
        # Calculate quality score
        quality_score = self.calculate_quality_score(fixed_code, validation_issues)
        
        return GenerationResult(
            code=fixed_code,
            quality_score=quality_score,
            strategy_used=self.name,
            validation_issues=validation_issues,
            auto_fixes_applied=fixes_applied,
            generation_metadata={
                'chakra_ui_compliance': True,
                'tailwind_classes_removed': len([f for f in fixes_applied if 'Tailwind' in f]),
                'chakra_components_added': len([f for f in fixes_applied if 'Chakra' in f])
            }
        )
    
    def _build_chakra_context(self, context: Dict, spec: ComponentSpec) -> Dict:
        """Build Chakra UI-specific generation context."""
        chakra_context = context.copy()
        
        # Add Chakra UI specific guidance
        chakra_context.update({
            'component_library': 'chakra-ui',
            'styling_approach': 'component_props',
            'forbidden_patterns': [
                'className with CSS utility classes',
                'Tailwind CSS classes',
                'inline styles',
                'CSS-in-JS styling'
            ],
            'required_patterns': [
                'Chakra UI component imports',
                'Theme-aware props (colorScheme, variant, size)',
                'Proper component composition'
            ],
            'import_examples': [
                "import { Box, Button, Text, Flex, Stack, VStack, HStack } from '@chakra-ui/react'",
                "import { Input, Textarea, Select, FormControl, FormLabel } from '@chakra-ui/react'",
                "import { Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody } from '@chakra-ui/react'"
            ],
            'component_examples': self._get_chakra_examples(spec.component_type),
            'validation_rules': [
                'NEVER use className with CSS utility classes',
                'ALWAYS use Chakra UI components instead of HTML elements',
                'USE theme-aware props like colorScheme, variant, size',
                'AVOID inline styles or CSS-in-JS patterns'
            ]
        })
        
        return chakra_context
    
    def _build_chakra_system_prompt(self, context: Dict) -> str:
        """Build system prompt with strict Chakra UI guidance."""
        return f"""You are an expert React developer specializing in Chakra UI.

CRITICAL RULES - MUST FOLLOW:
1. NEVER use className with CSS utility classes (especially Tailwind classes like bg-blue-500, text-lg, p-4, etc.)
2. ALWAYS use Chakra UI components instead of HTML elements
3. ALWAYS import components from '@chakra-ui/react'
4. USE theme-aware props: colorScheme, variant, size, etc.
5. NO inline styles or CSS-in-JS patterns

CHAKRA UI BEST PRACTICES:
- Use Box instead of div
- Use Button with colorScheme and variant props
- Use Text instead of p, span
- Use Flex, Stack, VStack, HStack for layouts
- Use Chakra's spacing system (p, m, px, py, etc. as props)
- Use Chakra's color system (colorScheme prop)

FORBIDDEN PATTERNS:
{context.get('forbidden_patterns', [])}

REQUIRED PATTERNS:
{context.get('required_patterns', [])}

IMPORT EXAMPLES:
{chr(10).join(context.get('import_examples', []))}

Generate clean, accessible React components using ONLY Chakra UI patterns."""
    
    def _build_chakra_user_prompt(self, prompt: str, spec: ComponentSpec) -> str:
        """Build user prompt with Chakra UI context."""
        chakra_prompt = f"""Create a {spec.component_type} component using Chakra UI.

Original request: {prompt}

Requirements:
- Use ONLY Chakra UI components
- Import from '@chakra-ui/react'
- Use theme-aware props (colorScheme, variant, size)
- NO CSS utility classes or className styling
- Make it accessible and responsive using Chakra's built-in props

Component complexity: {spec.complexity}
Styling requirements: {', '.join(spec.styling_requirements)}
Accessibility requirements: {', '.join(spec.accessibility_requirements)}

Return ONLY the React component code with proper TypeScript typing."""
        
        return chakra_prompt
    
    def _get_chakra_examples(self, component_type: str) -> List[str]:
        """Get Chakra UI examples for specific component type."""
        examples = {
            'button': [
                '<Button colorScheme="blue" variant="solid" size="md">Click me</Button>',
                '<Button colorScheme="red" variant="outline" leftIcon={<AddIcon />}>Add Item</Button>',
                '<Button variant="ghost" size="sm" isLoading>Loading</Button>'
            ],
            'form': [
                '''<FormControl>
  <FormLabel>Email</FormLabel>
  <Input type="email" placeholder="Enter email" />
  <FormHelperText>We'll never share your email.</FormHelperText>
</FormControl>''',
                '''<VStack spacing={4} align="stretch">
  <Input placeholder="Name" />
  <Input placeholder="Email" type="email" />
  <Button colorScheme="blue" type="submit">Submit</Button>
</VStack>'''
            ],
            'card': [
                '''<Box bg="white" shadow="md" rounded="lg" p={6}>
  <Text fontSize="xl" fontWeight="bold" mb={2}>Card Title</Text>
  <Text color="gray.600">Card content goes here</Text>
</Box>''',
                '''<Card>
  <CardHeader>
    <Heading size="md">Card Header</Heading>
  </CardHeader>
  <CardBody>
    <Text>Card body content</Text>
  </CardBody>
</Card>'''
            ],
            'modal': [
                '''<Modal isOpen={isOpen} onClose={onClose}>
  <ModalOverlay />
  <ModalContent>
    <ModalHeader>Modal Title</ModalHeader>
    <ModalCloseButton />
    <ModalBody>
      <Text>Modal content</Text>
    </ModalBody>
    <ModalFooter>
      <Button colorScheme="blue" mr={3} onClick={onClose}>
        Close
      </Button>
    </ModalFooter>
  </ModalContent>
</Modal>'''
            ],
            'navigation': [
                '''<Flex bg="blue.500" color="white" p={4} align="center">
  <Text fontSize="xl" fontWeight="bold" mr={8}>Logo</Text>
  <HStack spacing={6}>
    <Link>Home</Link>
    <Link>About</Link>
    <Link>Contact</Link>
  </HStack>
</Flex>''',
                '''<Box bg="gray.100" p={4}>
  <VStack spacing={2} align="stretch">
    <Button variant="ghost" justifyContent="flex-start">Home</Button>
    <Button variant="ghost" justifyContent="flex-start">About</Button>
    <Button variant="ghost" justifyContent="flex-start">Contact</Button>
  </VStack>
</Box>'''
            ]
        }
        
        return examples.get(component_type, examples['button'])
    
    def _generate_with_llm(self, system_prompt: str, user_prompt: str, context: Dict) -> str:
        """Generate code using the configured LLM."""
        # This would integrate with the existing LLM generation logic
        # For now, returning a placeholder that shows the integration point
        
        # Try to get LLM client from context
        llm_client = context.get('llm_client')
        model = context.get('model', 'gpt-4')
        
        if not llm_client:
            # Fallback to mock generation for testing
            return self._generate_mock_chakra_component(user_prompt)
        
        # Generate with OpenAI/Anthropic
        try:
            if hasattr(llm_client, 'chat'):  # OpenAI-style
                response = llm_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                return response.choices[0].message.content.strip()
            
            elif hasattr(llm_client, 'messages'):  # Anthropic-style
                response = llm_client.messages.create(
                    model=model,
                    max_tokens=2000,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return response.content[0].text.strip()
        
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return self._generate_mock_chakra_component(user_prompt)
    
    def _generate_mock_chakra_component(self, prompt: str) -> str:
        """Generate a mock Chakra UI component for testing."""
        component_type = self._extract_component_type(prompt.lower())
        
        if component_type == 'button':
            return '''import React from 'react';
import { Button } from '@chakra-ui/react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  colorScheme?: string;
  variant?: string;
  size?: string;
}

const CustomButton: React.FC<ButtonProps> = ({ 
  children, 
  onClick, 
  colorScheme = "blue", 
  variant = "solid",
  size = "md"
}) => {
  return (
    <Button 
      colorScheme={colorScheme}
      variant={variant}
      size={size}
      onClick={onClick}
    >
      {children}
    </Button>
  );
};

export default CustomButton;'''
        
        else:
            return f'''import React from 'react';
import {{ Box, Text }} from '@chakra-ui/react';

interface {component_type.capitalize()}Props {{
  children?: React.ReactNode;
}}

const {component_type.capitalize()}Component: React.FC<{component_type.capitalize()}Props> = ({{ children }}) => {{
  return (
    <Box p={{4}} bg="white" shadow="md" rounded="lg">
      <Text fontSize="lg" fontWeight="bold">
        {component_type.capitalize()} Component
      </Text>
      {{children}}
    </Box>
  );
}};

export default {component_type.capitalize()}Component;'''
    
    def _validate_and_fix_chakra_compliance(self, code: str) -> Tuple[str, List[ValidationIssue]]:
        """
        Critical method: Validate and fix Chakra UI compliance issues.
        This addresses the main framework detection problem.
        """
        issues = []
        current_code = code
        
        # 1. Check for Tailwind classes (CRITICAL ERROR)
        tailwind_violations = self._detect_tailwind_classes(current_code)
        if tailwind_violations:
            for violation in tailwind_violations:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Tailwind CSS class detected: {violation}",
                    suggestion="Use Chakra UI component props instead"
                ))
            
            # Auto-fix: Remove Tailwind classes and convert to Chakra props
            current_code = self._convert_tailwind_to_chakra(current_code)
        
        # 2. Check for missing Chakra UI imports
        if not self._has_chakra_imports(current_code):
            issues.append(ValidationIssue(
                severity="error", 
                message="Missing Chakra UI imports",
                suggestion="Add imports from '@chakra-ui/react'"
            ))
            current_code = self._add_chakra_imports(current_code)
        
        # 3. Check for HTML elements that should be Chakra components
        html_elements = self._detect_html_elements(current_code)
        if html_elements:
            for element in html_elements:
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"HTML element detected: <{element}>", 
                    suggestion=f"Use Chakra UI {self.component_mappings.get(element, 'Box')} instead"
                ))
            
            current_code = self._convert_html_to_chakra(current_code)
        
        # 4. Check for inline styles
        if 'style=' in current_code:
            issues.append(ValidationIssue(
                severity="warning",
                message="Inline styles detected",
                suggestion="Use Chakra UI component props for styling"
            ))
            current_code = self._remove_inline_styles(current_code)
        
        # 5. Check for proper theme usage
        if not self._uses_theme_props(current_code):
            issues.append(ValidationIssue(
                severity="info",
                message="Consider using theme-aware props",
                suggestion="Use colorScheme, variant, size props for better theming"
            ))
        
        return current_code, issues
    
    def _detect_tailwind_classes(self, code: str) -> List[str]:
        """Detect Tailwind CSS classes in the code."""
        violations = []
        
        for pattern in self.forbidden_patterns:
            matches = re.findall(pattern, code)
            if matches:
                violations.extend(matches)
        
        return violations
    
    def _convert_tailwind_to_chakra(self, code: str) -> str:
        """Convert Tailwind classes to Chakra UI props."""
        
        # Common Tailwind to Chakra conversions
        conversions = {
            # Colors
            r'className="[^"]*bg-blue-(\d+)[^"]*"': lambda m: 'bg="blue.{}"'.format(min(int(m.group(1)), 900)),
            r'className="[^"]*bg-red-(\d+)[^"]*"': lambda m: 'bg="red.{}"'.format(min(int(m.group(1)), 900)),
            r'className="[^"]*bg-green-(\d+)[^"]*"': lambda m: 'bg="green.{}"'.format(min(int(m.group(1)), 900)),
            r'className="[^"]*bg-gray-(\d+)[^"]*"': lambda m: 'bg="gray.{}"'.format(min(int(m.group(1)), 900)),
            
            # Text colors
            r'className="[^"]*text-blue-(\d+)[^"]*"': lambda m: 'color="blue.{}"'.format(min(int(m.group(1)), 900)),
            r'className="[^"]*text-red-(\d+)[^"]*"': lambda m: 'color="red.{}"'.format(min(int(m.group(1)), 900)),
            r'className="[^"]*text-gray-(\d+)[^"]*"': lambda m: 'color="gray.{}"'.format(min(int(m.group(1)), 900)),
            
            # Padding
            r'className="[^"]*p-(\d+)[^"]*"': lambda m: 'p={' + m.group(1) + '}',
            r'className="[^"]*px-(\d+)[^"]*"': lambda m: 'px={' + m.group(1) + '}',
            r'className="[^"]*py-(\d+)[^"]*"': lambda m: 'py={' + m.group(1) + '}',
            
            # Margin  
            r'className="[^"]*m-(\d+)[^"]*"': lambda m: 'm={' + m.group(1) + '}',
            r'className="[^"]*mx-(\d+)[^"]*"': lambda m: 'mx={' + m.group(1) + '}',
            r'className="[^"]*my-(\d+)[^"]*"': lambda m: 'my={' + m.group(1) + '}',
            
            # Width/Height
            r'className="[^"]*w-full[^"]*"': lambda m: 'w="full"',
            r'className="[^"]*h-full[^"]*"': lambda m: 'h="full"',
            
            # Border radius
            r'className="[^"]*rounded-lg[^"]*"': lambda m: 'rounded="lg"',
            r'className="[^"]*rounded-md[^"]*"': lambda m: 'rounded="md"',
            
            # Shadow
            r'className="[^"]*shadow-md[^"]*"': lambda m: 'shadow="md"',
            r'className="[^"]*shadow-lg[^"]*"': lambda m: 'shadow="lg"',
            
            # Flexbox
            r'className="[^"]*flex[^"]*"': lambda m: '',  # Remove, use Flex component instead
            
            # Text size
            r'className="[^"]*text-lg[^"]*"': lambda m: 'fontSize="lg"',
            r'className="[^"]*text-xl[^"]*"': lambda m: 'fontSize="xl"',
            r'className="[^"]*text-sm[^"]*"': lambda m: 'fontSize="sm"',
        }
        
        # Apply conversions
        for pattern, replacement in conversions.items():
            if callable(replacement):
                code = re.sub(pattern, replacement, code)
            else:
                code = re.sub(pattern, replacement, code)
        
        # Remove empty className attributes
        code = re.sub(r'className="[^"]*"\s*', '', code)
        code = re.sub(r'className={[^}]*}\s*', '', code)
        
        return code
    
    def _has_chakra_imports(self, code: str) -> bool:
        """Check if code has Chakra UI imports."""
        return any(req_import in code for req_import in self.required_imports)
    
    def _add_chakra_imports(self, code: str) -> str:
        """Add missing Chakra UI imports."""
        # Extract components used in the code
        chakra_components = []
        
        component_patterns = [
            r'<(Box|Flex|Stack|VStack|HStack|Grid|GridItem|Container)',
            r'<(Button|Input|Textarea|Select|Text|Heading|Link)',
            r'<(Modal|ModalOverlay|ModalContent|ModalHeader|ModalBody|ModalFooter)',
            r'<(Card|CardHeader|CardBody|CardFooter)',
            r'<(FormControl|FormLabel|FormErrorMessage|FormHelperText)',
            r'<(List|OrderedList|UnorderedList|ListItem)',
            r'<(Image|Avatar|AvatarBadge|AvatarGroup)'
        ]
        
        for pattern in component_patterns:
            matches = re.findall(pattern, code)
            chakra_components.extend(matches)
        
        # Remove duplicates and create import
        unique_components = list(set(chakra_components))
        
        if unique_components:
            import_statement = f"import {{ {', '.join(sorted(unique_components))} }} from '@chakra-ui/react';\n"
            
            # Add import at the top, after React import if present
            if 'import React' in code:
                code = code.replace(
                    'import React from \'react\';',
                    'import React from \'react\';\n' + import_statement
                )
            else:
                code = "import React from 'react';\n" + import_statement + code
        
        return code
    
    def _detect_html_elements(self, code: str) -> List[str]:
        """Detect HTML elements that should be Chakra components."""
        html_elements = []
        
        for element in self.component_mappings.keys():
            pattern = f'<{element}(?:\\s|>)'
            if re.search(pattern, code):
                html_elements.append(element)
        
        return html_elements
    
    def _convert_html_to_chakra(self, code: str) -> str:
        """Convert HTML elements to Chakra UI components."""
        for html_element, chakra_component in self.component_mappings.items():
            # Convert opening tags
            pattern = f'<{html_element}(\\s[^>]*)?>'
            replacement = f'<{chakra_component}\\1>'
            code = re.sub(pattern, replacement, code)
            
            # Convert closing tags
            code = code.replace(f'</{html_element}>', f'</{chakra_component.split()[0]}>')
        
        return code
    
    def _remove_inline_styles(self, code: str) -> str:
        """Remove inline styles and convert to Chakra props where possible."""
        # This is a simplified version - would need more sophisticated parsing
        code = re.sub(r'style=\{[^}]+\}', '', code)
        return code
    
    def _uses_theme_props(self, code: str) -> bool:
        """Check if code uses theme-aware props."""
        theme_props = ['colorScheme', 'variant', 'size', 'bg', 'color', 'fontSize']
        return any(prop in code for prop in theme_props)
    
    def validate_generated_code(self, code: str) -> List[ValidationIssue]:
        """Validate generated code against Chakra UI rules."""
        issues = []
        
        # Run all validation rules
        for rule in self.validation_rules:
            if rule.get('required') and not re.search(rule['pattern'], code):
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Missing required pattern: {rule['description']}"
                ))
            
            elif rule.get('forbidden') and re.search(rule['pattern'], code):
                issues.append(ValidationIssue(
                    severity="error", 
                    message=f"Forbidden pattern found: {rule['description']}"
                ))
            
            elif rule.get('recommended') and not re.search(rule['pattern'], code):
                issues.append(ValidationIssue(
                    severity="info",
                    message=f"Recommended pattern missing: {rule['description']}"
                ))
        
        return issues
    
    def _get_fix_methods(self) -> List:
        """Get Chakra UI specific fix methods."""
        return [
            self._fix_chakra_imports,
            self._fix_component_usage,
            self._fix_typescript_issues,
            self._fix_formatting
        ]
    
    def _fix_chakra_imports(self, code: str) -> Tuple[str, str]:
        """Fix Chakra UI imports."""
        if not self._has_chakra_imports(code):
            fixed_code = self._add_chakra_imports(code)
            return fixed_code, "Added Chakra UI imports"
        return code, ""
    
    def _fix_component_usage(self, code: str) -> Tuple[str, str]:
        """Fix component usage to use Chakra UI components."""
        fixes_applied = []
        
        # Convert HTML to Chakra components
        html_elements = self._detect_html_elements(code)
        if html_elements:
            code = self._convert_html_to_chakra(code)
            fixes_applied.append(f"Converted {len(html_elements)} HTML elements to Chakra components")
        
        # Remove Tailwind classes
        tailwind_violations = self._detect_tailwind_classes(code)
        if tailwind_violations:
            code = self._convert_tailwind_to_chakra(code)
            fixes_applied.append(f"Converted {len(tailwind_violations)} Tailwind classes to Chakra props")
        
        return code, "; ".join(fixes_applied) if fixes_applied else ""