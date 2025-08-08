#!/usr/bin/env python3
"""
Ant Design MCP Server for Palette Component Generation
Provides comprehensive Ant Design component knowledge and OpenAI optimization.
"""

import json
import sys
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the parent directory to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from palette.mcp.ui_library_server_base import UILibraryMCPServer, UIComponent, UILibraryContext, UILibraryType


class AntDesignServer(UILibraryMCPServer):
    """Ant Design MCP server with comprehensive component knowledge."""
    
    def __init__(self, project_path: str = "."):
        super().__init__(project_path)
        self.library_type = UILibraryType.ANT_DESIGN
        
        # Initialize Ant Design specific knowledge
        self._initialize_ant_design_knowledge()
    
    def _initialize_ant_design_knowledge(self):
        """Initialize comprehensive Ant Design component knowledge."""
        
        # Ant Design component catalog
        self.component_catalog = {
            "Button": {
                "name": "Button",
                "description": "Ant Design button with various types and states",
                "category": "general",
                "props": [
                    "type", "size", "shape", "icon", "loading", "disabled", 
                    "ghost", "block", "danger", "href", "onClick", "children"
                ],
                "examples": [
                    {
                        "title": "Primary Button",
                        "code": '<Button type="primary">Primary Button</Button>'
                    },
                    {
                        "title": "Button with Icon",
                        "code": '<Button type="primary" icon={<SearchOutlined />}>Search</Button>'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation support",
                    "Screen reader compatibility",
                    "Focus management",
                    "ARIA attributes"
                ],
                "styling": {
                    "types": ["default", "primary", "dashed", "text", "link"],
                    "sizes": ["large", "middle", "small"],
                    "shapes": ["default", "circle", "round"]
                }
            },
            
            "Input": {
                "name": "Input",
                "description": "Ant Design input field with validation and formatting",
                "category": "data-entry",
                "props": [
                    "placeholder", "value", "defaultValue", "onChange", "onPressEnter",
                    "size", "prefix", "suffix", "addonBefore", "addonAfter", 
                    "disabled", "maxLength", "showCount", "allowClear"
                ],
                "examples": [
                    {
                        "title": "Basic Input",
                        "code": '<Input placeholder="Enter your name" />'
                    },
                    {
                        "title": "Input with Icon",
                        "code": '<Input prefix={<UserOutlined />} placeholder="Username" />'
                    }
                ],
                "accessibility": [
                    "Proper label association",
                    "Keyboard navigation",
                    "Screen reader support"
                ],
                "styling": {
                    "sizes": ["large", "middle", "small"],
                    "variants": ["outlined", "borderless", "filled"]
                }
            },
            
            "Card": {
                "name": "Card",
                "description": "Ant Design card container for content grouping",
                "category": "data-display",
                "props": [
                    "title", "extra", "bordered", "hoverable", "loading", "size", 
                    "cover", "actions", "bodyStyle", "headStyle", "children"
                ],
                "examples": [
                    {
                        "title": "Basic Card",
                        "code": '<Card title="Card Title"><p>Card content</p></Card>'
                    },
                    {
                        "title": "Card with Actions",
                        "code": '<Card title="Card Title" actions={[<SettingOutlined key="setting" />, <EditOutlined key="edit" />]}><p>Card content</p></Card>'
                    }
                ],
                "accessibility": [
                    "Semantic structure",
                    "Keyboard navigation",
                    "Screen reader support"
                ],
                "styling": {
                    "sizes": ["default", "small"],
                    "variants": ["bordered", "borderless"]
                }
            },
            
            "Form": {
                "name": "Form",
                "description": "Ant Design form with validation and layout management",
                "category": "data-entry",
                "props": [
                    "layout", "labelCol", "wrapperCol", "size", "disabled",
                    "colon", "hideRequiredMark", "requiredMark", "scrollToFirstError",
                    "onFinish", "onFinishFailed", "onFieldsChange", "onValuesChange"
                ],
                "examples": [
                    {
                        "title": "Basic Form",
                        "code": '<Form layout="vertical" onFinish={onFinish}><Form.Item label="Name" name="name" rules={[{ required: true }]}><Input /></Form.Item></Form>'
                    }
                ],
                "accessibility": [
                    "Form validation announcements",
                    "Label associations",
                    "Keyboard navigation",
                    "Error message display"
                ],
                "styling": {
                    "layouts": ["horizontal", "vertical", "inline"],
                    "sizes": ["large", "middle", "small"]
                }
            },
            
            "Table": {
                "name": "Table",
                "description": "Ant Design data table with sorting, filtering, and pagination",
                "category": "data-display",
                "props": [
                    "columns", "dataSource", "rowKey", "pagination", "loading",
                    "size", "bordered", "showHeader", "scroll", "expandable",
                    "rowSelection", "onChange", "onRow"
                ],
                "examples": [
                    {
                        "title": "Basic Table",
                        "code": '<Table columns={columns} dataSource={data} rowKey="id" />'
                    }
                ],
                "accessibility": [
                    "Table headers",
                    "Row/column navigation",
                    "Screen reader support",
                    "Keyboard sorting"
                ],
                "styling": {
                    "sizes": ["large", "middle", "small"],
                    "variants": ["bordered", "borderless"]
                }
            },
            
            "Modal": {
                "name": "Modal",
                "description": "Ant Design modal dialog for displaying content",
                "category": "feedback",
                "props": [
                    "open", "title", "onOk", "onCancel", "okText", "cancelText",
                    "width", "centered", "closable", "maskClosable", "keyboard",
                    "footer", "bodyStyle", "maskStyle", "wrapClassName"
                ],
                "examples": [
                    {
                        "title": "Basic Modal",
                        "code": '<Modal title="Basic Modal" open={isModalOpen} onOk={handleOk} onCancel={handleCancel}><p>Modal content</p></Modal>'
                    }
                ],
                "accessibility": [
                    "Focus trap",
                    "Keyboard navigation",
                    "Screen reader announcements",
                    "Escape key handling"
                ],
                "styling": {
                    "positions": ["center", "top"],
                    "sizes": ["small", "large", "fullscreen"]
                }
            },
            
            "Select": {
                "name": "Select",
                "description": "Ant Design select dropdown with search and multi-selection",
                "category": "data-entry",
                "props": [
                    "options", "value", "defaultValue", "onChange", "onSelect",
                    "mode", "size", "placeholder", "disabled", "loading",
                    "allowClear", "showSearch", "filterOption", "notFoundContent"
                ],
                "examples": [
                    {
                        "title": "Basic Select",
                        "code": '<Select placeholder="Select an option" options={[{value: "1", label: "Option 1"}]} />'
                    },
                    {
                        "title": "Multi Select",
                        "code": '<Select mode="multiple" placeholder="Select options" options={options} />'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Screen reader support",
                    "Option announcements",
                    "Search functionality"
                ],
                "styling": {
                    "sizes": ["large", "middle", "small"],
                    "modes": ["multiple", "tags"]
                }
            },
            
            "DatePicker": {
                "name": "DatePicker",
                "description": "Ant Design date picker for date selection",
                "category": "data-entry",
                "props": [
                    "value", "defaultValue", "onChange", "format", "picker",
                    "placeholder", "disabled", "size", "allowClear",
                    "disabledDate", "locale", "showTime", "showToday"
                ],
                "examples": [
                    {
                        "title": "Basic DatePicker",
                        "code": '<DatePicker placeholder="Select date" />'
                    },
                    {
                        "title": "DateTime Picker",
                        "code": '<DatePicker showTime placeholder="Select date and time" />'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Calendar navigation",
                    "Screen reader support",
                    "Date announcements"
                ],
                "styling": {
                    "sizes": ["large", "middle", "small"],
                    "pickers": ["date", "week", "month", "quarter", "year"]
                }
            },
            
            "Menu": {
                "name": "Menu",
                "description": "Ant Design navigation menu with hierarchy support",
                "category": "navigation",
                "props": [
                    "items", "mode", "theme", "selectedKeys", "defaultSelectedKeys",
                    "openKeys", "defaultOpenKeys", "onSelect", "onOpenChange",
                    "inlineCollapsed", "triggerSubMenuAction"
                ],
                "examples": [
                    {
                        "title": "Horizontal Menu",
                        "code": '<Menu mode="horizontal" items={[{key: "1", label: "Home"}, {key: "2", label: "About"}]} />'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "ARIA menu roles",
                    "Focus management",
                    "Submenu handling"
                ],
                "styling": {
                    "modes": ["vertical", "horizontal", "inline"],
                    "themes": ["light", "dark"]
                }
            },
            
            "Notification": {
                "name": "notification",
                "description": "Ant Design global notification display",
                "category": "feedback",
                "props": [
                    "message", "description", "type", "placement", "duration",
                    "closable", "closeIcon", "key", "onClick", "onClose"
                ],
                "examples": [
                    {
                        "title": "Basic Notification",
                        "code": "notification.success({message: 'Success', description: 'This is a success message'});"
                    }
                ],
                "accessibility": [
                    "Screen reader announcements",
                    "Keyboard dismissal",
                    "Focus management"
                ],
                "styling": {
                    "types": ["success", "info", "warning", "error"],
                    "placements": ["topLeft", "topRight", "bottomLeft", "bottomRight"]
                }
            },
            
            "Steps": {
                "name": "Steps",
                "description": "Ant Design step-by-step navigation component",
                "category": "navigation",
                "props": [
                    "items", "current", "direction", "size", "status",
                    "type", "onChange", "labelPlacement", "responsive"
                ],
                "examples": [
                    {
                        "title": "Basic Steps",
                        "code": '<Steps current={1} items={[{title: "Step 1"}, {title: "Step 2"}, {title: "Step 3"}]} />'
                    }
                ],
                "accessibility": [
                    "Step navigation",
                    "Progress indication",
                    "Screen reader support",
                    "Keyboard navigation"
                ],
                "styling": {
                    "types": ["default", "navigation"],
                    "sizes": ["default", "small"],
                    "directions": ["horizontal", "vertical"]
                }
            },
            
            "Tabs": {
                "name": "Tabs",
                "description": "Ant Design tabbed interface component",
                "category": "data-display",
                "props": [
                    "items", "activeKey", "defaultActiveKey", "onChange",
                    "type", "size", "position", "centered", "hideAdd",
                    "addIcon", "removeIcon", "onEdit", "onTabClick"
                ],
                "examples": [
                    {
                        "title": "Basic Tabs",
                        "code": '<Tabs items={[{key: "1", label: "Tab 1", children: <div>Content 1</div>}]} />'
                    }
                ],
                "accessibility": [
                    "Keyboard navigation",
                    "Tab panel associations",
                    "ARIA tab roles",
                    "Focus management"
                ],
                "styling": {
                    "types": ["line", "card", "editable-card"],
                    "sizes": ["large", "middle", "small"],
                    "positions": ["top", "right", "bottom", "left"]
                }
            },
            
            "Drawer": {
                "name": "Drawer",
                "description": "Ant Design slide-out panel component",
                "category": "feedback",
                "props": [
                    "open", "title", "onClose", "placement", "width", "height",
                    "closable", "maskClosable", "keyboard", "bodyStyle",
                    "headerStyle", "footerStyle", "extra", "footer"
                ],
                "examples": [
                    {
                        "title": "Basic Drawer",
                        "code": '<Drawer title="Basic Drawer" onClose={onClose} open={open}><p>Drawer content</p></Drawer>'
                    }
                ],
                "accessibility": [
                    "Focus trap",
                    "Keyboard navigation",
                    "Screen reader support",
                    "Escape key handling"
                ],
                "styling": {
                    "placements": ["top", "right", "bottom", "left"],
                    "sizes": ["default", "large"]
                }
            }
        }
        
        # Ant Design design tokens
        self.design_tokens = {
            "colors": {
                "primary": "#1890ff",
                "success": "#52c41a",
                "warning": "#faad14",
                "error": "#ff4d4f",
                "info": "#1890ff",
                "text": {
                    "primary": "rgba(0, 0, 0, 0.85)",
                    "secondary": "rgba(0, 0, 0, 0.65)",
                    "disabled": "rgba(0, 0, 0, 0.25)"
                },
                "background": {
                    "base": "#ffffff",
                    "layout": "#f0f2f5",
                    "component": "#ffffff"
                },
                "border": {
                    "base": "#d9d9d9",
                    "split": "#f0f0f0"
                }
            },
            "spacing": {
                "xs": 4,
                "sm": 8,
                "md": 12,
                "lg": 16,
                "xl": 20,
                "xxl": 24
            },
            "typography": {
                "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif",
                "fontSize": {
                    "base": 14,
                    "lg": 16,
                    "xl": 20,
                    "xxl": 24
                },
                "lineHeight": {
                    "base": 1.5715,
                    "lg": 1.5,
                    "xl": 1.4
                }
            },
            "borderRadius": {
                "sm": 2,
                "base": 6,
                "lg": 8
            },
            "shadows": {
                "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)",
                "base": "0 1px 2px 0 rgba(0, 0, 0, 0.05), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)",
                "lg": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
            },
            "breakpoints": {
                "xs": 480,
                "sm": 576,
                "md": 768,
                "lg": 992,
                "xl": 1200,
                "xxl": 1600
            }
        }
        
        # Ant Design best practices
        self.best_practices = [
            "Use Ant Design's design language principles",
            "Follow consistent spacing and typography scales",
            "Implement proper form validation with Form.Item rules",
            "Use appropriate component sizes for different contexts",
            "Leverage Ant Design's built-in accessibility features",
            "Use ConfigProvider for global theme customization",
            "Implement proper loading states for data components",
            "Use Ant Design icons for consistency",
            "Follow Ant Design's color system for semantic meaning",
            "Use responsive design with Ant Design's grid system"
        ]
    
    async def get_component_catalog(self) -> List[UIComponent]:
        """Get comprehensive Ant Design component catalog."""
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
        """Get Ant Design design tokens."""
        return self.design_tokens
    
    async def get_openai_system_prompt(self) -> str:
        """Get OpenAI-optimized system prompt for Ant Design."""
        return """You are an expert Ant Design developer who creates production-ready React components following Ant Design principles.

**Ant Design Standards:**
- Use Ant Design v5 (antd) with proper imports from 'antd'
- Follow Ant Design's design language and component guidelines
- Use Ant Design's design tokens for consistent styling
- Implement proper component hierarchy and layout patterns
- Use appropriate Ant Design icons from '@ant-design/icons'

**Component Quality Requirements:**
- Write TypeScript by default with comprehensive prop interfaces
- Use semantic HTML with proper ARIA attributes for accessibility
- Implement responsive design using Ant Design's grid system
- Follow React best practices with hooks and functional components
- Use proper component composition with Ant Design components

**Ant Design Principles:**
- Follow consistent spacing and typography scales
- Use Ant Design's color system for semantic meaning (primary, success, warning, error)
- Implement proper form validation with Form.Item rules
- Use appropriate component sizes (large, middle, small) for different contexts
- Follow Ant Design's interaction and animation patterns

**Code Structure:**
- Export components as default exports with named interfaces
- Include proper imports for Ant Design components and icons
- Add helpful JSDoc comments for complex props
- Handle edge cases and loading states appropriately
- Use Ant Design's CSS-in-JS styling approach when needed

**Accessibility Standards:**
- Ensure keyboard navigation works properly with Ant Design components
- Use proper ARIA labels and descriptions
- Implement focus management for interactive components
- Provide appropriate error messages and validation feedback
- Support screen readers with semantic markup

Generate clean, production-ready Ant Design components that follow these standards."""

    async def get_openai_examples(self) -> List[Dict[str, str]]:
        """Get Ant Design examples optimized for OpenAI prompts."""
        return [
            {
                "prompt": "Create an Ant Design button with primary type",
                "response": '''import React from 'react';
import { Button } from 'antd';
import { SearchOutlined } from '@ant-design/icons';

interface PrimaryButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  size?: 'large' | 'middle' | 'small';
  block?: boolean;
}

const PrimaryButton: React.FC<PrimaryButtonProps> = ({ 
  children, 
  onClick, 
  loading = false,
  disabled = false,
  icon,
  size = 'middle',
  block = false
}) => {
  return (
    <Button
      type="primary"
      onClick={onClick}
      loading={loading}
      disabled={disabled}
      icon={icon}
      size={size}
      block={block}
      style={{
        borderRadius: '6px',
        fontWeight: 400,
      }}
    >
      {children}
    </Button>
  );
};

export default PrimaryButton;'''
            },
            {
                "prompt": "Build an Ant Design card with content and actions",
                "response": '''import React from 'react';
import { Card, Avatar, Button } from 'antd';
import { EditOutlined, SettingOutlined, EllipsisOutlined } from '@ant-design/icons';

const { Meta } = Card;

interface ContentCardProps {
  title: string;
  description: string;
  avatar?: string;
  cover?: string;
  actions?: React.ReactNode[];
  loading?: boolean;
}

const ContentCard: React.FC<ContentCardProps> = ({
  title,
  description,
  avatar,
  cover,
  actions,
  loading = false
}) => {
  const defaultActions = [
    <SettingOutlined key="setting" />,
    <EditOutlined key="edit" />,
    <EllipsisOutlined key="ellipsis" />,
  ];

  return (
    <Card
      style={{ 
        width: 300,
        borderRadius: '8px',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02)'
      }}
      cover={cover ? <img alt="cover" src={cover} /> : undefined}
      actions={actions || defaultActions}
      loading={loading}
      hoverable
    >
      <Meta
        avatar={<Avatar src={avatar} />}
        title={title}
        description={description}
      />
    </Card>
  );
};

export default ContentCard;'''
            },
            {
                "prompt": "Create an Ant Design form with validation",
                "response": '''import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';

interface FormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface RegistrationFormProps {
  onSubmit: (data: FormData) => Promise<void>;
}

const RegistrationForm: React.FC<RegistrationFormProps> = ({ onSubmit }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: FormData) => {
    try {
      setLoading(true);
      await onSubmit(values);
      message.success('Registration successful!');
      form.resetFields();
    } catch (error) {
      message.error('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card 
      title="Create Account" 
      style={{ 
        maxWidth: 400, 
        margin: '0 auto',
        borderRadius: '8px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
      }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        autoComplete="off"
        size="large"
      >
        <Form.Item
          label="Username"
          name="username"
          rules={[
            { required: true, message: 'Please enter your username!' },
            { min: 3, message: 'Username must be at least 3 characters!' }
          ]}
        >
          <Input 
            prefix={<UserOutlined />} 
            placeholder="Enter username" 
          />
        </Form.Item>

        <Form.Item
          label="Email"
          name="email"
          rules={[
            { required: true, message: 'Please enter your email!' },
            { type: 'email', message: 'Please enter a valid email!' }
          ]}
        >
          <Input 
            prefix={<MailOutlined />} 
            placeholder="Enter email" 
          />
        </Form.Item>

        <Form.Item
          label="Password"
          name="password"
          rules={[
            { required: true, message: 'Please enter your password!' },
            { min: 8, message: 'Password must be at least 8 characters!' }
          ]}
        >
          <Input.Password 
            prefix={<LockOutlined />} 
            placeholder="Enter password" 
          />
        </Form.Item>

        <Form.Item
          label="Confirm Password"
          name="confirmPassword"
          dependencies={['password']}
          rules={[
            { required: true, message: 'Please confirm your password!' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('Passwords do not match!'));
              },
            }),
          ]}
        >
          <Input.Password 
            prefix={<LockOutlined />} 
            placeholder="Confirm password" 
          />
        </Form.Item>

        <Form.Item>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={loading}
            block
            style={{ 
              height: '40px',
              borderRadius: '6px',
              fontSize: '16px'
            }}
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default RegistrationForm;'''
            }
        ]
    
    # Implement all the required tool methods
    
    async def get_component_info(self, component_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific Ant Design component."""
        if component_name.lower() == "all":
            return {
                "components": list(self.component_catalog.keys()),
                "total": len(self.component_catalog),
                "categories": list(set(info["category"] for info in self.component_catalog.values()))
            }
        
        if component_name in self.component_catalog:
            return self.component_catalog[component_name]
        
        return {"error": f"Component '{component_name}' not found in Ant Design catalog"}
    
    async def search_components(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for Ant Design components matching the query."""
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
        """Validate Ant Design usage in component code."""
        issues = []
        suggestions = []
        score = 100
        
        # Check for proper Ant Design imports
        if "antd" not in component_code:
            issues.append("Missing Ant Design imports from 'antd'")
            score -= 20
        
        # Check for proper TypeScript interfaces
        if "interface" not in component_code and strict_mode:
            issues.append("Missing TypeScript interface definitions")
            score -= 15
        
        # Check for form validation
        if "Form" in component_code and "rules=" not in component_code:
            suggestions.append("Consider adding validation rules to Form.Item components")
        
        # Check for icons usage
        if ("Button" in component_code or "Input" in component_code) and "@ant-design/icons" not in component_code:
            suggestions.append("Consider using Ant Design icons for consistency")
        
        # Check for accessibility
        if "aria-" not in component_code and ("Button" in component_code or "Input" in component_code):
            suggestions.append("Consider adding ARIA attributes for better accessibility")
            score -= 5
        
        return {
            "valid": len(issues) == 0,
            "score": max(score, 0),
            "issues": issues,
            "suggestions": suggestions,
            "library": "Ant Design"
        }
    
    async def generate_openai_prompt(self, 
                                   user_request: str, 
                                   component_type: Optional[str] = None,
                                   complexity_level: str = "intermediate") -> Dict[str, Any]:
        """Generate OpenAI-optimized prompt with Ant Design context."""
        
        system_prompt = await self.get_openai_system_prompt()
        
        # Build enhanced user prompt
        enhanced_prompt = f"**User Request:** {user_request}\n\n"
        
        if component_type:
            enhanced_prompt += f"**Component Type:** {component_type}\n"
            
            # Find relevant Ant Design components
            search_results = await self.search_components(component_type, limit=3)
            if search_results["results"]:
                enhanced_prompt += f"**Relevant Ant Design Components:**\n"
                for result in search_results["results"][:2]:
                    enhanced_prompt += f"- {result['name']}: {result['description']}\n"
                enhanced_prompt += "\n"
        
        enhanced_prompt += f"**Complexity Level:** {complexity_level}\n\n"
        
        # Add Ant Design specific guidance
        enhanced_prompt += "**Ant Design Guidelines:**\n"
        enhanced_prompt += "- Use Ant Design v5 components with proper imports\n"
        enhanced_prompt += "- Follow Ant Design's design language principles\n"
        enhanced_prompt += "- Use appropriate component sizes and types\n"
        enhanced_prompt += "- Implement proper form validation with Form.Item rules\n"
        enhanced_prompt += "- Use Ant Design icons for consistency\n\n"
        
        # Add design tokens context
        enhanced_prompt += "**Available Design Tokens:**\n"
        enhanced_prompt += f"- Colors: primary, success, warning, error, info\n"
        enhanced_prompt += f"- Sizes: large, middle, small\n"
        enhanced_prompt += f"- Spacing: xs(4px), sm(8px), md(12px), lg(16px), xl(20px), xxl(24px)\n"
        enhanced_prompt += f"- Border radius: sm(2px), base(6px), lg(8px)\n\n"
        
        # Add relevant examples
        examples = await self.get_openai_examples()
        if examples:
            enhanced_prompt += "**Reference Examples:**\n"
            for i, example in enumerate(examples[:2], 1):
                enhanced_prompt += f"Example {i}: {example['prompt']}\n"
                enhanced_prompt += f"Shows Ant Design best practices and component composition\n\n"
        
        return {
            "system_prompt": system_prompt,
            "enhanced_user_prompt": enhanced_prompt,
            "library_context": "ant-design",
            "complexity_level": complexity_level,
            "relevant_examples": len(examples),
            "design_tokens": self.design_tokens
        }


def main():
    """Main function to run the Ant Design MCP server."""
    parser = argparse.ArgumentParser(description="Ant Design MCP Server")
    parser.add_argument("--project", default=".", help="Project path")
    args = parser.parse_args()
    
    server = AntDesignServer(args.project)
    server.run()


if __name__ == "__main__":
    main()