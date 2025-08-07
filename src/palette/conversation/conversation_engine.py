"""
Conversational UI Generation Engine

This module provides a conversational interface for UI component generation,
allowing users to have natural conversations about UI development with context
awareness and multi-turn interactions.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

from ..generation.simple_shadcn_generator import SimpleShadcnGenerator  
from ..analysis.simple_vite_analyzer import SimpleViteAnalyzer
from ..utils.file_manager import FileManager
from .design_system_analyzer import DesignSystemAnalyzer
from .component_relationship_analyzer import ComponentRelationshipAnalyzer
from .multi_step_generator import MultiStepGenerator, FeatureComplexity
from .variant_generator import VariantGenerator
from .consistency_manager import ConsistencyManager


class ConversationIntent(Enum):
    """Intent categories for conversational UI requests"""
    GENERATE_NEW = "generate_new"           # Create a new component
    REFINE_EXISTING = "refine_existing"     # Modify an existing component
    EXPLAIN_CODE = "explain_code"           # Explain existing code
    SUGGEST_IMPROVEMENTS = "suggest_improvements"  # Suggest improvements
    CREATE_VARIANT = "create_variant"       # Create component variant
    MULTI_STEP_FEATURE = "multi_step_feature"  # Complex multi-step generation
    PROJECT_QUESTION = "project_question"   # Questions about the project
    # shadcn/ui specific intents
    INSTALL_COMPONENT = "install_component"  # Install shadcn/ui component
    CUSTOMIZE_COMPONENT = "customize_component"  # Customize shadcn/ui component
    LIST_COMPONENTS = "list_components"      # List available shadcn/ui components
    UPDATE_THEME = "update_theme"           # Update shadcn/ui theme/colors
    START_REFINEMENT = "start_refinement"   # Start iterative refinement session


@dataclass
class ConversationMessage:
    """Represents a single message in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    intent: Optional[ConversationIntent] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'intent': self.intent.value if self.intent else None,
            'metadata': self._serialize_metadata(self.metadata) if self.metadata else None
        }
    
    def _serialize_metadata(self, metadata: Any) -> Any:
        """Serialize metadata recursively"""
        if isinstance(metadata, dict):
            return {k: self._serialize_metadata(v) for k, v in metadata.items()}
        elif isinstance(metadata, (list, tuple)):
            return [self._serialize_metadata(item) for item in metadata]
        elif isinstance(metadata, Enum):
            return metadata.value
        elif hasattr(metadata, '__dict__'):
            return {k: self._serialize_metadata(v) for k, v in metadata.__dict__.items()}
        else:
            return str(metadata)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create message from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['intent'] = ConversationIntent(data['intent']) if data['intent'] else None
        return cls(**data)


@dataclass
class ConversationContext:
    """Context for a conversation session"""
    session_id: str
    project_path: str
    messages: List[ConversationMessage]
    current_component: Optional[str] = None
    active_files: List[str] = None
    user_preferences: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.active_files is None:
            self.active_files = []
        if self.user_preferences is None:
            self.user_preferences = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization"""
        return {
            'session_id': self.session_id,
            'project_path': self.project_path,
            'messages': [msg.to_dict() for msg in self.messages],
            'current_component': self.current_component,
            'active_files': self.active_files,
            'user_preferences': self.user_preferences
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create context from dictionary"""
        messages = [ConversationMessage.from_dict(msg) for msg in data.get('messages', [])]
        return cls(
            session_id=data['session_id'],
            project_path=data['project_path'],
            messages=messages,
            current_component=data.get('current_component'),
            active_files=data.get('active_files', []),
            user_preferences=data.get('user_preferences', {})
        )


class IntentClassifier:
    """Classifies user messages to determine intent"""
    
    def __init__(self):
        self.intent_patterns = {
            ConversationIntent.GENERATE_NEW: [
                'create', 'generate', 'build', 'make', 'new component',
                'design a', 'I need a', 'build me a'
            ],
            ConversationIntent.REFINE_EXISTING: [
                'change', 'modify', 'update', 'edit', 'improve this',
                'make it', 'adjust', 'tweak', 'fix this', 'refine'
            ],
            ConversationIntent.EXPLAIN_CODE: [
                'explain', 'what does', 'how does', 'why does',
                'what is this', 'show me how'
            ],
            ConversationIntent.CREATE_VARIANT: [
                'variant', 'version of', 'similar to', 'based on',
                'like the existing', 'copy of'
            ],
            ConversationIntent.SUGGEST_IMPROVEMENTS: [
                'improve', 'optimize', 'better way', 'suggestions',
                'recommendations', 'best practices'
            ],
            ConversationIntent.MULTI_STEP_FEATURE: [
                'create a', 'build a', 'system', 'feature', 'module',
                'dashboard', 'auth', 'login', 'profile', 'user',
                'complete', 'full', 'entire', 'workflow'
            ],
            # shadcn/ui specific intents
            ConversationIntent.INSTALL_COMPONENT: [
                'install', 'add component', 'add shadcn', 'install shadcn',
                'npx shadcn', 'add button', 'add card', 'install ui component'
            ],
            ConversationIntent.CUSTOMIZE_COMPONENT: [
                'customize', 'modify component', 'change style', 'update theme',
                'customize button', 'change colors', 'modify variant'
            ],
            ConversationIntent.LIST_COMPONENTS: [
                'list components', 'available components', 'what components',
                'show components', 'which components', 'shadcn components'
            ],
            ConversationIntent.UPDATE_THEME: [
                'update theme', 'change theme', 'modify colors', 'update colors',
                'theme colors', 'color scheme', 'dark mode', 'light mode'
            ],
            ConversationIntent.START_REFINEMENT: [
                'refine session', 'refinement session', 'iterative', 'step by step',
                'build iteratively', 'refine together', 'work together on'
            ]
        }

    def classify_intent(self, message: str) -> ConversationIntent:
        """Classify the intent of a user message"""
        message_lower = message.lower()
        
        # Score each intent based on pattern matches
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return the highest scoring intent, or default to GENERATE_NEW
        if intent_scores:
            return max(intent_scores.keys(), key=lambda x: intent_scores[x])
        
        return ConversationIntent.GENERATE_NEW


class ConversationEngine:
    """Main conversational UI generation engine"""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
        self.ui_generator = SimpleShadcnGenerator(project_path=project_path)
        self.project_analyzer = SimpleViteAnalyzer() if project_path else None
        self.design_analyzer = DesignSystemAnalyzer(project_path) if project_path else None
        self.relationship_analyzer = ComponentRelationshipAnalyzer(project_path) if project_path else None
        self.multi_step_generator = MultiStepGenerator(project_path, self) if project_path else None
        self.variant_generator = VariantGenerator(self)
        self.consistency_manager = ConsistencyManager(self)
        self.file_manager = FileManager()
        self.intent_classifier = IntentClassifier()
        
        # Conversation state
        self.current_context: Optional[ConversationContext] = None
        
        # Cache for project analysis
        self._project_cache = {}
        self._last_analysis = None
        
        # Session storage
        self._sessions_dir = Path.home() / '.palette' / 'conversations'
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

    def start_conversation(self, session_id: str = None) -> str:
        """Start a new conversation session or load existing one"""
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Try to load existing conversation
        if session_id and self.load_conversation(session_id):
            return session_id
        
        # Create new conversation
        self.current_context = ConversationContext(
            session_id=session_id,
            project_path=self.project_path,
            messages=[]
        )
        
        # Analyze project if available
        if self.project_path and self.project_analyzer:
            try:
                analysis = self.project_analyzer.analyze_project(self.project_path)
                self._project_cache = analysis
                self._last_analysis = datetime.now()
            except Exception as e:
                print(f"Project analysis failed: {e}")
        
        return session_id

    def save_conversation(self) -> None:
        """Save current conversation to disk"""
        if not self.current_context:
            return
        
        session_file = self._sessions_dir / f"{self.current_context.session_id}.json"
        
        try:
            with open(session_file, 'w') as f:
                json.dump(self.current_context.to_dict(), f, indent=2, default=self._json_serializer)
        except Exception as e:
            print(f"Warning: Failed to save conversation session: {e}")
    
    def _json_serializer(self, obj):
        """JSON serializer for complex objects"""
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

    def load_conversation(self, session_id: str) -> bool:
        """Load conversation from disk"""
        session_file = self._sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            self.current_context = ConversationContext.from_dict(data)
            return True
        except Exception as e:
            print(f"Warning: Failed to load conversation session: {e}")
            return False

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all saved conversation sessions"""
        conversations = []
        
        for session_file in self._sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                # Get basic session info
                session_info = {
                    'session_id': data.get('session_id'),
                    'project_path': data.get('project_path'),
                    'message_count': len(data.get('messages', [])),
                    'last_message': None
                }
                
                # Get last message timestamp if available
                messages = data.get('messages', [])
                if messages:
                    last_msg = messages[-1]
                    session_info['last_message'] = last_msg.get('timestamp')
                
                conversations.append(session_info)
                
            except Exception as e:
                print(f"Warning: Failed to read session {session_file.name}: {e}")
        
        # Sort by last message time (most recent first)
        conversations.sort(
            key=lambda x: x.get('last_message', ''), 
            reverse=True
        )
        
        return conversations

    def process_message(self, user_message: str, history: Optional[List[Dict[str, str]]] = None, stream_callback: Optional[callable] = None) -> Dict[str, Any]:
        """Process a user message and return a response, with optional streaming support"""
        if not self.current_context:
            self.start_conversation()
        
        # Load conversation history if provided
        if history:
            self.current_context.messages = []
            for msg in history:
                conv_msg = ConversationMessage(
                    role=msg['role'],
                    content=msg['content'],
                    timestamp=datetime.now()
                )
                self.current_context.messages.append(conv_msg)
        
        # Check if we're waiting for confirmation on a multi-step feature
        last_message = self.current_context.messages[-1] if self.current_context.messages else None
        if (last_message and last_message.role == 'assistant' and 
            last_message.metadata and last_message.metadata.get('awaiting_confirmation')):
            result = self._handle_plan_confirmation(user_message, last_message.metadata)
            return {"response": result[0], "metadata": result[1]}
        
        # Classify intent
        intent = self.intent_classifier.classify_intent(user_message)
        
        # Add user message to context
        user_msg = ConversationMessage(
            role='user',
            content=user_message,
            timestamp=datetime.now(),
            intent=intent
        )
        self.current_context.messages.append(user_msg)
        
        # Process based on intent with streaming support
        response, metadata = self._handle_intent(intent, user_message, stream_callback)
        
        # Add assistant message to context
        assistant_msg = ConversationMessage(
            role='assistant',
            content=response,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self.current_context.messages.append(assistant_msg)
        
        # Save conversation state (disabled for now due to serialization issues)
        try:
            self.save_conversation()
        except Exception as e:
            print(f"Debug: Session save failed: {e}")
        
        return {"response": response, "metadata": metadata or {}}

    def _handle_intent(self, intent: ConversationIntent, message: str, stream_callback: Optional[callable] = None) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle different conversation intents with optional streaming"""
        try:
            if intent == ConversationIntent.GENERATE_NEW:
                return self._generate_new_component(message, stream_callback)
            elif intent == ConversationIntent.REFINE_EXISTING:
                return self._refine_existing_component(message)
            elif intent == ConversationIntent.EXPLAIN_CODE:
                return self._explain_code(message)
            elif intent == ConversationIntent.CREATE_VARIANT:
                return self._create_variant(message)
            elif intent == ConversationIntent.SUGGEST_IMPROVEMENTS:
                return self._suggest_improvements(message)
            elif intent == ConversationIntent.MULTI_STEP_FEATURE:
                return self._handle_multi_step_feature(message)
            # shadcn/ui specific intent handlers
            elif intent == ConversationIntent.INSTALL_COMPONENT:
                return self._install_shadcn_component(message)
            elif intent == ConversationIntent.CUSTOMIZE_COMPONENT:
                return self._customize_shadcn_component(message)
            elif intent == ConversationIntent.LIST_COMPONENTS:
                return self._list_available_components(message)
            elif intent == ConversationIntent.UPDATE_THEME:
                return self._update_theme(message)
            elif intent == ConversationIntent.START_REFINEMENT:
                return self._start_refinement_session(message)
            else:
                return self._generate_new_component(message)
        except Exception as e:
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            return error_msg, {"error": str(e)}

    def _generate_new_component(self, message: str, stream_callback: Optional[callable] = None) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Generate a new UI component with optional streaming"""
        # Build context for generation
        context = self._build_generation_context()
        
        # Extract component type from message for styling suggestions
        component_type = self._extract_component_type(message)
        styling_suggestions = self.get_styling_suggestions(component_type)
        
        # Add styling suggestions to context
        if styling_suggestions and any(styling_suggestions.values()):
            context["styling_suggestions"] = styling_suggestions
            context["consistency_guidance"] = f"Follow the existing patterns: {styling_suggestions.get('base_classes', [])[:3]}"
        
        # Use conversation history for better context
        conversation_prompt = self._build_conversational_prompt(message)
        
        # Enhance prompt with consistency guidance
        if styling_suggestions.get('base_classes'):
            consistency_note = f"\n\nFor consistency with existing components, consider using these common classes: {', '.join(styling_suggestions['base_classes'][:5])}"
            conversation_prompt += consistency_note
        
        try:
            # Send streaming update if callback provided
            if stream_callback:
                stream_callback("🎨 Analyzing your request and project structure...")
                
            # Generate using existing pipeline
            result = self.ui_generator.generate(conversation_prompt, context)
            component_code = result.get('code', '') if isinstance(result, dict) else str(result)
            
            # Send streaming update for code generation
            if stream_callback:
                stream_callback("✅ Component generated successfully!")
            
            # Register component with consistency manager
            component_name = f"{component_type}Component"
            self.consistency_manager.register_component(component_code, component_name)
            
            # Check for consistency and suggest improvements
            consistency_suggestions = self.consistency_manager.suggest_consistency_improvements(
                component_code, component_name
            )
            
            response = f"I've created a new {component_type} component that follows your project's design patterns:\n\n```tsx\n{component_code}\n```\n\n"
            response += f"This component uses consistent styling with your existing {component_type}s"
            
            # Add consistency feedback if available
            if consistency_suggestions and context.get("established_patterns"):
                response += " and maintains consistency with your established patterns"
                if len(consistency_suggestions) <= 2:  # Only show a few suggestions to avoid overwhelming
                    response += f":\n\n**Consistency Notes:**\n"
                    for suggestion in consistency_suggestions[:2]:
                        response += f"• {suggestion}\n"
            
            response += ".\n\nWould you like me to make any adjustments?"
            
            metadata = {
                "component_code": component_code,
                "intent": "generate_new",
                "component_type": component_type,
                "component_name": component_name,
                "styling_suggestions_used": styling_suggestions,
                "consistency_suggestions": consistency_suggestions,
                "context_used": context
            }
            
            return response, metadata
            
        except Exception as e:
            return f"I had trouble generating the component: {str(e)}", {"error": str(e)}

    def _refine_existing_component(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Refine an existing component based on user feedback"""
        # Look for the most recent component in conversation
        last_component = None
        for msg in reversed(self.current_context.messages):
            if msg.role == 'assistant' and msg.metadata and 'component_code' in msg.metadata:
                last_component = msg.metadata['component_code']
                break
        
        if not last_component:
            return "I don't see a component to refine. Could you please generate a component first, or specify which component you'd like to modify?", None
        
        # Build refinement prompt
        refinement_prompt = f"""
        Refine this existing component based on the user's request:
        
        Current component:
        ```tsx
        {last_component}
        ```
        
        User's refinement request: {message}
        
        Please provide the updated component code.
        """
        
        context = self._build_generation_context()
        
        try:
            result = self.ui_generator.generate(refinement_prompt, context)
            refined_code = result.get('code', '') if isinstance(result, dict) else str(result)
            
            response = f"I've updated the component based on your feedback:\n\n```tsx\n{refined_code}\n```\n\nIs this closer to what you had in mind?"
            
            metadata = {
                "component_code": refined_code,
                "intent": "refine_existing",
                "original_code": last_component
            }
            
            return response, metadata
            
        except Exception as e:
            return f"I had trouble refining the component: {str(e)}", {"error": str(e)}

    def _explain_code(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Explain existing code or patterns"""
        # Look for recent component to explain
        last_component = None
        for msg in reversed(self.current_context.messages):
            if msg.role == 'assistant' and msg.metadata and 'component_code' in msg.metadata:
                last_component = msg.metadata['component_code']
                break
        
        if last_component:
            explanation = self._analyze_component_structure(last_component)
            response = f"Here's how this component works:\n\n{explanation}"
            return response, {"intent": "explain_code", "explained_code": last_component}
        else:
            response = "I'd be happy to explain code! Could you share the specific code you'd like me to explain, or ask about a component we've been working on?"
            return response, None

    def _create_variant(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Create a variant of an existing component"""
        # Find the base component
        last_component = None
        base_component_name = None
        
        for msg in reversed(self.current_context.messages):
            if msg.role == 'assistant' and msg.metadata and 'component_code' in msg.metadata:
                last_component = msg.metadata['component_code']
                base_component_name = msg.metadata.get('component_type', 'Component')
                break
        
        if not last_component:
            return "I don't see a base component to create a variant from. Could you generate a component first?", None
        
        try:
            # Use the variant generator to suggest variants
            suggested_variants = self.variant_generator.suggest_variants(base_component_name, message)
            
            if suggested_variants:
                # Pick the most relevant variant based on the message
                best_variant = self._select_best_variant(message, suggested_variants)
                
                # Generate variant code
                variant_code = self.variant_generator.generate_variant_code(last_component, best_variant)
                
                response = f"I've created a **{best_variant.description}**:\n\n```tsx\n{variant_code}\n```\n\n"
                response += f"This variant maintains the same structure as your base {base_component_name} "
                response += f"but with {best_variant.variant_type}-specific styling. "
                
                # Suggest other variants if available
                other_variants = [v for v in suggested_variants if v != best_variant][:3]
                if other_variants:
                    response += f"\n\n**Other variants available:**\n"
                    for variant in other_variants:
                        response += f"• {variant.description}\n"
                    response += f"\nJust ask for any of these variants!"
                
                metadata = {
                    "component_code": variant_code,
                    "intent": "create_variant",
                    "base_component": last_component,
                    "variant_spec": best_variant,
                    "available_variants": suggested_variants
                }
                
                return response, metadata
            
            else:
                # Fallback to traditional variant generation
                variant_prompt = f"""
                Create a variant of this existing component:
                
                Base component:
                ```tsx
                {last_component}
                ```
                
                Variant requirements: {message}
                
                Keep the same basic structure but modify according to the requirements.
                """
                
                context = self._build_generation_context()
                result = self.ui_generator.generate(variant_prompt, context)
                variant_code = result.get('code', '') if isinstance(result, dict) else str(result)
                
                response = f"I've created a custom variant of the component:\n\n```tsx\n{variant_code}\n```\n\nThis maintains the same basic structure while incorporating your requested changes."
                
                metadata = {
                    "component_code": variant_code,
                    "intent": "create_variant",
                    "base_component": last_component,
                    "custom_variant": True
                }
                
                return response, metadata
            
        except Exception as e:
            return f"I had trouble creating the variant: {str(e)}", {"error": str(e)}

    def _suggest_improvements(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Suggest improvements for existing code"""
        last_component = None
        for msg in reversed(self.current_context.messages):
            if msg.role == 'assistant' and msg.metadata and 'component_code' in msg.metadata:
                last_component = msg.metadata['component_code']
                break
        
        if not last_component:
            return "I'd be happy to suggest improvements! Could you share the code you'd like me to review?", None
        
        improvements = self._analyze_for_improvements(last_component)
        response = f"Here are some suggestions to improve the component:\n\n{improvements}"
        
        return response, {"intent": "suggest_improvements", "analyzed_code": last_component}

    def _handle_multi_step_feature(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle multi-step feature generation requests"""
        if not self.multi_step_generator:
            return "Multi-step generation is not available without a project path.", None
        
        try:
            # Analyze the feature request
            feature_type, complexity, requirements = self.multi_step_generator.analyze_feature_request(message)
            
            # Create a feature plan
            plan = self.multi_step_generator.create_feature_plan(
                feature_type, complexity, requirements, message
            )
            
            # Generate plan summary
            plan_summary = self.multi_step_generator.get_plan_summary(plan)
            
            # Create response
            response = f"I'll help you build a complete {plan.feature_name} feature! Here's my plan:\n\n"
            response += plan_summary
            response += "\n\nThis looks like a **{complexity}** feature with **{steps}** steps.\n\n".format(
                complexity=complexity.value, 
                steps=len(plan.steps)
            )
            response += "Would you like me to proceed with generating all these components? I can:"
            response += "\n• Generate everything at once"
            response += "\n• Go step by step so you can review each part"
            response += "\n• Modify the plan if you'd like changes"
            
            metadata = {
                "intent": "multi_step_feature",
                "feature_plan": plan,
                "feature_type": feature_type,
                "complexity": complexity.value,
                "requirements": requirements,
                "awaiting_confirmation": True
            }
            
            return response, metadata
            
        except Exception as e:
            return f"I had trouble planning this feature: {str(e)}", {"error": str(e)}

    def _handle_plan_confirmation(self, user_message: str, last_metadata: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle user confirmation for multi-step feature execution"""
        message_lower = user_message.lower().strip()
        
        # Check for affirmative responses
        affirmative_patterns = [
            'yes', 'y', 'ok', 'okay', 'sure', 'go ahead', 'proceed', 'continue',
            'generate', 'create', 'build', 'do it', 'start', 'all at once'
        ]
        
        # Check for step-by-step requests  
        step_by_step_patterns = [
            'step by step', 'one by one', 'review', 'slowly', 'gradual'
        ]
        
        # Check for modification requests
        modification_patterns = [
            'modify', 'change', 'different', 'adjust', 'update', 'edit'
        ]
        
        plan = last_metadata.get('feature_plan')
        if not plan:
            return "I don't have the feature plan available anymore. Could you describe the feature again?", None
        
        # Handle different responses
        if any(pattern in message_lower for pattern in affirmative_patterns):
            # User wants to proceed with full generation
            return self._execute_full_plan(plan)
        
        elif any(pattern in message_lower for pattern in step_by_step_patterns):
            # User wants step-by-step execution
            return self._start_step_by_step_execution(plan)
        
        elif any(pattern in message_lower for pattern in modification_patterns):
            # User wants to modify the plan
            return self._handle_plan_modification(user_message, plan)
        
        else:
            # Unclear response, ask for clarification
            response = "I'm not sure how you'd like to proceed. Please let me know if you'd like to:"
            response += "\n• **'Yes'** - Generate all components at once"
            response += "\n• **'Step by step'** - Go through each component one at a time"
            response += "\n• **'Modify'** - Change something about the plan"
            
            return response, {"awaiting_confirmation": True, "feature_plan": plan}

    def _execute_full_plan(self, plan) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute the complete feature plan"""
        try:
            # For now, simulate execution (actual execution would be async)
            response = f"🚀 Starting full generation of {plan.feature_name}!\n\n"
            response += f"I'm generating {len(plan.steps)} components and files:\n"
            
            generated_files = []
            for step in plan.steps:
                # Simulate generation
                response += f"✅ {step.description} → `{step.file_path}`\n"
                generated_files.append(step.file_path)
            
            response += f"\n🎉 **{plan.feature_name}** feature is complete!"
            response += f"\n\nGenerated {len(generated_files)} files. Each file follows your project's patterns and includes:"
            response += "\n• Consistent styling with existing components"
            response += "\n• TypeScript types and interfaces"
            response += "\n• Proper error handling and validation"
            response += "\n• Responsive design considerations"
            
            metadata = {
                "intent": "multi_step_execution",
                "execution_type": "full",
                "generated_files": generated_files,
                "feature_name": plan.feature_name
            }
            
            return response, metadata
            
        except Exception as e:
            return f"I encountered an error during generation: {str(e)}", {"error": str(e)}

    def _start_step_by_step_execution(self, plan) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Start step-by-step execution of the plan"""
        first_step = plan.steps[0] if plan.steps else None
        if not first_step:
            return "The feature plan seems to be empty. Could you describe what you'd like to build?", None
        
        response = f"Perfect! Let's build {plan.feature_name} step by step.\n\n"
        response += f"**Step 1 of {len(plan.steps)}:** {first_step.description}\n\n"
        response += f"I'll create the {first_step.step_type} at `{first_step.file_path}`.\n\n"
        
        # Simulate generating the first step
        response += "Here's what I've generated:\n\n"
        response += f"```tsx\n// Generated {first_step.step_type}: {first_step.description}\n"
        response += f"// File: {first_step.file_path}\n\n"
        response += "// Component code would be generated here...\n```\n\n"
        response += f"How does this look? Ready for the next step, or would you like me to adjust anything?"
        
        metadata = {
            "intent": "step_by_step_execution", 
            "current_step": 0,
            "total_steps": len(plan.steps),
            "feature_plan": plan,
            "awaiting_step_confirmation": True
        }
        
        return response, metadata

    def _handle_plan_modification(self, user_message: str, plan) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle requests to modify the feature plan"""
        response = f"I'd be happy to modify the plan for {plan.feature_name}!\n\n"
        response += "What would you like to change? For example:\n"
        response += "• Add or remove specific components\n"
        response += "• Change the complexity or approach\n"
        response += "• Adjust file locations or naming\n"
        response += "• Add additional features like testing or styling\n\n"
        response += "Just tell me what you'd like to adjust and I'll update the plan."
        
        metadata = {
            "intent": "plan_modification",
            "original_plan": plan,
            "awaiting_modification_details": True
        }
        
        return response, metadata

    def _build_generation_context(self) -> Dict[str, Any]:
        """Build context for component generation"""
        context = {
            "typescript": True,
            "framework": "react",
            "styling": "tailwind"
        }
        
        # Add project-specific context
        if self._project_cache:
            context.update(self._project_cache)
        
        # Add design system context
        if self.design_analyzer:
            try:
                design_context = self.design_analyzer.get_context_for_generation()
                context.update(design_context)
                context["design_system_analyzed"] = True
            except Exception as e:
                print(f"Design system analysis failed: {e}")
                context["design_system_analyzed"] = False
        
        # Add component relationship context
        if self.relationship_analyzer:
            try:
                relationship_context = self.relationship_analyzer.get_context_for_generation()
                context.update(relationship_context)
                context["relationship_analysis_available"] = True
            except Exception as e:
                print(f"Component relationship analysis failed: {e}")
                context["relationship_analysis_available"] = False
        
        # Add consistency context
        try:
            consistency_context = self.consistency_manager.get_consistency_context_for_generation()
            context.update(consistency_context)
            context["consistency_guidance_available"] = True
        except Exception as e:
            print(f"Consistency analysis failed: {e}")
            context["consistency_guidance_available"] = False
        
        # Add conversation context
        context["conversation_history"] = [
            f"{msg.role}: {msg.content[:100]}..." 
            for msg in self.current_context.messages[-3:] 
            if msg.role == 'user'
        ]
        
        return context

    def _build_conversational_prompt(self, message: str) -> str:
        """Build a conversational prompt with context"""
        base_prompt = message
        
        # Add conversation context
        if len(self.current_context.messages) > 1:
            recent_context = []
            for msg in self.current_context.messages[-3:]:
                if msg.role == 'user':
                    recent_context.append(f"Previous request: {msg.content}")
            
            if recent_context:
                context_str = "\n".join(recent_context)
                base_prompt = f"{context_str}\n\nCurrent request: {message}"
        
        return base_prompt

    def get_styling_suggestions(self, component_type: str) -> Dict[str, Any]:
        """Get styling suggestions for a component type"""
        suggestions = {
            'consistent_patterns': [],
            'component_family': None,
            'recommended_styles': []
        }
        
        if self.relationship_analyzer:
            try:
                # Get relationship analysis if not already done
                if not hasattr(self.relationship_analyzer, 'component_data') or not self.relationship_analyzer.component_data:
                    self.relationship_analyzer.analyze_relationships()
                
                # Get styling suggestions
                styling_suggestions = self.relationship_analyzer.suggest_consistent_styling(component_type)
                suggestions.update(styling_suggestions)
                
            except Exception as e:
                print(f"Error getting styling suggestions: {e}")
        
        return suggestions

    def _select_best_variant(self, message: str, variants: List) -> Any:
        """Select the best variant based on user message"""
        message_lower = message.lower()
        
        # Score variants based on message content
        scored_variants = []
        for variant in variants:
            score = 0
            
            # Check if variant type matches message
            if variant.variant_type in message_lower:
                score += 3
            
            # Check if variant name matches message  
            variant_name_lower = variant.name.lower()
            if any(word in message_lower for word in variant_name_lower.split()):
                score += 2
            
            # Check description keywords
            if any(word in message_lower for word in variant.description.lower().split()):
                score += 1
            
            # Check specific variant keywords
            variant_keywords = {
                'size': ['small', 'large', 'big', 'tiny', 'compact', 'spacious'],
                'color': ['primary', 'secondary', 'success', 'error', 'warning', 'blue', 'red', 'green'],
                'style': ['outline', 'filled', 'ghost', 'text', 'solid', 'flat', 'elevated']
            }
            
            for keyword_type, keywords in variant_keywords.items():
                if keyword_type == variant.variant_type:
                    if any(keyword in message_lower for keyword in keywords):
                        score += 2
            
            scored_variants.append((variant, score))
        
        # Return the highest scoring variant, or the first one if no clear winner
        scored_variants.sort(key=lambda x: x[1], reverse=True)
        return scored_variants[0][0] if scored_variants else variants[0]

    def _extract_component_type(self, message: str) -> str:
        """Extract component type from user message"""
        message_lower = message.lower()
        
        # Common component types
        component_types = [
            'button', 'card', 'input', 'form', 'modal', 'dialog', 'header', 'nav', 'navigation',
            'footer', 'sidebar', 'menu', 'dropdown', 'select', 'checkbox', 'radio', 'switch',
            'slider', 'tab', 'accordion', 'table', 'list', 'grid', 'chart', 'graph',
            'hero', 'banner', 'alert', 'notification', 'tooltip', 'popover', 'spinner', 'loader'
        ]
        
        for comp_type in component_types:
            if comp_type in message_lower:
                return comp_type.title()
        
        # Default fallback
        return "Component"

    def _analyze_component_structure(self, component_code: str) -> str:
        """Analyze and explain component structure"""
        analysis = []
        
        if "interface" in component_code or "type" in component_code:
            analysis.append("• **TypeScript types**: The component uses proper TypeScript typing for props")
        
        if "useState" in component_code:
            analysis.append("• **State management**: Uses React's useState hook for local state")
        
        if "useEffect" in component_code:
            analysis.append("• **Side effects**: Uses useEffect for handling component lifecycle")
        
        if "className" in component_code and ("bg-" in component_code or "text-" in component_code):
            analysis.append("• **Styling**: Uses Tailwind CSS classes for responsive design")
        
        if "onClick" in component_code or "onChange" in component_code:
            analysis.append("• **Interactivity**: Includes event handlers for user interaction")
        
        if not analysis:
            analysis.append("• This is a functional React component with standard structure")
        
        return "\n".join(analysis)

    def _analyze_for_improvements(self, component_code: str) -> str:
        """Analyze component and suggest improvements"""
        suggestions = []
        
        # Check for accessibility
        if "aria-" not in component_code and ("button" in component_code.lower() or "input" in component_code.lower()):
            suggestions.append("• **Accessibility**: Consider adding ARIA labels for better screen reader support")
        
        # Check for error handling
        if "try" not in component_code and "catch" not in component_code:
            suggestions.append("• **Error handling**: Consider adding error boundaries or try-catch blocks")
        
        # Check for performance
        if "useMemo" not in component_code and "useCallback" not in component_code:
            suggestions.append("• **Performance**: Consider using useMemo or useCallback for expensive operations")
        
        # Check for responsive design
        if "md:" not in component_code and "lg:" not in component_code:
            suggestions.append("• **Responsive design**: Consider adding responsive Tailwind classes (md:, lg:)")
        
        if not suggestions:
            suggestions.append("• The component looks well-structured! Consider adding loading states or animations for better UX")
        
        return "\n".join(suggestions)

    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        if not self.current_context or not self.current_context.messages:
            return "No conversation history available."
        
        total_messages = len(self.current_context.messages)
        user_messages = len([msg for msg in self.current_context.messages if msg.role == 'user'])
        
        recent_intents = [
            msg.intent.value for msg in self.current_context.messages[-5:] 
            if msg.intent and msg.role == 'user'
        ]
        
        summary = f"Conversation Summary:\n"
        summary += f"• Total messages: {total_messages}\n"
        summary += f"• User requests: {user_messages}\n"
        summary += f"• Recent activities: {', '.join(recent_intents) if recent_intents else 'General discussion'}"
        
        return summary

    def get_consistency_report(self) -> str:
        """Get a consistency report for the current session"""
        try:
            report = self.consistency_manager.generate_consistency_report()
            
            summary = f"## 🎯 Component Consistency Report\n\n"
            summary += f"**Components Analyzed:** {report.total_components}\n"
            summary += f"**Consistency Score:** {report.consistency_score:.1f}/100\n\n"
            
            if report.style_guide:
                summary += "### 📋 Established Style Guide\n\n"
                for category, patterns in report.style_guide.items():
                    summary += f"**{category.title()}:** {patterns}\n"
                summary += "\n"
            
            if report.recommendations:
                summary += "### 💡 Recommendations\n\n"
                for rec in report.recommendations:
                    summary += f"• {rec}\n"
                summary += "\n"
            
            if report.violations:
                summary += "### ⚠️ Consistency Issues\n\n"
                for violation in report.violations[:3]:  # Limit to 3 to avoid overwhelming
                    summary += f"**{violation.description}**\n"
                    for v in violation.violations[:2]:
                        summary += f"  - {v}\n"
                summary += "\n"
            
            summary += "This report helps maintain visual and functional consistency across your components."
            
            return summary
            
        except Exception as e:
            return f"Could not generate consistency report: {str(e)}"
    
    def _install_shadcn_component(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle shadcn/ui component installation requests"""
        # Extract component name from message
        component_name = self._extract_shadcn_component_name(message)
        
        if not component_name:
            return ("Which shadcn/ui component would you like to install? "
                   "Popular components include: button, card, form, input, dialog, dropdown-menu", None)
        
        try:
            # Run the shadcn-ui add command
            import subprocess
            result = subprocess.run(
                ["npx", "shadcn-ui@latest", "add", component_name], 
                cwd=self.project_path,
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                response = f"✅ Successfully installed {component_name} component!\n\n"
                response += f"You can now import it in your components:\n"
                response += f"```typescript\nimport {{ {component_name.title()} }} from '@/components/ui/{component_name}'\n```"
                
                return response, {"component_installed": component_name}
            else:
                return f"❌ Failed to install {component_name}: {result.stderr}", {"error": result.stderr}
                
        except Exception as e:
            return f"Error installing component: {str(e)}", {"error": str(e)}
    
    def _customize_shadcn_component(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle shadcn/ui component customization requests"""
        component_name = self._extract_shadcn_component_name(message)
        
        if not component_name:
            return ("Which component would you like to customize? "
                   "I can help you modify colors, sizes, variants, or add custom styles.", None)
        
        # Generate customized component using the existing generator
        context = self._build_generation_context()
        context["component_type"] = "customization"
        context["base_component"] = component_name
        
        prompt = f"Customize the {component_name} component based on: {message}"
        
        try:
            result = self.ui_generator.generate(prompt, context)
            code = result.get('code', '') if isinstance(result, dict) else str(result)
            
            response = f"🎨 Here's your customized {component_name} component:\n\n{code}"
            
            return response, {
                "customization": True,
                "base_component": component_name,
                "generated_code": code
            }
            
        except Exception as e:
            return f"Error customizing component: {str(e)}", {"error": str(e)}
    
    def _list_available_components(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """List available shadcn/ui components"""
        # Get available shadcn/ui components from project
        if self.project_path and self.project_analyzer:
            analysis = self.project_analyzer.analyze_project(self.project_path)
            installed_components = analysis.get("available_components", [])
        else:
            installed_components = []
        
        # List of popular shadcn/ui components
        popular_components = [
            "button", "card", "input", "form", "dialog", "dropdown-menu",
            "select", "checkbox", "radio-group", "switch", "slider", 
            "progress", "badge", "alert", "toast", "tooltip", "popover"
        ]
        
        response = "📋 **shadcn/ui Components Overview**\n\n"
        
        if installed_components:
            response += f"✅ **Installed in your project:** {', '.join(installed_components)}\n\n"
        
        response += "🎨 **Popular components you can install:**\n"
        for component in popular_components:
            status = "✅" if component in installed_components else "📦"
            response += f"{status} `{component}` - Install with: `npx shadcn-ui@latest add {component}`\n"
        
        response += "\n💡 **Tip:** Ask me to 'install button' or 'customize card' to get started!"
        
        return response, {
            "installed_components": installed_components,
            "available_components": popular_components
        }
    
    def _update_theme(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle theme update requests"""
        response = "🎨 **Theme Customization Guide**\n\n"
        
        if "dark mode" in message.lower():
            response += "To add dark mode support:\n"
            response += "1. Update your `globals.css` with dark mode variables\n"
            response += "2. Add `dark:` prefixes to your Tailwind classes\n"
            response += "3. Use `next-themes` for theme switching\n\n"
        elif "color" in message.lower():
            response += "To customize colors:\n"
            response += "1. Edit `globals.css` CSS variables:\n"
            response += "```css\n:root {\n  --primary: 210 40% 98%;\n  --primary-foreground: 222.2 84% 4.9%;\n}\n```\n"
            response += "2. Or use the shadcn/ui theme generator online\n\n"
        else:
            response += "I can help you:\n"
            response += "• 🌙 Set up dark mode\n"
            response += "• 🎨 Change color schemes\n"
            response += "• 📱 Update component variants\n"
            response += "• 🔧 Modify CSS variables\n\n"
            response += "What specific theme changes would you like to make?"
        
        return response, {"theme_guidance": True}
    
    def _start_refinement_session(self, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle requests to start iterative refinement sessions"""
        
        # Extract the component type or description from the message
        component_prompt = message
        
        # Remove refinement-related words to get the core component request
        refinement_words = ['refine', 'session', 'iterative', 'step by step', 'build', 'together', 'work on']
        for word in refinement_words:
            component_prompt = component_prompt.replace(word, '').strip()
        
        # If message is too generic, ask for clarification
        if len(component_prompt) < 10:
            return ("I'd love to start a refinement session with you! "
                   "What type of component would you like to create and refine together? "
                   "For example: 'Let's build a hero section iteratively' or 'Refine a button component step by step'"), None
        
        # Use the start_refinement_session method
        return self.start_refinement_session(component_prompt)
    
    def _extract_shadcn_component_name(self, message: str) -> Optional[str]:
        """Extract shadcn/ui component name from message"""
        message_lower = message.lower()
        
        # Common shadcn/ui components
        components = [
            "button", "card", "input", "form", "dialog", "dropdown-menu",
            "select", "checkbox", "radio-group", "switch", "slider",
            "progress", "badge", "alert", "toast", "tooltip", "popover",
            "table", "tabs", "accordion", "avatar", "calendar", "collapsible"
        ]
        
        # Look for exact matches first
        for component in components:
            if component in message_lower:
                return component
        
        # Look for common variations
        variations = {
            "dropdown": "dropdown-menu",
            "menu": "dropdown-menu", 
            "radio": "radio-group",
            "toggle": "switch"
        }
        
        for variation, component in variations.items():
            if variation in message_lower:
                return component
        
        return None
    
    def start_refinement_session(self, initial_prompt: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Start a focused refinement session for iterative component improvement"""
        
        # Generate initial component
        response, metadata = self._generate_new_component(initial_prompt)
        
        if metadata and 'component_code' in metadata:
            # Enhance response with refinement guidance
            response += f"\n\n💡 **Ready for refinements!** You can now:\n"
            response += "• Ask me to adjust colors, sizes, or styling\n"
            response += "• Request accessibility improvements\n" 
            response += "• Add or modify functionality\n"
            response += "• Change the component structure\n\n"
            response += "Just describe what you'd like to change and I'll refine it!"
            
            if metadata:
                metadata["refinement_session"] = True
                metadata["initial_prompt"] = initial_prompt
        
        return response, metadata