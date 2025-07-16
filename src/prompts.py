from typing import Dict

class UIPromptBuilder:
    """Builds UI-focused system prompts for LLM generation"""
    
    def build_ui_system_prompt(self, context: Dict) -> str:
        """Build comprehensive UI-focused system prompt"""
        
        framework = context.get('framework', 'react')
        styling = context.get('styling', 'tailwind')
        component_library = context.get('component_library', 'none')
        design_tokens = context.get('design_tokens', {})
        
        colors = ', '.join(design_tokens.get('colors', ['blue', 'gray', 'green']))
        spacing = ', '.join(design_tokens.get('spacing', ['4', '8', '16']))
        typography = ', '.join(design_tokens.get('typography', ['sm', 'base', 'lg']))
        
        prompt = f"""You are a UI/UX expert specializing in React + Tailwind CSS component generation.

PROJECT DESIGN SYSTEM:
- Framework: {framework}
- Styling: {styling}
- Component Library: {component_library}
- Color Palette: {colors}
- Spacing System: {spacing}
- Typography Scale: {typography}

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
    
    def build_user_prompt(self, user_request: str, context: Dict) -> str:
        """Build user prompt with context"""
        
        framework = context.get('framework', 'react')
        styling = context.get('styling', 'tailwind')
        
        prompt = f"""Create a {framework} component using {styling}: {user_request}

Requirements:
- Make it responsive and accessible
- Use modern design patterns
- Include proper TypeScript types
- Add appropriate animations and interactions
- Follow the project's design system (colors, spacing, typography)
- Ensure it works well on mobile and desktop
- Include proper error handling if applicable

Component request: {user_request}"""
        
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