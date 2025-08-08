#!/usr/bin/env python3
"""
shadcn/ui MCP Server for Palette Component Generation
Provides comprehensive shadcn/ui component knowledge and OpenAI optimization.
"""

import json
import sys
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the parent directory to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from palette.mcp.ui_library_server_base import UILibraryMCPServer, UIComponent, UILibraryContext, UILibraryType


class ShadcnUIServer(UILibraryMCPServer):
    """shadcn/ui MCP server with comprehensive component knowledge."""
    
    def __init__(self, project_path: str = "."):
        super().__init__(project_path)
        self.library_type = UILibraryType.SHADCN_UI
        
        # Initialize shadcn/ui specific knowledge
        self._initialize_shadcn_knowledge()
    
    def _initialize_shadcn_knowledge(self):
        """Initialize comprehensive shadcn/ui component knowledge."""
        
        # shadcn/ui component catalog
        self.component_catalog = {
            "Button": {
                "name": "Button",
                "description": "A customizable button component built on Radix UI with Tailwind CSS styling",
                "category": "ui",
                "props": [
                    "variant", "size", "asChild", "className", "disabled", 
                    "onClick", "type", "children"
                ],
                "examples": [
                    {
                        "title": "Primary Button",
                        "code": '<Button variant="default">Click me</Button>'
                    },
                    {
                        "title": "Secondary Button", 
                        "code": '<Button variant="secondary">Secondary</Button>'
                    },
                    {
                        "title": "Destructive Button",
                        "code": '<Button variant="destructive">Delete</Button>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation support",
                    "Screen reader compatible",
                    "Focus management",
                    "ARIA attributes from Radix UI"
                ],
                "styling": {
                    "variants": ["default", "destructive", "outline", "secondary", "ghost", "link"],
                    "sizes": ["default", "sm", "lg", "icon"]
                }
            },
            
            "Input": {
                "name": "Input",
                "description": "A styled input component with Tailwind CSS classes",
                "category": "ui",
                "props": [
                    "type", "placeholder", "value", "onChange", "disabled", 
                    "className", "id", "name", "required"
                ],
                "examples": [
                    {
                        "title": "Basic Input",
                        "code": '<Input type="text" placeholder="Enter your name" />'
                    },
                    {
                        "title": "Email Input",
                        "code": '<Input type="email" placeholder="your@email.com" />'
                    }
                ],
                "accessibility": [
                    "Proper label association",
                    "Keyboard navigation",
                    "Screen reader support"
                ],
                "styling": {
                    "variants": ["default", "file"],
                    "states": ["default", "focus", "disabled", "invalid"]
                }
            },
            
            "Card": {
                "name": "Card",
                "description": "A versatile card container with header, content, and footer sections",
                "category": "ui",
                "props": ["className", "children"],
                "subcomponents": ["CardHeader", "CardContent", "CardFooter", "CardTitle", "CardDescription"],
                "examples": [
                    {
                        "title": "Basic Card",
                        "code": '<Card><CardHeader><CardTitle>Card Title</CardTitle></CardHeader><CardContent>Card content goes here</CardContent></Card>'
                    },
                    {
                        "title": "Card with Footer",
                        "code": '<Card><CardHeader><CardTitle>Title</CardTitle><CardDescription>Description</CardDescription></CardHeader><CardContent>Content</CardContent><CardFooter>Footer actions</CardFooter></Card>'
                    }
                ],
                "accessibility": [
                    "Semantic structure",
                    "Keyboard navigation",
                    "Screen reader support"
                ],
                "styling": {
                    "variants": ["default"],
                    "sections": ["header", "content", "footer"]
                }
            },
            
            "Dialog": {
                "name": "Dialog",
                "description": "A modal dialog built on Radix UI Dialog primitive",
                "category": "ui",
                "props": ["open", "onOpenChange", "children"],
                "subcomponents": ["DialogTrigger", "DialogContent", "DialogHeader", "DialogTitle", "DialogDescription", "DialogFooter", "DialogClose"],
                "examples": [
                    {
                        "title": "Basic Dialog",
                        "code": '<Dialog><DialogTrigger asChild><Button>Open Dialog</Button></DialogTrigger><DialogContent><DialogHeader><DialogTitle>Dialog Title</DialogTitle></DialogHeader><DialogDescription>Dialog description here</DialogDescription></DialogContent></Dialog>'
                    }
                ],
                "accessibility": [
                    "Focus trap",
                    "Keyboard navigation",
                    "Screen reader announcements",
                    "Escape key handling",
                    "ARIA modal from Radix UI"
                ],
                "styling": {
                    "variants": ["default"],
                    "positions": ["center", "top", "bottom"]
                }
            },
            
            "Badge": {
                "name": "Badge",
                "description": "A small status indicator or label component",
                "category": "ui",
                "props": ["variant", "className", "children"],
                "examples": [
                    {
                        "title": "Default Badge",
                        "code": '<Badge>New</Badge>'
                    },
                    {
                        "title": "Secondary Badge",
                        "code": '<Badge variant="secondary">Beta</Badge>'
                    },
                    {
                        "title": "Destructive Badge",
                        "code": '<Badge variant="destructive">Error</Badge>'
                    }
                ],
                "accessibility": [
                    "Screen reader support",
                    "Semantic meaning"
                ],
                "styling": {
                    "variants": ["default", "secondary", "destructive", "outline"]
                }
            },
            
            "Select": {
                "name": "Select",
                "description": "A customizable select component built on Radix UI Select",
                "category": "ui",
                "props": ["value", "onValueChange", "disabled", "children"],
                "subcomponents": ["SelectTrigger", "SelectContent", "SelectItem", "SelectValue", "SelectSeparator", "SelectGroup", "SelectLabel"],
                "examples": [
                    {
                        "title": "Basic Select",
                        "code": '<Select><SelectTrigger><SelectValue placeholder="Select an option" /></SelectTrigger><SelectContent><SelectItem value="option1">Option 1</SelectItem><SelectItem value="option2">Option 2</SelectItem></SelectContent></Select>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Screen reader support",
                    "ARIA attributes from Radix UI",
                    "Focus management"
                ],
                "styling": {
                    "variants": ["default"],
                    "states": ["open", "closed", "disabled"]
                }
            },
            
            "Textarea": {
                "name": "Textarea",
                "description": "A multi-line text input component with Tailwind styling",
                "category": "ui",
                "props": [
                    "placeholder", "value", "onChange", "disabled", "rows", 
                    "className", "id", "name", "required"
                ],
                "examples": [
                    {
                        "title": "Basic Textarea",
                        "code": '<Textarea placeholder="Enter your message..." />'
                    },
                    {
                        "title": "Textarea with Rows",
                        "code": '<Textarea placeholder="Description..." rows={4} />'
                    }
                ],
                "accessibility": [
                    "Proper label association",
                    "Keyboard navigation",
                    "Screen reader support"
                ],
                "styling": {
                    "variants": ["default"],
                    "states": ["default", "focus", "disabled"]
                }
            },
            
            "Checkbox": {
                "name": "Checkbox", 
                "description": "A checkbox component built on Radix UI Checkbox",
                "category": "ui",
                "props": ["checked", "onCheckedChange", "disabled", "id", "className"],
                "examples": [
                    {
                        "title": "Basic Checkbox",
                        "code": '<Checkbox id="terms" /><label htmlFor="terms">Accept terms and conditions</label>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Screen reader support", 
                    "ARIA attributes from Radix UI",
                    "Label association"
                ],
                "styling": {
                    "variants": ["default"],
                    "states": ["checked", "unchecked", "indeterminate", "disabled"]
                }
            },
            
            "RadioGroup": {
                "name": "RadioGroup",
                "description": "A radio group component built on Radix UI RadioGroup",
                "category": "ui", 
                "props": ["value", "onValueChange", "disabled", "className", "children"],
                "subcomponents": ["RadioGroupItem"],
                "examples": [
                    {
                        "title": "Basic Radio Group",
                        "code": '<RadioGroup defaultValue="option1"><div className="flex items-center space-x-2"><RadioGroupItem value="option1" id="r1" /><label htmlFor="r1">Option 1</label></div></RadioGroup>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Screen reader support",
                    "ARIA attributes from Radix UI",
                    "Label associations"
                ],
                "styling": {
                    "variants": ["default"],
                    "states": ["selected", "unselected", "disabled"]
                }
            },
            
            "Switch": {
                "name": "Switch",
                "description": "A toggle switch component built on Radix UI Switch",
                "category": "ui",
                "props": ["checked", "onCheckedChange", "disabled", "id", "className"],
                "examples": [
                    {
                        "title": "Basic Switch",
                        "code": '<Switch id="airplane-mode" /><label htmlFor="airplane-mode">Airplane Mode</label>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Screen reader support",
                    "ARIA attributes from Radix UI",
                    "Label association"
                ],
                "styling": {
                    "variants": ["default"],
                    "states": ["checked", "unchecked", "disabled"]
                }
            },
            
            "Label": {
                "name": "Label",
                "description": "A label component with proper styling and accessibility",
                "category": "ui",
                "props": ["htmlFor", "className", "children"],
                "examples": [
                    {
                        "title": "Basic Label",
                        "code": '<Label htmlFor="email">Email Address</Label>'
                    }
                ],
                "accessibility": [
                    "Proper form control association",
                    "Screen reader support"
                ],
                "styling": {
                    "variants": ["default"]
                }
            },
            
            "Separator": {
                "name": "Separator",
                "description": "A visual separator component built on Radix UI Separator",
                "category": "ui",
                "props": ["orientation", "decorative", "className"],
                "examples": [
                    {
                        "title": "Horizontal Separator",
                        "code": '<Separator className="my-4" />'
                    },
                    {
                        "title": "Vertical Separator", 
                        "code": '<Separator orientation="vertical" className="mx-4" />'
                    }
                ],
                "accessibility": [
                    "Semantic separation",
                    "Screen reader support",
                    "ARIA attributes from Radix UI"
                ],
                "styling": {
                    "variants": ["default"],
                    "orientations": ["horizontal", "vertical"]
                }
            },
            
            "Avatar": {
                "name": "Avatar",
                "description": "An avatar component for displaying user profile images",
                "category": "ui",
                "props": ["className", "children"],
                "subcomponents": ["AvatarImage", "AvatarFallback"],
                "examples": [
                    {
                        "title": "Avatar with Image",
                        "code": '<Avatar><AvatarImage src="/avatars/01.png" alt="@username" /><AvatarFallback>CN</AvatarFallback></Avatar>'
                    }
                ],
                "accessibility": [
                    "Alt text support",
                    "Screen reader friendly",
                    "Fallback handling"
                ],
                "styling": {
                    "variants": ["default"],
                    "sizes": ["sm", "default", "lg"]
                }
            },
            
            "Accordion": {
                "name": "Accordion",
                "description": "A collapsible accordion component built on Radix UI Accordion",
                "category": "ui",
                "props": ["type", "value", "onValueChange", "collapsible", "className", "children"],
                "subcomponents": ["AccordionItem", "AccordionTrigger", "AccordionContent"],
                "examples": [
                    {
                        "title": "Basic Accordion",
                        "code": '<Accordion type="single" collapsible><AccordionItem value="item-1"><AccordionTrigger>Is it accessible?</AccordionTrigger><AccordionContent>Yes. It adheres to the WAI-ARIA design pattern.</AccordionContent></AccordionItem></Accordion>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Screen reader support",
                    "ARIA attributes from Radix UI",
                    "Focus management"
                ],
                "styling": {
                    "variants": ["default"],
                    "types": ["single", "multiple"]
                }
            },
            
            "Tabs": {
                "name": "Tabs",
                "description": "A tabs component built on Radix UI Tabs",
                "category": "ui",
                "props": ["value", "onValueChange", "orientation", "className", "children"],
                "subcomponents": ["TabsList", "TabsTrigger", "TabsContent"],
                "examples": [
                    {
                        "title": "Basic Tabs",
                        "code": '<Tabs defaultValue="account"><TabsList><TabsTrigger value="account">Account</TabsTrigger><TabsTrigger value="password">Password</TabsTrigger></TabsList><TabsContent value="account">Account content</TabsContent></Tabs>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Screen reader support",
                    "ARIA attributes from Radix UI",
                    "Focus management"
                ],
                "styling": {
                    "variants": ["default"],
                    "orientations": ["horizontal", "vertical"]
                }
            }
        }
        
        # shadcn/ui design tokens (based on Tailwind CSS)
        self.design_tokens = {
            "colors": {
                "background": "hsl(0 0% 100%)",
                "foreground": "hsl(222.2 84% 4.9%)",
                "card": "hsl(0 0% 100%)",
                "card-foreground": "hsl(222.2 84% 4.9%)",
                "popover": "hsl(0 0% 100%)",
                "popover-foreground": "hsl(222.2 84% 4.9%)",
                "primary": "hsl(222.2 47.4% 11.2%)",
                "primary-foreground": "hsl(210 40% 98%)",
                "secondary": "hsl(210 40% 96%)",
                "secondary-foreground": "hsl(222.2 47.4% 11.2%)",
                "muted": "hsl(210 40% 96%)",
                "muted-foreground": "hsl(215.4 16.3% 46.9%)",
                "accent": "hsl(210 40% 96%)",
                "accent-foreground": "hsl(222.2 47.4% 11.2%)",
                "destructive": "hsl(0 84.2% 60.2%)",
                "destructive-foreground": "hsl(210 40% 98%)",
                "border": "hsl(214.3 31.8% 91.4%)",
                "input": "hsl(214.3 31.8% 91.4%)",
                "ring": "hsl(222.2 47.4% 11.2%)"
            },
            "spacing": {
                "xs": "0.25rem",
                "sm": "0.5rem", 
                "md": "1rem",
                "lg": "1.5rem",
                "xl": "2rem",
                "2xl": "3rem"
            },
            "typography": {
                "fontFamily": {
                    "sans": ["Inter", "ui-sans-serif", "system-ui"],
                    "mono": ["ui-monospace", "SFMono-Regular"]
                },
                "fontSize": {
                    "xs": "0.75rem",
                    "sm": "0.875rem",
                    "base": "1rem", 
                    "lg": "1.125rem",
                    "xl": "1.25rem",
                    "2xl": "1.5rem",
                    "3xl": "1.875rem",
                    "4xl": "2.25rem"
                }
            },
            "borderRadius": {
                "sm": "0.125rem",
                "md": "0.375rem",
                "lg": "0.5rem",
                "xl": "0.75rem"
            },
            "animation": {
                "accordion-down": "accordion-down 0.2s ease-out",
                "accordion-up": "accordion-up 0.2s ease-out"
            }
        }
        
        # shadcn/ui best practices
        self.best_practices = [
            "Use Tailwind CSS for styling with the provided design tokens",
            "Leverage Radix UI primitives for accessibility and behavior",
            "Use CSS variables for theming and dark mode support",
            "Follow component composition patterns with subcomponents",
            "Use the cn() utility function for conditional classes",
            "Import components individually to optimize bundle size",
            "Customize components by modifying the source code directly",
            "Use the asChild prop pattern for flexible component composition",
            "Follow Tailwind's utility-first approach for styling",
            "Implement proper TypeScript interfaces for all props"
        ]
    
    async def get_component_catalog(self) -> List[UIComponent]:
        """Get comprehensive shadcn/ui component catalog."""
        components = []
        
        for name, info in self.component_catalog.items():
            component = UIComponent(
                name=info["name"],
                description=info["description"],
                category=info["category"],
                props=info["props"],
                examples=info["examples"],
                accessibility_notes=info["accessibility"],
                styling_options=info["styling"]
            )
            components.append(component)
        
        return components
    
    async def get_design_tokens(self) -> Dict[str, Any]:
        """Get shadcn/ui design tokens."""
        return self.design_tokens
    
    async def get_openai_system_prompt(self) -> str:
        """Get OpenAI-optimized system prompt for shadcn/ui."""
        return """You are an expert shadcn/ui developer who creates production-ready React components using shadcn/ui, Radix UI, and Tailwind CSS.

**shadcn/ui Standards:**
- Use shadcn/ui components with proper imports from './components/ui/*'
- Build on Radix UI primitives for accessibility and behavior
- Use Tailwind CSS with the shadcn/ui design system
- Follow the utility-first CSS approach with semantic color variables
- Use the cn() utility function for conditional styling

**Component Quality Requirements:**
- Write TypeScript by default with comprehensive prop interfaces
- Use Radix UI primitives for complex interactions and accessibility
- Follow the shadcn/ui component composition patterns
- Implement proper keyboard navigation and screen reader support
- Use semantic HTML with proper ARIA attributes from Radix UI

**Design System Principles:**
- Use CSS variables (hsl values) for theming and dark mode support
- Follow the shadcn/ui color palette with semantic naming
- Implement consistent spacing using Tailwind's spacing scale
- Use appropriate border radius values from the design system
- Follow proper typography hierarchy with font sizes and weights

**Code Structure:**
- Export components as default exports with named interfaces
- Use the asChild prop pattern for flexible component composition
- Include proper imports for Radix UI primitives and Tailwind classes
- Add helpful JSDoc comments for complex component logic
- Handle edge cases with proper fallbacks and error states

**Accessibility Standards:**
- Leverage Radix UI's built-in accessibility features
- Ensure keyboard navigation works for all interactive elements
- Use proper ARIA labels, descriptions, and roles
- Implement focus management and focus trapping where needed
- Support screen readers with semantic markup and announcements

**Styling Guidelines:**
- Use Tailwind utility classes with shadcn/ui design tokens
- Apply conditional styling with the cn() utility function
- Use CSS variables for theming (--background, --foreground, etc.)
- Implement hover, focus, and active states consistently
- Support both light and dark mode through CSS variables

Generate clean, accessible shadcn/ui components that follow these standards."""

    async def get_openai_examples(self) -> List[Dict[str, str]]:
        """Get shadcn/ui examples optimized for OpenAI prompts."""
        return [
            {
                "prompt": "Create a shadcn/ui button component with variants",
                "response": '''import React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };'''
            },
            {
                "prompt": "Build a shadcn/ui dialog component",
                "response": '''import React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

const Dialog = DialogPrimitive.Root;
const DialogTrigger = DialogPrimitive.Trigger;
const DialogPortal = DialogPrimitive.Portal;
const DialogClose = DialogPrimitive.Close;

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-background/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg",
        className
      )}
      {...props}
    >
      {children}
      <DialogPrimitive.Close className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogPrimitive.Close>
    </DialogPrimitive.Content>
  </DialogPortal>
));
DialogContent.displayName = DialogPrimitive.Content.displayName;

const DialogHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col space-y-1.5 text-center sm:text-left",
      className
    )}
    {...props}
  />
);
DialogHeader.displayName = "DialogHeader";

const DialogFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className
    )}
    {...props}
  />
);
DialogFooter.displayName = "DialogFooter";

const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;

export {
  Dialog,
  DialogPortal,
  DialogOverlay,
  DialogClose,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
};'''
            },
            {
                "prompt": "Create a shadcn/ui form with validation",
                "response": '''import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

const formSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address'),
  message: z.string().min(10, 'Message must be at least 10 characters'),
});

type FormData = z.infer<typeof formSchema>;

interface ContactFormProps {
  onSubmit: (data: FormData) => Promise<void>;
}

const ContactForm: React.FC<ContactFormProps> = ({ onSubmit }) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const handleFormSubmit = async (data: FormData) => {
    try {
      setIsSubmitting(true);
      setSubmitError(null);
      await onSubmit(data);
      reset();
    } catch (error) {
      setSubmitError('Failed to submit form. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Contact Us</CardTitle>
      </CardHeader>
      <CardContent>
        {submitError && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        )}
        
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              {...register('name')}
              className={errors.name ? 'border-destructive' : ''}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              {...register('email')}
              className={errors.email ? 'border-destructive' : ''}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <textarea
              id="message"
              {...register('message')}
              rows={4}
              className={cn(
                "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                errors.message ? 'border-destructive' : ''
              )}
            />
            {errors.message && (
              <p className="text-sm text-destructive">{errors.message.message}</p>
            )}
          </div>

          <Button 
            type="submit" 
            className="w-full" 
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Send Message'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default ContactForm;'''
            }
        ]
    
    # Implement all the required tool methods
    
    async def get_component_info(self, component_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific shadcn/ui component."""
        if component_name.lower() == "all":
            return {
                "components": list(self.component_catalog.keys()),
                "total": len(self.component_catalog),
                "categories": list(set(info["category"] for info in self.component_catalog.values()))
            }
        
        if component_name in self.component_catalog:
            return self.component_catalog[component_name]
        
        return {"error": f"Component '{component_name}' not found in shadcn/ui catalog"}
    
    async def search_components(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for shadcn/ui components matching the query."""
        query_lower = query.lower()
        results = []
        
        for name, info in self.component_catalog.items():
            score = 0
            
            # Match component name
            if query_lower in name.lower():
                score += 10
            
            # Match description
            if query_lower in info["description"].lower():
                score += 5
            
            # Match category
            if query_lower in info["category"].lower():
                score += 3
            
            # Match props
            for prop in info["props"]:
                if query_lower in prop.lower():
                    score += 2
                    break
            
            if score > 0:
                results.append({
                    "name": name,
                    "description": info["description"],
                    "category": info["category"],
                    "score": score,
                    "props": info["props"][:5]  # First 5 props
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:limit]
        
        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
    
    async def validate_library_usage(self, component_code: str, strict_mode: bool = False) -> Dict[str, Any]:
        """Validate shadcn/ui usage in component code."""
        issues = []
        suggestions = []
        score = 100
        
        # Check for proper shadcn/ui imports
        if "@/components/ui/" not in component_code and "./components/ui/" not in component_code:
            issues.append("Missing shadcn/ui component imports from '@/components/ui/*'")
            score -= 20
        
        # Check for Radix UI usage
        if "@radix-ui/" not in component_code and ("Dialog" in component_code or "Select" in component_code):
            suggestions.append("Consider using Radix UI primitives for complex components")
        
        # Check for cn() utility usage
        if "className=" in component_code and "cn(" not in component_code:
            suggestions.append("Consider using the cn() utility for conditional styling")
            score -= 5
        
        # Check for proper TypeScript interfaces
        if "interface" not in component_code and strict_mode:
            issues.append("Missing TypeScript interface definitions")
            score -= 15
        
        # Check for Tailwind classes
        if "className=" in component_code and not any(tw_class in component_code for tw_class in ["flex", "grid", "text-", "bg-", "border", "rounded"]):
            suggestions.append("Consider using Tailwind CSS utility classes for styling")
        
        # Check for accessibility
        if "aria-" not in component_code and ("button" in component_code.lower() or "input" in component_code.lower()):
            suggestions.append("Consider adding ARIA attributes for better accessibility")
            score -= 5
        
        return {
            "valid": len(issues) == 0,
            "score": max(score, 0),
            "issues": issues,
            "suggestions": suggestions,
            "library": "shadcn/ui"
        }
    
    async def generate_openai_prompt(self, 
                                   user_request: str, 
                                   component_type: Optional[str] = None,
                                   complexity_level: str = "intermediate") -> Dict[str, Any]:
        """Generate OpenAI-optimized prompt with shadcn/ui context."""
        
        system_prompt = await self.get_openai_system_prompt()
        
        # Build enhanced user prompt
        enhanced_prompt = f"**User Request:** {user_request}\n\n"
        
        if component_type:
            enhanced_prompt += f"**Component Type:** {component_type}\n"
            
            # Find relevant shadcn/ui components
            search_results = await self.search_components(component_type, limit=3)
            if search_results["results"]:
                enhanced_prompt += f"**Relevant shadcn/ui Components:**\n"
                for result in search_results["results"][:2]:
                    enhanced_prompt += f"- {result['name']}: {result['description']}\n"
                enhanced_prompt += "\n"
        
        enhanced_prompt += f"**Complexity Level:** {complexity_level}\n\n"
        
        # Add shadcn/ui specific guidance
        enhanced_prompt += "**shadcn/ui Guidelines:**\n"
        enhanced_prompt += "- Use shadcn/ui components with proper imports from '@/components/ui/*'\n"
        enhanced_prompt += "- Build on Radix UI primitives with Tailwind CSS styling\n"
        enhanced_prompt += "- Use the cn() utility function for conditional classes\n"
        enhanced_prompt += "- Follow component composition patterns with subcomponents\n"
        enhanced_prompt += "- Use CSS variables for theming and design tokens\n\n"
        
        # Add design tokens context
        enhanced_prompt += "**Available Design Tokens:**\n"
        enhanced_prompt += f"- Colors: primary, secondary, destructive, muted, accent, border\n"
        enhanced_prompt += f"- Sizes: sm, default, lg, icon (for buttons)\n"
        enhanced_prompt += f"- Spacing: Use Tailwind spacing scale with semantic classes\n"
        enhanced_prompt += f"- Typography: Use Tailwind typography with font sizes\n\n"
        
        # Add relevant examples
        examples = await self.get_openai_examples()
        if examples:
            enhanced_prompt += "**Reference Examples:**\n"
            for i, example in enumerate(examples[:2], 1):
                enhanced_prompt += f"Example {i}: {example['prompt']}\n"
                enhanced_prompt += f"Shows shadcn/ui best practices and Radix UI integration\n\n"
        
        return {
            "system_prompt": system_prompt,
            "enhanced_user_prompt": enhanced_prompt,
            "library_context": "shadcn/ui",
            "complexity_level": complexity_level,
            "relevant_examples": len(examples),
            "design_tokens": self.design_tokens
        }


def main():
    """Main function to run the shadcn/ui MCP server."""
    parser = argparse.ArgumentParser(description="shadcn/ui MCP Server")
    parser.add_argument("--project", default=".", help="Project path")
    args = parser.parse_args()
    
    server = ShadcnUIServer(args.project)
    server.run()


if __name__ == "__main__":
    main()