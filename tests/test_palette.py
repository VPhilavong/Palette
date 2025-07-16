#!/usr/bin/env python3
"""
Pytest test suite for Code Palette
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestImports:
    """Test that all modules can be imported"""

    def test_cli_import(self):
        """Test CLI module imports"""
        from palette.cli import main
        from palette.cli import simple
        assert hasattr(main, "main")
        assert hasattr(simple, "main")

    def test_analysis_import(self):
        """Test analysis module imports"""
        from palette.analysis.context import ProjectAnalyzer
        assert ProjectAnalyzer is not None

    def test_generation_import(self):
        """Test generation module imports"""
        from palette.generation.generator import UIGenerator
        from palette.generation.prompts import UIPromptBuilder
        assert UIGenerator is not None
        assert UIPromptBuilder is not None

    def test_utils_import(self):
        """Test utils module imports"""
        from palette.utils.file_manager import FileManager
        assert FileManager is not None


class TestProjectAnalysis:
    """Test project analysis functionality"""

    def setup_method(self):
        """Setup for each test method"""
        from palette.analysis.context import ProjectAnalyzer
        self.analyzer = ProjectAnalyzer()

    def test_analyze_current_project(self):
        """Test analyzing the current project"""
        context = self.analyzer.analyze_project(str(project_root))
        
        assert "framework" in context
        assert "styling" in context
        assert "design_tokens" in context
        
        # Should detect Next.js from app/ directory
        assert context["framework"] == "next.js"

    def test_context_structure(self):
        """Test that context has expected structure"""
        context = self.analyzer.analyze_project(str(project_root))
        
        required_keys = [
            "framework",
            "styling", 
            "component_library",
            "design_tokens",
            "project_structure"
        ]
        
        for key in required_keys:
            assert key in context

    def test_design_tokens_detection(self):
        """Test design tokens are detected"""
        context = self.analyzer.analyze_project(str(project_root))
        tokens = context["design_tokens"]
        
        assert "colors" in tokens
        assert "spacing" in tokens
        assert "typography" in tokens
        
        # Should find at least the 'white' color from Button.tsx
        assert len(tokens["colors"]) >= 1


class TestPromptBuilding:
    """Test prompt building functionality"""

    def setup_method(self):
        """Setup for each test method"""
        from palette.generation.prompts import UIPromptBuilder
        self.builder = UIPromptBuilder()
        self.sample_context = {
            "framework": "react",
            "styling": "tailwind",
            "component_library": "none",
            "design_tokens": {
                "colors": ["blue", "gray", "green"],
                "spacing": ["4", "8", "16"],
                "typography": ["sm", "base", "lg"]
            }
        }

    def test_system_prompt_generation(self):
        """Test system prompt generation"""
        prompt = self.builder.build_ui_system_prompt(self.sample_context)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be substantial
        assert "react" in prompt.lower()
        assert "tailwind" in prompt.lower()

    def test_user_prompt_generation(self):
        """Test user prompt generation"""
        user_prompt = self.builder.build_user_prompt(
            "Create a button component", 
            self.sample_context
        )
        
        assert isinstance(user_prompt, str)
        assert "button component" in user_prompt
        assert len(user_prompt) > 50

    def test_prompt_contains_context(self):
        """Test that prompts contain context information"""
        system_prompt = self.builder.build_ui_system_prompt(self.sample_context)
        
        # Should mention the detected colors
        assert any(color in system_prompt for color in ["blue", "gray", "green"])


class TestFileManagement:
    """Test file management functionality"""

    def setup_method(self):
        """Setup for each test method"""
        from palette.utils.file_manager import FileManager
        self.manager = FileManager()

    def test_component_name_extraction(self):
        """Test extracting component names from code"""
        sample_code = '''
const MyButton = ({ children }) => {
  return <button>{children}</button>;
};

export default MyButton;
'''
        component_name = self.manager._extract_component_name(sample_code)
        assert component_name == "MyButton"

    def test_arrow_function_extraction(self):
        """Test extracting names from arrow function components"""
        sample_code = '''
const Card = () => {
  return <div>Card content</div>;
};
'''
        component_name = self.manager._extract_component_name(sample_code)
        assert component_name == "Card"

    def test_function_declaration_extraction(self):
        """Test extracting names from function declarations"""
        sample_code = '''
function Header() {
  return <header>Site header</header>;
}
'''
        component_name = self.manager._extract_component_name(sample_code)
        assert component_name == "Header"


class TestCLIFunctionality:
    """Test CLI functionality"""

    def test_main_cli_help(self):
        """Test that main CLI shows help"""
        # This would require subprocess testing
        # For now, just test that we can import the main function
        from palette.cli.main import main
        assert callable(main)

    def test_simple_cli_help(self):
        """Test that simple CLI shows help"""
        from palette.cli.simple import main
        assert callable(main)


@pytest.mark.integration
class TestIntegration:
    """Integration tests using real project analysis"""

    def test_full_analysis_workflow(self):
        """Test complete analysis workflow"""
        from palette.analysis.context import ProjectAnalyzer
        from palette.generation.prompts import UIPromptBuilder
        
        # Analyze project
        analyzer = ProjectAnalyzer()
        context = analyzer.analyze_project(str(project_root))
        
        # Build prompts with real context
        builder = UIPromptBuilder()
        system_prompt = builder.build_ui_system_prompt(context)
        user_prompt = builder.build_user_prompt("Create a card component", context)
        
        # Verify prompts are reasonable
        assert len(system_prompt) > 1000
        assert len(user_prompt) > 100
        assert "card component" in user_prompt
