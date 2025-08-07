# Palette Generation Testing Guide

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

### Simple Scenarios (4 scenarios)

These test basic component generation and should complete quickly:


#### Simple Button Component
**Description**: Basic button component with primary/secondary variants
**Test Message**: `"Create a button component with primary and secondary variants"`
**Expected Duration**: 30 seconds
**Expected Files**: src/components/ui/button.tsx
**Validation**: 
- typescript: Should have proper TypeScript interface
- styling: Should use Tailwind CSS classes
- accessibility: Should have proper button type and aria attributes
- reusability: Should accept children and onClick props


#### Card Component
**Description**: Reusable card component with header, content, and footer slots
**Test Message**: `"Create a card component with header, content area, and optional footer"`
**Expected Duration**: 45 seconds
**Expected Files**: src/components/ui/card.tsx
**Validation**: 
- structure: Should use compound component pattern
- styling: Should have consistent spacing and borders
- flexibility: Should allow custom content in each section


#### Contact Form
**Description**: Basic contact form with validation
**Test Message**: `"Create a contact form with name, email, and message fields with validation"`
**Expected Duration**: 60 seconds
**Expected Files**: src/components/ContactForm.tsx
**Validation**: 
- validation: Should validate email format and required fields
- accessibility: Should have proper labels and error messages
- ux: Should provide clear feedback on form submission


#### Component Without Tailwind
**Description**: Test generation in project without Tailwind CSS setup
**Test Message**: `"Create a button component with styling in a project without Tailwind CSS"`
**Expected Duration**: 45 seconds
**Expected Files**: src/components/Button.tsx
**Validation**: 
- styling: Should use alternative styling method
- fallback: Should work without Tailwind dependencies
- adaptability: Should adapt to project constraints


### Medium Scenarios (5 scenarios)

These test interactive features and multi-component generation:


#### Todo List Application
**Description**: Interactive todo list with add, complete, delete, and filter functionality
**Test Message**: `"Create a todo list app with add, complete, delete and filter (all/active/completed) functionality"`
**Expected Duration**: 120 seconds
**Expected Components**: TodoApp, TodoItem, TodoList, TodoFilters
**Key Features**: State management with useState/useReducer, Local storage persistence, Filter functionality, CRUD operations


#### Image Gallery with Modal
**Description**: Responsive image gallery with lightbox modal for viewing full-size images
**Test Message**: `"Create a responsive image gallery with thumbnail grid and modal lightbox for viewing full-size images"`
**Expected Duration**: 90 seconds
**Expected Components**: ImageGallery, ImageModal, ImageThumbnail
**Key Features**: Responsive grid layout, Modal overlay, Navigation between images, Keyboard accessibility


#### Data Table with Sorting
**Description**: Data table component with sorting, pagination, and search functionality
**Test Message**: `"Create a data table that displays user data with sorting, pagination, and search functionality"`
**Expected Duration**: 110 seconds
**Expected Components**: DataTable, TableHeader, TablePagination, TableSearch
**Key Features**: Column sorting, Pagination controls, Search/filter functionality, Responsive design


#### Next.js App Router Page
**Description**: Test generation with Next.js App Router structure
**Test Message**: `"Create a blog page with posts listing and individual post view using Next.js App Router"`
**Expected Duration**: 100 seconds
**Expected Components**: BlogCard, BlogPost
**Key Features**: Next.js App Router structure, Dynamic routes, Server components


#### High Accessibility Component
**Description**: Test generation with explicit accessibility requirements
**Test Message**: `"Create a modal dialog component with full ARIA support, keyboard navigation, and screen reader compatibility"`
**Expected Duration**: 80 seconds
**Expected Components**: AccessibleModal
**Key Features**: Full ARIA support, Keyboard navigation, Focus management, Screen reader compatibility


### Complex Scenarios (3 scenarios)

These test complete page/application generation:


#### Admin Dashboard
**Description**: Complete admin dashboard with sidebar navigation, header, charts, and data tables
**Test Message**: `"Create a complete admin dashboard with sidebar navigation, header with user profile, data visualization charts, and user management table"`
**Expected Duration**: 300 seconds (5 minutes)
**Architecture**: Multi-file with 8 expected files
**Key Validation**: 
- layout: Should have proper dashboard layout structure
- navigation: Should include working navigation system
- responsive: Should work on mobile and desktop
- data_viz: Should display charts and data tables
- composition: Should properly compose multiple components


#### E-commerce Product Page
**Description**: Complete e-commerce product page with gallery, details, reviews, and shopping cart integration
**Test Message**: `"Create a complete e-commerce product page with image gallery, product details, customer reviews, related products, and add to cart functionality"`
**Expected Duration**: 350 seconds (5 minutes)
**Architecture**: Multi-file with 8 expected files
**Key Validation**: 
- gallery: Should have working image gallery with navigation
- variants: Should handle product variants (size, color, etc.)
- reviews: Should display and manage customer reviews
- cart: Should integrate with shopping cart functionality
- ux: Should provide excellent shopping experience


#### SaaS Landing Page
**Description**: Complete SaaS landing page with hero, features, testimonials, pricing, and CTA sections
**Test Message**: `"Create a complete SaaS landing page with hero section, features showcase, customer testimonials, pricing tiers, and call-to-action sections"`
**Expected Duration**: 280 seconds (4 minutes)
**Architecture**: Multi-file with 8 expected files
**Key Validation**: 
- design: Should have modern, professional design
- responsive: Should work perfectly on all devices
- conversion: Should optimize for user conversion
- performance: Should load quickly and smoothly
- sections: Should have all required landing page sections


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
