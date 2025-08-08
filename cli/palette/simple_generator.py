#!/usr/bin/env python3
"""
Simple, reliable UI component generator
No MCP, no complex pipelines, just working generation
"""

import os
from typing import Dict, Optional
from openai import OpenAI


class SimpleGenerator:
    """Simplified component generator that actually works"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")
        
        self.client = OpenAI(api_key=api_key)
    
    def generate_component(self, prompt: str, context: Dict = None) -> str:
        """Generate a React component from a prompt"""
        
        # Build effective prompt
        system_prompt = self._build_system_prompt(context or {})
        user_prompt = self._build_user_prompt(prompt, context or {})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise RuntimeError(f"Component generation failed: {e}")
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt based on project context"""
        
        framework = context.get('framework', 'react')
        styling = context.get('styling', 'tailwind')
        ui_library = context.get('ui_library', 'none')
        
        base_prompt = f"""You are an expert React developer creating high-quality, professional UI components.

REQUIREMENTS:
- Framework: {framework.title()}
- Styling: {styling.title()}
- UI Library: {ui_library if ui_library != 'none' else 'None'}
- Generate clean, production-ready code
- Include TypeScript interfaces
- Follow modern React patterns (functional components, hooks)
- Ensure accessibility (ARIA labels, keyboard navigation)
- Include usage example in comments

CODE STYLE:
- Use clear, descriptive variable names
- Include proper TypeScript types
- Add helpful comments
- Export component as default
- Keep components focused and reusable"""

        # Add styling-specific instructions
        if styling == 'tailwind':
            base_prompt += """

TAILWIND CSS REQUIREMENTS:
- Use Tailwind utility classes exclusively
- Apply responsive design (sm:, md:, lg: prefixes)
- Use semantic color classes (primary, secondary, accent)
- Include hover and focus states
- Follow 8pt grid system for spacing (p-2, p-4, p-6, p-8)
- Ensure proper contrast ratios"""

        # Add UI library specific instructions
        if ui_library == 'shadcn/ui':
            base_prompt += """

SHADCN/UI REQUIREMENTS:
- Use shadcn/ui components and patterns
- Import from "@/components/ui/"
- Follow shadcn/ui design system
- Use class-variance-authority for variants
- Include proper button variants (default, destructive, outline, secondary, ghost)
- Apply shadcn/ui color system and spacing"""

        return base_prompt
    
    def _build_user_prompt(self, prompt: str, context: Dict) -> str:
        """Build user prompt with context"""
        
        user_prompt = f"""Create a {context.get('framework', 'React')} component: {prompt}

SPECIFIC REQUIREMENTS:
- Make it visually appealing and professional
- Include proper error handling
- Add loading states if applicable
- Ensure mobile responsiveness
- Include accessibility features
- Follow modern design principles

Return only the component code with usage example. No explanations needed."""

        return user_prompt


class ShadcnGenerator(SimpleGenerator):
    """Specialized generator for shadcn/ui components"""
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Enhanced system prompt for shadcn/ui generation"""
        
        return """You are an expert React developer specializing in shadcn/ui components.

SHADCN/UI REQUIREMENTS:
- Use only shadcn/ui components and patterns
- Import components from "@/components/ui/"
- Follow shadcn/ui design system exactly
- Use class-variance-authority (cva) for component variants
- Apply proper Tailwind CSS classes
- Include all standard variants (default, destructive, outline, secondary, ghost, link)
- Use proper sizing (sm, default, lg, xl)
- Include hover, focus, and active states
- Apply shadcn/ui color tokens

COMPONENT STRUCTURE:
```typescript
import { cn } from "@/lib/utils"
import { cva, type VariantProps } from "class-variance-authority"

const componentVariants = cva(
  "base-classes",
  {
    variants: {
      variant: {
        default: "variant-classes",
        // ... other variants
      },
      size: {
        sm: "size-classes",
        // ... other sizes
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
)

export interface ComponentProps
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof componentVariants> {
  // additional props
}

const Component = React.forwardRef<HTMLElement, ComponentProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <element
        className={cn(componentVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Component.displayName = "Component"

export { Component, componentVariants }
```

DESIGN PRINCIPLES:
- Clean, modern aesthetics
- Subtle shadows and rounded corners
- Consistent spacing (8pt grid)
- Professional color palette
- Smooth transitions and hover effects
- Accessibility-first design"""
    
    def _build_user_prompt(self, prompt: str, context: Dict) -> str:
        """Enhanced user prompt for shadcn/ui"""
        
        return f"""Create a beautiful shadcn/ui component: {prompt}

REQUIREMENTS:
- Follow shadcn/ui patterns exactly
- Include all necessary variants and sizes
- Use proper TypeScript interfaces
- Add accessibility features (ARIA labels, keyboard navigation)
- Include smooth animations and transitions
- Apply modern design principles
- Make it production-ready

Return the complete component with proper imports and exports."""


# Factory function for easy usage
def create_generator(ui_library: str = "none", model: str = "gpt-4o-mini") -> SimpleGenerator:
    """Create appropriate generator based on UI library"""
    
    if ui_library == "shadcn/ui":
        return ShadcnGenerator(model)
    else:
        return SimpleGenerator(model)