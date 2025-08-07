#!/usr/bin/env python3
"""
Simple file manager for saving generated components
"""

import os
import re
from typing import Dict, Optional
from pathlib import Path


class SimpleFileManager:
    """Simplified file operations that actually work"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
    
    def save_component(self, code: str, output_path: Optional[str] = None, context: Dict = None) -> str:
        """Save generated component to appropriate location"""
        
        context = context or {}
        
        # Extract component name from code
        component_name = self._extract_component_name(code)
        
        # Determine output path
        if output_path:
            file_path = Path(output_path)
        else:
            file_path = self._determine_output_path(component_name, context)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write component code
        with open(file_path, 'w') as f:
            f.write(code)
        
        return str(file_path)
    
    def _extract_component_name(self, code: str) -> str:
        """Extract component name from generated code"""
        
        # Try to find component name from various patterns
        patterns = [
            r'const\s+(\w+)\s*[:=]',  # const Component = 
            r'function\s+(\w+)\s*\(',  # function Component(
            r'export\s+default\s+(\w+)',  # export default Component
            r'class\s+(\w+)\s+extends',  # class Component extends
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code)
            if match and match.group(1) != 'React':
                return match.group(1)
        
        # Fallback
        return 'Component'
    
    def _determine_output_path(self, component_name: str, context: Dict) -> Path:
        """Determine where to save the component"""
        
        # Find components directory
        components_dir = self._find_components_directory()
        
        # Determine file extension
        extension = '.tsx' if context.get('typescript', True) else '.jsx'
        
        # Create filename
        filename = f"{component_name}{extension}"
        
        return components_dir / filename
    
    def _find_components_directory(self) -> Path:
        """Find or create appropriate components directory"""
        
        # Common component directory patterns
        common_paths = [
            'src/components',
            'components',
            'src/app/components', 
            'app/components',
            'lib/components'
        ]
        
        # Check if any exist
        for path in common_paths:
            full_path = self.project_path / path
            if full_path.exists() and full_path.is_dir():
                return full_path
        
        # Create default components directory
        default_path = self.project_path / 'src' / 'components'
        default_path.mkdir(parents=True, exist_ok=True)
        
        return default_path
    
    def create_directory_structure(self, component_name: str, context: Dict = None) -> Dict[str, Path]:
        """Create complete directory structure for a component"""
        
        context = context or {}
        components_dir = self._find_components_directory()
        
        # Create component directory
        component_dir = components_dir / component_name
        component_dir.mkdir(exist_ok=True)
        
        # Determine extensions
        script_ext = '.tsx' if context.get('typescript', True) else '.jsx'
        style_ext = self._get_style_extension(context)
        
        paths = {
            'component': component_dir / f"{component_name}{script_ext}",
            'styles': component_dir / f"{component_name}{style_ext}",
            'index': component_dir / f"index{script_ext}",
            'stories': component_dir / f"{component_name}.stories{script_ext}",
            'test': component_dir / f"{component_name}.test{script_ext}"
        }
        
        return paths
    
    def _get_style_extension(self, context: Dict) -> str:
        """Get appropriate style file extension"""
        
        styling = context.get('styling', 'css')
        
        extensions = {
            'css': '.css',
            'scss': '.scss',
            'sass': '.sass',  
            'less': '.less',
            'styled-components': '.ts',
            'emotion': '.ts'
        }
        
        return extensions.get(styling, '.css')
    
    def save_component_with_files(self, 
                                 component_code: str, 
                                 component_name: str,
                                 context: Dict = None,
                                 include_styles: bool = True,
                                 include_stories: bool = False,
                                 include_tests: bool = False) -> Dict[str, str]:
        """Save component with additional files (styles, stories, tests)"""
        
        context = context or {}
        paths = self.create_directory_structure(component_name, context)
        saved_files = {}
        
        # Save main component
        with open(paths['component'], 'w') as f:
            f.write(component_code)
        saved_files['component'] = str(paths['component'])
        
        # Save index file
        index_content = self._generate_index_file(component_name, context)
        with open(paths['index'], 'w') as f:
            f.write(index_content)
        saved_files['index'] = str(paths['index'])
        
        # Save styles if requested and not using CSS-in-JS
        if include_styles and context.get('styling') not in ['styled-components', 'emotion']:
            style_content = self._generate_style_file(component_name, context)
            with open(paths['styles'], 'w') as f:
                f.write(style_content)
            saved_files['styles'] = str(paths['styles'])
        
        # Save stories if requested
        if include_stories:
            stories_content = self._generate_stories_file(component_name, context)
            with open(paths['stories'], 'w') as f:
                f.write(stories_content)
            saved_files['stories'] = str(paths['stories'])
        
        # Save tests if requested
        if include_tests:
            test_content = self._generate_test_file(component_name, context)
            with open(paths['test'], 'w') as f:
                f.write(test_content)
            saved_files['test'] = str(paths['test'])
        
        return saved_files
    
    def _generate_index_file(self, component_name: str, context: Dict) -> str:
        """Generate index.ts/js file for component"""
        
        return f"export {{ default }} from './{component_name}';\n"
    
    def _generate_style_file(self, component_name: str, context: Dict) -> str:
        """Generate basic style file"""
        
        return f"""/* {component_name} Styles */
.{component_name.lower()} {{
  /* Add your styles here */
}}
"""
    
    def _generate_stories_file(self, component_name: str, context: Dict) -> str:
        """Generate Storybook stories file"""
        
        return f"""import type {{ Meta, StoryObj }} from '@storybook/react';
import {component_name} from './{component_name}';

const meta: Meta<typeof {component_name}> = {{
  title: 'Components/{component_name}',
  component: {component_name},
  parameters: {{
    layout: 'centered',
  }},
  tags: ['autodocs'],
}};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {{
  args: {{
    // Add default props here
  }},
}};
"""
    
    def _generate_test_file(self, component_name: str, context: Dict) -> str:
        """Generate basic test file"""
        
        return f"""import {{ render, screen }} from '@testing-library/react';
import {component_name} from './{component_name}';

describe('{component_name}', () => {{
  it('renders without crashing', () => {{
    render(<{component_name} />);
    // Add more specific tests here
  }});
}});
"""