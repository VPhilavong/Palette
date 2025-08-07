#!/usr/bin/env python3
"""
Sample Generation Scenarios for Palette Testing
Provides realistic test scenarios with expected outputs for validating the generation functionality.
These scenarios help users understand how to test the system and what results to expect.
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
import time

@dataclass
class GenerationScenario:
    id: str
    name: str
    description: str
    message: str
    complexity: str  # "simple", "medium", "complex"
    expected_files: List[str]
    expected_components: List[str]
    expected_features: List[str]
    test_project_type: str  # "vite-react-shadcn", "next-shadcn", etc.
    estimated_duration: int  # seconds
    validation_criteria: Dict[str, str]
    tags: List[str]

class SampleScenarioGenerator:
    def __init__(self):
        self.scenarios = []
        self.output_dir = Path(__file__).parent / "test_scenarios"
        
    def generate_all_scenarios(self):
        """Generate comprehensive test scenarios for different complexity levels"""
        print("🎯 Generating Sample Generation Scenarios")
        print("=" * 50)
        
        # Create scenarios for different complexity levels
        self.create_simple_scenarios()
        self.create_medium_scenarios() 
        self.create_complex_scenarios()
        self.create_edge_case_scenarios()
        
        # Save scenarios to files
        self.save_scenarios()
        self.create_testing_guide()
        
        print(f"\n✅ Generated {len(self.scenarios)} test scenarios")
        print(f"📁 Output directory: {self.output_dir}")
        
    def create_simple_scenarios(self):
        """Create simple generation scenarios"""
        simple_scenarios = [
            GenerationScenario(
                id="simple-button",
                name="Simple Button Component",
                description="Basic button component with primary/secondary variants",
                message="Create a button component with primary and secondary variants",
                complexity="simple",
                expected_files=["src/components/ui/button.tsx"],
                expected_components=["Button"],
                expected_features=["TypeScript types", "Tailwind styling", "Variant support"],
                test_project_type="vite-react-shadcn",
                estimated_duration=30,
                validation_criteria={
                    "typescript": "Should have proper TypeScript interface",
                    "styling": "Should use Tailwind CSS classes",
                    "accessibility": "Should have proper button type and aria attributes",
                    "reusability": "Should accept children and onClick props"
                },
                tags=["component", "ui", "basic"]
            ),
            
            GenerationScenario(
                id="simple-card",
                name="Card Component",
                description="Reusable card component with header, content, and footer slots",
                message="Create a card component with header, content area, and optional footer",
                complexity="simple",
                expected_files=["src/components/ui/card.tsx"],
                expected_components=["Card", "CardHeader", "CardContent", "CardFooter"],
                expected_features=["Compound component pattern", "Flexible layout", "TypeScript support"],
                test_project_type="vite-react-shadcn",
                estimated_duration=45,
                validation_criteria={
                    "structure": "Should use compound component pattern",
                    "styling": "Should have consistent spacing and borders",
                    "flexibility": "Should allow custom content in each section"
                },
                tags=["component", "ui", "layout"]
            ),
            
            GenerationScenario(
                id="simple-form",
                name="Contact Form",
                description="Basic contact form with validation",
                message="Create a contact form with name, email, and message fields with validation",
                complexity="simple",
                expected_files=["src/components/ContactForm.tsx"],
                expected_components=["ContactForm"],
                expected_features=["Form validation", "Error handling", "Submit functionality"],
                test_project_type="vite-react-shadcn",
                estimated_duration=60,
                validation_criteria={
                    "validation": "Should validate email format and required fields",
                    "accessibility": "Should have proper labels and error messages",
                    "ux": "Should provide clear feedback on form submission"
                },
                tags=["form", "validation", "user-input"]
            )
        ]
        
        self.scenarios.extend(simple_scenarios)
        
    def create_medium_scenarios(self):
        """Create medium complexity scenarios"""
        medium_scenarios = [
            GenerationScenario(
                id="medium-todo-app",
                name="Todo List Application",
                description="Interactive todo list with add, complete, delete, and filter functionality",
                message="Create a todo list app with add, complete, delete and filter (all/active/completed) functionality",
                complexity="medium",
                expected_files=[
                    "src/components/TodoApp.tsx",
                    "src/components/TodoItem.tsx", 
                    "src/components/TodoList.tsx",
                    "src/components/TodoFilters.tsx"
                ],
                expected_components=["TodoApp", "TodoItem", "TodoList", "TodoFilters"],
                expected_features=[
                    "State management with useState/useReducer",
                    "Local storage persistence",
                    "Filter functionality",
                    "CRUD operations"
                ],
                test_project_type="vite-react-shadcn",
                estimated_duration=120,
                validation_criteria={
                    "functionality": "Should support all CRUD operations",
                    "persistence": "Should save todos to localStorage",
                    "filtering": "Should filter todos by status",
                    "state": "Should manage complex state correctly"
                },
                tags=["app", "state-management", "crud", "interactive"]
            ),
            
            GenerationScenario(
                id="medium-image-gallery",
                name="Image Gallery with Modal",
                description="Responsive image gallery with lightbox modal for viewing full-size images",
                message="Create a responsive image gallery with thumbnail grid and modal lightbox for viewing full-size images",
                complexity="medium",
                expected_files=[
                    "src/components/ImageGallery.tsx",
                    "src/components/ImageModal.tsx",
                    "src/components/ImageThumbnail.tsx"
                ],
                expected_components=["ImageGallery", "ImageModal", "ImageThumbnail"],
                expected_features=[
                    "Responsive grid layout",
                    "Modal overlay",
                    "Navigation between images",
                    "Keyboard accessibility"
                ],
                test_project_type="vite-react-shadcn",
                estimated_duration=90,
                validation_criteria={
                    "responsive": "Should adapt to different screen sizes",
                    "accessibility": "Should support keyboard navigation",
                    "performance": "Should optimize image loading",
                    "ux": "Should provide smooth transitions"
                },
                tags=["gallery", "modal", "responsive", "media"]
            ),
            
            GenerationScenario(
                id="medium-data-table",
                name="Data Table with Sorting",
                description="Data table component with sorting, pagination, and search functionality",
                message="Create a data table that displays user data with sorting, pagination, and search functionality",
                complexity="medium", 
                expected_files=[
                    "src/components/DataTable.tsx",
                    "src/components/TableHeader.tsx",
                    "src/components/TablePagination.tsx",
                    "src/components/TableSearch.tsx"
                ],
                expected_components=["DataTable", "TableHeader", "TablePagination", "TableSearch"],
                expected_features=[
                    "Column sorting",
                    "Pagination controls",
                    "Search/filter functionality",
                    "Responsive design"
                ],
                test_project_type="vite-react-shadcn",
                estimated_duration=110,
                validation_criteria={
                    "sorting": "Should sort data by columns",
                    "pagination": "Should paginate large datasets",
                    "search": "Should filter data by search term",
                    "performance": "Should handle large datasets efficiently"
                },
                tags=["table", "data", "sorting", "pagination"]
            )
        ]
        
        self.scenarios.extend(medium_scenarios)
        
    def create_complex_scenarios(self):
        """Create complex, multi-file scenarios"""
        complex_scenarios = [
            GenerationScenario(
                id="complex-dashboard",
                name="Admin Dashboard",
                description="Complete admin dashboard with sidebar navigation, header, charts, and data tables",
                message="Create a complete admin dashboard with sidebar navigation, header with user profile, data visualization charts, and user management table",
                complexity="complex",
                expected_files=[
                    "src/pages/Dashboard.tsx",
                    "src/components/layout/Sidebar.tsx",
                    "src/components/layout/Header.tsx",
                    "src/components/layout/DashboardLayout.tsx",
                    "src/components/charts/BarChart.tsx",
                    "src/components/charts/LineChart.tsx",
                    "src/components/UserTable.tsx",
                    "src/components/StatsCards.tsx"
                ],
                expected_components=[
                    "Dashboard", "Sidebar", "Header", "DashboardLayout",
                    "BarChart", "LineChart", "UserTable", "StatsCards"
                ],
                expected_features=[
                    "Responsive layout with sidebar",
                    "Data visualization with charts",
                    "User management interface",
                    "Statistics overview cards",
                    "Mobile-responsive navigation"
                ],
                test_project_type="vite-react-shadcn",
                estimated_duration=300,
                validation_criteria={
                    "layout": "Should have proper dashboard layout structure",
                    "navigation": "Should include working navigation system",
                    "responsive": "Should work on mobile and desktop",
                    "data_viz": "Should display charts and data tables",
                    "composition": "Should properly compose multiple components"
                },
                tags=["dashboard", "admin", "charts", "layout", "complex"]
            ),
            
            GenerationScenario(
                id="complex-ecommerce",
                name="E-commerce Product Page",
                description="Complete e-commerce product page with gallery, details, reviews, and shopping cart integration",
                message="Create a complete e-commerce product page with image gallery, product details, customer reviews, related products, and add to cart functionality",
                complexity="complex",
                expected_files=[
                    "src/pages/ProductPage.tsx",
                    "src/components/product/ProductGallery.tsx",
                    "src/components/product/ProductInfo.tsx",
                    "src/components/product/ProductReviews.tsx",
                    "src/components/product/RelatedProducts.tsx",
                    "src/components/cart/AddToCartButton.tsx",
                    "src/components/product/ProductVariants.tsx",
                    "src/components/reviews/ReviewCard.tsx"
                ],
                expected_components=[
                    "ProductPage", "ProductGallery", "ProductInfo", "ProductReviews",
                    "RelatedProducts", "AddToCartButton", "ProductVariants", "ReviewCard"
                ],
                expected_features=[
                    "Image gallery with zoom",
                    "Product variant selection",
                    "Customer reviews system",
                    "Shopping cart integration",
                    "Related products recommendations"
                ],
                test_project_type="vite-react-shadcn",
                estimated_duration=350,
                validation_criteria={
                    "gallery": "Should have working image gallery with navigation",
                    "variants": "Should handle product variants (size, color, etc.)",
                    "reviews": "Should display and manage customer reviews",
                    "cart": "Should integrate with shopping cart functionality",
                    "ux": "Should provide excellent shopping experience"
                },
                tags=["ecommerce", "product", "gallery", "reviews", "cart"]
            ),
            
            GenerationScenario(
                id="complex-landing-page",
                name="SaaS Landing Page",
                description="Complete SaaS landing page with hero, features, testimonials, pricing, and CTA sections",
                message="Create a complete SaaS landing page with hero section, features showcase, customer testimonials, pricing tiers, and call-to-action sections",
                complexity="complex",
                expected_files=[
                    "src/pages/LandingPage.tsx",
                    "src/components/landing/HeroSection.tsx",
                    "src/components/landing/FeaturesSection.tsx",
                    "src/components/landing/TestimonialsSection.tsx",
                    "src/components/landing/PricingSection.tsx",
                    "src/components/landing/CTASection.tsx",
                    "src/components/landing/Navbar.tsx",
                    "src/components/landing/Footer.tsx"
                ],
                expected_components=[
                    "LandingPage", "HeroSection", "FeaturesSection", "TestimonialsSection",
                    "PricingSection", "CTASection", "Navbar", "Footer"
                ],
                expected_features=[
                    "Responsive design",
                    "Smooth scrolling navigation",
                    "Pricing comparison table",
                    "Customer testimonials carousel",
                    "Call-to-action optimization"
                ],
                test_project_type="vite-react-shadcn",
                estimated_duration=280,
                validation_criteria={
                    "design": "Should have modern, professional design",
                    "responsive": "Should work perfectly on all devices",
                    "conversion": "Should optimize for user conversion",
                    "performance": "Should load quickly and smoothly",
                    "sections": "Should have all required landing page sections"
                },
                tags=["landing-page", "saas", "marketing", "responsive", "conversion"]
            )
        ]
        
        self.scenarios.extend(complex_scenarios)
        
    def create_edge_case_scenarios(self):
        """Create edge case and specialized scenarios"""
        edge_scenarios = [
            GenerationScenario(
                id="edge-no-tailwind",
                name="Component Without Tailwind",
                description="Test generation in project without Tailwind CSS setup",
                message="Create a button component with styling in a project without Tailwind CSS",
                complexity="simple",
                expected_files=["src/components/Button.tsx"],
                expected_components=["Button"],
                expected_features=["CSS modules or styled-components", "Fallback styling approach"],
                test_project_type="no-tailwind",
                estimated_duration=45,
                validation_criteria={
                    "styling": "Should use alternative styling method",
                    "fallback": "Should work without Tailwind dependencies",
                    "adaptability": "Should adapt to project constraints"
                },
                tags=["edge-case", "no-tailwind", "fallback"]
            ),
            
            GenerationScenario(
                id="edge-next-js",
                name="Next.js App Router Page",
                description="Test generation with Next.js App Router structure",
                message="Create a blog page with posts listing and individual post view using Next.js App Router",
                complexity="medium",
                expected_files=[
                    "app/blog/page.tsx",
                    "app/blog/[slug]/page.tsx",
                    "components/BlogCard.tsx",
                    "components/BlogPost.tsx"
                ],
                expected_components=["BlogCard", "BlogPost"],
                expected_features=["Next.js App Router structure", "Dynamic routes", "Server components"],
                test_project_type="next-shadcn",
                estimated_duration=100,
                validation_criteria={
                    "structure": "Should follow Next.js App Router conventions",
                    "routing": "Should implement dynamic routing correctly",
                    "ssr": "Should work with server-side rendering"
                },
                tags=["next-js", "app-router", "dynamic-routes"]
            ),
            
            GenerationScenario(
                id="edge-accessibility",
                name="High Accessibility Component",
                description="Test generation with explicit accessibility requirements",
                message="Create a modal dialog component with full ARIA support, keyboard navigation, and screen reader compatibility",
                complexity="medium",
                expected_files=["src/components/AccessibleModal.tsx"],
                expected_components=["AccessibleModal"],
                expected_features=[
                    "Full ARIA support",
                    "Keyboard navigation",
                    "Focus management",
                    "Screen reader compatibility"
                ],
                test_project_type="vite-react-shadcn",
                estimated_duration=80,
                validation_criteria={
                    "aria": "Should have proper ARIA attributes",
                    "keyboard": "Should support full keyboard navigation",
                    "focus": "Should manage focus correctly",
                    "screenreader": "Should work with screen readers"
                },
                tags=["accessibility", "modal", "aria", "keyboard-nav"]
            )
        ]
        
        self.scenarios.extend(edge_scenarios)
        
    def save_scenarios(self):
        """Save scenarios to JSON files for easy consumption"""
        self.output_dir.mkdir(exist_ok=True)
        
        # Save all scenarios
        all_scenarios_file = self.output_dir / "all_scenarios.json"
        with open(all_scenarios_file, 'w') as f:
            json.dump([asdict(scenario) for scenario in self.scenarios], f, indent=2)
        
        # Save by complexity
        for complexity in ["simple", "medium", "complex"]:
            complexity_scenarios = [s for s in self.scenarios if s.complexity == complexity]
            complexity_file = self.output_dir / f"{complexity}_scenarios.json"
            with open(complexity_file, 'w') as f:
                json.dump([asdict(scenario) for scenario in complexity_scenarios], f, indent=2)
        
        # Save summary
        summary = {
            "total_scenarios": len(self.scenarios),
            "by_complexity": {
                "simple": len([s for s in self.scenarios if s.complexity == "simple"]),
                "medium": len([s for s in self.scenarios if s.complexity == "medium"]),
                "complex": len([s for s in self.scenarios if s.complexity == "complex"])
            },
            "by_project_type": {},
            "estimated_total_duration": sum(s.estimated_duration for s in self.scenarios),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for project_type in ["vite-react-shadcn", "next-shadcn", "basic-react", "no-tailwind"]:
            summary["by_project_type"][project_type] = len([s for s in self.scenarios if s.test_project_type == project_type])
        
        summary_file = self.output_dir / "scenarios_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
    def create_testing_guide(self):
        """Create a comprehensive testing guide using the scenarios"""
        guide_content = f"""# Palette Generation Testing Guide

This guide provides comprehensive scenarios for testing Palette's generation capabilities. Each scenario includes expected outcomes and validation criteria.

## Quick Start

1. **Setup Test Environment**
   ```bash
   # Run the test project generator
   python3 create_test_projects.py
   
   # Start the Palette server
   python3 -m palette.cli.main conversation
   ```

2. **Choose Test Scenarios**
   - **Simple (15-60 seconds)**: Basic components and forms
   - **Medium (60-120 seconds)**: Interactive apps and features  
   - **Complex (3-6 minutes)**: Complete pages and multi-file projects

3. **Run Test Scenarios**
   Use the scenarios below to test different aspects of generation.

## Test Scenarios

### Simple Scenarios ({len([s for s in self.scenarios if s.complexity == "simple"])} scenarios)

These test basic component generation and should complete quickly:

"""
        
        # Add simple scenarios
        for scenario in [s for s in self.scenarios if s.complexity == "simple"]:
            guide_content += f"""
#### {scenario.name}
**Description**: {scenario.description}
**Test Message**: `"{scenario.message}"`
**Expected Duration**: {scenario.estimated_duration} seconds
**Expected Files**: {', '.join(scenario.expected_files)}
**Validation**: 
{chr(10).join(f"- {k}: {v}" for k, v in scenario.validation_criteria.items())}

"""

        guide_content += f"""
### Medium Scenarios ({len([s for s in self.scenarios if s.complexity == "medium"])} scenarios)

These test interactive features and multi-component generation:

"""
        
        # Add medium scenarios  
        for scenario in [s for s in self.scenarios if s.complexity == "medium"]:
            guide_content += f"""
#### {scenario.name}
**Description**: {scenario.description}
**Test Message**: `"{scenario.message}"`
**Expected Duration**: {scenario.estimated_duration} seconds
**Expected Components**: {', '.join(scenario.expected_components)}
**Key Features**: {', '.join(scenario.expected_features)}

"""

        guide_content += f"""
### Complex Scenarios ({len([s for s in self.scenarios if s.complexity == "complex"])} scenarios)

These test complete page/application generation:

"""
        
        # Add complex scenarios
        for scenario in [s for s in self.scenarios if s.complexity == "complex"]:
            guide_content += f"""
#### {scenario.name}
**Description**: {scenario.description}
**Test Message**: `"{scenario.message}"`
**Expected Duration**: {scenario.estimated_duration} seconds ({scenario.estimated_duration//60} minutes)
**Architecture**: Multi-file with {len(scenario.expected_files)} expected files
**Key Validation**: 
{chr(10).join(f"- {k}: {v}" for k, v in scenario.validation_criteria.items())}

"""

        guide_content += """
## Testing Process

### 1. Manual Testing
1. Navigate to a test project directory
2. Start Palette conversation mode
3. Use a test message from the scenarios above
4. Validate the output against the criteria
5. Test the generated code in the browser

### 2. Automated Testing
```bash
# Run all automated tests
python3 run_all_tests.py

# Run specific test suites
python3 test_generation_pipeline.py
python3 test_quality_workflow.py
python3 test_vscode_integration.py
```

### 3. Performance Testing
- Simple scenarios should complete in < 60 seconds
- Medium scenarios should complete in < 2 minutes
- Complex scenarios should complete in < 6 minutes

### 4. Quality Validation
Each generated output should meet these standards:
- **TypeScript**: Proper types and interfaces
- **Styling**: Consistent Tailwind CSS usage
- **Accessibility**: ARIA attributes and semantic HTML
- **Code Quality**: Clean, readable, maintainable code
- **Functionality**: Working features as requested

## Common Issues and Solutions

1. **Slow Generation**: Check network connection and API keys
2. **Quality Issues**: Review project structure and dependencies  
3. **TypeScript Errors**: Ensure proper tsconfig.json setup
4. **Styling Issues**: Verify Tailwind CSS configuration

## Test Project Types

- **vite-react-shadcn**: Primary target with full shadcn/ui setup
- **next-shadcn**: Next.js with shadcn/ui for App Router testing
- **basic-react**: Basic React without TypeScript for fallback testing
- **no-tailwind**: React project without Tailwind for edge case testing

## Expected Outcomes

### Success Criteria
- Generated code compiles without errors
- Components render correctly in browser
- Code follows project conventions
- Meets accessibility standards
- Performance is acceptable

### Quality Metrics
- TypeScript coverage > 90%
- Accessibility score > 85%
- Code readability score > 80%
- Feature completeness > 95%

---
*Generated on: {time.strftime("%Y-%m-%d %H:%M:%S")}*
*Total Scenarios: {len(self.scenarios)}*
*Estimated Total Testing Time: {sum(s.estimated_duration for s in self.scenarios)//60} minutes*
"""

        guide_file = self.output_dir / "TESTING_SCENARIOS_GUIDE.md"
        with open(guide_file, 'w') as f:
            f.write(guide_content)
        
        print(f"📖 Created testing guide: {guide_file}")

def main():
    """Generate all sample scenarios"""
    generator = SampleScenarioGenerator()
    generator.generate_all_scenarios()
    
    return {
        "scenarios_created": len(generator.scenarios),
        "output_directory": str(generator.output_dir),
        "files_created": [
            "all_scenarios.json",
            "simple_scenarios.json", 
            "medium_scenarios.json",
            "complex_scenarios.json",
            "scenarios_summary.json",
            "TESTING_SCENARIOS_GUIDE.md"
        ]
    }

if __name__ == "__main__":
    result = main()
    print(f"✅ Scenario generation complete: {result}")