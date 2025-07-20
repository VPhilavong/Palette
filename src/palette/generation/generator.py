import os
import subprocess
import tempfile
from typing import Dict, Optional

import anthropic
from openai import OpenAI

from .prompts import UIPromptBuilder
from .enhanced_prompts import EnhancedPromptBuilder


class UIGenerator:
    """Core UI generation logic using LLM APIs"""

    def __init__(self, model: str = None, project_path: str = None, enhanced_mode: bool = True):
        # Use environment variable or provided model or fallback
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Initialize prompt builder (enhanced or basic)
        if enhanced_mode and project_path:
            try:
                self.prompt_builder = EnhancedPromptBuilder()
                self.prompt_builder.initialize_project_analysis(project_path)
                print("✅ Enhanced prompt engineering enabled with project analysis")
            except Exception as e:
                print(f"⚠️ Enhanced mode failed, falling back to basic: {e}")
                self.prompt_builder = UIPromptBuilder()
        else:
            self.prompt_builder = UIPromptBuilder()

        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None

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
            # Extract content between first pair of triple backticks
            start_marker = response.find("```")
            if start_marker != -1:
                # Skip the opening ```tsx or ```javascript
                start_content = response.find("\n", start_marker) + 1
                end_marker = response.find("```", start_content)
                if end_marker != -1:
                    response = response[start_content:end_marker].strip()

        return response

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

    def _find_eslint_config(self, project_path: str = None) -> Optional[str]:
        """Find ESLint configuration file"""

        if not project_path:
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
