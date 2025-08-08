#!/usr/bin/env python3
"""
Material-UI MCP Server for Palette Component Generation
Provides comprehensive Material-UI component knowledge and OpenAI optimization.
"""

import json
import sys
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the parent directory to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from palette.mcp.ui_library_server_base import UILibraryMCPServer, UIComponent, UILibraryContext, UILibraryType


class MaterialUIServer(UILibraryMCPServer):
    """Material-UI MCP server with comprehensive component knowledge."""
    
    def __init__(self, project_path: str = "."):
        super().__init__(project_path)
        self.library_type = UILibraryType.MATERIAL_UI
        
        # Initialize Material-UI specific knowledge
        self._initialize_material_ui_knowledge()
    
    def _initialize_material_ui_knowledge(self):
        """Initialize comprehensive Material-UI component knowledge."""
        
        # Material-UI component catalog
        self.component_catalog = {
            "Button": {
                "name": "Button",
                "description": "Material Design button component with elevation and ripple effects",
                "category": "inputs",
                "props": [
                    "variant", "color", "size", "disabled", "startIcon", "endIcon", 
                    "fullWidth", "href", "onClick", "children"
                ],
                "examples": [
                    {
                        "title": "Basic Button",
                        "code": '<Button variant="contained">Hello World</Button>'
                    },
                    {
                        "title": "Button with Icon",
                        "code": '<Button variant="contained" startIcon={<DeleteIcon />}>Delete</Button>'
                    }
                ],
                "accessibility": [
                    "Supports keyboard navigation",
                    "Proper ARIA labels",
                    "Focus management",
                    "Screen reader compatible"
                ],
                "styling": {
                    "variants": ["text", "outlined", "contained"],
                    "colors": ["primary", "secondary", "error", "warning", "info", "success"],
                    "sizes": ["small", "medium", "large"]
                }
            },
            
            "TextField": {
                "name": "TextField",
                "description": "Material Design text input with floating labels and validation",
                "category": "inputs",
                "props": [
                    "variant", "label", "placeholder", "value", "onChange", "error", 
                    "helperText", "required", "disabled", "multiline", "rows", "type"
                ],
                "examples": [
                    {
                        "title": "Basic TextField",
                        "code": '<TextField label="Name" variant="outlined" />'
                    },
                    {
                        "title": "TextField with Validation",
                        "code": '<TextField label="Email" variant="outlined" error={!isValid} helperText={error} />'
                    }
                ],
                "accessibility": [
                    "Proper label association",
                    "Error announcement",
                    "Required field indication"
                ],
                "styling": {
                    "variants": ["standard", "filled", "outlined"],
                    "colors": ["primary", "secondary", "error", "warning", "info", "success"]
                }
            },
            
            "Card": {
                "name": "Card",
                "description": "Material Design card container with elevation shadow",
                "category": "surfaces",
                "props": ["elevation", "variant", "children"],
                "examples": [
                    {
                        "title": "Basic Card",
                        "code": '<Card><CardContent><Typography>Card Content</Typography></CardContent></Card>'
                    },
                    {
                        "title": "Card with Actions",
                        "code": '<Card><CardContent><Typography>Title</Typography></CardContent><CardActions><Button>Action</Button></CardActions></Card>'
                    }
                ],
                "accessibility": [
                    "Semantic structure",
                    "Keyboard accessible"
                ],
                "styling": {
                    "elevations": [0, 1, 2, 3, 4, 6, 8, 12, 16, 24],
                    "variants": ["elevation", "outlined"]
                }
            },
            
            "AppBar": {
                "name": "AppBar",
                "description": "Material Design app bar for navigation and branding",
                "category": "navigation",
                "props": ["position", "color", "elevation", "children"],
                "examples": [
                    {
                        "title": "Basic AppBar",
                        "code": '<AppBar position="static"><Toolbar><Typography variant="h6">App Title</Typography></Toolbar></AppBar>'
                    }
                ],
                "accessibility": [
                    "Landmark navigation",
                    "Proper heading structure"
                ],
                "styling": {
                    "positions": ["fixed", "absolute", "sticky", "static", "relative"],
                    "colors": ["default", "inherit", "primary", "secondary", "transparent"]
                }
            },
            
            "Dialog": {
                "name": "Dialog",
                "description": "Material Design modal dialog with backdrop",
                "category": "feedback",
                "props": [
                    "open", "onClose", "maxWidth", "fullWidth", "fullScreen", 
                    "scroll", "children"
                ],
                "examples": [
                    {
                        "title": "Basic Dialog",
                        "code": '<Dialog open={open} onClose={handleClose}><DialogTitle>Title</DialogTitle><DialogContent>Content</DialogContent></Dialog>'
                    }
                ],
                "accessibility": [
                    "Focus trap",
                    "Escape key handling",
                    "Backdrop click handling",
                    "ARIA modal"
                ],
                "styling": {
                    "maxWidths": ["xs", "sm", "md", "lg", "xl"],
                    "scroll": ["paper", "body"]
                }
            },
            
            "Chip": {
                "name": "Chip",
                "description": "Material Design chip for tags and filters",
                "category": "data-display",
                "props": [
                    "label", "variant", "color", "size", "icon", "avatar", "clickable", 
                    "deletable", "onDelete", "onClick"
                ],
                "examples": [
                    {
                        "title": "Basic Chip",
                        "code": '<Chip label="Basic chip" />'
                    },
                    {
                        "title": "Deletable Chip",
                        "code": '<Chip label="Deletable" onDelete={handleDelete} />'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Screen reader support"
                ],
                "styling": {
                    "variants": ["filled", "outlined"],
                    "colors": ["default", "primary", "secondary", "error", "info", "success", "warning"],
                    "sizes": ["small", "medium"]
                }
            },
            
            "Typography": {
                "name": "Typography",
                "description": "Material Design typography component with theme integration",
                "category": "data-display",
                "props": [
                    "variant", "component", "color", "align", "gutterBottom", 
                    "noWrap", "paragraph", "children"
                ],
                "examples": [
                    {
                        "title": "Heading",
                        "code": '<Typography variant="h1" component="h2">Title</Typography>'
                    },
                    {
                        "title": "Body Text",
                        "code": '<Typography variant="body1">Body text content</Typography>'
                    }
                ],
                "accessibility": [
                    "Semantic HTML elements",
                    "Proper heading hierarchy"
                ],
                "styling": {
                    "variants": [
                        "h1", "h2", "h3", "h4", "h5", "h6",
                        "subtitle1", "subtitle2", "body1", "body2",
                        "caption", "button", "overline"
                    ],
                    "colors": [
                        "primary", "secondary", "textPrimary", "textSecondary", 
                        "error", "warning", "info", "success"
                    ],
                    "align": ["inherit", "left", "center", "right", "justify"]
                }
            },
            
            "Grid": {
                "name": "Grid",
                "description": "Material-UI responsive grid system with flexbox",
                "category": "layout",
                "props": [
                    "container", "item", "xs", "sm", "md", "lg", "xl", 
                    "spacing", "direction", "justify", "alignItems", "wrap"
                ],
                "examples": [
                    {
                        "title": "Basic Grid",
                        "code": '<Grid container spacing={2}><Grid item xs={12} sm={6}><Paper>Item</Paper></Grid></Grid>'
                    }
                ],
                "accessibility": [
                    "Responsive design",
                    "Semantic structure"
                ],
                "styling": {
                    "breakpoints": ["xs", "sm", "md", "lg", "xl"],
                    "spacing": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                }
            },
            
            "Accordion": {
                "name": "Accordion",
                "description": "Material Design expandable content panels",
                "category": "surfaces",
                "props": [
                    "expanded", "onChange", "disabled", "square", "children"
                ],
                "examples": [
                    {
                        "title": "Basic Accordion",
                        "code": '<Accordion><AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography>Panel</Typography></AccordionSummary><AccordionDetails><Typography>Content</Typography></AccordionDetails></Accordion>'
                    }
                ],
                "accessibility": [
                    "ARIA expanded states",
                    "Keyboard navigation",
                    "Focus management"
                ],
                "styling": {
                    "variants": ["elevation", "outlined"]
                }
            },
            
            "Fab": {
                "name": "Fab",
                "description": "Material Design floating action button",
                "category": "inputs",
                "props": [
                    "color", "size", "variant", "disabled", "href", "onClick", "children"
                ],
                "examples": [
                    {
                        "title": "Basic FAB",
                        "code": '<Fab color="primary"><AddIcon /></Fab>'
                    },
                    {
                        "title": "Extended FAB",
                        "code": '<Fab variant="extended" color="primary"><NavigationIcon />Navigate</Fab>'
                    }
                ],
                "accessibility": [
                    "Keyboard accessible",
                    "Proper ARIA labels",
                    "Focus management"
                ],
                "styling": {
                    "colors": ["default", "inherit", "primary", "secondary", "error", "info", "success", "warning"],
                    "sizes": ["small", "medium", "large"],
                    "variants": ["circular", "extended"]
                }
            },
            
            "Snackbar": {
                "name": "Snackbar",
                "description": "Material Design temporary notification",
                "category": "feedback",
                "props": [
                    "open", "autoHideDuration", "onClose", "message", "action",
                    "anchorOrigin", "children"
                ],
                "examples": [
                    {
                        "title": "Basic Snackbar",
                        "code": '<Snackbar open={open} autoHideDuration={6000} onClose={handleClose} message="Note archived" />'
                    }
                ],
                "accessibility": [
                    "Screen reader announcements",
                    "Keyboard dismissal",
                    "Focus management"
                ],
                "styling": {
                    "anchorOrigin": {
                        "vertical": ["top", "bottom"],
                        "horizontal": ["left", "center", "right"]
                    }
                }
            },
            
            "List": {
                "name": "List",
                "description": "Material Design list component for displaying collections",
                "category": "data-display",
                "props": ["dense", "disablePadding", "subheader", "children"],
                "examples": [
                    {
                        "title": "Basic List",
                        "code": '<List><ListItem><ListItemText primary="Item 1" /></ListItem><ListItem><ListItemText primary="Item 2" /></ListItem></List>'
                    }
                ],
                "accessibility": [
                    "Proper list semantics",
                    "Keyboard navigation",
                    "Screen reader support"
                ],
                "styling": {
                    "variants": ["standard", "dense"]
                }
            },
            
            "Menu": {
                "name": "Menu",
                "description": "Material Design dropdown menu",
                "category": "navigation",
                "props": [
                    "anchorEl", "open", "onClose", "MenuListProps", 
                    "PopoverClasses", "children"
                ],
                "examples": [
                    {
                        "title": "Basic Menu",
                        "code": '<Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleClose}><MenuItem onClick={handleClose}>Profile</MenuItem></Menu>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Focus management",
                    "ARIA menu role",
                    "Escape key handling"
                ],
                "styling": {
                    "positions": ["top", "bottom", "left", "right"]
                }
            }
        }
        
        # Material-UI design tokens
        self.design_tokens = {
            "colors": {
                "primary": {
                    "main": "#1976d2",
                    "light": "#42a5f5", 
                    "dark": "#1565c0",
                    "contrastText": "#fff"
                },
                "secondary": {
                    "main": "#dc004e",
                    "light": "#f50057",
                    "dark": "#c51162",
                    "contrastText": "#fff"
                },
                "error": {
                    "main": "#d32f2f",
                    "light": "#ef5350",
                    "dark": "#c62828",
                    "contrastText": "#fff"
                },
                "warning": {
                    "main": "#ed6c02",
                    "light": "#ff9800",
                    "dark": "#e65100",
                    "contrastText": "#fff"
                },
                "info": {
                    "main": "#0288d1",
                    "light": "#03a9f4",
                    "dark": "#01579b",
                    "contrastText": "#fff"
                },
                "success": {
                    "main": "#2e7d32",
                    "light": "#4caf50",
                    "dark": "#1b5e20",
                    "contrastText": "#fff"
                }
            },
            "spacing": {
                "unit": 8,
                "values": [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40]
            },
            "typography": {
                "fontFamily": '"Roboto", "Helvetica", "Arial", sans-serif',
                "fontSize": 14,
                "h1": {"fontSize": "6rem", "fontWeight": 300},
                "h2": {"fontSize": "3.75rem", "fontWeight": 300},
                "h3": {"fontSize": "3rem", "fontWeight": 400},
                "h4": {"fontSize": "2.125rem", "fontWeight": 400},
                "h5": {"fontSize": "1.5rem", "fontWeight": 400},
                "h6": {"fontSize": "1.25rem", "fontWeight": 500},
                "subtitle1": {"fontSize": "1rem", "fontWeight": 400},
                "subtitle2": {"fontSize": "0.875rem", "fontWeight": 500},
                "body1": {"fontSize": "1rem", "fontWeight": 400},
                "body2": {"fontSize": "0.875rem", "fontWeight": 400}
            },
            "shadows": [
                "none",
                "0px 2px 1px -1px rgba(0,0,0,0.2),0px 1px 1px 0px rgba(0,0,0,0.14),0px 1px 3px 0px rgba(0,0,0,0.12)",
                "0px 3px 1px -2px rgba(0,0,0,0.2),0px 2px 2px 0px rgba(0,0,0,0.14),0px 1px 5px 0px rgba(0,0,0,0.12)",
                "0px 3px 3px -2px rgba(0,0,0,0.2),0px 3px 4px 0px rgba(0,0,0,0.14),0px 1px 8px 0px rgba(0,0,0,0.12)"
            ],
            "breakpoints": {
                "xs": 0,
                "sm": 600,
                "md": 900,
                "lg": 1200,
                "xl": 1536
            }
        }
        
        # Material-UI best practices
        self.best_practices = [
            "Use Material-UI's theme provider for consistent theming",
            "Follow Material Design spacing guidelines (8px grid)",
            "Use proper elevation levels for visual hierarchy",
            "Implement proper color contrast for accessibility",
            "Use responsive breakpoints for mobile-first design",
            "Follow Material Design animation and motion principles",
            "Use appropriate typography variants for content hierarchy",
            "Implement proper keyboard navigation for accessibility",
            "Use semantic HTML with Material-UI components",
            "Follow Material Design component usage guidelines"
        ]
    
    async def get_component_catalog(self) -> List[UIComponent]:
        """Get comprehensive Material-UI component catalog."""
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
        """Get Material-UI design tokens."""
        return self.design_tokens
    
    async def get_openai_system_prompt(self) -> str:
        """Get OpenAI-optimized system prompt for Material-UI."""
        return """You are an expert Material-UI developer who creates production-ready React components following Material Design principles.

**Material-UI Standards:**
- Use Material-UI v5 (MUI) with proper imports from '@mui/material'
- Follow Material Design guidelines for spacing, typography, and color
- Use the theme system for consistent styling and responsive design
- Implement proper elevation and shadows for visual hierarchy
- Use appropriate component variants (text, outlined, contained for buttons)

**Component Quality Requirements:**
- Write TypeScript by default with comprehensive prop interfaces
- Use semantic HTML with proper ARIA attributes for accessibility
- Implement responsive design using Material-UI breakpoints
- Follow React best practices with hooks and functional components
- Use proper component composition with Material-UI components

**Material Design Principles:**
- Follow the 8px spacing grid system
- Use Material color palette (primary, secondary, error, warning, info, success)
- Implement proper typography hierarchy with Material-UI Typography variants
- Use appropriate elevation levels for surfaces and components
- Follow Material motion and animation guidelines

**Code Structure:**
- Export components as default exports with named interfaces
- Include proper imports for Material-UI components and icons
- Add helpful JSDoc comments for complex props
- Handle edge cases and loading states appropriately
- Use Material-UI's sx prop for custom styling when needed

**Accessibility Standards:**
- Ensure keyboard navigation works properly
- Use proper ARIA labels and descriptions
- Implement focus management for interactive components
- Provide appropriate color contrast ratios
- Support screen readers with semantic markup

Generate clean, production-ready Material-UI components that follow these standards."""

    async def get_openai_examples(self) -> List[Dict[str, str]]:
        """Get Material-UI examples optimized for OpenAI prompts."""
        return [
            {
                "prompt": "Create a Material-UI button with primary variant",
                "response": '''import React from 'react';
import { Button } from '@mui/material';

interface PrimaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  fullWidth?: boolean;
}

const PrimaryButton: React.FC<PrimaryButtonProps> = ({ 
  children, 
  onClick, 
  disabled = false,
  fullWidth = false 
}) => {
  return (
    <Button
      variant="contained"
      color="primary"
      onClick={onClick}
      disabled={disabled}
      fullWidth={fullWidth}
      sx={{
        textTransform: 'none',
        borderRadius: 2,
        py: 1.5,
      }}
    >
      {children}
    </Button>
  );
};

export default PrimaryButton;'''
            },
            {
                "prompt": "Build a Material-UI card with header and content",
                "response": '''import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  CardActions,
  Typography,
  Avatar,
  IconButton,
  Button
} from '@mui/material';
import { MoreVert as MoreVertIcon } from '@mui/icons-material';

interface ContentCardProps {
  title: string;
  subtitle?: string;
  content: string;
  avatar?: string;
  actions?: React.ReactNode;
}

const ContentCard: React.FC<ContentCardProps> = ({
  title,
  subtitle,
  content,
  avatar,
  actions
}) => {
  return (
    <Card
      elevation={3}
      sx={{
        maxWidth: 400,
        margin: 'auto',
        borderRadius: 2,
      }}
    >
      <CardHeader
        avatar={
          avatar ? (
            <Avatar src={avatar} aria-label="user avatar" />
          ) : (
            <Avatar aria-label="default avatar">{title.charAt(0)}</Avatar>
          )
        }
        action={
          <IconButton aria-label="settings">
            <MoreVertIcon />
          </IconButton>
        }
        title={
          <Typography variant="h6" component="h2">
            {title}
          </Typography>
        }
        subheader={subtitle}
      />
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {content}
        </Typography>
      </CardContent>
      {actions && (
        <CardActions disableSpacing>
          {actions}
        </CardActions>
      )}
    </Card>
  );
};

export default ContentCard;'''
            },
            {
                "prompt": "Create a Material-UI form with validation",
                "response": '''import React, { useState } from 'react';
import {
  TextField,
  Button,
  Box,
  Typography,
  Paper,
  Alert
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';

interface FormData {
  name: string;
  email: string;
  message: string;
}

interface ContactFormProps {
  onSubmit: (data: FormData) => Promise<void>;
}

const ContactForm: React.FC<ContactFormProps> = ({ onSubmit }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  
  const {
    control,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm<FormData>();

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
    <Paper
      elevation={3}
      sx={{
        p: 4,
        maxWidth: 500,
        margin: 'auto',
        borderRadius: 2,
      }}
    >
      <Typography variant="h5" component="h1" gutterBottom>
        Contact Us
      </Typography>
      
      {submitError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {submitError}
        </Alert>
      )}

      <Box
        component="form"
        onSubmit={handleSubmit(handleFormSubmit)}
        sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}
      >
        <Controller
          name="name"
          control={control}
          rules={{ required: 'Name is required' }}
          render={({ field }) => (
            <TextField
              {...field}
              label="Name"
              variant="outlined"
              fullWidth
              error={!!errors.name}
              helperText={errors.name?.message}
            />
          )}
        />

        <Controller
          name="email"
          control={control}
          rules={{
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email address'
            }
          }}
          render={({ field }) => (
            <TextField
              {...field}
              label="Email"
              type="email"
              variant="outlined"
              fullWidth
              error={!!errors.email}
              helperText={errors.email?.message}
            />
          )}
        />

        <Controller
          name="message"
          control={control}
          rules={{ required: 'Message is required' }}
          render={({ field }) => (
            <TextField
              {...field}
              label="Message"
              variant="outlined"
              multiline
              rows={4}
              fullWidth
              error={!!errors.message}
              helperText={errors.message?.message}
            />
          )}
        />

        <Button
          type="submit"
          variant="contained"
          color="primary"
          size="large"
          disabled={isSubmitting}
          sx={{
            py: 1.5,
            textTransform: 'none',
            fontSize: '1rem',
          }}
        >
          {isSubmitting ? 'Submitting...' : 'Send Message'}
        </Button>
      </Box>
    </Paper>
  );
};

export default ContactForm;'''
            }
        ]
    
    # Implement all the required tool methods
    
    async def get_component_info(self, component_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific Material-UI component."""
        if component_name.lower() == "all":
            return {
                "components": list(self.component_catalog.keys()),
                "total": len(self.component_catalog),
                "categories": list(set(info["category"] for info in self.component_catalog.values()))
            }
        
        if component_name in self.component_catalog:
            return self.component_catalog[component_name]
        
        return {"error": f"Component '{component_name}' not found in Material-UI catalog"}
    
    async def search_components(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for Material-UI components matching the query."""
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
        """Validate Material-UI usage in component code."""
        issues = []
        suggestions = []
        score = 100
        
        # Check for proper Material-UI imports
        if "@mui/material" not in component_code:
            issues.append("Missing Material-UI imports from '@mui/material'")
            score -= 20
        
        # Check for theme usage
        if "theme" not in component_code and "sx=" in component_code:
            suggestions.append("Consider using Material-UI theme for consistent styling")
        
        # Check for proper TypeScript interfaces
        if "interface" not in component_code and strict_mode:
            issues.append("Missing TypeScript interface definitions")
            score -= 15
        
        # Check for Material Design principles
        if "elevation" not in component_code and "Card" in component_code:
            suggestions.append("Consider using elevation prop for Material Design cards")
        
        # Check for accessibility
        if "aria-" not in component_code and ("Button" in component_code or "TextField" in component_code):
            suggestions.append("Consider adding ARIA attributes for better accessibility")
            score -= 5
        
        return {
            "valid": len(issues) == 0,
            "score": max(score, 0),
            "issues": issues,
            "suggestions": suggestions,
            "library": "Material-UI"
        }
    
    async def generate_openai_prompt(self, 
                                   user_request: str, 
                                   component_type: Optional[str] = None,
                                   complexity_level: str = "intermediate") -> Dict[str, Any]:
        """Generate OpenAI-optimized prompt with Material-UI context."""
        
        system_prompt = await self.get_openai_system_prompt()
        
        # Build enhanced user prompt
        enhanced_prompt = f"**User Request:** {user_request}\n\n"
        
        if component_type:
            enhanced_prompt += f"**Component Type:** {component_type}\n"
            
            # Find relevant Material-UI components
            search_results = await self.search_components(component_type, limit=3)
            if search_results["results"]:
                enhanced_prompt += f"**Relevant Material-UI Components:**\n"
                for result in search_results["results"][:2]:
                    enhanced_prompt += f"- {result['name']}: {result['description']}\n"
                enhanced_prompt += "\n"
        
        enhanced_prompt += f"**Complexity Level:** {complexity_level}\n\n"
        
        # Add Material-UI specific guidance
        enhanced_prompt += "**Material-UI Guidelines:**\n"
        enhanced_prompt += "- Use Material-UI v5 components with proper imports\n"
        enhanced_prompt += "- Follow Material Design principles for spacing and typography\n"
        enhanced_prompt += "- Use theme system for colors and responsive design\n"
        enhanced_prompt += "- Implement proper elevation and shadows\n"
        enhanced_prompt += "- Ensure accessibility with ARIA attributes\n\n"
        
        # Add design tokens context
        enhanced_prompt += "**Available Design Tokens:**\n"
        enhanced_prompt += f"- Colors: {', '.join(self.design_tokens['colors'].keys())}\n"
        enhanced_prompt += f"- Typography variants: h1-h6, subtitle1-2, body1-2, button, caption\n"
        enhanced_prompt += f"- Spacing: 8px grid system\n"
        enhanced_prompt += f"- Breakpoints: xs, sm, md, lg, xl\n\n"
        
        # Add relevant examples
        examples = await self.get_openai_examples()
        if examples:
            enhanced_prompt += "**Reference Examples:**\n"
            for i, example in enumerate(examples[:2], 1):
                enhanced_prompt += f"Example {i}: {example['prompt']}\n"
                enhanced_prompt += f"Shows Material-UI best practices and component composition\n\n"
        
        return {
            "system_prompt": system_prompt,
            "enhanced_user_prompt": enhanced_prompt,
            "library_context": "material-ui",
            "complexity_level": complexity_level,
            "relevant_examples": len(examples),
            "design_tokens": self.design_tokens
        }


def main():
    """Main function to run the Material-UI MCP server."""
    parser = argparse.ArgumentParser(description="Material-UI MCP Server")
    parser.add_argument("--project", default=".", help="Project path")
    args = parser.parse_args()
    
    server = MaterialUIServer(args.project)
    server.run()


if __name__ == "__main__":
    main()