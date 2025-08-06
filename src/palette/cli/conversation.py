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
@click.option('--message', '-m', required=True, help='User message to process')
@click.option('--project-path', '-p', help='Path to the project directory')
@click.option('--session-id', '-s', help='Conversation session ID to continue')
@click.option('--history', help='JSON string of conversation history')
def conversation(message: str, project_path: Optional[str] = None, 
                session_id: Optional[str] = None, history: Optional[str] = None):
    """Interactive conversational UI generation"""
    
    # Redirect all print statements to stderr to keep stdout clean for JSON
    original_stdout = sys.stdout
    sys.stdout = sys.stderr
    
    try:
        # Initialize conversation engine
        project_path = project_path or str(Path.cwd())
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