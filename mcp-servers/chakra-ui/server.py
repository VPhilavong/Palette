#!/usr/bin/env python3
"""
Chakra UI MCP Server for Palette.
Provides comprehensive Chakra UI knowledge, components, and OpenAI-optimized prompts.
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the main palette source to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from palette.mcp.ui_library_server_base import (
    UILibraryMCPServer, UILibraryType, UIComponent
)


class ChakraUIMCPServer(UILibraryMCPServer):
    """MCP Server for Chakra UI operations and knowledge."""
    
    @property
    def library_type(self) -> UILibraryType:
        return UILibraryType.CHAKRA_UI
    
    @property
    def server_name(self) -> str:
        return "chakra-ui"
    
    @property
    def server_version(self) -> str:
        return "1.0.0"
    
    def _initialize_library_data(self):
        """Initialize Chakra UI specific data structures."""
        # Initialize component catalog
        self._component_catalog = None
        
        # Chakra UI specific configurations
        self.chakra_theme_keys = {
            "colors": [
                "gray", "red", "orange", "yellow", "green", "teal", "blue", 
                "cyan", "purple", "pink", "blackAlpha", "whiteAlpha"
            ],
            "sizes": ["xs", "sm", "md", "lg", "xl", "2xl"],
            "variants": {
                "button": ["solid", "outline", "ghost", "link", "unstyled"],
                "input": ["outline", "filled", "flushed", "unstyled"],
                "badge": ["solid", "subtle", "outline"]
            }
        }
    
    async def get_component_catalog(self) -> List[UIComponent]:
        """Get the complete Chakra UI component catalog."""
        if self._component_catalog is None:
            self._component_catalog = await self._build_chakra_component_catalog()
        return self._component_catalog
    
    async def _build_chakra_component_catalog(self) -> List[UIComponent]:
        """Build comprehensive Chakra UI component catalog."""
        return [
            # Layout Components
            UIComponent(
                name="Box",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "as", "type": "ElementType", "required": False, "description": "The HTML element or component to render"},
                    {"name": "bg", "type": "string", "required": False, "description": "Background color"},
                    {"name": "color", "type": "string", "required": False, "description": "Text color"},
                    {"name": "p", "type": "ResponsiveValue<string>", "required": False, "description": "Padding"},
                    {"name": "m", "type": "ResponsiveValue<string>", "required": False, "description": "Margin"},
                    {"name": "w", "type": "ResponsiveValue<string>", "required": False, "description": "Width"},
                    {"name": "h", "type": "ResponsiveValue<string>", "required": False, "description": "Height"}
                ],
                variants=["responsive"],
                examples=[
                    '<Box bg="blue.500" w="100%" p={4} color="white">Simple Box</Box>',
                    '<Box as="section" maxW="md" mx="auto" p={6} bg="gray.50" borderRadius="lg">Card-like Box</Box>'
                ],
                description="Box is the most abstract component on top of which all other Chakra UI components are built.",
                category="layout",
                tags=["layout", "container", "fundamental"],
                dependencies=[],
                typescript_types="BoxProps extends HTMLChakraProps<'div'>",
                accessibility_features=["Semantic HTML support via 'as' prop"],
                design_tokens_used=["colors", "spacing", "radii", "shadows"]
            ),
            
            UIComponent(
                name="Stack",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "direction", "type": "ResponsiveValue<'row' | 'column'>", "required": False, "description": "Stack direction"},
                    {"name": "spacing", "type": "ResponsiveValue<string>", "required": False, "description": "Spacing between items"},
                    {"name": "align", "type": "ResponsiveValue<AlignItems>", "required": False, "description": "Align items"},
                    {"name": "justify", "type": "ResponsiveValue<JustifyContent>", "required": False, "description": "Justify content"},
                    {"name": "wrap", "type": "ResponsiveValue<FlexWrap>", "required": False, "description": "Wrap items"},
                    {"name": "divider", "type": "ReactElement", "required": False, "description": "Divider between stack items"}
                ],
                variants=["VStack", "HStack"],
                examples=[
                    '<Stack spacing={4}><Box>Item 1</Box><Box>Item 2</Box></Stack>',
                    '<VStack spacing={3} align="start"><Text>Vertical Stack</Text><Button>Action</Button></VStack>',
                    '<HStack spacing={2}><Badge>Tag 1</Badge><Badge>Tag 2</Badge></HStack>'
                ],
                description="Stack is used to group elements together and apply consistent spacing between them.",
                category="layout",
                tags=["layout", "flexbox", "spacing"],
                dependencies=[],
                typescript_types="StackProps extends HTMLChakraProps<'div'>",
                accessibility_features=["Maintains reading order", "Keyboard navigation friendly"],
                design_tokens_used=["spacing"]
            ),
            
            UIComponent(
                name="Grid",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "templateColumns", "type": "ResponsiveValue<string>", "required": False, "description": "Grid template columns"},
                    {"name": "templateRows", "type": "ResponsiveValue<string>", "required": False, "description": "Grid template rows"},
                    {"name": "gap", "type": "ResponsiveValue<string>", "required": False, "description": "Gap between grid items"},
                    {"name": "rowGap", "type": "ResponsiveValue<string>", "required": False, "description": "Row gap"},
                    {"name": "columnGap", "type": "ResponsiveValue<string>", "required": False, "description": "Column gap"},
                    {"name": "autoFlow", "type": "ResponsiveValue<string>", "required": False, "description": "Grid auto flow"}
                ],
                variants=["SimpleGrid"],
                examples=[
                    '<Grid templateColumns="repeat(3, 1fr)" gap={6}><GridItem>1</GridItem><GridItem>2</GridItem></Grid>',
                    '<SimpleGrid columns={[1, 2, 3]} spacing={4}><Box bg="blue.100">Item 1</Box><Box bg="green.100">Item 2</Box></SimpleGrid>'
                ],
                description="Grid is a primitive useful for building CSS Grid layouts.",
                category="layout",
                tags=["layout", "grid", "responsive"],
                dependencies=[],
                typescript_types="GridProps extends HTMLChakraProps<'div'>",
                accessibility_features=["Screen reader friendly", "Keyboard navigation"],
                design_tokens_used=["spacing"]
            ),
            
            # Form Components
            UIComponent(
                name="Button",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "variant", "type": "'solid' | 'outline' | 'ghost' | 'link' | 'unstyled'", "required": False, "description": "Button variant"},
                    {"name": "size", "type": "'xs' | 'sm' | 'md' | 'lg'", "required": False, "description": "Button size"},
                    {"name": "colorScheme", "type": "string", "required": False, "description": "Color scheme"},
                    {"name": "isLoading", "type": "boolean", "required": False, "description": "Loading state"},
                    {"name": "loadingText", "type": "string", "required": False, "description": "Loading text"},
                    {"name": "isDisabled", "type": "boolean", "required": False, "description": "Disabled state"},
                    {"name": "leftIcon", "type": "ReactElement", "required": False, "description": "Left icon"},
                    {"name": "rightIcon", "type": "ReactElement", "required": False, "description": "Right icon"}
                ],
                variants=["solid", "outline", "ghost", "link", "unstyled"],
                examples=[
                    '<Button colorScheme="blue">Primary Button</Button>',
                    '<Button variant="outline" colorScheme="teal" size="lg">Large Outline</Button>',
                    '<Button isLoading loadingText="Saving...">Save</Button>',
                    '<Button leftIcon={<AddIcon />} colorScheme="green">Add Item</Button>'
                ],
                description="Button component is used to trigger an action or event.",
                category="form",
                tags=["form", "interactive", "action"],
                dependencies=[],
                typescript_types="ButtonProps extends HTMLChakraProps<'button'>",
                accessibility_features=["ARIA attributes", "Keyboard support", "Focus management", "Loading states"],
                design_tokens_used=["colors", "spacing", "radii", "fontSizes"]
            ),
            
            UIComponent(
                name="Input",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "variant", "type": "'outline' | 'filled' | 'flushed' | 'unstyled'", "required": False, "description": "Input variant"},
                    {"name": "size", "type": "'xs' | 'sm' | 'md' | 'lg'", "required": False, "description": "Input size"},
                    {"name": "focusBorderColor", "type": "string", "required": False, "description": "Focus border color"},
                    {"name": "errorBorderColor", "type": "string", "required": False, "description": "Error border color"},
                    {"name": "isInvalid", "type": "boolean", "required": False, "description": "Invalid state"},
                    {"name": "isDisabled", "type": "boolean", "required": False, "description": "Disabled state"},
                    {"name": "isReadOnly", "type": "boolean", "required": False, "description": "Read-only state"},
                    {"name": "placeholder", "type": "string", "required": False, "description": "Placeholder text"}
                ],
                variants=["outline", "filled", "flushed", "unstyled"],
                examples=[
                    '<Input placeholder="Enter text..." />',
                    '<Input variant="filled" size="lg" focusBorderColor="blue.500" />',
                    '<Input isInvalid errorBorderColor="red.300" />',
                    '<InputGroup><InputLeftElement><SearchIcon /></InputLeftElement><Input placeholder="Search..." /></InputGroup>'
                ],
                description="Input component is a component that is used to get user input in a text field.",
                category="form",
                tags=["form", "input", "text"],
                dependencies=[],
                typescript_types="InputProps extends HTMLChakraProps<'input'>",
                accessibility_features=["ARIA labels", "Focus management", "Error states", "Placeholder support"],
                design_tokens_used=["colors", "spacing", "radii", "fontSizes", "borders"]
            ),
            
            UIComponent(
                name="FormControl",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "isInvalid", "type": "boolean", "required": False, "description": "Invalid state"},
                    {"name": "isRequired", "type": "boolean", "required": False, "description": "Required state"},
                    {"name": "isDisabled", "type": "boolean", "required": False, "description": "Disabled state"},
                    {"name": "isReadOnly", "type": "boolean", "required": False, "description": "Read-only state"}
                ],
                variants=["with validation states"],
                examples=[
                    '<FormControl><FormLabel>Email</FormLabel><Input type="email" /><FormHelperText>We will never share your email.</FormHelperText></FormControl>',
                    '<FormControl isRequired isInvalid><FormLabel>Name</FormLabel><Input /><FormErrorMessage>Name is required.</FormErrorMessage></FormControl>'
                ],
                description="FormControl provides context such as isInvalid, isDisabled, and isRequired to form elements.",
                category="form",
                tags=["form", "validation", "accessibility"],
                dependencies=["FormLabel", "FormHelperText", "FormErrorMessage"],
                typescript_types="FormControlProps extends HTMLChakraProps<'div'>",
                accessibility_features=["ARIA attributes", "Form validation", "Screen reader support", "Error states"],
                design_tokens_used=["colors", "spacing"]
            ),
            
            # Data Display Components
            UIComponent(
                name="Text",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "fontSize", "type": "ResponsiveValue<string>", "required": False, "description": "Font size"},
                    {"name": "fontWeight", "type": "ResponsiveValue<string>", "required": False, "description": "Font weight"},
                    {"name": "color", "type": "string", "required": False, "description": "Text color"},
                    {"name": "align", "type": "ResponsiveValue<'left' | 'center' | 'right' | 'justify'>", "required": False, "description": "Text alignment"},
                    {"name": "decoration", "type": "string", "required": False, "description": "Text decoration"},
                    {"name": "transform", "type": "string", "required": False, "description": "Text transform"},
                    {"name": "noOfLines", "type": "number", "required": False, "description": "Number of lines to truncate"}
                ],
                variants=["responsive typography"],
                examples=[
                    '<Text fontSize="xl" fontWeight="bold">Heading Text</Text>',
                    '<Text color="gray.500" noOfLines={2}>Long text that will be truncated after two lines...</Text>',
                    '<Text as="mark" bg="yellow.200">Highlighted text</Text>'
                ],
                description="Text component is the used to render text and paragraphs within an interface.",
                category="typography",
                tags=["typography", "text", "content"],
                dependencies=[],
                typescript_types="TextProps extends HTMLChakraProps<'p'>",
                accessibility_features=["Semantic HTML", "Screen reader friendly", "Text truncation"],
                design_tokens_used=["fontSizes", "fontWeights", "colors", "lineHeights"]
            ),
            
            UIComponent(
                name="Heading",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "as", "type": "'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'", "required": False, "description": "HTML heading element"},
                    {"name": "size", "type": "'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl'", "required": False, "description": "Heading size"},
                    {"name": "color", "type": "string", "required": False, "description": "Text color"},
                    {"name": "fontWeight", "type": "ResponsiveValue<string>", "required": False, "description": "Font weight"},
                    {"name": "fontFamily", "type": "string", "required": False, "description": "Font family"}
                ],
                variants=["h1", "h2", "h3", "h4", "h5", "h6"],
                examples=[
                    '<Heading as="h1" size="xl">Page Title</Heading>',
                    '<Heading as="h2" size="lg" color="blue.500">Section Title</Heading>',
                    '<Heading size="md" fontWeight="semibold">Card Title</Heading>'
                ],
                description="Heading component is used to render semantic HTML heading elements.",
                category="typography",
                tags=["typography", "heading", "semantic"],
                dependencies=[],
                typescript_types="HeadingProps extends HTMLChakraProps<'h1'>",
                accessibility_features=["Semantic HTML", "Heading hierarchy", "Screen reader navigation"],
                design_tokens_used=["fontSizes", "fontWeights", "colors", "lineHeights"]
            ),
            
            UIComponent(
                name="Badge",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "variant", "type": "'solid' | 'subtle' | 'outline'", "required": False, "description": "Badge variant"},
                    {"name": "colorScheme", "type": "string", "required": False, "description": "Color scheme"},
                    {"name": "size", "type": "'sm' | 'md' | 'lg'", "required": False, "description": "Badge size"}
                ],
                variants=["solid", "subtle", "outline"],
                examples=[
                    '<Badge colorScheme="green">Success</Badge>',
                    '<Badge variant="outline" colorScheme="purple">New</Badge>',
                    '<Badge colorScheme="red" variant="subtle">Error</Badge>'
                ],
                description="Badge component is used to display the status of an item.",
                category="data-display",
                tags=["status", "label", "indicator"],
                dependencies=[],
                typescript_types="BadgeProps extends HTMLChakraProps<'span'>",
                accessibility_features=["Screen reader support", "Color contrast", "Status indication"],
                design_tokens_used=["colors", "fontSizes", "radii", "spacing"]
            ),
            
            UIComponent(
                name="Card",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "variant", "type": "'elevated' | 'outline' | 'filled' | 'unstyled'", "required": False, "description": "Card variant"},
                    {"name": "size", "type": "'sm' | 'md' | 'lg'", "required": False, "description": "Card size"},
                    {"name": "colorScheme", "type": "string", "required": False, "description": "Color scheme"},
                    {"name": "direction", "type": "'row' | 'column'", "required": False, "description": "Card direction"}
                ],
                variants=["elevated", "outline", "filled", "unstyled"],
                examples=[
                    '<Card><CardHeader><Heading>Title</Heading></CardHeader><CardBody><Text>Content</Text></CardBody></Card>',
                    '<Card variant="outline" size="lg"><CardBody><VStack align="start"><Heading size="md">Card Title</Heading><Text>Card description</Text></VStack></CardBody></Card>'
                ],
                description="Card component is a flexible container for displaying content in a structured format.",
                category="data-display",
                tags=["container", "content", "layout"],
                dependencies=["CardHeader", "CardBody", "CardFooter"],
                typescript_types="CardProps extends HTMLChakraProps<'div'>",
                accessibility_features=["Semantic structure", "Focus management", "Screen reader support"],
                design_tokens_used=["colors", "shadows", "radii", "spacing"]
            ),
            
            # Feedback Components
            UIComponent(
                name="Alert",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "status", "type": "'error' | 'success' | 'warning' | 'info' | 'loading'", "required": False, "description": "Alert status"},
                    {"name": "variant", "type": "'subtle' | 'left-accent' | 'top-accent' | 'solid'", "required": False, "description": "Alert variant"},
                    {"name": "colorScheme", "type": "string", "required": False, "description": "Color scheme"}
                ],
                variants=["subtle", "left-accent", "top-accent", "solid"],
                examples=[
                    '<Alert status="success"><AlertIcon />Data uploaded successfully!</Alert>',
                    '<Alert status="error" variant="left-accent"><AlertIcon /><AlertTitle>Error!</AlertTitle><AlertDescription>Something went wrong.</AlertDescription></Alert>'
                ],
                description="Alert component is used to communicate the state or status of a page, feature, or action.",
                category="feedback",
                tags=["feedback", "status", "notification"],
                dependencies=["AlertIcon", "AlertTitle", "AlertDescription"],
                typescript_types="AlertProps extends HTMLChakraProps<'div'>",
                accessibility_features=["ARIA live regions", "Status communication", "Icon semantics", "Screen reader announcements"],
                design_tokens_used=["colors", "spacing", "radii"]
            ),
            
            UIComponent(
                name="Toast",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "title", "type": "string", "required": False, "description": "Toast title"},
                    {"name": "description", "type": "string", "required": False, "description": "Toast description"},
                    {"name": "status", "type": "'error' | 'success' | 'warning' | 'info' | 'loading'", "required": False, "description": "Toast status"},
                    {"name": "duration", "type": "number", "required": False, "description": "Duration in milliseconds"},
                    {"name": "isClosable", "type": "boolean", "required": False, "description": "Closable state"},
                    {"name": "position", "type": "string", "required": False, "description": "Toast position"},
                    {"name": "variant", "type": "'solid' | 'subtle' | 'left-accent' | 'top-accent'", "required": False, "description": "Toast variant"}
                ],
                variants=["solid", "subtle", "left-accent", "top-accent"],
                examples=[
                    'toast({ title: "Success", description: "Data saved successfully!", status: "success", duration: 3000, isClosable: true })',
                    'toast({ title: "Error", description: "Failed to save data", status: "error", variant: "left-accent" })'
                ],
                description="Toast component is used to give feedback to users after an action has taken place.",
                category="feedback",
                tags=["feedback", "notification", "temporary"],
                dependencies=["useToast hook"],
                typescript_types="UseToastOptions interface",
                accessibility_features=["ARIA live regions", "Keyboard dismissal", "Auto-focus management", "Screen reader announcements"],
                design_tokens_used=["colors", "spacing", "radii", "shadows"]
            ),
            
            # Navigation Components  
            UIComponent(
                name="Breadcrumb",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "separator", "type": "ReactElement | string", "required": False, "description": "Breadcrumb separator"},
                    {"name": "spacing", "type": "ResponsiveValue<string>", "required": False, "description": "Spacing between items"}
                ],
                variants=["with custom separators"],
                examples=[
                    '<Breadcrumb><BreadcrumbItem><BreadcrumbLink href="/">Home</BreadcrumbLink></BreadcrumbItem><BreadcrumbItem isCurrentPage><BreadcrumbLink href="/products">Products</BreadcrumbLink></BreadcrumbItem></Breadcrumb>',
                    '<Breadcrumb separator={<ChevronRightIcon />}><BreadcrumbItem><BreadcrumbLink>Home</BreadcrumbLink></BreadcrumbItem><BreadcrumbItem><BreadcrumbLink>Category</BreadcrumbLink></BreadcrumbItem></Breadcrumb>'
                ],
                description="Breadcrumb component helps users understand where they are in a website's hierarchy.",
                category="navigation",
                tags=["navigation", "hierarchy", "wayfinding"],
                dependencies=["BreadcrumbItem", "BreadcrumbLink"],
                typescript_types="BreadcrumbProps extends HTMLChakraProps<'nav'>",
                accessibility_features=["ARIA navigation", "Current page indication", "Screen reader support", "Keyboard navigation"],
                design_tokens_used=["colors", "fontSizes", "spacing"]
            ),
            
            UIComponent(
                name="Tabs",
                import_path="@chakra-ui/react",
                props=[
                    {"name": "variant", "type": "'line' | 'enclosed' | 'enclosed-colored' | 'soft-rounded' | 'solid-rounded' | 'unstyled'", "required": False, "description": "Tab variant"},
                    {"name": "orientation", "type": "'horizontal' | 'vertical'", "required": False, "description": "Tab orientation"},
                    {"name": "size", "type": "'sm' | 'md' | 'lg'", "required": False, "description": "Tab size"},
                    {"name": "colorScheme", "type": "string", "required": False, "description": "Color scheme"},
                    {"name": "index", "type": "number", "required": False, "description": "Controlled index"},
                    {"name": "defaultIndex", "type": "number", "required": False, "description": "Default index"},
                    {"name": "onChange", "type": "function", "required": False, "description": "Change handler"}
                ],
                variants=["line", "enclosed", "enclosed-colored", "soft-rounded", "solid-rounded", "unstyled"],
                examples=[
                    '<Tabs><TabList><Tab>One</Tab><Tab>Two</Tab></TabList><TabPanels><TabPanel>Panel 1</TabPanel><TabPanel>Panel 2</TabPanel></TabPanels></Tabs>',
                    '<Tabs variant="soft-rounded" colorScheme="green"><TabList><Tab>Account</Tab><Tab>Settings</Tab></TabList><TabPanels><TabPanel>Account Panel</TabPanel><TabPanel>Settings Panel</TabPanel></TabPanels></Tabs>'
                ],
                description="Tabs component is used to organize content into multiple sections that can be accessed via clickable tabs.",
                category="navigation",
                tags=["navigation", "tabs", "content-organization"],
                dependencies=["TabList", "Tab", "TabPanels", "TabPanel"],
                typescript_types="TabsProps extends HTMLChakraProps<'div'>",
                accessibility_features=["ARIA tablist", "Keyboard navigation", "Focus management", "Screen reader support"],
                design_tokens_used=["colors", "spacing", "radii", "borders"]
            )
        ]
    
    async def get_design_tokens(self) -> Dict[str, Any]:
        """Get Chakra UI design tokens."""
        return {
            "colors": {
                "gray": {
                    "50": "#F7FAFC",
                    "100": "#EDF2F7",
                    "200": "#E2E8F0",
                    "300": "#CBD5E0",
                    "400": "#A0AEC0",
                    "500": "#718096",
                    "600": "#4A5568",
                    "700": "#2D3748",
                    "800": "#1A202C",
                    "900": "#171923"
                },
                "red": {
                    "50": "#FED7D7",
                    "100": "#FEB2B2",
                    "200": "#FC8181",
                    "300": "#F56565",
                    "400": "#E53E3E",
                    "500": "#C53030",
                    "600": "#9B2C2C",
                    "700": "#742A2A",
                    "800": "#63171B",
                    "900": "#1A202C"
                },
                "blue": {
                    "50": "#EBF8FF",
                    "100": "#BEE3F8",
                    "200": "#90CDF4",
                    "300": "#63B3ED",
                    "400": "#4299E1",
                    "500": "#3182CE",
                    "600": "#2B6CB0",
                    "700": "#2C5282",
                    "800": "#2A4365",
                    "900": "#1A365D"
                },
                "green": {
                    "50": "#F0FFF4",
                    "100": "#C6F6D5",
                    "200": "#9AE6B4",
                    "300": "#68D391",
                    "400": "#48BB78",
                    "500": "#38A169",
                    "600": "#2F855A",
                    "700": "#276749",
                    "800": "#22543D",
                    "900": "#1C4532"
                }
            },
            "spacing": {
                "px": "1px",
                "0.5": "0.125rem",
                "1": "0.25rem",
                "1.5": "0.375rem",
                "2": "0.5rem",
                "2.5": "0.625rem",
                "3": "0.75rem",
                "3.5": "0.875rem",
                "4": "1rem",
                "5": "1.25rem",
                "6": "1.5rem",
                "7": "1.75rem",
                "8": "2rem",
                "9": "2.25rem",
                "10": "2.5rem",
                "12": "3rem",
                "14": "3.5rem",
                "16": "4rem",
                "20": "5rem",
                "24": "6rem",
                "28": "7rem",
                "32": "8rem",
                "36": "9rem",
                "40": "10rem",
                "44": "11rem",
                "48": "12rem",
                "52": "13rem",
                "56": "14rem",
                "60": "15rem",
                "64": "16rem",
                "72": "18rem",
                "80": "20rem",
                "96": "24rem"
            },
            "fontSizes": {
                "xs": "0.75rem",
                "sm": "0.875rem",
                "md": "1rem",
                "lg": "1.125rem",
                "xl": "1.25rem",
                "2xl": "1.5rem",
                "3xl": "1.875rem",
                "4xl": "2.25rem",
                "5xl": "3rem",
                "6xl": "3.75rem",
                "7xl": "4.5rem",
                "8xl": "6rem",
                "9xl": "8rem"
            },
            "fontWeights": {
                "hairline": 100,
                "thin": 200,
                "light": 300,
                "normal": 400,
                "medium": 500,
                "semibold": 600,
                "bold": 700,
                "extrabold": 800,
                "black": 900
            },
            "radii": {
                "none": "0",
                "sm": "0.125rem",
                "base": "0.25rem",
                "md": "0.375rem",
                "lg": "0.5rem",
                "xl": "0.75rem",
                "2xl": "1rem",
                "3xl": "1.5rem",
                "full": "9999px"
            },
            "shadows": {
                "xs": "0 0 0 1px rgba(0, 0, 0, 0.05)",
                "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
                "base": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
                "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
                "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
                "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
                "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)"
            }
        }
    
    async def get_openai_system_prompt(self) -> str:
        """Get OpenAI-optimized system prompt for Chakra UI."""
        return """You are an expert React developer specializing in Chakra UI. You create high-quality, accessible, and responsive React components using Chakra UI's component library and design system.

**Chakra UI Expertise:**
- Always use Chakra UI components from '@chakra-ui/react' 
- Follow Chakra UI's design system principles and color palette
- Use responsive props with array syntax: [mobile, tablet, desktop]
- Prefer Chakra UI's built-in accessibility features
- Use proper color schemes: gray, red, orange, yellow, green, teal, blue, cyan, purple, pink
- Apply consistent spacing using Chakra's spacing scale (1-96, px, rem values)

**Component Standards:**
- Write TypeScript by default with proper prop interfaces
- Use semantic HTML through Chakra's 'as' prop when appropriate
- Implement proper ARIA attributes and accessibility patterns
- Follow responsive design with mobile-first approach
- Use Chakra's theming and variant systems

**Code Quality:**
- Export components as default exports
- Use consistent naming conventions (PascalCase for components)
- Include proper imports from '@chakra-ui/react'
- Add helpful comments for complex logic
- Follow React best practices and hooks guidelines

**Design Principles:**
- Maintain visual hierarchy with proper heading levels (h1-h6)
- Use appropriate color contrasts for accessibility
- Apply consistent spacing and sizing
- Leverage Chakra's built-in responsive breakpoints
- Use loading states and feedback patterns

Generate clean, production-ready code that follows these standards and leverages Chakra UI's full potential."""
    
    async def get_openai_examples(self) -> List[Dict[str, str]]:
        """Get OpenAI few-shot examples for Chakra UI."""
        return [
            {
                "prompt": "Create a responsive card component with title, description, and action button",
                "response": """import { Box, Card, CardBody, CardFooter, Heading, Text, Button, VStack } from '@chakra-ui/react';

interface ProductCardProps {
  title: string;
  description: string;
  price: string;
  onAddToCart: () => void;
}

const ProductCard: React.FC<ProductCardProps> = ({ title, description, price, onAddToCart }) => {
  return (
    <Card maxW="sm" variant="outline" _hover={{ shadow: "md" }}>
      <CardBody>
        <VStack align="start" spacing={3}>
          <Heading size="md" color="gray.700">
            {title}
          </Heading>
          <Text color="gray.600" noOfLines={3}>
            {description}
          </Text>
          <Text fontSize="xl" fontWeight="bold" color="blue.500">
            {price}
          </Text>
        </VStack>
      </CardBody>
      <CardFooter>
        <Button 
          colorScheme="blue" 
          size="sm" 
          onClick={onAddToCart}
          w="full"
        >
          Add to Cart
        </Button>
      </CardFooter>
    </Card>
  );
};

export default ProductCard;"""
            },
            {
                "prompt": "Build a form component with validation for user registration",
                "response": """import { 
  VStack, 
  FormControl, 
  FormLabel, 
  FormErrorMessage, 
  Input, 
  Button, 
  useToast 
} from '@chakra-ui/react';
import { useState } from 'react';

interface RegistrationFormData {
  email: string;
  password: string;
  confirmPassword: string;
}

interface RegistrationFormProps {
  onSubmit: (data: RegistrationFormData) => Promise<void>;
}

const RegistrationForm: React.FC<RegistrationFormProps> = ({ onSubmit }) => {
  const [formData, setFormData] = useState<RegistrationFormData>({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState<Partial<RegistrationFormData>>({});
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const validateForm = (): boolean => {
    const newErrors: Partial<RegistrationFormData> = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\\S+@\\S+\\.\\S+/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsLoading(true);
    
    try {
      await onSubmit(formData);
      toast({
        title: "Registration successful!",
        status: "success",
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: "Registration failed",
        description: "Please try again later",
        status: "error",
        duration: 3000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: keyof RegistrationFormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <VStack as="form" onSubmit={handleSubmit} spacing={4} w="full" maxW="md">
      <FormControl isInvalid={!!errors.email} isRequired>
        <FormLabel>Email</FormLabel>
        <Input
          type="email"
          value={formData.email}
          onChange={handleChange('email')}
          focusBorderColor="blue.500"
        />
        <FormErrorMessage>{errors.email}</FormErrorMessage>
      </FormControl>

      <FormControl isInvalid={!!errors.password} isRequired>
        <FormLabel>Password</FormLabel>
        <Input
          type="password"
          value={formData.password}
          onChange={handleChange('password')}
          focusBorderColor="blue.500"
        />
        <FormErrorMessage>{errors.password}</FormErrorMessage>
      </FormControl>

      <FormControl isInvalid={!!errors.confirmPassword} isRequired>
        <FormLabel>Confirm Password</FormLabel>
        <Input
          type="password"
          value={formData.confirmPassword}
          onChange={handleChange('confirmPassword')}
          focusBorderColor="blue.500"
        />
        <FormErrorMessage>{errors.confirmPassword}</FormErrorMessage>
      </FormControl>

      <Button
        type="submit"
        colorScheme="blue"
        size="lg"
        w="full"
        isLoading={isLoading}
        loadingText="Creating account..."
      >
        Create Account
      </Button>
    </VStack>
  );
};

export default RegistrationForm;"""
            },
            {
                "prompt": "Create a responsive navigation header with menu items and user profile",
                "response": """import {
  Box,
  Flex,
  Heading,
  Spacer,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Avatar,
  HStack,
  useDisclosure,
  IconButton,
  VStack,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useBreakpointValue
} from '@chakra-ui/react';
import { HamburgerIcon } from '@chakra-ui/icons';

interface NavItem {
  label: string;
  href: string;
}

interface User {
  name: string;
  email: string;
  avatar?: string;
}

interface NavigationHeaderProps {
  user?: User;
  navItems: NavItem[];
  onLogin: () => void;
  onLogout: () => void;
}

const NavigationHeader: React.FC<NavigationHeaderProps> = ({ 
  user, 
  navItems, 
  onLogin, 
  onLogout 
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const isMobile = useBreakpointValue({ base: true, md: false });

  const NavLinks = ({ items }: { items: NavItem[] }) => (
    <HStack spacing={6}>
      {items.map((item) => (
        <Button key={item.href} variant="ghost" as="a" href={item.href}>
          {item.label}
        </Button>
      ))}
    </HStack>
  );

  const UserSection = () => {
    if (!user) {
      return <Button colorScheme="blue" onClick={onLogin}>Login</Button>;
    }

    return (
      <Menu>
        <MenuButton>
          <Avatar size="sm" name={user.name} src={user.avatar} />
        </MenuButton>
        <MenuList>
          <MenuItem>Profile</MenuItem>
          <MenuItem>Settings</MenuItem>
          <MenuItem onClick={onLogout} color="red.500">
            Logout
          </MenuItem>
        </MenuList>
      </Menu>
    );
  };

  return (
    <Box bg="white" shadow="sm" w="full">
      <Flex maxW="7xl" mx="auto" px={[4, 6]} py={4} align="center">
        <Heading size="lg" color="blue.600">
          YourApp
        </Heading>

        <Spacer />

        {isMobile ? (
          <IconButton
            aria-label="Open menu"
            icon={<HamburgerIcon />}
            variant="ghost"
            onClick={onOpen}
          />
        ) : (
          <HStack spacing={6}>
            <NavLinks items={navItems} />
            <UserSection />
          </HStack>
        )}
      </Flex>

      {/* Mobile Drawer */}
      <Drawer isOpen={isOpen} onClose={onClose} placement="right">
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>Menu</DrawerHeader>
          <DrawerBody>
            <VStack align="start" spacing={4}>
              {navItems.map((item) => (
                <Button key={item.href} variant="ghost" as="a" href={item.href} w="full" justifyContent="start">
                  {item.label}
                </Button>
              ))}
              <Box pt={4} w="full">
                <UserSection />
              </Box>
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};

export default NavigationHeader;"""
            }
        ]
    
    async def validate_component_usage(self, component_code: str) -> Dict[str, Any]:
        """Validate component code against Chakra UI best practices."""
        issues = []
        suggestions = []
        
        # Check for proper imports
        if '@chakra-ui/react' not in component_code:
            issues.append({
                "type": "error",
                "category": "imports",
                "message": "Missing Chakra UI import",
                "suggestion": "Import components from '@chakra-ui/react'"
            })
        
        # Check for proper color usage
        import re
        
        # Check for hardcoded colors instead of Chakra colors
        hardcoded_colors = re.findall(r'color\s*[:=]\s*["\']#[0-9a-fA-F]{3,6}["\']', component_code)
        if hardcoded_colors:
            issues.append({
                "type": "warning", 
                "category": "colors",
                "message": f"Found {len(hardcoded_colors)} hardcoded colors",
                "suggestion": "Use Chakra UI color palette (e.g., 'blue.500', 'gray.600')"
            })
        
        # Check for responsive patterns
        if not any(pattern in component_code for pattern in ['[', 'base:', 'md:', 'lg:']):
            suggestions.append({
                "type": "info",
                "category": "responsive",
                "message": "Consider adding responsive design",
                "suggestion": "Use responsive props like fontSize={['sm', 'md', 'lg']}"
            })
        
        # Check for accessibility
        if '<Button' in component_code and 'aria-label' not in component_code:
            suggestions.append({
                "type": "info",
                "category": "accessibility", 
                "message": "Consider adding aria-label to buttons",
                "suggestion": "Add aria-label for better accessibility"
            })
        
        # Check for TypeScript usage
        if 'interface' not in component_code and 'type' not in component_code:
            suggestions.append({
                "type": "info",
                "category": "typescript",
                "message": "Consider adding TypeScript interfaces",
                "suggestion": "Define prop interfaces for better type safety"
            })
        
        score = max(0, 100 - (len(issues) * 15) - (len(suggestions) * 5))
        
        return {
            "valid": len(issues) == 0,
            "score": score,
            "issues": issues,
            "suggestions": suggestions,
            "library": "Chakra UI"
        }
    
    async def suggest_component_alternatives(self, component_name: str) -> List[str]:
        """Suggest alternative Chakra UI components."""
        alternatives = {
            "div": ["Box", "Container", "Center", "Square", "Circle"],
            "button": ["Button", "IconButton", "ButtonGroup"],
            "input": ["Input", "Textarea", "NumberInput", "PinInput"],
            "img": ["Image", "Avatar"],
            "p": ["Text", "Heading"],
            "span": ["Text", "Badge", "Tag"],
            "form": ["FormControl", "Stack", "VStack"],
            "ul": ["List", "Stack", "VStack"],
            "nav": ["Breadcrumb", "Tabs", "Menu"]
        }
        
        return alternatives.get(component_name.lower(), [])
    
    async def generate_usage_example(self, component_name: str, props: Dict[str, Any] = None) -> str:
        """Generate usage example for a Chakra UI component."""
        props = props or {}
        
        examples = {
            "Button": f'<Button colorScheme="blue" size="md" {self._format_props(props)}>Click me</Button>',
            "Input": f'<Input placeholder="Enter text..." {self._format_props(props)} />',
            "Box": f'<Box p={4} bg="gray.50" {self._format_props(props)}>Content</Box>',
            "Text": f'<Text fontSize="md" {self._format_props(props)}>Your text here</Text>',
            "Heading": f'<Heading as="h2" size="lg" {self._format_props(props)}>Your heading</Heading>',
            "Stack": f'<Stack spacing={4} {self._format_props(props)}><Box>Item 1</Box><Box>Item 2</Box></Stack>',
            "Card": f'<Card {self._format_props(props)}><CardBody><Text>Card content</Text></CardBody></Card>',
            "Alert": f'<Alert status="info" {self._format_props(props)}><AlertIcon />Alert message</Alert>'
        }
        
        return examples.get(component_name, f'<{component_name} {self._format_props(props)} />')
    
    def _format_props(self, props: Dict[str, Any]) -> str:
        """Format props dictionary into JSX props string."""
        if not props:
            return ""
        
        prop_strings = []
        for key, value in props.items():
            if isinstance(value, bool):
                if value:
                    prop_strings.append(key)
            elif isinstance(value, str):
                prop_strings.append(f'{key}="{value}"')
            else:
                prop_strings.append(f'{key}={{{value}}}')
        
        return " ".join(prop_strings)
    
    # Implementation of abstract methods
    
    async def _get_library_version(self) -> str:
        return "2.8.0"
    
    async def _get_theme_config(self) -> Dict[str, Any]:
        return {
            "colors": "Chakra UI color palette with semantic tokens",
            "fonts": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            "components": "Comprehensive component theme overrides",
            "config": {
                "initialColorMode": "light",
                "useSystemColorMode": False
            }
        }
    
    async def _get_installation_guide(self) -> str:
        return """# Chakra UI Installation Guide

## NPM Installation
```bash
npm i @chakra-ui/react @emotion/react @emotion/styled framer-motion
```

## Yarn Installation  
```bash
yarn add @chakra-ui/react @emotion/react @emotion/styled framer-motion
```

## Setup Provider
```tsx
import { ChakraProvider } from '@chakra-ui/react'

function App() {
  return (
    <ChakraProvider>
      <App />
    </ChakraProvider>
  )
}
```

## TypeScript Support
Chakra UI provides excellent TypeScript support out of the box. No additional setup required.

## Theme Customization
```tsx
import { extendTheme } from '@chakra-ui/react'

const theme = extendTheme({
  colors: {
    brand: {
      900: '#1a365d',
      800: '#153e75',
      700: '#2a69ac',
    },
  },
})
```
"""
    
    async def _get_best_practices(self) -> List[str]:
        return [
            "Use responsive props with array syntax for mobile-first design",
            "Leverage Chakra UI's color palette instead of hardcoded hex colors",
            "Utilize the 'as' prop for semantic HTML while maintaining styling",
            "Implement proper TypeScript interfaces for component props",
            "Take advantage of Chakra's built-in accessibility features",
            "Use Stack components for consistent spacing between elements",
            "Apply theme customization through extendTheme for consistency",
            "Utilize useColorModeValue for proper dark mode support",
            "Implement proper form validation with FormControl components",
            "Use Chakra's responsive breakpoints for consistent behavior"
        ]
    
    async def _get_common_patterns(self) -> List[str]:
        return [
            "Layout: Use Box and Stack components for flexible layouts",
            "Forms: Combine FormControl, FormLabel, and Input components",
            "Cards: Structure with Card, CardHeader, CardBody, CardFooter",
            "Navigation: Build with Breadcrumb, Tabs, or Menu components",
            "Feedback: Implement with Alert, Toast, or loading states",
            "Responsive: Use array syntax props and useBreakpointValue hook",
            "Theming: Extend theme with custom colors and component variants",
            "State Management: Integrate with React hooks and state libraries",
            "Accessibility: Leverage built-in ARIA attributes and focus management",
            "Animation: Use Chakra's animation props with Framer Motion"
        ]
    
    async def _has_typescript_support(self) -> bool:
        return True
    
    async def _get_library_migration_map(self) -> Dict[str, str]:
        return {
            # Material-UI to Chakra UI
            "@material-ui/core": "@chakra-ui/react",
            "@mui/material": "@chakra-ui/react", 
            
            # Bootstrap to Chakra UI
            "react-bootstrap": "@chakra-ui/react",
            
            # Ant Design to Chakra UI
            "antd": "@chakra-ui/react",
            
            # Mantine to Chakra UI
            "@mantine/core": "@chakra-ui/react"
        }
    
    async def _get_theme_customization_guide(self) -> str:
        return """# Chakra UI Theme Customization

## Extending the Default Theme
```tsx
import { extendTheme } from '@chakra-ui/react'

const theme = extendTheme({
  colors: {
    brand: {
      900: '#1a365d',
      800: '#153e75', 
      700: '#2a69ac',
    },
  },
  fonts: {
    heading: 'Open Sans, sans-serif',
    body: 'Raleway, sans-serif',
  },
})
```

## Component Theming
```tsx
const theme = extendTheme({
  components: {
    Button: {
      variants: {
        solid: {
          bg: 'brand.500',
          _hover: { bg: 'brand.600' }
        }
      }
    }
  }
})
```

## Global Styles
```tsx
const theme = extendTheme({
  styles: {
    global: {
      body: {
        bg: 'gray.50',
        color: 'gray.800'
      }
    }
  }
})
```
"""


async def main():
    """Main server loop."""
    parser = argparse.ArgumentParser(description="Chakra UI MCP Server")
    parser.add_argument("--project", default=".", help="Project path to analyze")
    args = parser.parse_args()
    
    server = ChakraUIMCPServer(args.project)
    
    # Initialize
    init_result = await server.initialize()
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": init_result
    }))
    
    # Main message loop
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                message = json.loads(line.strip())
                response = {"jsonrpc": "2.0", "id": message.get("id")}
                
                method = message.get("method")
                params = message.get("params", {})
                
                if method == "tools/list":
                    result = await server.list_tools()
                elif method == "resources/list":
                    result = await server.list_resources()
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await server.call_tool(tool_name, arguments)
                elif method == "resources/read":
                    uri = params.get("uri")
                    result = await server.read_resource(uri)
                else:
                    result = {"error": f"Unknown method: {method}"}
                
                response["result"] = result
                print(json.dumps(response))
                
            except json.JSONDecodeError:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"}
                }
                print(json.dumps(error_response))
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0", 
                    "id": message.get("id") if 'message' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response))
                
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())