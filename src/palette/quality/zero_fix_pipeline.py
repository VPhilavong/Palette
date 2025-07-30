"""
Zero-Fix Validation Pipeline.
Combines OpenAI, MCP, and real project validation for guaranteed perfect components.
"""

import asyncio
import json
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..openai_integration.assistant import PaletteAssistant
from ..openai_integration.structured_output import StructuredOutputGenerator, GeneratedComponent, ValidationResult
from ..openai_integration.function_calling import FunctionCallingSystem
from ..mcp.client import MCPClient
from .validator import ComponentValidator, QualityReport


@dataclass
class ZeroFixResult:
    """Result of the zero-fix pipeline."""
    final_code: str
    iterations: int
    original_issues: int
    final_issues: int
    confidence_score: float
    validation_reports: List[Dict[str, Any]]
    mcp_validations: List[Dict[str, Any]]
    openai_fixes: List[str]
    success: bool
    error: Optional[str] = None


class ZeroFixPipeline:
    """Multi-stage validation and auto-fixing pipeline for perfect components."""
    
    def __init__(
        self,
        openai_assistant: Optional[PaletteAssistant] = None,
        mcp_client: Optional[MCPClient] = None,
        project_path: Optional[str] = None
    ):
        self.openai_assistant = openai_assistant or PaletteAssistant()
        self.mcp_client = mcp_client
        self.project_path = Path(project_path) if project_path else Path.cwd()
        
        # Initialize supporting systems
        self.structured_generator = StructuredOutputGenerator()
        self.function_caller = FunctionCallingSystem(str(self.project_path))
        self.traditional_validator = ComponentValidator(str(self.project_path))
        
        # Pipeline configuration
        self.max_iterations = 5
        self.confidence_threshold = 0.95
        self.enable_mcp_validation = True
        self.enable_real_project_tests = True
    
    async def process(
        self,
        component_code: str,
        context: Dict[str, Any],
        target_path: Optional[str] = None
    ) -> ZeroFixResult:
        """
        Main pipeline process for achieving zero manual fixes.
        
        Stages:
        1. OpenAI Code Interpreter validation
        2. Structured output regeneration if needed
        3. MCP design system compliance
        4. Real project validation (TypeScript, linting, tests)
        5. AI-powered final polish
        """
        
        validation_reports = []
        mcp_validations = []
        openai_fixes = []
        current_code = component_code
        iteration = 0
        
        try:
            print("🚀 Starting Zero-Fix Pipeline...")
            self._print_progress_header()
            
            # Stage 1: Initial OpenAI validation
            self._print_stage_progress(1, "OpenAI Code Interpreter validation")
            initial_validation = await self.openai_assistant.validate_with_interpreter(current_code)
            validation_reports.append({"stage": "openai_initial", "result": initial_validation})
            
            original_issues = len(initial_validation.get("errors", []))
            print(f"   Found {original_issues} initial issues")
            
            # Stage 2: Iterative fixing with structured outputs
            self._print_stage_progress(2, "Structured Output Auto-Fixing")
            while iteration < self.max_iterations:
                iteration += 1
                self._print_iteration_progress(iteration, self.max_iterations)
                
                # Check if we need to fix issues
                has_errors = initial_validation.get("has_errors", False) if iteration == 1 else validation_result.get("has_errors", False)
                
                if not has_errors:
                    print("   ✅ No errors found, proceeding to next stage")
                    break
                
                # Use structured output to fix issues
                print("   🛠️ Applying structured fixes...")
                fixed_code, fix_metadata = await self._fix_with_structured_output(
                    current_code,
                    validation_reports[-1]["result"],
                    context
                )
                
                if fixed_code != current_code:
                    current_code = fixed_code
                    openai_fixes.append(f"Iteration {iteration}: {fix_metadata}")
                    
                    # Validate the fixed code
                    validation_result = await self.openai_assistant.validate_with_interpreter(current_code)
                    validation_reports.append({"stage": f"openai_iteration_{iteration}", "result": validation_result})
                    
                    remaining_errors = len(validation_result.get("errors", []))
                    print(f"   📉 Reduced errors to {remaining_errors}")
                    
                    if remaining_errors == 0:
                        break
                else:
                    print("   ⚠️ No changes made, trying alternative approach")
                    break
            
            # Stage 3: MCP Design System Compliance
            if self.enable_mcp_validation and self.mcp_client:
                self._print_stage_progress(3, "MCP Design System Compliance")
                mcp_result = await self._validate_with_mcp(current_code, context)
                mcp_validations.append(mcp_result)
                
                if not mcp_result.get("compliant", True):
                    print("   🔧 Applying MCP-suggested fixes...")
                    current_code = await self._apply_mcp_fixes(current_code, mcp_result, context)
                    
                    # Re-validate with MCP
                    mcp_revalidation = await self._validate_with_mcp(current_code, context)
                    mcp_validations.append(mcp_revalidation)
            
            # Stage 4: Real Project Validation
            if self.enable_real_project_tests:
                self._print_stage_progress(4, "Real Project Validation")
                real_validation = await self._validate_in_real_project(current_code, target_path or "Component.tsx")
                validation_reports.append({"stage": "real_project", "result": real_validation})
                
                if not real_validation.get("success", False):
                    print("   🛠️ Fixing real project issues...")
                    current_code = await self._fix_real_project_issues(current_code, real_validation, context)
                    
                    # Re-validate
                    final_real_validation = await self._validate_in_real_project(current_code, target_path or "Component.tsx")
                    validation_reports.append({"stage": "real_project_final", "result": final_real_validation})
            
            # Stage 5: Final AI Polish
            self._print_stage_progress(5, "Final AI Polish")
            final_code = await self._apply_final_polish(current_code, validation_reports, mcp_validations, context)
            
            # Final validation
            final_validation = await self.openai_assistant.validate_with_interpreter(final_code)
            validation_reports.append({"stage": "final", "result": final_validation})
            
            final_issues = len(final_validation.get("errors", []))
            confidence_score = self._calculate_confidence_score(validation_reports, mcp_validations)
            
            success = final_issues == 0 and confidence_score >= self.confidence_threshold
            
            self._print_completion_summary(original_issues, final_issues, confidence_score, success)
            
            return ZeroFixResult(
                final_code=final_code,
                iterations=iteration,
                original_issues=original_issues,
                final_issues=final_issues,
                confidence_score=confidence_score,
                validation_reports=validation_reports,
                mcp_validations=mcp_validations,
                openai_fixes=openai_fixes,
                success=success
            )
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return ZeroFixResult(
                final_code=current_code,
                iterations=iteration,
                original_issues=original_issues if 'original_issues' in locals() else 0,
                final_issues=999,  # Error state
                confidence_score=0.0,
                validation_reports=validation_reports,
                mcp_validations=mcp_validations,
                openai_fixes=openai_fixes,
                success=False,
                error=str(e)
            )
    
    async def _fix_with_structured_output(
        self,
        code: str,
        validation_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[str, str]:
        """Fix code using structured output generation."""
        
        # Build a fix prompt from the validation result
        errors = validation_result.get("errors", [])
        warnings = validation_result.get("warnings", [])
        
        fix_prompt = f"""
        Fix the following issues in this React component:
        
        ERRORS:
        {json.dumps(errors, indent=2)}
        
        WARNINGS:
        {json.dumps(warnings, indent=2)}
        
        Original component:
        ```typescript
        {code}
        ```
        
        Generate a corrected version that addresses all issues while maintaining functionality.
        """
        
        # Use structured output to ensure valid result
        try:
            fixed_component = self.structured_generator.generate_component(
                fix_prompt,
                context
            )
            
            return fixed_component.component_code, f"Fixed {len(errors)} errors, {len(warnings)} warnings"
        except Exception as e:
            print(f"   ⚠️ Structured fix failed: {e}")
            return code, f"Fix failed: {str(e)}"
    
    async def _validate_with_mcp(
        self,
        code: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate component using MCP design system server."""
        
        if not self.mcp_client:
            return {"error": "MCP client not available"}
        
        try:
            # Call MCP design system validation
            result = await self.mcp_client.call_tool(
                "design-system",
                "validate_component_compliance",
                {
                    "component_code": code,
                    "rules": ["color_usage", "spacing_consistency", "typography_scale", "accessibility_basics"]
                }
            )
            
            if result.get("success"):
                return result["result"]
            else:
                return {"error": result.get("error", "MCP validation failed")}
                
        except Exception as e:
            return {"error": f"MCP validation error: {str(e)}"}
    
    async def _apply_mcp_fixes(
        self,
        code: str,
        mcp_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Apply fixes suggested by MCP validation."""
        
        issues = mcp_result.get("issues", [])
        suggestions = mcp_result.get("suggestions", [])
        
        if not issues and not suggestions:
            return code
        
        # Build fix prompt from MCP feedback
        fix_prompt = f"""
        Apply these design system compliance fixes to the component:
        
        Issues found:
        {json.dumps(issues, indent=2)}
        
        Suggestions:
        {json.dumps(suggestions, indent=2)}
        
        Component code:
        ```typescript
        {code}
        ```
        
        Return the component with design system compliance fixes applied.
        """
        
        try:
            # Use OpenAI to apply the fixes
            response = await self.openai_assistant.generate_component_async(
                fix_prompt,
                context
            )
            
            return response[0] if response else code
        except Exception as e:
            print(f"   ⚠️ Failed to apply MCP fixes: {e}")
            return code
    
    async def _validate_in_real_project(
        self,
        code: str,
        file_name: str
    ) -> Dict[str, Any]:
        """Validate component in the actual project environment."""
        
        validation_results = {
            "typescript": None,
            "eslint": None,
            "imports": None,
            "overall_success": False
        }
        
        try:
            # TypeScript validation
            ts_result = await self.function_caller.execute_function(
                "validate_typescript",
                {"code": code, "file_name": file_name}
            )
            validation_results["typescript"] = ts_result
            
            # ESLint validation
            eslint_result = await self.function_caller.execute_function(
                "run_linter",
                {"code": code, "file_name": file_name, "fix": True}
            )
            validation_results["eslint"] = eslint_result
            
            # Import validation (check if all imports are available)
            import_issues = await self._validate_imports(code)
            validation_results["imports"] = import_issues
            
            # Determine overall success
            ts_valid = ts_result.get("success") and ts_result.get("result", {}).get("valid", False)
            eslint_success = eslint_result.get("success") and eslint_result.get("result", {}).get("success", False)
            imports_valid = len(import_issues) == 0
            
            validation_results["overall_success"] = ts_valid and eslint_success and imports_valid
            
            return validation_results
            
        except Exception as e:
            validation_results["error"] = str(e)
            return validation_results
    
    async def _validate_imports(self, code: str) -> List[Dict[str, Any]]:
        """Validate all imports in the component."""
        
        import re
        
        # Extract all import statements
        import_pattern = r'import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, code)
        
        import_issues = []
        
        for import_path in imports:
            # Check if import is available
            result = await self.function_caller.execute_function(
                "check_import_availability",
                {"import_path": import_path}
            )
            
            if result.get("success"):
                availability = result["result"]
                if not availability.get("available", False):
                    import_issues.append({
                        "import": import_path,
                        "issue": "Import not available",
                        "suggestion": availability.get("suggestion")
                    })
        
        return import_issues
    
    async def _fix_real_project_issues(
        self,
        code: str,
        validation_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Fix real project validation issues."""
        
        issues = []
        
        # Collect all issues
        if validation_result.get("typescript", {}).get("result", {}).get("errors"):
            issues.extend(validation_result["typescript"]["result"]["errors"])
        
        if validation_result.get("eslint", {}).get("result", {}).get("issues"):
            issues.extend(validation_result["eslint"]["result"]["issues"])
        
        if validation_result.get("imports"):
            issues.extend(validation_result["imports"])
        
        if not issues:
            return code
        
        # Build comprehensive fix prompt
        fix_prompt = f"""
        Fix these real project validation issues:
        
        TypeScript Errors:
        {json.dumps(validation_result.get("typescript", {}).get("result", {}).get("errors", []), indent=2)}
        
        ESLint Issues:
        {json.dumps(validation_result.get("eslint", {}).get("result", {}).get("issues", []), indent=2)}
        
        Import Issues:
        {json.dumps(validation_result.get("imports", []), indent=2)}
        
        Component code to fix:
        ```typescript
        {code}
        ```
        
        Return the component with all validation issues resolved.
        The component must compile with TypeScript, pass ESLint, and have valid imports.
        """
        
        try:
            response = await self.openai_assistant.generate_component_async(
                fix_prompt,
                context
            )
            
            return response[0] if response else code
        except Exception as e:
            print(f"   ⚠️ Failed to fix real project issues: {e}")
            return code
    
    async def _apply_final_polish(
        self,
        code: str,
        validation_reports: List[Dict[str, Any]],
        mcp_validations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Apply final AI polish based on all validation feedback."""
        
        # Summarize all feedback
        feedback_summary = {
            "validation_stages": len(validation_reports),
            "mcp_checks": len(mcp_validations),
            "remaining_issues": []
        }
        
        # Collect any remaining issues
        for report in validation_reports:
            result = report.get("result", {})
            if result.get("errors"):
                feedback_summary["remaining_issues"].extend(result["errors"])
        
        for mcp_validation in mcp_validations:
            if mcp_validation.get("issues"):
                feedback_summary["remaining_issues"].extend(mcp_validation["issues"])
        
        # Only apply polish if there are minor issues or improvements
        if not feedback_summary["remaining_issues"]:
            polish_prompt = f"""
            Apply final polish to this React component for production readiness:
            
            ```typescript
            {code}
            ```
            
            Ensure:
            - Code is properly formatted and readable
            - Comments are helpful but not excessive
            - Performance optimizations are applied where beneficial
            - All edge cases are handled
            - Component follows React best practices
            
            Return the polished component.
            """
        else:
            polish_prompt = f"""
            Apply final fixes and polish to this React component:
            
            Remaining issues to address:
            {json.dumps(feedback_summary["remaining_issues"], indent=2)}
            
            ```typescript
            {code}
            ```
            
            Fix all remaining issues and apply production-ready polish.
            """
        
        try:
            response = await self.openai_assistant.generate_component_async(
                polish_prompt,
                context
            )
            
            return response[0] if response else code
        except Exception as e:
            print(f"   ⚠️ Final polish failed: {e}")
            return code
    
    def _calculate_confidence_score(
        self,
        validation_reports: List[Dict[str, Any]],
        mcp_validations: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score based on final validation state only."""
        
        score = 1.0
        
        # Only consider the FINAL validation report
        final_report = next(
            (r for r in reversed(validation_reports) if r.get("stage") == "final"),
            validation_reports[-1] if validation_reports else None
        )
        
        if final_report:
            result = final_report.get("result", {})
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])
            
            # Heavy penalty for errors in final state
            score -= len(errors) * 0.15
            # Light penalty for warnings in final state
            score -= len(warnings) * 0.03
        
        # Bonus for successful fixing (if we started with errors and ended with none)
        if validation_reports:
            initial_report = validation_reports[0]
            initial_errors = len(initial_report.get("result", {}).get("errors", []))
            final_errors = len(final_report.get("result", {}).get("errors", [])) if final_report else 0
            
            if initial_errors > 0 and final_errors == 0:
                # Bonus for successfully fixing all errors
                score += 0.15
        
        # Penalize for MCP compliance issues (if available)
        for mcp_validation in mcp_validations:
            issues = mcp_validation.get("issues", [])
            score -= len(issues) * 0.05
        
        # Bonus for passing real project validation
        real_validation = next(
            (r for r in validation_reports if r.get("stage") in ["real_project_final", "real_project"]),
            None
        )
        
        if real_validation and real_validation.get("result", {}).get("overall_success"):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    async def batch_process(
        self,
        components: List[Tuple[str, Dict[str, Any]]],
        progress_callback: Optional[callable] = None
    ) -> List[ZeroFixResult]:
        """Process multiple components through the zero-fix pipeline."""
        
        results = []
        
        for i, (code, context) in enumerate(components):
            if progress_callback:
                progress_callback(i, len(components))
            
            result = await self.process(code, context)
            results.append(result)
        
        return results
    
    def _print_progress_header(self):
        """Print the pipeline progress header."""
        print("\n" + "="*60)
        print("🚀 ZERO-FIX VALIDATION PIPELINE")
        print("="*60)
        print("📋 Pipeline Stages:")
        print("   1️⃣ OpenAI Code Interpreter validation")
        print("   2️⃣ Structured Output Auto-Fixing")
        print("   3️⃣ MCP Design System Compliance")
        print("   4️⃣ Real Project Validation")
        print("   5️⃣ Final AI Polish")
        print("="*60)
    
    def _print_stage_progress(self, stage: int, description: str):
        """Print progress for a specific stage."""
        stage_emoji = ["", "📊", "🛠️", "🎨", "🔍", "✨"]
        print(f"\n{stage_emoji[stage]} Stage {stage}/5: {description}")
        print("-" * 50)
    
    def _print_iteration_progress(self, iteration: int, max_iterations: int):
        """Print progress for iterations within a stage."""
        progress_bar = "█" * iteration + "░" * (max_iterations - iteration)
        print(f"   🔄 Iteration {iteration}/{max_iterations} [{progress_bar}]")
    
    def _print_completion_summary(self, original_issues: int, final_issues: int, confidence_score: float, success: bool):
        """Print the final completion summary."""
        print("\n" + "="*60)
        print("🎯 PIPELINE COMPLETE!")
        print("="*60)
        
        # Issues reduction
        issues_fixed = original_issues - final_issues
        if original_issues > 0:
            reduction_percent = (issues_fixed / original_issues) * 100
            print(f"📉 Issues: {original_issues} → {final_issues} (-{issues_fixed}, {reduction_percent:.1f}% reduction)")
        else:
            print(f"📉 Issues: {original_issues} → {final_issues}")
        
        # Confidence score with visual indicator
        confidence_bar = "█" * int(confidence_score * 20) + "░" * (20 - int(confidence_score * 20))
        print(f"📊 Confidence: {confidence_score:.2%} [{confidence_bar}]")
        
        # Success indicator
        if success:
            print("✅ Status: SUCCESS - Component ready for production!")
        else:
            print("❌ Status: ISSUES REMAIN - Review may be needed")
        
        print("="*60)
    
    def get_pipeline_stats(self, results: List[ZeroFixResult]) -> Dict[str, Any]:
        """Get statistics from pipeline results."""
        
        if not results:
            return {"error": "No results to analyze"}
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        return {
            "total_processed": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results),
            "average_iterations": sum(r.iterations for r in results) / len(results),
            "average_confidence": sum(r.confidence_score for r in successful) / len(successful) if successful else 0,
            "total_issues_fixed": sum(r.original_issues - r.final_issues for r in results),
            "zero_issue_components": len([r for r in results if r.final_issues == 0])
        }