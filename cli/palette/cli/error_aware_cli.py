"""
Example CLI implementation with comprehensive error handling.
Shows how to use the error handling system in practice.
"""

import click
import sys
from typing import Optional

from ..errors import (
    PaletteError, AnalysisError, GenerationError,
    ValidationError, ConfigurationError
)
from ..errors.handlers import ConsoleErrorHandler, FileErrorHandler, CompositeErrorHandler
from ..errors.decorators import handle_errors, retry_on_error
from ..interfaces import IAnalyzer, IGenerator
from ..di import Container


class ErrorAwareCLI:
    """
    CLI implementation with comprehensive error handling.
    """
    
    def __init__(self, verbose: bool = False, log_errors: bool = True):
        """
        Initialize CLI with error handling configuration.
        
        Args:
            verbose: Show detailed error information
            log_errors: Log errors to file
        """
        self.verbose = verbose
        self.container = Container()
        
        # Set up error handlers
        handlers = [ConsoleErrorHandler(verbose=verbose, color=True)]
        if log_errors:
            handlers.append(FileErrorHandler())
        
        self.error_handler = CompositeErrorHandler(handlers)
    
    def run(self, command: str, **kwargs):
        """
        Run a CLI command with error handling.
        
        Args:
            command: Command to run
            **kwargs: Command arguments
        """
        try:
            if command == "generate":
                self._generate(**kwargs)
            elif command == "analyze":
                self._analyze(**kwargs)
            elif command == "validate":
                self._validate(**kwargs)
            else:
                raise ValueError(f"Unknown command: {command}")
                
        except PaletteError as e:
            # Handle Palette-specific errors
            self.error_handler.handle(e)
            sys.exit(1)
        except KeyboardInterrupt:
            # Handle user interruption
            click.echo("\n\nOperation cancelled by user.")
            sys.exit(130)
        except Exception as e:
            # Handle unexpected errors
            self.error_handler.handle(e)
            if self.verbose:
                raise
            sys.exit(1)
    
    @handle_errors(reraise=True)
    @retry_on_error(
        max_attempts=3,
        delay=1.0,
        error_types=[GenerationError],
        on_retry=lambda e, attempt: click.echo(f"Retrying after error ({attempt}/3)...")
    )
    def _generate(self, prompt: str, project_path: str, **options):
        """
        Generate component with error handling and retry logic.
        
        Args:
            prompt: Generation prompt
            project_path: Path to project
            **options: Additional options
        """
        # Get services from container
        analyzer = self.container.resolve(IAnalyzer)
        generator = self.container.resolve(IGenerator)
        
        # Analyze project
        click.echo("Analyzing project...")
        try:
            analysis = analyzer.analyze(project_path)
        except AnalysisError as e:
            # Add user-friendly context
            e.add_context(
                hint="Ensure you're running from the project root directory",
                project_path=project_path
            )
            raise
        
        # Generate component
        click.echo(f"Generating: {prompt}")
        try:
            result = generator.generate(
                prompt=prompt,
                analysis_result=analysis,
                **options
            )
        except GenerationError as e:
            # Check for specific error conditions
            if "rate limit" in str(e).lower():
                e.add_context(
                    hint="You've hit the API rate limit. Please wait a moment.",
                    suggestion="Consider using a different API key or model"
                )
            elif "timeout" in str(e).lower():
                e.add_context(
                    hint="The request timed out. Try a simpler prompt.",
                    suggestion="Break down complex components into smaller parts"
                )
            raise
        
        click.echo(f"✅ Generated successfully: {result.file_path}")
        return result
    
    @handle_errors(reraise=True)
    def _analyze(self, project_path: str, output_format: str = "json"):
        """
        Analyze project with error handling.
        
        Args:
            project_path: Path to project
            output_format: Output format (json, summary)
        """
        analyzer = self.container.resolve(IAnalyzer)
        
        click.echo(f"Analyzing project: {project_path}")
        
        try:
            result = analyzer.analyze(project_path)
        except AnalysisError as e:
            # Provide helpful context based on error
            if "permission" in str(e).lower():
                e.add_context(
                    hint="Check file permissions in the project directory",
                    suggestion=f"Run: chmod -R u+r {project_path}"
                )
            raise
        
        # Output results
        if output_format == "json":
            import json
            click.echo(json.dumps(result.to_dict(), indent=2))
        else:
            self._print_analysis_summary(result)
    
    def _print_analysis_summary(self, result):
        """Print analysis summary."""
        click.echo("\n📊 Analysis Summary")
        click.echo("=" * 50)
        
        # Project info
        structure = result.project_structure
        click.echo(f"Framework: {structure.framework}")
        click.echo(f"React Version: {structure.react_version or 'Not detected'}")
        click.echo(f"TypeScript: {'Yes' if structure.has_typescript else 'No'}")
        click.echo(f"Styling: {structure.styling_approach}")
        
        # Components
        click.echo(f"\n📦 Components Found: {len(result.components)}")
        for comp in result.components[:5]:  # Show first 5
            click.echo(f"  - {comp.name}: {comp.purpose}")
        if len(result.components) > 5:
            click.echo(f"  ... and {len(result.components) - 5} more")
        
        # Design tokens
        tokens = result.design_tokens
        click.echo(f"\n🎨 Design Tokens:")
        click.echo(f"  - Colors: {len(tokens.colors)}")
        click.echo(f"  - Spacing: {len(tokens.spacing)}")
        click.echo(f"  - Typography: {len(tokens.typography)}")
    
    @handle_errors(reraise=True)
    def _validate(self, file_path: str, fix: bool = False):
        """
        Validate generated code with error handling.
        
        Args:
            file_path: Path to file to validate
            fix: Whether to attempt auto-fix
        """
        from ..quality import ComponentValidator
        
        validator = ComponentValidator()
        
        click.echo(f"Validating: {file_path}")
        
        try:
            issues = validator.validate_file(file_path)
            
            if not issues:
                click.echo("✅ No issues found!")
                return
            
            # Display issues
            click.echo(f"\n⚠️  Found {len(issues)} issues:")
            for i, issue in enumerate(issues, 1):
                click.echo(f"\n{i}. {issue['type']}: {issue['message']}")
                if issue.get('line'):
                    click.echo(f"   Line {issue['line']}: {issue.get('context', '')}")
            
            # Attempt fix if requested
            if fix:
                click.echo("\n🔧 Attempting to fix issues...")
                fixed = validator.fix_issues(file_path, issues)
                click.echo(f"✅ Fixed {fixed} issues")
                
        except ValidationError as e:
            e.add_context(
                hint="Ensure the file contains valid TypeScript/React code",
                file_path=file_path
            )
            raise


# Example usage in a Click command
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Verbose error output')
@click.option('--no-log', is_flag=True, help='Disable error logging')
@click.pass_context
def cli(ctx, verbose, no_log):
    """Palette CLI with comprehensive error handling."""
    ctx.obj = ErrorAwareCLI(verbose=verbose, log_errors=not no_log)


@cli.command()
@click.argument('prompt')
@click.option('--project', '-p', default='.', help='Project path')
@click.option('--framework', '-f', help='Target framework')
@click.pass_obj
def generate(cli_obj, prompt, project, framework):
    """Generate a component with error handling."""
    cli_obj.run('generate', prompt=prompt, project_path=project, framework=framework)


@cli.command()
@click.argument('project_path', default='.')
@click.option('--format', '-f', type=click.Choice(['json', 'summary']), default='summary')
@click.pass_obj
def analyze(cli_obj, project_path, format):
    """Analyze a project with error handling."""
    cli_obj.run('analyze', project_path=project_path, output_format=format)


@cli.command()
@click.argument('file_path')
@click.option('--fix', is_flag=True, help='Attempt to fix issues')
@click.pass_obj
def validate(cli_obj, file_path, fix):
    """Validate generated code with error handling."""
    cli_obj.run('validate', file_path=file_path, fix=fix)


if __name__ == '__main__':
    cli()