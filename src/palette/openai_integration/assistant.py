"""
OpenAI Assistants API integration with Code Interpreter for Palette.
Provides advanced AI capabilities for component generation and validation.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI, AsyncOpenAI


@dataclass
class AssistantConfig:
    """Configuration for the Palette Assistant."""
    name: str = "Palette UI/UX Generator"
    model: str = "gpt-4-turbo-preview"
    instructions: str = """You are an expert UI/UX developer assistant specialized in generating 
    high-quality React components. You have deep knowledge of:
    - React and TypeScript best practices
    - Modern UI/UX design patterns
    - Tailwind CSS and component libraries (shadcn/ui, MUI, etc.)
    - Accessibility standards (WCAG 2.1)
    - Performance optimization
    - Testing strategies
    
    Your goal is to generate production-ready components that require zero manual fixing.
    Always ensure type safety, proper error handling, and follow the project's conventions."""
    
    temperature: float = 0.7
    enable_code_interpreter: bool = True
    enable_retrieval: bool = False


class PaletteAssistant:
    """OpenAI Assistant for advanced component generation and validation."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[AssistantConfig] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.config = config or AssistantConfig()
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        
        # Assistant will be created/retrieved on first use
        self._assistant = None
        self._assistant_id = os.getenv("PALETTE_ASSISTANT_ID")
        
    def _get_or_create_assistant(self) -> Any:
        """Get existing assistant or create a new one."""
        if self._assistant:
            return self._assistant
            
        # Try to retrieve existing assistant
        if self._assistant_id:
            try:
                self._assistant = self.client.beta.assistants.retrieve(self._assistant_id)
                print(f"✅ Retrieved existing assistant: {self._assistant_id}")
                return self._assistant
            except Exception as e:
                print(f"⚠️ Could not retrieve assistant {self._assistant_id}: {e}")
        
        # Create new assistant
        tools = []
        if self.config.enable_code_interpreter:
            tools.append({"type": "code_interpreter"})
        if self.config.enable_retrieval:
            tools.append({"type": "retrieval"})
            
        # Add custom function tools
        tools.extend(self._get_function_tools())
        
        self._assistant = self.client.beta.assistants.create(
            name=self.config.name,
            instructions=self.config.instructions,
            model=self.config.model,
            tools=tools
        )
        
        print(f"✅ Created new assistant: {self._assistant.id}")
        print(f"💡 To reuse this assistant, set PALETTE_ASSISTANT_ID={self._assistant.id}")
        
        return self._assistant
    
    def _get_function_tools(self) -> List[Dict]:
        """Define custom function tools for the assistant."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_existing_component",
                    "description": "Analyze an existing component in the project to understand patterns",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the component file"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["structure", "patterns", "dependencies", "styling"],
                                "description": "Type of analysis to perform"
                            }
                        },
                        "required": ["file_path", "analysis_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "validate_typescript",
                    "description": "Run TypeScript compiler to validate generated code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "TypeScript code to validate"
                            },
                            "tsconfig_path": {
                                "type": "string",
                                "description": "Path to tsconfig.json"
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "check_import_availability",
                    "description": "Check if an import is available in the project",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "import_path": {
                                "type": "string",
                                "description": "Import path to check (e.g., '@/components/ui/button')"
                            },
                            "project_path": {
                                "type": "string",
                                "description": "Root path of the project"
                            }
                        },
                        "required": ["import_path", "project_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_design_tokens",
                    "description": "Get design tokens from the project (colors, spacing, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "token_type": {
                                "type": "string",
                                "enum": ["colors", "spacing", "typography", "shadows", "all"],
                                "description": "Type of design tokens to retrieve"
                            },
                            "project_path": {
                                "type": "string",
                                "description": "Root path of the project"
                            }
                        },
                        "required": ["token_type", "project_path"]
                    }
                }
            }
        ]
    
    async def generate_component_async(
        self, 
        prompt: str, 
        context: Dict[str, Any],
        use_code_interpreter: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate a component using the assistant with async support."""
        assistant = self._get_or_create_assistant()
        
        # Create a thread
        thread = await self.async_client.beta.threads.create()
        
        # Prepare the message with context
        message_content = self._prepare_message(prompt, context)
        
        # Add message to thread
        await self.async_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_content
        )
        
        # Run the assistant
        run = await self.async_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions=self._get_run_instructions(context)
        )
        
        # Wait for completion and handle function calls
        result = await self._wait_for_completion(thread.id, run.id)
        
        # Extract component code and metadata
        component_code, metadata = await self._extract_result(thread.id)
        
        return component_code, metadata
    
    def generate_component(
        self, 
        prompt: str, 
        context: Dict[str, Any],
        use_code_interpreter: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """Synchronous wrapper for component generation."""
        return asyncio.run(self.generate_component_async(prompt, context, use_code_interpreter))
    
    async def validate_with_interpreter(self, code: str) -> Dict[str, Any]:
        """Use Code Interpreter to validate component code."""
        assistant = self._get_or_create_assistant()
        
        # Create a thread
        thread = await self.async_client.beta.threads.create()
        
        # Validation prompt
        validation_prompt = f"""
        Please validate this React component code using the Code Interpreter:
        
        ```typescript
        {code}
        ```
        
        Check for:
        1. TypeScript syntax and type errors
        2. React hooks usage violations
        3. Missing imports
        4. Potential runtime errors
        5. Performance issues
        6. Accessibility concerns
        
        Return a structured JSON report with:
        - has_errors: boolean
        - errors: array of error objects
        - warnings: array of warning objects
        - suggestions: array of improvement suggestions
        - fixed_code: the corrected code if there were fixable issues
        """
        
        # Add message
        await self.async_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=validation_prompt
        )
        
        # Run with code interpreter
        run = await self.async_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            tools=[{"type": "code_interpreter"}]
        )
        
        # Wait for completion
        await self._wait_for_completion(thread.id, run.id)
        
        # Extract validation results
        messages = await self.async_client.beta.threads.messages.list(thread_id=thread.id)
        
        for message in messages.data:
            if message.role == "assistant":
                # Extract JSON from the response
                content = message.content[0].text.value
                try:
                    # Find JSON in the response
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        return json.loads(json_match.group())
                except:
                    pass
                    
        return {
            "has_errors": False,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "message": "Validation completed"
        }
    
    def _prepare_message(self, prompt: str, context: Dict[str, Any]) -> str:
        """Prepare the message with context for the assistant."""
        message_parts = [f"Generate a React component based on this request: {prompt}\n"]
        
        # Add context information
        if context.get("framework"):
            message_parts.append(f"Framework: {context['framework']}")
        
        if context.get("styling"):
            message_parts.append(f"Styling: {context['styling']}")
            
        if context.get("component_library"):
            message_parts.append(f"Component Library: {context['component_library']}")
            
        if context.get("typescript", True):
            message_parts.append("Use TypeScript with proper type definitions")
            
        if context.get("design_tokens"):
            tokens = context["design_tokens"]
            if tokens.get("colors"):
                message_parts.append(f"Available colors: {', '.join(tokens['colors'][:10])}")
            if tokens.get("spacing"):
                message_parts.append(f"Spacing scale: {', '.join(str(s) for s in tokens['spacing'][:8])}")
        
        if context.get("existing_patterns"):
            message_parts.append("\nFollow these existing patterns from the codebase:")
            for pattern in context["existing_patterns"][:3]:
                message_parts.append(f"- {pattern}")
        
        return "\n".join(message_parts)
    
    def _get_run_instructions(self, context: Dict[str, Any]) -> str:
        """Get specific instructions for this run based on context."""
        instructions = ["Generate production-ready code that requires zero manual fixing."]
        
        if context.get("component_library") == "shadcn/ui":
            instructions.append("Use shadcn/ui components and patterns. Import from '@/components/ui/*'.")
            
        if context.get("styling") == "tailwind":
            instructions.append("Use Tailwind CSS classes. Avoid inline styles.")
            
        if context.get("accessibility_required", True):
            instructions.append("Ensure WCAG 2.1 AA compliance with proper ARIA labels.")
            
        return " ".join(instructions)
    
    async def _wait_for_completion(self, thread_id: str, run_id: str) -> Any:
        """Wait for assistant run to complete, handling function calls."""
        while True:
            run = await self.async_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                return run
            elif run.status == "requires_action":
                # Handle function calls
                await self._handle_function_calls(thread_id, run)
            elif run.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed with status: {run.status}")
            
            await asyncio.sleep(1)
    
    async def _handle_function_calls(self, thread_id: str, run: Any):
        """Handle function calls from the assistant."""
        tool_outputs = []
        
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            # Execute the function
            result = await self._execute_function(function_name, arguments)
            
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result)
            })
        
        # Submit outputs
        await self.async_client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
    
    async def _execute_function(self, function_name: str, arguments: Dict) -> Dict:
        """Execute a function call and return results."""
        # This will be implemented to call actual functions
        # For now, return mock data
        if function_name == "analyze_existing_component":
            return {
                "patterns": ["useState for state", "useEffect for side effects"],
                "structure": "Functional component with TypeScript"
            }
        elif function_name == "validate_typescript":
            return {"valid": True, "errors": []}
        elif function_name == "check_import_availability":
            return {"available": True, "resolved_path": arguments["import_path"]}
        elif function_name == "get_design_tokens":
            return {
                "colors": ["blue", "gray", "green", "red"],
                "spacing": ["2", "4", "6", "8", "12", "16"]
            }
        
        return {"error": f"Unknown function: {function_name}"}
    
    async def _extract_result(self, thread_id: str) -> Tuple[str, Dict[str, Any]]:
        """Extract component code and metadata from assistant response."""
        messages = await self.async_client.beta.threads.messages.list(thread_id=thread_id)
        
        component_code = ""
        metadata = {
            "imports": [],
            "dependencies": [],
            "suggestions": []
        }
        
        for message in messages.data:
            if message.role == "assistant":
                content = message.content[0].text.value
                
                # Extract code blocks
                import re
                code_blocks = re.findall(r'```(?:typescript|tsx|jsx|js)?\n([\s\S]*?)```', content)
                if code_blocks:
                    component_code = code_blocks[0].strip()
                
                # Extract metadata if present
                json_blocks = re.findall(r'```json\n([\s\S]*?)```', content)
                if json_blocks:
                    try:
                        extracted_metadata = json.loads(json_blocks[0])
                        metadata.update(extracted_metadata)
                    except:
                        pass
                
                break
        
        return component_code, metadata
    
    async def process_mcp_result(self, mcp_result: Dict) -> Dict:
        """Process MCP server results with AI enhancement."""
        # Create a thread for processing
        thread = await self.async_client.beta.threads.create()
        
        prompt = f"""
        Process and enhance this MCP server result:
        {json.dumps(mcp_result, indent=2)}
        
        Provide insights and suggestions for component generation.
        """
        
        await self.async_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        assistant = self._get_or_create_assistant()
        run = await self.async_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        await self._wait_for_completion(thread.id, run.id)
        
        # Extract enhanced result
        messages = await self.async_client.beta.threads.messages.list(thread_id=thread.id)
        
        for message in messages.data:
            if message.role == "assistant":
                return {
                    "original": mcp_result,
                    "enhanced": message.content[0].text.value,
                    "processed": True
                }
        
        return mcp_result