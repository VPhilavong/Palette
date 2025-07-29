import os
import subprocess
import tempfile
from typing import Dict, Optional, Tuple

import anthropic
from openai import OpenAI

from .prompts import UIUXCopilotPromptBuilder
from .enhanced_prompts import EnhancedPromptBuilder
from ..quality import ComponentValidator, QualityReport
from ..analysis.project_structure import ProjectStructureDetector
from ..quality.zero_fix_pipeline import ZeroFixPipeline
from ..mcp.registry import MCPServerRegistry


class UIGenerator:
    """Core UI generation logic using LLM APIs"""

    def __init__(self, model: str = None, project_path: str = None, enhanced_mode: bool = True, quality_assurance: bool = True):
        # Use environment variable or provided model or fallback
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.project_path = project_path
        self.quality_assurance = quality_assurance
        
        # Initialize prompt builder (enhanced or basic)
        if enhanced_mode and project_path:
            try:
                self.prompt_builder = EnhancedPromptBuilder()
                self.prompt_builder.initialize_project_analysis(project_path)
                print("✅ Enhanced prompt engineering enabled with project analysis")
            except Exception as e:
                print(f"⚠️ Enhanced mode failed, falling back to basic: {e}")
                self.prompt_builder = UIUXCopilotPromptBuilder()
        else:
            self.prompt_builder = UIUXCopilotPromptBuilder()

        # Initialize quality validator
        if quality_assurance and project_path:
            try:
                self.validator = ComponentValidator(project_path)
                print("✅ Quality assurance enabled")
            except Exception as e:
                print(f"⚠️ QA initialization failed: {e}")
                self.validator = None
        else:
            self.validator = None

        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize project context
        self._project_context = None
        if project_path:
            self._analyze_project(project_path)
            # Auto-discover MCP servers based on project configuration
            self._auto_discover_mcp_servers(project_path)

        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

    def generate_component(self, prompt: str, context: Dict) -> str:
        """Generate a React component from a prompt and project context"""

        # Build prompts using enhanced or basic builder
        if isinstance(self.prompt_builder, EnhancedPromptBuilder):
            # Use enhanced prompts with few-shot learning and RAG
            system_prompt = self.prompt_builder.build_enhanced_system_prompt(context, prompt)
            user_prompt = self.prompt_builder.build_rag_enhanced_user_prompt(prompt, context)
        else:
            # Use basic prompts
            system_prompt = self.prompt_builder.build_ui_system_prompt(context)
            user_prompt = self.prompt_builder.build_user_prompt(prompt, context)

        # Choose API based on model
        if self.model.startswith("gpt"):
            return self._generate_with_openai(system_prompt, user_prompt)
        elif self.model.startswith("claude"):
            return self._generate_with_anthropic(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def generate_component_with_qa(self, prompt: str, context: Dict, target_path: str = None) -> Tuple[str, QualityReport]:
        """Generate component with comprehensive quality assurance and traditional validation."""
        print("🎨 Generating component with traditional quality assurance...")
        
        # Step 1: Generate initial component
        component_code = self.generate_component(prompt, context)
        
        # Clean the response first
        component_code = self.clean_response(component_code)
        
        # Step 2: If QA is disabled, return without validation
        if not self.validator:
            print("⚠️ Quality assurance disabled, skipping validation")
            # Create dummy report
            from ..quality.validator import QualityReport, ValidationLevel
            dummy_report = QualityReport(
                score=75.0, issues=[], passed_checks=["Generation"],
                failed_checks=[], auto_fixes_applied=[],
                compilation_success=True, rendering_success=True,
                accessibility_score=75.0, performance_score=75.0
            )
            return component_code, dummy_report
        
        # Step 3: Use traditional validation (Zero-Fix Pipeline temporarily disabled)
        # TODO: Re-enable Zero-Fix Pipeline after fixing async event loop issues
        print("🔄 Using traditional quality assurance...")
        
        # Skip Zero-Fix Pipeline to avoid async issues
        # try:
        #     import asyncio
        #     
        #     # Initialize Zero-Fix Pipeline with auto-discovered MCP servers
        #     from ..mcp.client import MCPClient
        #     mcp_client = None
            
        #     # Use auto-discovered MCP servers if available
        #     if hasattr(self, '_mcp_discovery') and self._mcp_discovery.get('enabled'):
        #         try:
        #             mcp_registry = MCPServerRegistry()
        #             enabled_servers = mcp_registry.get_enabled_servers()
        #             if enabled_servers:
        #                 mcp_client = MCPClient(servers=enabled_servers)
        #                 print(f"🎯 Zero-Fix Pipeline using {len(enabled_servers)} MCP servers")
        #         except Exception as e:
        #             print(f"⚠️ MCP client initialization failed: {e}")
        #     
        #     zero_fix_pipeline = ZeroFixPipeline(
        #         project_path=self.project_path,
        #         mcp_client=mcp_client
        #     )
        #     
        #     # Run the pipeline
        #     pipeline_result = asyncio.run(zero_fix_pipeline.process(
        #         component_code, 
        #         context, 
        #         target_path or "Component.tsx"
        #     ))
        #     
        #     # Convert ZeroFixResult to QualityReport format
        #     quality_report = self._convert_zero_fix_to_quality_report(pipeline_result)
        #     
        #     # Display pipeline summary
        #     self._display_zero_fix_summary(pipeline_result)
        #     
        #     # Use the pipeline result as the final code
        #     final_code = pipeline_result.final_code
        #     
        #     # Step 4: Final formatting (after all fixes)
        #     print("🎨 Final formatting pass...")
        #     formatted_code = self.format_and_lint_code(final_code, self.project_path or os.getcwd())
        #     
        #     return formatted_code, quality_report
        #     
        # except Exception as e:
        #     print(f"⚠️ Zero-Fix Pipeline failed, fallingback to traditional QA: {e}")
        #     
        # Traditional validation
        target_file = target_path or "Component.tsx"
        refined_code, quality_report = self.validator.iterative_refinement(
            component_code, target_file, max_iterations=3
        )
        
        # Display quality summary
        self._display_quality_summary(quality_report)
        
        # Final formatting
        print("🎨 Final formatting pass...")
        formatted_code = self.format_and_lint_code(refined_code, self.project_path or os.getcwd())
        
        return formatted_code, quality_report
    
    def _convert_zero_fix_to_quality_report(self, zero_fix_result):
        """Convert ZeroFixResult to QualityReport format for compatibility."""
        from ..quality.validator import QualityReport, ValidationLevel
        
        # Calculate overall score based on success and confidence
        if zero_fix_result.success:
            overall_score = zero_fix_result.confidence_score * 100
        else:
            overall_score = max(0, (1 - zero_fix_result.final_issues / max(1, zero_fix_result.original_issues)) * 50)
        
        # Convert pipeline fixes to auto_fixes_applied format
        auto_fixes = zero_fix_result.openai_fixes + [
            f"Pipeline Stage {i+1}" for i in range(len(zero_fix_result.validation_reports))
        ]
        
        return QualityReport(
            score=overall_score,
            issues=[],  # Zero-fix pipeline handles issues internally
            passed_checks=["Zero-Fix Pipeline"] if zero_fix_result.success else [],
            failed_checks=[] if zero_fix_result.success else ["Zero-Fix Pipeline"],
            auto_fixes_applied=auto_fixes,
            compilation_success=zero_fix_result.final_issues == 0,
            rendering_success=zero_fix_result.success,
            accessibility_score=zero_fix_result.confidence_score * 100,
            performance_score=zero_fix_result.confidence_score * 100
        )
    
    def _display_zero_fix_summary(self, pipeline_result):
        """Display Zero-Fix Pipeline summary."""
        print(f"\n🚀 Zero-Fix Pipeline Results:")
        print(f"Status: {'✅ SUCCESS' if pipeline_result.success else '❌ FAILED'}")
        print(f"Iterations: {pipeline_result.iterations}")
        print(f"Original Issues: {pipeline_result.original_issues}")
        print(f"Final Issues: {pipeline_result.final_issues}")
        print(f"Confidence Score: {pipeline_result.confidence_score:.2%}")
        
        if pipeline_result.openai_fixes:
            print(f"\n🔧 AI Fixes Applied: {len(pipeline_result.openai_fixes)}")
            for i, fix in enumerate(pipeline_result.openai_fixes[:3]):  # Show first 3
                print(f"  {i+1}. {fix}")
            if len(pipeline_result.openai_fixes) > 3:
                print(f"  ... and {len(pipeline_result.openai_fixes) - 3} more fixes")
        
        if pipeline_result.mcp_validations:
            print(f"\n🎨 MCP Validations: {len(pipeline_result.mcp_validations)}")
            
        if pipeline_result.validation_reports:
            print(f"📊 Validation Stages: {len(pipeline_result.validation_reports)}")
        
        if pipeline_result.error:
            print(f"❌ Error: {pipeline_result.error}")

    def _display_quality_summary(self, report: QualityReport):
        """Display quality assurance summary."""
        print(f"\n📊 Quality Report:")
        print(f"Overall Score: {report.score:.1f}/100")
        
        if report.compilation_success:
            print("✅ TypeScript compilation: PASSED")
        else:
            print("❌ TypeScript compilation: FAILED")
        
        if report.rendering_success:
            print("✅ Component rendering: PASSED") 
        else:
            print("❌ Component rendering: FAILED")
        
        print(f"🛡️ Accessibility: {report.accessibility_score:.1f}/100")
        print(f"⚡ Performance: {report.performance_score:.1f}/100")
        
        if report.issues:
            print(f"\n⚠️ Issues Found: {len(report.issues)}")
            for issue in report.issues[:5]:  # Show first 5 issues
                level_emoji = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
                emoji = level_emoji.get(issue.level.value, "•")
                print(f"  {emoji} {issue.category}: {issue.message}")
            
            if len(report.issues) > 5:
                print(f"  ... and {len(report.issues) - 5} more issues")
        
        if report.auto_fixes_applied:
            print(f"\n🔧 Auto-fixes Applied: {len(report.auto_fixes_applied)}")
            for fix in report.auto_fixes_applied:
                print(f"  ✅ {fix}")

    def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Generate component using OpenAI API"""

        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=2000,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _generate_with_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Generate component using Anthropic API"""

        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")

        try:
            response = self.anthropic_client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            return response.content[0].text.strip()

        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    def clean_response(self, response: str) -> str:
        """Clean and extract code from LLM response"""

        # Remove markdown code blocks if present
        if "```" in response:
            # Find all code blocks
            parts = response.split("```")
            if len(parts) >= 3:
                # Take the content of the first code block (index 1)
                code_content = parts[1]
                
                # Remove language specifier from first line if present
                lines = code_content.split('\n')
                if lines and lines[0].strip() in ['tsx', 'typescript', 'javascript', 'jsx', 'ts', 'js']:
                    lines = lines[1:]
                
                response = '\n'.join(lines).strip()
        
        # Additional cleanup - remove any remaining markdown artifacts
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            # Skip lines that are pure markdown artifacts
            stripped = line.strip()
            if stripped in ['```tsx', '```typescript', '```javascript', '```jsx', '```ts', '```js', '```']:
                continue
            cleaned_lines.append(line)
        
        response = '\n'.join(cleaned_lines)
        return response.strip()

    def validate_component(self, code: str) -> bool:
        """Basic validation of generated component code"""

        # Check for basic React component structure
        required_patterns = [
            "export",  # Should export the component
            "return",  # Should have a return statement
            "<",  # Should contain JSX
        ]

        for pattern in required_patterns:
            if pattern not in code:
                return False

        # Check for common syntax issues
        if code.count("(") != code.count(")"):
            return False

        if code.count("{") != code.count("}"):
            return False

        return True

    def format_and_lint_code(self, code: str, project_path: str = None) -> str:
        """Format and lint generated code using Prettier and ESLint"""

        # Clean the code first
        cleaned_code = self.clean_response(code)

        # Try to format with Prettier
        formatted_code = self._format_with_prettier(cleaned_code, project_path)

        # Try to lint with ESLint if available
        linted_code = self._lint_with_eslint(formatted_code, project_path)

        return linted_code

    def _format_with_prettier(self, code: str, project_path: str = None) -> str:
        """Format code using project's own Prettier if available"""

        if not project_path:
            return code

        try:
            # Check if Prettier is available in the project
            if not self._is_prettier_available(project_path):
                print("Info: Prettier not found in project, skipping formatting")
                return code

            # Write code to a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".tsx", delete=False
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            # Try to run Prettier using the project's own installation
            prettier_config = self._find_prettier_config(project_path)
            prettier_cmd = ["npx", "prettier", "--write", temp_file_path]

            # Add config file if found
            if prettier_config:
                prettier_cmd.extend(["--config", prettier_config])
            else:
                # Use default options for TypeScript/React
                prettier_cmd.extend(
                    [
                        "--parser",
                        "typescript",
                        "--single-quote",
                        "--trailing-comma",
                        "es5",
                        "--tab-width",
                        "2",
                        "--semi",
                    ]
                )

            # Run Prettier in the project directory to use project's dependencies
            result = subprocess.run(
                prettier_cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=project_path,
            )

            if result.returncode == 0:
                # Read the formatted code
                with open(temp_file_path, "r") as f:
                    formatted_code = f.read()

                # Clean up temp file
                os.unlink(temp_file_path)

                return formatted_code
            else:
                # Prettier failed, clean up and return original
                os.unlink(temp_file_path)
                print(f"Info: Prettier formatting skipped: {result.stderr}")
                return code

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # Clean up temp file if it exists
            if "temp_file_path" in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

            if isinstance(e, FileNotFoundError):
                print("Info: Prettier not available, skipping formatting")
            else:
                print(f"Info: Prettier formatting skipped: {e}")

            return code

    def _lint_with_eslint(self, code: str, project_path: str = None) -> str:
        """Lint code using project's own ESLint if available"""

        if not project_path:
            return code

        try:
            # Check if ESLint is available in the project
            if not self._is_eslint_available(project_path):
                print("Info: ESLint not found in project, skipping linting")
                return code

            # Write code to a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".tsx", delete=False
            ) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            # Try to run ESLint with auto-fix using project's own installation
            eslint_config = self._find_eslint_config(project_path)
            eslint_cmd = ["npx", "eslint", "--fix", temp_file_path]

            # Add config file if found
            if eslint_config:
                eslint_cmd.extend(["--config", eslint_config])

            # Run ESLint in the project directory
            result = subprocess.run(
                eslint_cmd, capture_output=True, text=True, timeout=10, cwd=project_path
            )

            # ESLint returns 0 for no issues, 1 for warnings/errors
            # We only proceed if it's 0 (no issues) or 1 (fixed issues)
            if result.returncode in [0, 1]:
                # Read the potentially fixed code
                with open(temp_file_path, "r") as f:
                    linted_code = f.read()

                # Clean up temp file
                os.unlink(temp_file_path)

                return linted_code
            else:
                # ESLint failed, clean up and return original
                os.unlink(temp_file_path)
                print(f"Info: ESLint linting skipped: {result.stderr}")
                return code

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # Clean up temp file if it exists
            if "temp_file_path" in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

            if isinstance(e, FileNotFoundError):
                print("Info: ESLint not available, skipping linting")
            else:
                print(f"Info: ESLint linting skipped: {e}")

            return code

    def _find_prettier_config(self, project_path: str = None) -> Optional[str]:
        """Find Prettier configuration file"""

        if not project_path:
            return None

        config_files = [
            ".prettierrc",
            ".prettierrc.json",
            ".prettierrc.js",
            "prettier.config.js",
            ".prettierrc.yaml",
            ".prettierrc.yml",
        ]

        for config_file in config_files:
            config_path = os.path.join(project_path, config_file)
            if os.path.exists(config_path):
                return config_path

        return None

    def _find_eslint_config(self, project_path: str = None) -> Optional[str]:
        """Find ESLint configuration file"""

        if not project_path:
            return None

        config_files = [
            ".eslintrc",
            ".eslintrc.json",
            ".eslintrc.js",
            ".eslintrc.yaml",
            ".eslintrc.yml",
            "eslint.config.js",
        ]

        for config_file in config_files:
            config_path = os.path.join(project_path, config_file)
            if os.path.exists(config_path):
                return config_path

        return None

    def _is_prettier_available(self, project_path: str) -> bool:
        """Check if Prettier is available in the project"""

        package_json_path = os.path.join(project_path, "package.json")
        if not os.path.exists(package_json_path):
            return False

        try:
            with open(package_json_path, "r") as f:
                import json

                package_data = json.load(f)
                dependencies = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

                # Check if prettier is in dependencies
                return "prettier" in dependencies
        except (json.JSONDecodeError, Exception):
            return False

    def _is_eslint_available(self, project_path: str) -> bool:
        """Check if ESLint is available in the project"""

        package_json_path = os.path.join(project_path, "package.json")
        if not os.path.exists(package_json_path):
            return False

        try:
            with open(package_json_path, "r") as f:
                import json

                package_data = json.load(f)
                dependencies = {
                    **package_data.get("dependencies", {}),
                    **package_data.get("devDependencies", {}),
                }

                # Check if eslint is in dependencies
                return "eslint" in dependencies
        except (json.JSONDecodeError, Exception):
            return False
    
    @property
    def project_context(self) -> Dict:
        """Get project analysis context."""
        return self._project_context or {}
    
    def _analyze_project(self, project_path: str):
        """Analyze project structure and patterns."""
        from ..analysis.context import ProjectAnalyzer
        
        try:
            analyzer = ProjectAnalyzer()
            self._project_context = analyzer.analyze_project(project_path)
        except Exception as e:
            print(f"⚠️ Project analysis failed: {e}")
            # Use intelligent fallback with basic framework detection
            fallback_framework = self._detect_framework_fallback(project_path)
            self._project_context = {
                'framework': fallback_framework,
                'styling': 'tailwind',
                'component_library': 'none',
                'typescript': True,
                'project_path': project_path
            }
    
    def _detect_framework_fallback(self, project_path: str) -> str:
        """Basic framework detection for fallback scenarios."""
        import json
        import os
        
        # Check for Next.js first
        next_config_files = ['next.config.js', 'next.config.ts', 'next.config.mjs']
        if any(os.path.exists(os.path.join(project_path, config)) for config in next_config_files):
            return 'next.js'
        
        # Check package.json for framework dependencies
        package_json_path = os.path.join(project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                dependencies = {
                    **package_data.get('dependencies', {}),
                    **package_data.get('devDependencies', {})
                }
                
                # Check for framework-specific dependencies
                if 'next' in dependencies:
                    return 'next.js'
                elif '@remix-run/dev' in dependencies or '@remix-run/node' in dependencies:
                    return 'remix'
                elif 'vite' in dependencies:
                    return 'vite'
                elif 'react' in dependencies:
                    return 'react'
            except Exception:
                pass
        
        # Check for Vite config
        if os.path.exists(os.path.join(project_path, 'vite.config.js')) or os.path.exists(os.path.join(project_path, 'vite.config.ts')):
            return 'vite'
        
        # Check for Remix config
        if os.path.exists(os.path.join(project_path, 'remix.config.js')):
            return 'remix'
        
        # Default to react if nothing else is detected
        return 'react'
    
    def _detect_generation_type(self, prompt: str) -> str:
        """Detect generation type from prompt."""
        prompt_lower = prompt.lower()
        
        # Check for multi-file patterns
        if any(word in prompt_lower for word in ['multi', 'multiple', 'files', 'separate']):
            return 'multi'
        
        # Check for page patterns
        if any(word in prompt_lower for word in ['page', 'route', 'screen']):
            return 'page'
        
        # Check for feature patterns
        if any(word in prompt_lower for word in ['feature', 'module', 'system']):
            return 'feature'
        
        # Check for utility patterns
        if any(word in prompt_lower for word in ['util', 'helper', 'function']):
            return 'utils'
        
        # Check for hook patterns
        if any(word in prompt_lower for word in ['hook', 'use']):
            return 'hooks'
        
        # Default to single component
        return 'single'

    def generate(self, request) -> Dict[str, str]:
        """Generate component(s) based on a GenerationRequest."""
        # Convert request to context format
        context = {
            'framework': request.framework.value,
            'styling': request.styling.value,
            'component_library': request.component_library.value,
            'typescript': True,
            'project_path': self.project_path
        }
        
        # Add project context if available
        if self._project_context:
            context.update(self._project_context)
        
        # Generate the component
        if hasattr(self, 'validator') and self.validator and self.quality_assurance:
            component_code, quality_report = self.generate_component_with_qa(
                request.prompt, 
                context,
                target_path="Component.tsx"
            )
        else:
            component_code = self.generate_component(request.prompt, context)
        
        # Determine the correct file path using smart project structure detection
        file_path = self._determine_file_path_smart(request)
        
        # Return in the expected format
        return {file_path: component_code}
    
    def _determine_file_path_smart(self, request) -> str:
        """Use ProjectStructureDetector to determine the correct file path."""
        if not self.project_path:
            # Fallback to current directory if no project path
            project_path = os.getcwd()
        else:
            project_path = self.project_path
            
        try:
            detector = ProjectStructureDetector(project_path)
            return detector.generate_file_path(request.prompt)
        except Exception as e:
            print(f"⚠️ Smart path detection failed: {e}")
            # Fallback to simple component naming
            return self._fallback_file_path(request.prompt)
    
    def _fallback_file_path(self, prompt: str) -> str:
        """Fallback file path generation when smart detection fails."""
        prompt_lower = prompt.lower()
        
        # Simple name extraction
        if 'hero' in prompt_lower:
            name = 'HeroSection'
        elif 'pricing' in prompt_lower:
            name = 'PricingSection'  
        elif 'nav' in prompt_lower:
            name = 'Navigation'
        elif 'card' in prompt_lower:
            name = 'Card'
        elif 'button' in prompt_lower:
            name = 'Button'
        else:
            name = 'Component'
        
        # Default to components directory with TypeScript extension
        return f"components/{name}.tsx"
    
    def _auto_discover_mcp_servers(self, project_path: str):
        """Auto-discover and configure MCP servers based on project setup."""
        try:
            # Initialize MCP registry
            mcp_registry = MCPServerRegistry()
            
            # Run auto-discovery
            discovery_result = mcp_registry.auto_discover_servers(project_path)
            
            # Store discovery results for potential use in Zero-Fix Pipeline
            self._mcp_discovery = discovery_result
            
            if discovery_result['enabled']:
                print(f"🎯 MCP integration enabled with {len(discovery_result['enabled'])} servers")
            
        except Exception as e:
            print(f"⚠️ MCP auto-discovery failed: {e}")
            # Don't fail the entire initialization if MCP discovery fails
            self._mcp_discovery = {"discovered": [], "enabled": []}