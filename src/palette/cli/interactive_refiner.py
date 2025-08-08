"""
Interactive Component Refinement System.

Enables conversational, iterative refinement of generated components through
a chat-like interface. Users can request modifications, improvements, and
variations in natural language.
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown

console = Console()


@dataclass
class RefinementSession:
    """Tracks an interactive refinement session."""
    initial_prompt: str
    current_code: Dict[str, str]  # filename -> code content
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    refinement_count: int = 0
    project_config: Optional[Any] = None
    generation_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefinementRequest:
    """A user's refinement request."""
    request: str
    category: str  # 'style', 'functionality', 'structure', 'content'
    complexity: str  # 'simple', 'medium', 'complex'
    suggested_approach: str


class InteractiveRefiner:
    """Manages interactive component refinement sessions."""
    
    def __init__(self):
        self.current_session: Optional[RefinementSession] = None
        self.max_refinements = 10  # Prevent infinite loops
        
        # Refinement patterns and suggestions
        self.refinement_patterns = {
            'style': {
                'keywords': ['color', 'size', 'spacing', 'layout', 'theme', 'responsive', 'mobile'],
                'suggestions': [
                    'Change colors or theme',
                    'Adjust spacing and padding',
                    'Make responsive for mobile',
                    'Modify component size',
                    'Update typography'
                ]
            },
            'functionality': {
                'keywords': ['click', 'hover', 'state', 'data', 'api', 'form', 'validation'],
                'suggestions': [
                    'Add click handlers',
                    'Include loading states',
                    'Add form validation',
                    'Connect to API',
                    'Add hover effects'
                ]
            },
            'structure': {
                'keywords': ['layout', 'organize', 'split', 'combine', 'component', 'props'],
                'suggestions': [
                    'Split into smaller components',
                    'Reorganize component structure',
                    'Add new props',
                    'Change component hierarchy',
                    'Extract reusable parts'
                ]
            },
            'content': {
                'keywords': ['text', 'content', 'data', 'example', 'placeholder'],
                'suggestions': [
                    'Update placeholder content',
                    'Add example data',
                    'Change text content',
                    'Include more variety',
                    'Add documentation'
                ]
            }
        }
    
    def start_refinement_session(self, initial_prompt: str, generated_files: Dict[str, str], 
                                 project_config: Any = None) -> RefinementSession:
        """Start a new interactive refinement session."""
        
        self.current_session = RefinementSession(
            initial_prompt=initial_prompt,
            current_code=generated_files.copy(),
            project_config=project_config,
            generation_context={
                'framework': project_config.framework.value if project_config and project_config.framework else 'react',
                'styling': project_config.styling_system.value if project_config and project_config.styling_system else 'tailwind',
                'typescript': project_config.typescript if project_config else True
            }
        )
        
        # Add initial generation to conversation history
        self.current_session.conversation_history.append({
            'role': 'assistant',
            'content': f'I generated a component based on your request: "{initial_prompt}". The component includes {len(generated_files)} file(s). What would you like to adjust or improve?',
            'files': list(generated_files.keys())
        })
        
        return self.current_session
    
    def run_interactive_session(self) -> Dict[str, str]:
        """Run the main interactive refinement loop."""
        
        if not self.current_session:
            raise ValueError("No active refinement session")
        
        console.print(Panel(
            "[bold blue]🤝 Interactive Refinement Mode[/bold blue]\n"
            "Let's refine your component together! I'll ask questions and make improvements based on your feedback.",
            title="Conversational Development",
            border_style="blue"
        ))
        
        # Show initial generation
        self._show_current_state()
        
        # Main conversation loop
        while self.current_session.refinement_count < self.max_refinements:
            try:
                # Get user feedback
                user_request = self._get_user_input()
                
                if user_request.lower() in ['done', 'finish', 'exit', 'quit']:
                    console.print("✅ [green]Refinement session completed![/green]")
                    break
                
                # Analyze and categorize the request
                refinement_request = self._analyze_refinement_request(user_request)
                
                # Show what we're about to do
                self._show_refinement_plan(refinement_request)
                
                # Apply the refinement
                success = self._apply_refinement(refinement_request)
                
                if success:
                    # Show updated state
                    self._show_current_state()
                    
                    # Ask for further refinements
                    if self.current_session.refinement_count < self.max_refinements - 1:
                        continue_refining = self._ask_for_more_refinements()
                        if not continue_refining:
                            break
                else:
                    console.print("❌ [red]Failed to apply refinement. Let's try a different approach.[/red]")
                
            except KeyboardInterrupt:
                console.print("\\n🛑 [yellow]Refinement session cancelled by user[/yellow]")
                break
            except Exception as e:
                console.print(f"❌ [red]Error during refinement: {str(e)}[/red]")
                console.print("Let's try a different approach...")
        
        if self.current_session.refinement_count >= self.max_refinements:
            console.print(f"🔄 [yellow]Reached maximum refinements ({self.max_refinements}). Session completed.[/yellow]")
        
        return self.current_session.current_code
    
    def _show_current_state(self):
        """Display the current state of the component."""
        
        console.print("\\n📝 CURRENT COMPONENT STATE", style="bold blue")
        console.print("=" * 50)
        
        for filename, code in self.current_session.current_code.items():
            console.print(f"\\n[cyan]📄 {filename}[/cyan]")
            
            # Show first 15 lines of code
            lines = code.split('\\n')
            preview_lines = lines[:15]
            if len(lines) > 15:
                preview_lines.append("... (truncated)")
            
            preview_code = '\\n'.join(preview_lines)
            
            # Determine language for syntax highlighting
            lang = 'typescript' if filename.endswith(('.tsx', '.ts')) else 'javascript'
            if filename.endswith('.css'):
                lang = 'css'
            
            syntax = Syntax(preview_code, lang, theme="monokai", line_numbers=True)
            console.print(syntax)
        
        # Show refinement history
        if self.current_session.refinement_count > 0:
            console.print(f"\\n[dim]Refinements applied: {self.current_session.refinement_count}[/dim]")
    
    def _get_user_input(self) -> str:
        """Get refinement request from user with helpful prompts."""
        
        console.print("\\n💬 What would you like to adjust?", style="bold yellow")
        
        # Show suggestions based on current context
        suggestions = self._get_contextual_suggestions()
        if suggestions:
            console.print("\\n[dim]💡 Suggestions:[/dim]")
            for i, suggestion in enumerate(suggestions[:3], 1):
                console.print(f"[dim]  {i}. {suggestion}[/dim]")
        
        console.print("[dim]\\nType 'done' when finished, or describe what you'd like to change:[/dim]")
        
        user_input = Prompt.ask("🎨", default="")
        
        if not user_input.strip():
            console.print("[yellow]Please provide some feedback about what you'd like to change.[/yellow]")
            return self._get_user_input()
        
        return user_input.strip()
    
    def _get_contextual_suggestions(self) -> List[str]:
        """Get contextual suggestions based on current component."""
        
        suggestions = []
        current_code = ' '.join(self.current_session.current_code.values()).lower()
        
        # Analyze current code to suggest improvements
        if 'button' in current_code:
            suggestions.extend([
                "Add loading state with spinner",
                "Include hover and focus styles",
                "Add icon support"
            ])
        
        if 'form' in current_code or 'input' in current_code:
            suggestions.extend([
                "Add validation messages",
                "Include error states",
                "Add form submission handling"
            ])
        
        if 'card' in current_code:
            suggestions.extend([
                "Add hover effects",
                "Include action buttons",
                "Make it more compact"
            ])
        
        # Framework-specific suggestions
        framework = self.current_session.generation_context.get('framework', 'react')
        if framework == 'react':
            if 'usestate' not in current_code:
                suggestions.append("Add interactive state management")
        
        # Styling suggestions
        styling = self.current_session.generation_context.get('styling', 'tailwind')
        if styling == 'tailwind':
            suggestions.append("Make it responsive for mobile devices")
        
        return suggestions[:5]  # Limit to avoid noise
    
    def _analyze_refinement_request(self, user_request: str) -> RefinementRequest:
        """Analyze user request to determine category and approach."""
        
        request_lower = user_request.lower()
        
        # Determine category based on keywords
        category_scores = {}
        for category, data in self.refinement_patterns.items():
            score = sum(1 for keyword in data['keywords'] if keyword in request_lower)
            if score > 0:
                category_scores[category] = score
        
        # Choose highest scoring category, default to 'functionality'
        category = max(category_scores, key=category_scores.get) if category_scores else 'functionality'
        
        # Determine complexity
        complexity_indicators = {
            'simple': ['color', 'text', 'size', 'padding', 'margin'],
            'medium': ['state', 'click', 'hover', 'responsive', 'validation'],
            'complex': ['api', 'database', 'authentication', 'routing', 'optimization']
        }
        
        complexity = 'simple'
        for level, indicators in complexity_indicators.items():
            if any(indicator in request_lower for indicator in indicators):
                complexity = level
        
        # Generate suggested approach
        suggested_approach = self._generate_refinement_approach(user_request, category, complexity)
        
        return RefinementRequest(
            request=user_request,
            category=category,
            complexity=complexity,
            suggested_approach=suggested_approach
        )
    
    def _generate_refinement_approach(self, request: str, category: str, complexity: str) -> str:
        """Generate a suggested approach for the refinement."""
        
        request_lower = request.lower()
        
        # Style refinements
        if category == 'style':
            if any(word in request_lower for word in ['color', 'theme']):
                return "Update color scheme and theme variables"
            elif any(word in request_lower for word in ['compact', 'smaller', 'size']):
                return "Reduce component size and spacing"
            elif 'responsive' in request_lower:
                return "Add responsive breakpoints and mobile-first design"
            else:
                return "Apply visual style improvements"
        
        # Functionality refinements
        elif category == 'functionality':
            if any(word in request_lower for word in ['click', 'button', 'action']):
                return "Add click handlers and interactive behavior"
            elif any(word in request_lower for word in ['loading', 'state']):
                return "Implement loading states and state management"
            elif 'validation' in request_lower:
                return "Add form validation and error handling"
            else:
                return "Enhance component functionality"
        
        # Structure refinements
        elif category == 'structure':
            if any(word in request_lower for word in ['split', 'separate']):
                return "Break component into smaller, reusable parts"
            elif any(word in request_lower for word in ['props', 'customizable']):
                return "Add configurable props and options"
            else:
                return "Restructure component organization"
        
        # Content refinements
        else:  # content
            if 'example' in request_lower:
                return "Update with more realistic example data"
            elif 'placeholder' in request_lower:
                return "Improve placeholder content and messaging"
            else:
                return "Update component content and text"
    
    def _show_refinement_plan(self, refinement_request: RefinementRequest):
        """Show the user what refinement will be applied."""
        
        plan_content = f"""[bold]Request:[/bold] {refinement_request.request}

[yellow]Category:[/yellow] {refinement_request.category.title()}
[blue]Complexity:[/blue] {refinement_request.complexity.title()}
[green]Approach:[/green] {refinement_request.suggested_approach}"""
        
        panel = Panel(
            plan_content,
            title="🔧 Refinement Plan",
            border_style="green"
        )
        console.print(panel)
        
        # Ask for confirmation for complex changes
        if refinement_request.complexity == 'complex':
            confirmed = Confirm.ask("This is a complex change. Proceed?")
            if not confirmed:
                console.print("[yellow]Skipping complex refinement. Try a simpler change.[/yellow]")
                return False
        
        return True
    
    def _apply_refinement(self, refinement_request: RefinementRequest) -> bool:
        """Apply the refinement to the current code."""
        
        try:
            # For this demonstration, we'll simulate the refinement
            # In a real implementation, this would use the generation system
            # with the refinement request as additional context
            
            console.print("🔄 [dim]Applying refinement...[/dim]")
            
            # Simulate refinement by adding comments showing what would be changed
            refined_code = {}
            for filename, code in self.current_session.current_code.items():
                
                # Add refinement indicator comment
                refinement_comment = f"// Refinement {self.current_session.refinement_count + 1}: {refinement_request.suggested_approach}\\n"
                
                # Apply category-specific changes (simulated)
                if refinement_request.category == 'style':
                    refined_code[filename] = self._apply_style_refinement(code, refinement_request)
                elif refinement_request.category == 'functionality':
                    refined_code[filename] = self._apply_functionality_refinement(code, refinement_request)
                elif refinement_request.category == 'structure':
                    refined_code[filename] = self._apply_structure_refinement(code, refinement_request)
                else:  # content
                    refined_code[filename] = self._apply_content_refinement(code, refinement_request)
                
                # Add refinement comment at the top
                refined_code[filename] = refinement_comment + refined_code[filename]
            
            # Update session
            self.current_session.current_code = refined_code
            self.current_session.refinement_count += 1
            
            # Add to conversation history
            self.current_session.conversation_history.append({
                'role': 'user',
                'content': refinement_request.request
            })
            self.current_session.conversation_history.append({
                'role': 'assistant',
                'content': f"Applied refinement: {refinement_request.suggested_approach}. The component has been updated.",
                'category': refinement_request.category,
                'files_modified': list(refined_code.keys())
            })
            
            console.print("✅ [green]Refinement applied successfully![/green]")
            return True
            
        except Exception as e:
            console.print(f"❌ [red]Failed to apply refinement: {str(e)}[/red]")
            return False
    
    def _apply_style_refinement(self, code: str, request: RefinementRequest) -> str:
        """Apply style-related refinements."""
        
        request_lower = request.request.lower()
        
        # Simulate style changes
        if 'compact' in request_lower or 'smaller' in request_lower:
            # Reduce padding/spacing
            code = code.replace('p-6', 'p-4').replace('p-4', 'p-2').replace('space-y-4', 'space-y-2')
            code += "\\n// Made component more compact by reducing padding and spacing"
        
        elif 'color' in request_lower:
            # Change color scheme
            code = code.replace('blue-500', 'green-500').replace('blue-600', 'green-600')
            code += "\\n// Updated color scheme as requested"
        
        elif 'responsive' in request_lower:
            # Add responsive classes
            code = code.replace('className="', 'className="sm:p-4 md:p-6 lg:p-8 ')
            code += "\\n// Added responsive breakpoints for mobile-first design"
        
        return code
    
    def _apply_functionality_refinement(self, code: str, request: RefinementRequest) -> str:
        """Apply functionality-related refinements."""
        
        request_lower = request.request.lower()
        
        if 'loading' in request_lower or 'state' in request_lower:
            # Add loading state
            code = code.replace('const [', 'const [isLoading, setIsLoading] = useState(false);\\n  const [')
            code += "\\n// Added loading state management"
        
        elif 'click' in request_lower:
            # Add click handler
            code = code.replace('onClick={', 'onClick={handleClick || ')
            code += "\\n// Enhanced click handling functionality"
        
        return code
    
    def _apply_structure_refinement(self, code: str, request: RefinementRequest) -> str:
        """Apply structure-related refinements."""
        
        request_lower = request.request.lower()
        
        if 'props' in request_lower:
            # Add more props
            code = code.replace('interface ', 'interface Enhanced')
            code += "\\n// Extended component props for better customization"
        
        return code
    
    def _apply_content_refinement(self, code: str, request: RefinementRequest) -> str:
        """Apply content-related refinements."""
        
        request_lower = request.request.lower()
        
        if 'example' in request_lower:
            # Update example content
            code = code.replace('Example', 'Real-world example')
            code += "\\n// Updated with more realistic example content"
        
        return code
    
    def _ask_for_more_refinements(self) -> bool:
        """Ask user if they want to continue refining."""
        
        console.print("\\n🎯 [bold]Component updated![/bold]")
        
        # Show quick options
        options_table = Table(title="What's next?", show_header=False)
        options_table.add_column("Option", style="cyan")
        options_table.add_column("Description", style="dim")
        
        options_table.add_row("1. Continue refining", "Make more adjustments")
        options_table.add_row("2. Finish", "Save current version")
        options_table.add_row("3. Preview", "See full code")
        
        console.print(options_table)
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "continue", "finish", "preview"], default="2")
        
        if choice in ["1", "continue"]:
            return True
        elif choice in ["3", "preview"]:
            self._show_full_code_preview()
            return self._ask_for_more_refinements()  # Ask again after preview
        else:  # finish or 2
            return False
    
    def _show_full_code_preview(self):
        """Show the complete current code."""
        
        console.print("\\n📖 FULL CODE PREVIEW", style="bold blue")
        console.print("=" * 60)
        
        for filename, code in self.current_session.current_code.items():
            console.print(f"\\n[bold cyan]📄 {filename}[/bold cyan]")
            
            # Determine language for syntax highlighting
            lang = 'typescript' if filename.endswith(('.tsx', '.ts')) else 'javascript'
            if filename.endswith('.css'):
                lang = 'css'
            
            syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
            console.print(syntax)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the refinement session."""
        
        if not self.current_session:
            return {}
        
        return {
            'initial_prompt': self.current_session.initial_prompt,
            'refinements_applied': self.current_session.refinement_count,
            'conversation_history': self.current_session.conversation_history,
            'final_files': list(self.current_session.current_code.keys()),
            'session_completed': True
        }