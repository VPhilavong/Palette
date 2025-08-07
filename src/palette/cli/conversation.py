"""
CLI handler for conversational UI generation.
"""

import json
import sys
import click
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum

from ..conversation import ConversationEngine
from rich.console import Console

console = Console()


def _serialize_metadata(metadata: Any) -> Dict[str, Any]:
    """Serialize metadata for JSON output"""
    if not metadata:
        return {}
    
    return _serialize_value(metadata)


def _serialize_value(value: Any) -> Any:
    """Serialize individual values for JSON output"""
    if value is None:
        return None
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, Enum):
        return value.value
    elif is_dataclass(value):
        # Use custom serializer to handle nested enums
        return _serialize_dataclass(value)
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    elif hasattr(value, '__dict__'):
        return {k: _serialize_value(v) for k, v in value.__dict__.items()}
    else:
        return str(value)


def _serialize_dataclass(obj: Any) -> Dict[str, Any]:
    """Serialize dataclass with proper enum handling"""
    if not is_dataclass(obj):
        return str(obj)
    
    result = {}
    for field_name, field_value in obj.__dict__.items():
        result[field_name] = _serialize_value(field_value)
    return result


@click.command()
@click.option('--message', '-m', help='User message to process')
@click.option('--project-path', '-p', help='Path to the project directory')
@click.option('--session-id', '-s', help='Conversation session ID to continue')
@click.option('--history', help='JSON string of conversation history')
@click.option('--interactive', '-i', is_flag=True, help='Start interactive conversation mode')
@click.option('--quick', '-q', help='Quick generation mode (e.g., --quick button)')
@click.option('--install', help='Install shadcn/ui component (e.g., --install button)')
@click.option('--list-components', is_flag=True, help='List available shadcn/ui components')
@click.option('--theme', help='Update theme (e.g., --theme dark-mode)')
def conversation(message: Optional[str] = None, project_path: Optional[str] = None, 
                session_id: Optional[str] = None, history: Optional[str] = None,
                interactive: bool = False, quick: Optional[str] = None,
                install: Optional[str] = None, list_components: bool = False,
                theme: Optional[str] = None):
    """Enhanced conversational UI generation for Vite + React + shadcn/ui"""
    
    # Redirect all print statements to stderr to keep stdout clean for JSON
    original_stdout = sys.stdout
    sys.stdout = sys.stderr
    
    try:
        # Initialize conversation engine
        project_path = project_path or str(Path.cwd())
        
        # Handle special modes first
        if list_components:
            return _handle_list_components(project_path, original_stdout)
        elif install:
            return _handle_install_component(install, project_path, original_stdout)
        elif theme:
            return _handle_theme_update(theme, project_path, original_stdout)
        elif quick:
            return _handle_quick_generation(quick, project_path, original_stdout)
        elif interactive:
            return _handle_interactive_mode(project_path, session_id, original_stdout)
        
        # Ensure we have a message for regular conversation mode
        if not message:
            error_result = {
                'error': 'Message required for conversation mode. Use --interactive for interactive mode.',
                'usage': 'palette conversation --message "create a button" or palette conversation --interactive'
            }
            sys.stdout = original_stdout
            sys.stdout.write(json.dumps(error_result, indent=2))
            sys.stdout.flush()
            sys.exit(1)
        
        engine = ConversationEngine(project_path=project_path)
        
        # Start or continue conversation
        if not session_id:
            session_id = engine.start_conversation()
        else:
            engine.start_conversation(session_id)
        
        # Process conversation history if provided
        if history:
            try:
                history_data = json.loads(history)
                for msg in history_data:
                    if msg.get('role') and msg.get('content'):
                        # Add to conversation context without generating response
                        from ..conversation.conversation_engine import ConversationMessage
                        from datetime import datetime
                        message_obj = ConversationMessage(
                            role=msg['role'],
                            content=msg['content'], 
                            timestamp=datetime.now()
                        )
                        engine.current_context.messages.append(message_obj)
            except json.JSONDecodeError:
                console.print("Warning: Invalid conversation history format", style="yellow")
        
        # Process the user message
        response, metadata = engine.process_message(message)
        
        # Output response as JSON for structured handling
        result = {
            'response': response,
            'session_id': session_id,
            'metadata': _serialize_metadata(metadata) if metadata else None
        }
        
        # Restore stdout and send result to stdout
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.flush()
        
    except Exception as e:
        error_result = {
            'error': str(e),
            'response': f"I encountered an error: {str(e)}"
        }
        # Restore stdout and send error to stdout
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(error_result, indent=2))
        sys.stdout.flush()
        sys.exit(1)


def _handle_list_components(project_path: str, original_stdout):
    """Handle --list-components flag"""
    try:
        engine = ConversationEngine(project_path=project_path)
        session_id = engine.start_conversation()
        response, metadata = engine.process_message("list available components")
        
        result = {
            'response': response,
            'workflow': 'list_components',
            'metadata': _serialize_metadata(metadata) if metadata else None
        }
        
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.flush()
        
    except Exception as e:
        error_result = {
            'error': str(e),
            'workflow': 'list_components'
        }
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(error_result, indent=2))
        sys.stdout.flush()
        sys.exit(1)


def _handle_install_component(component_name: str, project_path: str, original_stdout):
    """Handle --install flag"""
    try:
        engine = ConversationEngine(project_path=project_path)
        session_id = engine.start_conversation()
        message = f"install {component_name} component"
        response, metadata = engine.process_message(message)
        
        result = {
            'response': response,
            'workflow': 'install_component',
            'component': component_name,
            'metadata': _serialize_metadata(metadata) if metadata else None
        }
        
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.flush()
        
    except Exception as e:
        error_result = {
            'error': str(e),
            'workflow': 'install_component',
            'component': component_name
        }
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(error_result, indent=2))
        sys.stdout.flush()
        sys.exit(1)


def _handle_theme_update(theme_request: str, project_path: str, original_stdout):
    """Handle --theme flag"""
    try:
        engine = ConversationEngine(project_path=project_path)
        session_id = engine.start_conversation()
        message = f"update theme to {theme_request}"
        response, metadata = engine.process_message(message)
        
        result = {
            'response': response,
            'workflow': 'theme_update',
            'theme_request': theme_request,
            'metadata': _serialize_metadata(metadata) if metadata else None
        }
        
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.flush()
        
    except Exception as e:
        error_result = {
            'error': str(e),
            'workflow': 'theme_update',
            'theme_request': theme_request
        }
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(error_result, indent=2))
        sys.stdout.flush()
        sys.exit(1)


def _handle_quick_generation(component_type: str, project_path: str, original_stdout):
    """Handle --quick flag for rapid component generation"""
    try:
        # Quick generation templates
        quick_templates = {
            'button': 'Create a modern button component with variants (primary, secondary, outline, ghost) and sizes (sm, md, lg)',
            'card': 'Create a card component with header, content, and footer sections',
            'form': 'Create a form component with input, label, and validation support',
            'modal': 'Create a modal component with backdrop, close button, and keyboard handling',
            'input': 'Create an input component with label, placeholder, and validation states',
            'navbar': 'Create a navigation bar component with logo, menu items, and mobile toggle',
            'hero': 'Create a hero section with headline, description, and call-to-action button',
            'footer': 'Create a footer component with links, social icons, and copyright',
            'sidebar': 'Create a sidebar navigation component with menu items and toggle',
            'table': 'Create a table component with sorting, pagination, and row selection'
        }
        
        template = quick_templates.get(component_type.lower())
        if not template:
            available = ', '.join(quick_templates.keys())
            error_result = {
                'error': f'Quick template not found for "{component_type}"',
                'available_templates': available,
                'workflow': 'quick_generation'
            }
            sys.stdout = original_stdout
            sys.stdout.write(json.dumps(error_result, indent=2))
            sys.stdout.flush()
            sys.exit(1)
        
        engine = ConversationEngine(project_path=project_path)
        session_id = engine.start_conversation()
        response, metadata = engine.process_message(template)
        
        result = {
            'response': response,
            'workflow': 'quick_generation',
            'component_type': component_type,
            'template_used': template,
            'metadata': _serialize_metadata(metadata) if metadata else None
        }
        
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.flush()
        
    except Exception as e:
        error_result = {
            'error': str(e),
            'workflow': 'quick_generation',
            'component_type': component_type
        }
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(error_result, indent=2))
        sys.stdout.flush()
        sys.exit(1)


def _handle_interactive_mode(project_path: str, session_id: Optional[str], original_stdout):
    """Handle --interactive flag for multi-turn conversation"""
    from rich.console import Console
    console = Console()
    
    try:
        console.print("\n🚀 [bold blue]Palette Interactive Mode[/bold blue] (Vite + React + shadcn/ui)")
        console.print("Type 'exit' or 'quit' to end the conversation\n")
        
        engine = ConversationEngine(project_path=project_path)
        
        if not session_id:
            session_id = engine.start_conversation()
            console.print(f"[dim]Session ID: {session_id}[/dim]\n")
        else:
            engine.start_conversation(session_id)
            console.print(f"[dim]Continuing session: {session_id}[/dim]\n")
        
        # Interactive loop
        while True:
            try:
                user_input = console.input("[bold green]You:[/bold green] ")
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("\n[bold blue]Thanks for using Palette! 👋[/bold blue]")
                    break
                
                if not user_input.strip():
                    continue
                
                # Process message
                console.print("[bold blue]Palette:[/bold blue]", end=" ")
                response, metadata = engine.process_message(user_input)
                console.print(response)
                console.print("")  # Empty line for readability
                
            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold blue]Thanks for using Palette! 👋[/bold blue]")
                break
        
        # Return session summary
        result = {
            'workflow': 'interactive_completed',
            'session_id': session_id,
            'message_count': len(engine.current_context.messages) if engine.current_context else 0
        }
        
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(result, indent=2))
        sys.stdout.flush()
        
    except Exception as e:
        error_result = {
            'error': str(e),
            'workflow': 'interactive_mode'
        }
        sys.stdout = original_stdout
        sys.stdout.write(json.dumps(error_result, indent=2))
        sys.stdout.flush()
        sys.exit(1)