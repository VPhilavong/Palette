from typing import Dict

class UIPromptBuilder:
    """Builds UI-focused system prompts for LLM generation"""
    
    def build_ui_system_prompt(self, context: Dict) -> str:
        """Build comprehensive UI-focused system prompt with dynamic content"""
        
        framework = context.get('framework', 'react')
        styling = context.get('styling', 'tailwind')
        component_library = context.get('component_library', 'none')
        design_tokens = context.get('design_tokens', {})
        
        # Enhanced design token extraction
        colors = design_tokens.get('colors', ['blue', 'gray', 'green'])
        semantic_colors = design_tokens.get('semantic_colors', [])
        color_structure = design_tokens.get('color_structure', {})
        spacing = design_tokens.get('spacing', ['4', '8', '16'])
        typography = design_tokens.get('typography', ['sm', 'base', 'lg'])
        shadows = design_tokens.get('shadows', ['sm', 'md', 'lg'])
        border_radius = design_tokens.get('border_radius', ['sm', 'md', 'lg'])
        
        # Build enhanced design system section
        design_system_section = self._build_design_system_section(
            framework, styling, component_library, colors, semantic_colors, color_structure, spacing, typography, shadows, border_radius
        )
        
        # Get available imports for validation
        available_imports = context.get('available_imports', {})
        import_rules = self._build_import_rules(available_imports)
        
        prompt = f"""You are a UI/UX expert specializing in React + Tailwind CSS component generation.

{design_system_section}

{import_rules}

UI GENERATION REQUIREMENTS:
1. Create modern, responsive React components using TypeScript
2. Use advanced Tailwind patterns (group-hover, peer, arbitrary values, modern utilities)
3. Mobile-first responsive design (sm:, md:, lg:, xl:, 2xl:)
4. Include proper TypeScript interfaces with variant systems
5. Add hover states, focus states, and micro-interactions
6. Follow accessibility best practices (ARIA labels, proper contrast, keyboard navigation)
7. Match existing design patterns from this project
8. Include proper error and loading states where applicable
9. Use semantic HTML elements
10. Implement proper component composition patterns

DESIGN TRENDS TO IMPLEMENT:
- Modern glassmorphism effects (backdrop-blur, bg-opacity)
- Subtle animations and transitions using Tailwind
- Clean visual hierarchy with proper spacing
- Modern shadow and border radius usage
- Gradient backgrounds where appropriate
- Card-based layouts with proper elevation
- Interactive elements with clear feedback
- Clean typography with proper line height and spacing

TAILWIND PATTERNS TO USE:
- Advanced selectors: group-hover:, peer-focus:, has-[:checked]:
- Modern spacing: space-y-*, gap-*, divide-*
- Responsive utilities: hidden md:block, md:w-1/2 lg:w-1/3
- Animation classes: transition-all, hover:scale-105, animate-pulse
- Grid layouts: grid-cols-1 md:grid-cols-2 lg:grid-cols-3
- Flexbox patterns: flex items-center justify-between
- Modern color utilities: text-slate-600, bg-gray-50/50

COMPONENT STRUCTURE:
- Always include TypeScript interfaces for props
- Use modern React patterns (functional components, hooks)
- Include JSDoc comments for complex props
- Export component as default
- Include variant systems using union types
- Add proper error boundaries where needed

OUTPUT FORMAT:
Return ONLY the complete component code, no explanations or markdown blocks.
Include imports, interfaces, component definition, and export.
Ensure the code is production-ready and follows React best practices."""

        # Add component library specific instructions
        if component_library == 'shadcn/ui':
            prompt += """

SHADCN/UI INTEGRATION:
- Use cn() utility for className merging
- Follow shadcn/ui variant patterns with class-variance-authority
- Import from @/components/ui/ when using existing components
- Use shadcn/ui design tokens and patterns"""
        
        elif component_library != 'none':
            prompt += f"""

{component_library.upper()} INTEGRATION:
- Follow {component_library} design patterns and component APIs
- Use {component_library} components where appropriate
- Maintain consistency with {component_library} design system"""
        
        return prompt
    
    def _build_import_rules(self, available_imports):
        """Build import validation rules based on available imports"""
        
        ui_components = available_imports.get('ui_components', {})
        utilities = available_imports.get('utilities', {})
        icons = available_imports.get('icons', [])
        
        rules = ["IMPORT VALIDATION RULES (CRITICAL - Follow exactly):"]
        
        # shadcn/ui components
        if ui_components.get('shadcn_ui'):
            available_components = ', '.join(ui_components['shadcn_ui'])
            rules.append(f"✅ AVAILABLE shadcn/ui components: {available_components}")
            rules.append("✅ Import shadcn/ui components from: @/components/ui")
        else:
            rules.append("❌ NO shadcn/ui components available - DO NOT import from @/components/ui")
        
        # cn utility
        if utilities.get('cn'):
            rules.append("✅ cn utility available - Import from: @/lib/utils")
        else:
            rules.append("❌ NO cn utility available - DO NOT import cn from @/lib/utils")
        
        # Other utilities
        if utilities.get('clsx'):
            rules.append("✅ clsx available - Import from: clsx")
        if utilities.get('classnames'):
            rules.append("✅ classnames available - Import from: classnames")
        
        # Icons
        if icons:
            icon_libs = ', '.join(icons)
            rules.append(f"✅ Icon libraries available: {icon_libs}")
        else:
            rules.append("❌ NO icon libraries detected - Use standard HTML elements or emojis")
        
        # Custom components
        if ui_components.get('custom'):
            custom_components = ', '.join(ui_components['custom'][:5])  # Limit to 5
            rules.append(f"✅ Custom components available: {custom_components}")
        
        # Fallback rules
        rules.append("")
        rules.append("FALLBACK BEHAVIOR:")
        rules.append("- If shadcn/ui not available: Create self-contained components with standard Tailwind")
        rules.append("- If cn() not available: Use template literals or clsx for className composition")
        rules.append("- If components not available: Build from basic HTML elements")
        rules.append("- NEVER import from paths that don't exist")
        
        return "\n".join(rules)
    
    def build_user_prompt(self, user_request: str, context: Dict) -> str:
        """Build user prompt with context and keyword-specific instructions"""
        
        framework = context.get('framework', 'react')
        styling = context.get('styling', 'tailwind')
        design_tokens = context.get('design_tokens', {})
        
        # Get actual project tokens for the prompt
        colors = design_tokens.get('colors', [])
        spacing = design_tokens.get('spacing', [])
        typography = design_tokens.get('typography', [])
        
        # Build base prompt
        prompt = f"""Create a {framework} component using {styling}: {user_request}

REQUIREMENTS:
- Make it responsive and accessible
- Use modern design patterns
- Include proper TypeScript types
- Add appropriate animations and interactions
- Follow the project's design system (colors, spacing, typography)
- Ensure it works well on mobile and desktop
- Include proper error handling if applicable

PROJECT-SPECIFIC REQUIREMENTS:
- Use ONLY the project's color palette: {', '.join(colors) if colors else 'default Tailwind colors'}
- Use ONLY the project's spacing scale: {', '.join(spacing) if spacing else 'default Tailwind spacing'}
- Use ONLY the project's typography scale: {', '.join(typography) if typography else 'default Tailwind typography'}

Component request: {user_request}"""
        
        # Add keyword-specific instructions
        prompt = self.add_keyword_specific_instructions(prompt, user_request)
        
        return prompt
    
    def get_component_examples(self, component_type: str) -> str:
        """Get example patterns for specific component types"""
        
        examples = {
            'button': '''
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

const Button = ({ variant = 'primary', size = 'md', disabled, children, onClick }: ButtonProps) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50';
  
  const variants = {
    primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
    secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
    outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
    ghost: 'hover:bg-accent hover:text-accent-foreground'
  };
  
  const sizes = {
    sm: 'h-9 rounded-md px-3 text-sm',
    md: 'h-10 px-4 py-2',
    lg: 'h-11 rounded-md px-8 text-lg'
  };
  
  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
};''',
            
            'card': '''
interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

const Card = ({ children, className = '', hover = false }: CardProps) => {
  return (
    <div
      className={`
        rounded-lg border bg-card text-card-foreground shadow-sm
        ${hover ? 'transition-all hover:shadow-md hover:-translate-y-1' : ''}
        ${className}
      `}
    >
      {children}
    </div>
  );
};'''
        }
        
        return examples.get(component_type, '')
    
    def get_layout_patterns(self) -> str:
        """Get common layout patterns"""
        
        return '''
COMMON LAYOUT PATTERNS:

1. Container with centered content:
<div className="container mx-auto px-4 py-8 max-w-6xl">

2. Responsive grid:
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

3. Flex layout with spacing:
<div className="flex flex-col md:flex-row items-center justify-between gap-4">

4. Card grid with proper spacing:
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4">

5. Sidebar layout:
<div className="flex h-screen">
  <aside className="w-64 bg-gray-50 hidden md:block">
  <main className="flex-1 overflow-auto">
</div>'''
    
    def _build_design_system_section(self, framework, styling, component_library, colors, semantic_colors, color_structure, spacing, typography, shadows, border_radius):
        """Build enhanced design system section with actual project tokens"""
        
        # Enhanced color palette with usage examples
        color_section = self._build_color_section(colors, semantic_colors, color_structure)
        
        # Enhanced spacing system with actual values
        spacing_section = self._build_spacing_section(spacing)
        
        # Enhanced typography with actual scale
        typography_section = self._build_typography_section(typography)
        
        # Enhanced shadows and border radius
        effects_section = self._build_effects_section(shadows, border_radius)
        
        return f"""PROJECT DESIGN SYSTEM:
- Framework: {framework}
- Styling: {styling}
- Component Library: {component_library}

{color_section}

{spacing_section}

{typography_section}

{effects_section}

DESIGN SYSTEM USAGE RULES:
- ALWAYS use the project's color palette (listed above) instead of generic colors
- ALWAYS use the project's spacing scale (listed above) for consistent spacing
- ALWAYS use the project's typography scale (listed above) for text sizing
- ALWAYS use the project's shadow and border radius values (listed above)
- When in doubt, prefer the project's design tokens over Tailwind defaults"""
    
    def _build_color_section(self, colors, semantic_colors, color_structure):
        """Build enhanced color section with proper semantic usage examples"""
        
        if not colors and not semantic_colors:
            return "COLOR PALETTE: Using default Tailwind colors (blue, gray, green, red, yellow)"
        
        color_examples = []
        
        # Prioritize semantic colors from CSS @theme blocks
        if semantic_colors:
            color_examples.append("SEMANTIC COLORS (Use these for consistent theming):")
            for color in semantic_colors[:6]:  # Show more semantic colors
                color_examples.append(f"  - {color}: bg-{color}, text-{color}, border-{color}")
            
            # Add specific usage examples for common semantic colors
            if 'primary' in semantic_colors:
                color_examples.append("  Example: bg-primary text-white (primary buttons)")
            if 'background' in semantic_colors:
                color_examples.append("  Example: bg-background text-foreground (page backgrounds)")
            if 'foreground' in semantic_colors:
                color_examples.append("  Example: text-foreground (main text)")
            if 'muted' in semantic_colors:
                color_examples.append("  Example: text-muted (secondary text)")
        
        # Build custom color examples with proper structure
        if colors:
            color_examples.append("CUSTOM COLORS (Use these project colors):")
            for color in colors[:6]:  # Show more custom colors
                # Check if it's a color object (has shades) or single value
                if color in color_structure and isinstance(color_structure[color], dict):
                    # Color with shades (e.g., primary: { 50: '#f0f9ff', 500: '#0ea5e9' })
                    color_examples.append(f"  - {color}: bg-{color}-500, text-{color}-600, border-{color}-200")
                else:
                    # Single color value (e.g., accent: '#f59e0b')
                    color_examples.append(f"  - {color}: bg-{color}, text-{color}, border-{color}")
        
        examples_text = "\n".join(color_examples)
        
        # Determine if we have CSS-parsed semantic colors
        has_css_semantic = len(semantic_colors) > 0
        primary_color = semantic_colors[0] if semantic_colors else (colors[0] if colors else 'primary')
        secondary_color = semantic_colors[1] if len(semantic_colors) > 1 else (colors[1] if len(colors) > 1 else 'secondary')
        
        return f"""COLOR PALETTE (MANDATORY - Use ONLY these project colors):
{examples_text}

CRITICAL COLOR USAGE RULES:
- NEVER use hardcoded colors like bg-blue-500, text-red-600, etc.
- ALWAYS use colors from the project palette above
- {'FOR SEMANTIC COLORS: Use bg-primary, text-foreground (no shade numbers)' if has_css_semantic else 'FOR CUSTOM COLORS: Use appropriate shade numbers'}
- {'This project uses @theme blocks with semantic color names' if has_css_semantic else 'This project uses tailwind.config.js with custom colors'}

USAGE EXAMPLES:
- Primary buttons: bg-{primary_color} text-white
- Secondary buttons: bg-{secondary_color}
- Text: text-{primary_color if has_css_semantic else primary_color + '-600'}
- Backgrounds: bg-{'background' if 'background' in semantic_colors else secondary_color}

ABSOLUTELY FORBIDDEN:
- Do NOT use generic colors like bg-blue-500, text-red-600, bg-green-400
- Do NOT use colors not in the project palette above
- Do NOT mix semantic and shade-based naming incorrectly"""
    
    def _build_spacing_section(self, spacing):
        """Build enhanced spacing section with actual values"""
        
        if not spacing:
            return "SPACING SYSTEM: Using default Tailwind spacing (4, 8, 16, 24, 32)"
        
        spacing_examples = []
        for space in spacing[:8]:  # Limit to 8 spacing values
            spacing_examples.append(f"  - {space}: p-{space}, m-{space}, gap-{space}, space-y-{space}")
        
        return f"""SPACING SYSTEM (Use these project spacing values):
{chr(10).join(spacing_examples)}

USAGE EXAMPLES:
- Component padding: p-{spacing[0] if spacing else '4'}, px-{spacing[1] if len(spacing) > 1 else '6'}, py-{spacing[0] if spacing else '4'}
- Component margins: m-{spacing[1] if len(spacing) > 1 else '4'}, mb-{spacing[2] if len(spacing) > 2 else '8'}
- Grid gaps: gap-{spacing[1] if len(spacing) > 1 else '4'}, gap-x-{spacing[0] if spacing else '4'}, gap-y-{spacing[1] if len(spacing) > 1 else '6'}
- Stack spacing: space-y-{spacing[1] if len(spacing) > 1 else '4'}, space-x-{spacing[0] if spacing else '4'}"""
    
    def _build_typography_section(self, typography):
        """Build enhanced typography section with actual scale"""
        
        if not typography:
            return "TYPOGRAPHY SCALE: Using default Tailwind typography (sm, base, lg, xl, 2xl)"
        
        typography_examples = []
        for typo in typography[:6]:  # Limit to 6 typography values
            typography_examples.append(f"  - {typo}: text-{typo}")
        
        return f"""TYPOGRAPHY SCALE (Use these project text sizes):
{chr(10).join(typography_examples)}

USAGE EXAMPLES:
- Headings: text-{typography[-1] if typography else '2xl'} font-bold, text-{typography[-2] if len(typography) > 1 else 'xl'} font-semibold
- Body text: text-{typography[1] if len(typography) > 1 else 'base'}, text-{typography[0] if typography else 'sm'} text-gray-600
- Small text: text-{typography[0] if typography else 'sm'} text-gray-500"""
    
    def _build_effects_section(self, shadows, border_radius):
        """Build enhanced effects section with actual values"""
        
        shadow_list = ', '.join(shadows[:4]) if shadows else 'sm, md, lg'
        radius_list = ', '.join(border_radius[:4]) if border_radius else 'sm, md, lg'
        
        return f"""VISUAL EFFECTS:
- Shadows: {shadow_list}
- Border Radius: {radius_list}

USAGE EXAMPLES:
- Cards: shadow-{shadows[0] if shadows else 'sm'} rounded-{border_radius[1] if len(border_radius) > 1 else 'md'}
- Buttons: shadow-{shadows[0] if shadows else 'sm'} rounded-{border_radius[0] if border_radius else 'sm'} hover:shadow-{shadows[1] if len(shadows) > 1 else 'md'}
- Modals: shadow-{shadows[-1] if shadows else 'lg'} rounded-{border_radius[-1] if border_radius else 'lg'}"""
    
    def add_keyword_specific_instructions(self, prompt, user_request):
        """Add specific instructions based on keywords in user request"""
        
        keyword_instructions = {
            'form': """
FORM-SPECIFIC REQUIREMENTS:
- Include proper form validation with error states
- Use semantic form elements (label, input, fieldset)
- Add proper ARIA labels and descriptions
- Include loading states for form submission
- Use proper input types (email, password, tel, etc.)
- Add proper focus management and keyboard navigation""",
            
            'modal': """
MODAL-SPECIFIC REQUIREMENTS:
- Include proper focus management (trap focus, return focus)
- Add proper ARIA attributes (role="dialog", aria-labelledby, aria-describedby)
- Include backdrop click to close and escape key handling
- Add proper z-index layering
- Include smooth open/close animations
- Add proper scrolling behavior for long content""",
            
            'navigation': """
NAVIGATION-SPECIFIC REQUIREMENTS:
- Include proper keyboard navigation (arrow keys, tab, enter)
- Add proper ARIA attributes (role="navigation", aria-current)
- Include mobile-responsive behavior (hamburger menu)
- Add proper active and hover states
- Include proper semantic HTML structure
- Add proper focus indicators""",
            
            'table': """
TABLE-SPECIFIC REQUIREMENTS:
- Use proper semantic table elements (thead, tbody, tfoot, th, td)
- Include proper ARIA attributes (role="table", aria-sort)
- Add proper responsive behavior (horizontal scroll, stacked layout)
- Include sorting, filtering, and pagination if needed
- Add proper hover and selection states
- Include proper loading and empty states""",
            
            'card': """
CARD-SPECIFIC REQUIREMENTS:
- Include proper hover effects and interactions
- Add proper semantic structure (article, section, header, footer)
- Include proper spacing and visual hierarchy
- Add proper action areas (buttons, links)
- Include proper image handling and aspect ratios
- Add proper responsive behavior""",
            
            'button': """
BUTTON-SPECIFIC REQUIREMENTS:
- Include proper variant system (primary, secondary, outline, ghost)
- Add proper size variants (sm, md, lg)
- Include proper disabled and loading states
- Add proper hover, focus, and active states
- Include proper ARIA attributes when needed
- Add proper icon support and positioning"""
        }
        
        # Add keyword-specific instructions
        for keyword, instructions in keyword_instructions.items():
            if keyword in user_request.lower():
                prompt += instructions
        
        return prompt