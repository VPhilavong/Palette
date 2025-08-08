"""
Interactive Error Resolution System - Coordinates error detection, fixing, and user interaction.

This system integrates all validation components into a comprehensive interactive workflow
that guides users through error resolution with intelligent suggestions and automatic fixes.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable

from .dependency_validator import PreGenerationDependencyValidator, DependencyValidationResult
from .realtime_syntax_validator import RealtimeSyntaxValidator, SyntaxValidationMode, ValidationPhase, GenerationContext
from .renderability_validator import RenderabilityValidator, RenderabilityResult
from .auto_fix_engine import AutoFixEngine, AutoFixResult
from .error_explainer_system import ErrorExplainerSystem, ExplanationLevel
from .validator import ValidationIssue, ValidationLevel


class ResolutionStrategy(Enum):
    """Strategies for error resolution."""
    
    AUTOMATIC = "automatic"      # Auto-fix everything possible
    INTERACTIVE = "interactive"  # Ask user for each fix
    GUIDED = "guided"           # Show options, user confirms
    MANUAL = "manual"           # Only explain, no auto-fixes


class ResolutionPhase(Enum):
    """Phases of the interactive error resolution process."""
    
    PRE_GENERATION = "pre_generation"      # Dependency validation
    REAL_TIME = "real_time"                # During generation validation
    POST_GENERATION = "post_generation"    # Final validation and fixing
    REFINEMENT = "refinement"              # Interactive improvements


@dataclass
class ResolutionAction:
    """Represents an action that can be taken to resolve an error."""
    
    id: str
    description: str
    action_type: str  # "auto_fix", "manual_fix", "install", "explanation"
    confidence: float
    estimated_time: int  # seconds
    requires_user_input: bool = False
    dependencies: List[str] = field(default_factory=list)
    fix_function: Optional[Callable] = None
    preview: Optional[str] = None


@dataclass
class ResolutionSession:
    """Tracks the state of an interactive error resolution session."""
    
    session_id: str
    component_name: str
    phase: ResolutionPhase
    strategy: ResolutionStrategy
    start_time: float
    
    # Current state
    current_code: str
    original_code: str
    context: GenerationContext
    
    # Resolution tracking
    actions_taken: List[ResolutionAction] = field(default_factory=list)
    actions_pending: List[ResolutionAction] = field(default_factory=list)
    errors_resolved: int = 0
    errors_remaining: int = 0
    
    # Results
    dependency_result: Optional[DependencyValidationResult] = None
    syntax_results: Dict[ValidationPhase, Any] = field(default_factory=dict)
    renderability_result: Optional[RenderabilityResult] = None
    final_result: Optional[Dict[str, Any]] = None


class InteractiveErrorResolver:
    """
    Interactive Error Resolution System.
    
    Coordinates all validation and fixing components to provide a comprehensive
    error resolution workflow with user interaction and intelligent automation.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        
        # Initialize all validation components
        self.dependency_validator = PreGenerationDependencyValidator(str(self.project_path))
        self.syntax_validator = RealtimeSyntaxValidator(SyntaxValidationMode.PROGRESSIVE)
        self.renderability_validator = RenderabilityValidator()
        self.auto_fix_engine = AutoFixEngine()
        self.error_explainer = ErrorExplainerSystem()
        
        # Session management
        self.active_sessions: Dict[str, ResolutionSession] = {}
        self.session_counter = 0
    
    def start_resolution_session(
        self,
        code: str,
        context: GenerationContext,
        strategy: ResolutionStrategy = ResolutionStrategy.GUIDED
    ) -> str:
        """
        Start a new interactive error resolution session.
        
        Args:
            code: The component code to validate and fix
            context: Generation context with framework, styling info
            strategy: Resolution strategy to use
            
        Returns:
            Session ID for tracking the resolution process
        """
        
        self.session_counter += 1
        session_id = f"session_{self.session_counter}_{int(time.time())}"
        
        session = ResolutionSession(
            session_id=session_id,
            component_name=context.component_name,
            phase=ResolutionPhase.PRE_GENERATION,
            strategy=strategy,
            start_time=time.time(),
            current_code=code,
            original_code=code,
            context=context
        )
        
        self.active_sessions[session_id] = session
        
        print(f"🚀 Starting interactive error resolution for {context.component_name}")
        print(f"   Session ID: {session_id}")
        print(f"   Strategy: {strategy.value}")
        print(f"   Framework: {context.framework} + {context.styling_system}")
        
        return session_id
    
    def run_comprehensive_resolution(self, session_id: str) -> Dict[str, Any]:
        """
        Run the complete error resolution workflow for a session.
        
        Args:
            session_id: The session to process
            
        Returns:
            Comprehensive resolution results
        """
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        try:
            # Phase 1: Pre-generation dependency validation
            print(f"\n🔍 Phase 1: Pre-Generation Validation")
            self._run_dependency_resolution(session)
            
            # Phase 2: Real-time syntax validation
            print(f"\n🔍 Phase 2: Real-Time Syntax Validation")
            self._run_syntax_resolution(session)
            
            # Phase 3: Post-generation comprehensive validation
            print(f"\n🔍 Phase 3: Post-Generation Validation")
            self._run_renderability_resolution(session)
            
            # Phase 4: Interactive refinement (if needed)
            if session.errors_remaining > 0:
                print(f"\n🔍 Phase 4: Interactive Refinement")
                self._run_interactive_refinement(session)
            
            # Generate final results
            session.final_result = self._generate_session_summary(session)
            
            print(f"\n✅ Resolution session {session_id} completed!")
            print(f"   Errors resolved: {session.errors_resolved}")
            print(f"   Actions taken: {len(session.actions_taken)}")
            print(f"   Final quality: {session.final_result.get('quality_score', 'N/A')}/100")
            
            return session.final_result
            
        except Exception as e:
            print(f"❌ Error in resolution session {session_id}: {e}")
            session.final_result = {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
            return session.final_result
    
    def _run_dependency_resolution(self, session: ResolutionSession) -> None:
        """Run dependency validation and resolution."""
        
        session.phase = ResolutionPhase.PRE_GENERATION
        
        # Validate dependencies
        dep_result = self.dependency_validator.validate_dependencies_for_generation(
            component_requirements=session.context.requirements,
            framework=session.context.framework,
            styling_system=session.context.styling_system,
            component_type="component"
        )
        
        session.dependency_result = dep_result
        
        if not dep_result.all_satisfied:
            print(f"   ⚠️ Found {len(dep_result.missing_dependencies)} missing dependencies")
            
            # Create resolution actions for missing dependencies
            for i, install_cmd in enumerate(dep_result.install_commands):
                action = ResolutionAction(
                    id=f"install_deps_{i}",
                    description=f"Install dependencies: {install_cmd}",
                    action_type="install",
                    confidence=0.95,
                    estimated_time=30,
                    requires_user_input=True,
                    preview=install_cmd
                )
                session.actions_pending.append(action)
            
            # Handle based on strategy
            if session.strategy == ResolutionStrategy.AUTOMATIC:
                self._execute_automatic_actions(session, "install")
            elif session.strategy == ResolutionStrategy.GUIDED:
                self._present_guided_actions(session, "dependencies")
        else:
            print(f"   ✅ All dependencies satisfied")
    
    def _run_syntax_resolution(self, session: ResolutionSession) -> None:
        """Run real-time syntax validation and resolution."""
        
        session.phase = ResolutionPhase.REAL_TIME
        
        # Start syntax validation session
        self.syntax_validator.start_validation_session(session.context)
        
        # Validate different phases of the code
        phases_to_validate = [
            ValidationPhase.IMPORTS,
            ValidationPhase.COMPONENT_SIGNATURE,
            ValidationPhase.PROPS_INTERFACE,
            ValidationPhase.JSX_STRUCTURE,
            ValidationPhase.STYLING,
            ValidationPhase.EXPORT,
            ValidationPhase.COMPLETE
        ]
        
        total_errors = 0
        total_fixes = 0
        
        for phase in phases_to_validate:
            result = self.syntax_validator.validate_phase(phase, session.current_code)
            session.syntax_results[phase] = result
            
            total_errors += len(result.errors)
            total_fixes += len(result.auto_fixes)
            
            # Apply auto-fixes if available and strategy allows
            if result.corrected_code and result.corrected_code != session.current_code:
                if session.strategy in [ResolutionStrategy.AUTOMATIC, ResolutionStrategy.GUIDED]:
                    session.current_code = result.corrected_code
                    
                    action = ResolutionAction(
                        id=f"syntax_fix_{phase.value}",
                        description=f"Auto-fixed {len(result.auto_fixes)} issues in {phase.value}",
                        action_type="auto_fix",
                        confidence=0.85,
                        estimated_time=1,
                        preview=f"Applied: {', '.join(result.auto_fixes)}"
                    )
                    session.actions_taken.append(action)
                    session.errors_resolved += len(result.auto_fixes)
        
        session.errors_remaining = total_errors - total_fixes
        
        print(f"   📊 Syntax validation complete:")
        print(f"      Total errors found: {total_errors}")
        print(f"      Auto-fixes applied: {total_fixes}")
        print(f"      Errors remaining: {session.errors_remaining}")
    
    def _run_renderability_resolution(self, session: ResolutionSession) -> None:
        """Run comprehensive renderability validation and auto-fixing."""
        
        session.phase = ResolutionPhase.POST_GENERATION
        
        # Run renderability validation
        renderability_result = self.renderability_validator.validate_renderability(
            session.current_code,
            session.context.target_file
        )
        
        session.renderability_result = renderability_result
        
        print(f"   📊 Renderability validation:")
        print(f"      Is renderable: {renderability_result.is_renderable}")
        print(f"      Tests passed: {renderability_result.render_tests_passed}/{renderability_result.render_tests_total}")
        print(f"      Errors found: {len(renderability_result.errors)}")
        print(f"      Performance score: {renderability_result.performance_score:.1f}")
        
        # Apply auto-fixes if there are errors
        all_issues = renderability_result.errors + renderability_result.warnings
        if len(all_issues) > 0 and session.strategy in [
            ResolutionStrategy.AUTOMATIC, ResolutionStrategy.GUIDED
        ]:
            auto_fix_result = self.auto_fix_engine.auto_fix_code(
                session.current_code,
                all_issues,
                session.context.framework
            )
            
            if len(auto_fix_result.fixes_applied) > 0:
                session.current_code = auto_fix_result.fixed_code
                session.errors_resolved += len(auto_fix_result.fixes_applied)
                
                action = ResolutionAction(
                    id="renderability_autofix",
                    description=f"Auto-fixed {len(auto_fix_result.fixes_applied)} renderability issues",
                    action_type="auto_fix",
                    confidence=auto_fix_result.success_rate,
                    estimated_time=2,
                    preview=f"Applied {len(auto_fix_result.fixes_applied)} fixes"
                )
                session.actions_taken.append(action)
                
                print(f"   🔧 Applied {len(auto_fix_result.fixes_applied)} auto-fixes")
    
    def _run_interactive_refinement(self, session: ResolutionSession) -> None:
        """Run interactive refinement for remaining issues."""
        
        session.phase = ResolutionPhase.REFINEMENT
        
        print(f"   🎯 Interactive refinement for {session.errors_remaining} remaining issues")
        
        # Re-validate to get current issues
        current_result = self.renderability_validator.validate_renderability(
            session.current_code,
            session.context.target_file
        )
        
        # Generate explanations for remaining issues
        all_issues = current_result.errors + current_result.warnings
        for issue in all_issues[:3]:  # Limit to top 3 issues
            explanation_report = self.error_explainer.explain_errors(
                [issue],
                session.renderability_result,
                ExplanationLevel.DETAILED
            )
            
            explanation = explanation_report.explanations[0] if explanation_report.explanations else None
            
            print(f"\n   🔍 Remaining issue: {issue.message}")
            print(f"      Category: {issue.category}")
            if explanation:
                print(f"      Explanation: {explanation.description}")
                print(f"      Fix steps: {', '.join(explanation.fix_steps[:2])}")  # Show first 2 steps
            else:
                print(f"      No explanation available")
            
            # Create manual resolution action
            action = ResolutionAction(
                id=f"manual_fix_{issue.category}",
                description=f"Manual fix needed: {issue.message}",
                action_type="manual_fix",
                confidence=0.7,
                estimated_time=300,  # 5 minutes
                requires_user_input=True,
                preview=explanation.fix_steps[0] if explanation and explanation.fix_steps else "Manual review required"
            )
            session.actions_pending.append(action)
        
        # For guided strategy, present options to user
        if session.strategy == ResolutionStrategy.GUIDED:
            self._present_guided_actions(session, "refinement")
    
    def _execute_automatic_actions(self, session: ResolutionSession, action_type: str) -> None:
        """Execute all automatic actions of a given type."""
        
        actions_to_execute = [
            action for action in session.actions_pending 
            if action.action_type == action_type and not action.requires_user_input
        ]
        
        for action in actions_to_execute:
            print(f"   🔧 Executing: {action.description}")
            session.actions_taken.append(action)
            session.actions_pending.remove(action)
    
    def _present_guided_actions(self, session: ResolutionSession, context: str) -> None:
        """Present actions to user for guided resolution."""
        
        if not session.actions_pending:
            return
        
        print(f"\n   🎯 Guided resolution options for {context}:")
        
        for i, action in enumerate(session.actions_pending[:5], 1):  # Limit to 5 actions
            confidence_indicator = "🟢" if action.confidence >= 0.8 else "🟡" if action.confidence >= 0.6 else "🔴"
            time_indicator = f"{action.estimated_time}s" if action.estimated_time < 60 else f"{action.estimated_time//60}m"
            
            print(f"      {i}. {confidence_indicator} {action.description}")
            print(f"         Type: {action.action_type} | Time: {time_indicator} | Confidence: {action.confidence:.1%}")
            if action.preview:
                print(f"         Preview: {action.preview}")
        
        # In a real implementation, this would wait for user input
        # For now, we'll simulate automatic selection of high-confidence actions
        auto_actions = [
            action for action in session.actions_pending 
            if action.confidence >= 0.8 and not action.requires_user_input
        ]
        
        for action in auto_actions:
            print(f"   ✅ Auto-selecting high-confidence action: {action.description}")
            session.actions_taken.append(action)
            session.actions_pending.remove(action)
    
    def _generate_session_summary(self, session: ResolutionSession) -> Dict[str, Any]:
        """Generate comprehensive summary of resolution session."""
        
        duration = time.time() - session.start_time
        
        # Calculate final quality metrics
        final_renderability = None
        if session.renderability_result:
            # Re-validate with final code
            final_renderability = self.renderability_validator.validate_renderability(
                session.current_code,
                session.context.target_file
            )
        
        summary = {
            "session_id": session.session_id,
            "component_name": session.component_name,
            "success": True,
            "duration_seconds": round(duration, 2),
            
            # Code evolution
            "original_code": session.original_code,
            "final_code": session.current_code,
            "code_changed": session.current_code != session.original_code,
            
            # Resolution metrics
            "errors_resolved": session.errors_resolved,
            "errors_remaining": session.errors_remaining,
            "actions_taken": len(session.actions_taken),
            "actions_pending": len(session.actions_pending),
            
            # Quality metrics  
            "performance_score": final_renderability.performance_score if final_renderability else 0,
            "accessibility_score": final_renderability.accessibility_score if final_renderability else 0,
            "is_renderable": final_renderability.is_renderable if final_renderability else False,
            
            # Dependency status
            "dependencies_satisfied": session.dependency_result.all_satisfied if session.dependency_result else True,
            "install_commands": session.dependency_result.install_commands if session.dependency_result else [],
            
            # Phase results
            "phases_completed": len([phase for phase in ResolutionPhase if hasattr(session, f"{phase.value}_completed")]),
            "syntax_validation_passed": session.errors_remaining == 0,
            
            # Recommendations
            "recommendations": self._generate_recommendations(session),
            
            # Metadata
            "strategy_used": session.strategy.value,
            "framework": session.context.framework,
            "styling_system": session.context.styling_system,
            "typescript": session.context.typescript
        }
        
        return summary
    
    def _generate_recommendations(self, session: ResolutionSession) -> List[str]:
        """Generate recommendations based on session results."""
        
        recommendations = []
        
        # Dependency recommendations
        if session.dependency_result and not session.dependency_result.all_satisfied:
            recommendations.append("Install missing dependencies before using component")
        
        # Quality recommendations
        if session.renderability_result:
            if session.renderability_result.performance_score < 80:
                recommendations.append("Consider optimizing for better performance")
            
            if not session.renderability_result.is_renderable:
                recommendations.append("Manual review required - component may not render correctly")
        
        # Performance recommendations
        if len(session.actions_taken) > 10:
            recommendations.append("Many fixes were applied - consider reviewing generated patterns")
        
        # Framework-specific recommendations
        if session.context.framework == "nextjs" and session.errors_remaining > 0:
            recommendations.append("Review Next.js specific requirements (use client directive, Image component)")
        
        return recommendations
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a resolution session."""
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "component_name": session.component_name,
            "phase": session.phase.value,
            "strategy": session.strategy.value,
            "errors_resolved": session.errors_resolved,
            "errors_remaining": session.errors_remaining,
            "actions_taken": len(session.actions_taken),
            "actions_pending": len(session.actions_pending),
            "duration": time.time() - session.start_time
        }
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up a completed session."""
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]