"""
Import Approval System with rich CLI prompts and user interaction.
Provides intelligent import management with user approval workflows.
"""

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from ..errors.decorators import handle_errors
from .import_detector import ImportAnalysisResult, ImportDetector, ImportSuggestion


class ApprovalMode(Enum):
    """Different modes for import approval."""
    INTERACTIVE = "interactive"      # Prompt for each import group
    BULK_APPROVE = "bulk_approve"    # Approve all at once with preview
    AUTO_APPROVE = "auto_approve"    # Auto-approve trusted imports
    PREVIEW_ONLY = "preview_only"    # Show what would be added without applying


class ApprovalScope(Enum):
    """Scope of import approval."""
    ALL = "all"                      # All detected imports
    CRITICAL_ONLY = "critical_only"  # Only critical imports (React core, etc.)
    UI_LIBRARY_ONLY = "ui_library"   # Only UI library imports
    SAFE_ONLY = "safe_only"          # Only high-confidence, safe imports


@dataclass
class ApprovalPreferences:
    """User preferences for import approval."""
    mode: ApprovalMode = ApprovalMode.INTERACTIVE
    scope: ApprovalScope = ApprovalScope.ALL
    auto_approve_confidence_threshold: float = 0.9
    auto_approve_sources: Set[str] = None
    always_prompt_sources: Set[str] = None
    remember_choices: bool = True
    show_reasoning: bool = True
    show_line_numbers: bool = False
    
    def __post_init__(self):
        if self.auto_approve_sources is None:
            self.auto_approve_sources = {'react', 'clsx', 'classnames'}
        if self.always_prompt_sources is None:
            self.always_prompt_sources = {'@types/react', '@types/node'}


@dataclass
class ApprovalResult:
    """Result of the import approval process."""
    approved_imports: List[ImportSuggestion]
    rejected_imports: List[ImportSuggestion]
    auto_approved_imports: List[ImportSuggestion]
    modified_code: str
    user_cancelled: bool = False
    approval_summary: str = ""
    preferences_updated: bool = False


class ImportApprovalSystem:
    """
    Advanced import approval system with rich CLI interface and intelligent defaults.
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.console = Console()
        self.detector = ImportDetector(str(project_path))
        self.preferences_file = self.project_path / ".palette" / "import-preferences.json"
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> ApprovalPreferences:
        """Load user preferences from project or global config."""
        preferences = ApprovalPreferences()
        
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert data back to ApprovalPreferences
                preferences.mode = ApprovalMode(data.get('mode', 'interactive'))
                preferences.scope = ApprovalScope(data.get('scope', 'all'))
                preferences.auto_approve_confidence_threshold = data.get('auto_approve_confidence_threshold', 0.9)
                preferences.auto_approve_sources = set(data.get('auto_approve_sources', ['react', 'clsx', 'classnames']))
                preferences.always_prompt_sources = set(data.get('always_prompt_sources', ['@types/react', '@types/node']))
                preferences.remember_choices = data.get('remember_choices', True)
                preferences.show_reasoning = data.get('show_reasoning', True)
                preferences.show_line_numbers = data.get('show_line_numbers', False)
                
            except (json.JSONDecodeError, KeyError, ValueError):
                # Fall back to defaults if config is invalid
                pass
        
        return preferences
    
    def _save_preferences(self):
        """Save current preferences to project config."""
        if not self.preferences.remember_choices:
            return
        
        # Ensure .palette directory exists
        self.preferences_file.parent.mkdir(exist_ok=True)
        
        # Convert preferences to dict for JSON serialization
        data = {
            'mode': self.preferences.mode.value,
            'scope': self.preferences.scope.value,
            'auto_approve_confidence_threshold': self.preferences.auto_approve_confidence_threshold,
            'auto_approve_sources': list(self.preferences.auto_approve_sources),
            'always_prompt_sources': list(self.preferences.always_prompt_sources),
            'remember_choices': self.preferences.remember_choices,
            'show_reasoning': self.preferences.show_reasoning,
            'show_line_numbers': self.preferences.show_line_numbers,
        }
        
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not save preferences: {e}[/yellow]")
    
    @handle_errors(reraise=True)
    def approve_imports(self, 
                       code: str, 
                       file_path: str = "Component.tsx",
                       mode: Optional[ApprovalMode] = None) -> ApprovalResult:
        """
        Main entry point for import approval workflow.
        
        Args:
            code: Component code to analyze
            file_path: Target file path
            mode: Override default approval mode
            
        Returns:
            Complete approval result with modified code
        """
        
        # Use provided mode or default from preferences
        approval_mode = mode or self.preferences.mode
        
        # Analyze imports
        analysis = self.detector.analyze_imports(code, file_path)
        
        if not analysis.missing_imports:
            return ApprovalResult(
                approved_imports=[],
                rejected_imports=[],
                auto_approved_imports=[],
                modified_code=code,
                approval_summary="✅ No missing imports detected"
            )
        
        # Filter imports based on scope preferences
        filtered_imports = self._filter_imports_by_scope(analysis.missing_imports)
        
        if not filtered_imports:
            return ApprovalResult(
                approved_imports=[],
                rejected_imports=[],
                auto_approved_imports=[],
                modified_code=code,
                approval_summary="✅ No imports in selected scope require approval"
            )
        
        # Show initial analysis
        self._show_import_analysis_summary(analysis, filtered_imports)
        
        # Handle different approval modes
        if approval_mode == ApprovalMode.INTERACTIVE:
            return self._interactive_approval(code, filtered_imports, analysis)
        elif approval_mode == ApprovalMode.BULK_APPROVE:
            return self._bulk_approval(code, filtered_imports, analysis)
        elif approval_mode == ApprovalMode.AUTO_APPROVE:
            return self._auto_approval(code, filtered_imports, analysis)
        elif approval_mode == ApprovalMode.PREVIEW_ONLY:
            return self._preview_only(code, filtered_imports, analysis)
        else:
            raise ValueError(f"Unknown approval mode: {approval_mode}")
    
    def _filter_imports_by_scope(self, imports: List[ImportSuggestion]) -> List[ImportSuggestion]:
        """Filter imports based on scope preferences."""
        
        if self.preferences.scope == ApprovalScope.ALL:
            return imports
        
        elif self.preferences.scope == ApprovalScope.CRITICAL_ONLY:
            return [imp for imp in imports if imp.source == 'react' or imp.confidence >= 0.95]
        
        elif self.preferences.scope == ApprovalScope.UI_LIBRARY_ONLY:
            ui_sources = {'@chakra-ui/react', '@mui/material', 'antd', '@mantine/core'}
            return [imp for imp in imports if imp.source in ui_sources]
        
        elif self.preferences.scope == ApprovalScope.SAFE_ONLY:
            return [imp for imp in imports if imp.confidence >= self.preferences.auto_approve_confidence_threshold]
        
        return imports
    
    def _show_import_analysis_summary(self, analysis: ImportAnalysisResult, filtered_imports: List[ImportSuggestion]):
        """Show summary of import analysis."""
        
        # Main analysis panel
        summary_text = f"[bold]Import Analysis Results[/bold]\n\n"
        summary_text += f"• Total missing imports: {len(analysis.missing_imports)}\n"
        summary_text += f"• In current scope: {len(filtered_imports)}\n"
        summary_text += f"• Existing imports: {len(analysis.existing_imports)}\n"
        summary_text += f"• Analysis confidence: {analysis.analysis_confidence:.1%}\n"
        
        if analysis.conflicts:
            summary_text += f"• Conflicts detected: {len(analysis.conflicts)}\n"
        
        self.console.print(Panel(summary_text, title="🔍 Import Analysis", border_style="blue"))
        
        # Show conflicts if any
        if analysis.conflicts:
            self._show_import_conflicts(analysis.conflicts)
    
    def _show_import_conflicts(self, conflicts: List[tuple]):
        """Show import conflicts in a table."""
        
        table = Table(title="⚠️ Import Conflicts Detected")
        table.add_column("Component", style="cyan")
        table.add_column("Conflicting Sources", style="yellow")
        table.add_column("Recommendation", style="green")
        
        for name, sources in conflicts:
            sources_str = " vs ".join(sources)
            
            # Provide specific recommendations
            if 'react' in sources:
                recommendation = "Use React core version"
            elif any('@chakra-ui' in s for s in sources) and any('@mui' in s for s in sources):
                recommendation = "Choose one UI library"
            else:
                recommendation = "Review manually"
            
            table.add_row(name, sources_str, recommendation)
        
        self.console.print(table)
        self.console.print("")
    
    def _interactive_approval(self, code: str, imports: List[ImportSuggestion], analysis: ImportAnalysisResult) -> ApprovalResult:
        """Interactive approval workflow with per-import or per-source prompting."""
        
        approved = []
        rejected = []
        auto_approved = []
        
        # Group imports by source for cleaner approval
        by_source = {}
        for imp in imports:
            if imp.source not in by_source:
                by_source[imp.source] = []
            by_source[imp.source].append(imp)
        
        self.console.print("\n[bold blue]📝 Interactive Import Approval[/bold blue]")
        self.console.print("[dim]You can approve imports by source or individually[/dim]\n")
        
        for source, source_imports in by_source.items():
            # Check if this source should be auto-approved
            if (source in self.preferences.auto_approve_sources and 
                all(imp.confidence >= self.preferences.auto_approve_confidence_threshold for imp in source_imports)):
                
                auto_approved.extend(source_imports)
                self.console.print(f"✅ [green]Auto-approved {len(source_imports)} imports from '{source}'[/green]")
                continue
            
            # Show source group
            self._show_source_import_group(source, source_imports)
            
            # Prompt for approval
            if len(source_imports) == 1:
                choice = self._prompt_single_import(source_imports[0])
            else:
                choice = self._prompt_source_group(source, source_imports)
            
            if choice == 'approve_all':
                approved.extend(source_imports)
            elif choice == 'reject_all':
                rejected.extend(source_imports)
            elif choice == 'individual':
                for imp in source_imports:
                    if self._prompt_single_import(imp) == 'approve':
                        approved.append(imp)
                    else:
                        rejected.append(imp)
            elif choice == 'skip':
                rejected.extend(source_imports)
        
        # Apply approved imports
        modified_code = self._apply_approved_imports(code, approved + auto_approved)
        
        # Generate summary
        summary = self._generate_approval_summary(approved, rejected, auto_approved)
        
        return ApprovalResult(
            approved_imports=approved,
            rejected_imports=rejected,
            auto_approved_imports=auto_approved,
            modified_code=modified_code,
            approval_summary=summary
        )
    
    def _show_source_import_group(self, source: str, imports: List[ImportSuggestion]):
        """Show a group of imports from the same source."""
        
        # Create table for this source
        table = Table(title=f"Imports from '{source}'")
        table.add_column("Import", style="cyan")
        table.add_column("Confidence", style="green")
        
        if self.preferences.show_reasoning:
            table.add_column("Reasoning", style="dim")
        
        if self.preferences.show_line_numbers:
            table.add_column("Lines", style="yellow")
        
        for imp in imports:
            row = [imp.name, f"{imp.confidence:.1%}"]
            
            if self.preferences.show_reasoning:
                row.append(imp.reasoning or "Component usage detected")
            
            if self.preferences.show_line_numbers and imp.line_numbers:
                lines_str = ", ".join(map(str, imp.line_numbers[:3]))  # Show first 3 lines
                if len(imp.line_numbers) > 3:
                    lines_str += f" (+{len(imp.line_numbers) - 3} more)"
                row.append(lines_str)
            
            table.add_row(*row)
        
        self.console.print(table)
        print()
    
    def _prompt_source_group(self, source: str, imports: List[ImportSuggestion]) -> str:
        """Prompt for approval of an entire source group."""
        
        choices = [
            ('a', 'approve_all', f'Approve all {len(imports)} imports from {source}'),
            ('r', 'reject_all', f'Reject all imports from {source}'),
            ('i', 'individual', 'Approve individually'),
            ('s', 'skip', 'Skip this source'),
        ]
        
        # Show choices
        for key, _, description in choices:
            self.console.print(f"  [{key}] {description}")
        
        while True:
            choice = Prompt.ask("\nYour choice", choices=['a', 'r', 'i', 's'], default='a')
            
            # Return the action corresponding to the choice
            for key, action, _ in choices:
                if choice == key:
                    return action
    
    def _prompt_single_import(self, imp: ImportSuggestion) -> str:
        """Prompt for approval of a single import."""
        
        import_statement = imp.to_import_statement()
        
        self.console.print(f"\n[bold]Import:[/bold] [cyan]{import_statement}[/cyan]")
        if self.preferences.show_reasoning and imp.reasoning:
            self.console.print(f"[dim]Reasoning: {imp.reasoning}[/dim]")
        
        if Confirm.ask("Add this import?", default=True):
            return 'approve'
        else:
            return 'reject'
    
    def _bulk_approval(self, code: str, imports: List[ImportSuggestion], analysis: ImportAnalysisResult) -> ApprovalResult:
        """Bulk approval with preview."""
        
        self.console.print("\n[bold blue]📦 Bulk Import Approval[/bold blue]\n")
        
        # Show what will be added
        self._show_import_preview(imports)
        
        # Show the modified code preview
        preview_code = self._apply_approved_imports(code, imports)
        self._show_code_diff_preview(code, preview_code)
        
        # Ask for bulk approval
        if Confirm.ask("\nApprove all these imports?", default=True):
            approved = imports
            rejected = []
        else:
            approved = []
            rejected = imports
        
        summary = self._generate_approval_summary(approved, rejected, [])
        
        return ApprovalResult(
            approved_imports=approved,
            rejected_imports=rejected,
            auto_approved_imports=[],
            modified_code=preview_code if approved else code,
            approval_summary=summary
        )
    
    def _auto_approval(self, code: str, imports: List[ImportSuggestion], analysis: ImportAnalysisResult) -> ApprovalResult:
        """Auto-approval based on confidence and trusted sources."""
        
        auto_approved = []
        requires_approval = []
        
        for imp in imports:
            should_auto_approve = (
                imp.source in self.preferences.auto_approve_sources and
                imp.confidence >= self.preferences.auto_approve_confidence_threshold and
                imp.source not in self.preferences.always_prompt_sources
            )
            
            if should_auto_approve:
                auto_approved.append(imp)
            else:
                requires_approval.append(imp)
        
        self.console.print(f"\n[green]✅ Auto-approved {len(auto_approved)} trusted imports[/green]")
        
        if requires_approval:
            self.console.print(f"[yellow]⚠️ {len(requires_approval)} imports require manual approval[/yellow]")
            
            # Fall back to interactive for remaining imports
            manual_result = self._interactive_approval(code, requires_approval, analysis)
            
            # Combine results
            approved = manual_result.approved_imports
            rejected = manual_result.rejected_imports
            
        else:
            approved = []
            rejected = []
        
        # Apply all approved imports
        all_approved = auto_approved + approved
        modified_code = self._apply_approved_imports(code, all_approved)
        
        summary = self._generate_approval_summary(approved, rejected, auto_approved)
        
        return ApprovalResult(
            approved_imports=approved,
            rejected_imports=rejected,
            auto_approved_imports=auto_approved,
            modified_code=modified_code,
            approval_summary=summary
        )
    
    def _preview_only(self, code: str, imports: List[ImportSuggestion], analysis: ImportAnalysisResult) -> ApprovalResult:
        """Preview-only mode - show what would be added without applying."""
        
        self.console.print("\n[bold blue]👁️ Import Preview Mode[/bold blue]\n")
        
        self._show_import_preview(imports)
        
        # Show code preview
        preview_code = self._apply_approved_imports(code, imports)
        self._show_code_diff_preview(code, preview_code)
        
        self.console.print("\n[dim]Preview mode - no changes applied[/dim]")
        
        return ApprovalResult(
            approved_imports=[],
            rejected_imports=imports,
            auto_approved_imports=[],
            modified_code=code,
            approval_summary=f"Preview shown for {len(imports)} imports - no changes applied"
        )
    
    def _show_import_preview(self, imports: List[ImportSuggestion]):
        """Show a preview of all import statements that would be added."""
        
        # Group by source for display
        by_source = {}
        for imp in imports:
            if imp.source not in by_source:
                by_source[imp.source] = []
            by_source[imp.source].append(imp)
        
        import_statements = []
        for source, source_imports in by_source.items():
            # Generate the import statements for this source
            default_imports = [imp.name for imp in source_imports if imp.is_default]
            named_imports = [imp.name for imp in source_imports if not imp.is_default and not imp.is_type_import]
            type_imports = [imp.name for imp in source_imports if imp.is_type_import]
            
            # Add statements
            for default_import in default_imports:
                import_statements.append(f"import {default_import} from '{source}';")
            
            if named_imports:
                named_str = ', '.join(sorted(named_imports))
                import_statements.append(f"import {{ {named_str} }} from '{source}';")
            
            if type_imports:
                type_str = ', '.join(sorted(type_imports))
                import_statements.append(f"import type {{ {type_str} }} from '{source}';")
        
        # Display the import statements
        import_code = '\n'.join(import_statements)
        syntax = Syntax(import_code, "typescript", theme="monokai", line_numbers=True)
        
        self.console.print(Panel(syntax, title="📝 Import Statements to Add", border_style="green"))
    
    def _show_code_diff_preview(self, original: str, modified: str):
        """Show a diff preview of the code changes."""
        
        # For now, just show the import section of the modified code
        modified_lines = modified.split('\n')
        import_section_end = 0
        
        for i, line in enumerate(modified_lines):
            if line.strip().startswith('import ') or line.strip() == '':
                import_section_end = i
            else:
                break
        
        if import_section_end > 0:
            import_section = '\n'.join(modified_lines[:import_section_end + 2])  # Include some context
            syntax = Syntax(import_section, "typescript", theme="monokai", line_numbers=True)
            self.console.print(Panel(syntax, title="📄 Code Preview (Import Section)", border_style="blue"))
    
    def _apply_approved_imports(self, code: str, approved_imports: List[ImportSuggestion]) -> str:
        """Apply approved imports to the code."""
        
        if not approved_imports:
            return code
        
        return self.detector.apply_import_suggestions(code, approved_imports)
    
    def _generate_approval_summary(self, approved: List[ImportSuggestion], rejected: List[ImportSuggestion], auto_approved: List[ImportSuggestion]) -> str:
        """Generate a summary of the approval process."""
        
        summary_parts = []
        
        if auto_approved:
            summary_parts.append(f"✅ Auto-approved {len(auto_approved)} trusted imports")
        
        if approved:
            summary_parts.append(f"✅ Manually approved {len(approved)} imports")
        
        if rejected:
            summary_parts.append(f"❌ Rejected {len(rejected)} imports")
        
        total_applied = len(approved) + len(auto_approved)
        if total_applied > 0:
            summary_parts.append(f"🎉 Applied {total_applied} import statements to component")
        
        return " • ".join(summary_parts) if summary_parts else "No imports processed"
    
    def configure_preferences(self) -> bool:
        """Interactive configuration of import approval preferences."""
        
        self.console.print("\n[bold blue]⚙️ Configure Import Approval Preferences[/bold blue]\n")
        
        # Mode selection
        mode_choices = {
            '1': ApprovalMode.INTERACTIVE,
            '2': ApprovalMode.BULK_APPROVE,
            '3': ApprovalMode.AUTO_APPROVE,
            '4': ApprovalMode.PREVIEW_ONLY
        }
        
        self.console.print("Approval Mode:")
        self.console.print("  [1] Interactive - Prompt for each import group")
        self.console.print("  [2] Bulk Approve - Show preview and approve all at once")
        self.console.print("  [3] Auto Approve - Automatically approve trusted imports")
        self.console.print("  [4] Preview Only - Show what would be imported without applying")
        
        mode_choice = Prompt.ask("Choose mode", choices=['1', '2', '3', '4'], default='1')
        self.preferences.mode = mode_choices[mode_choice]
        
        # Scope selection
        scope_choices = {
            '1': ApprovalScope.ALL,
            '2': ApprovalScope.CRITICAL_ONLY,
            '3': ApprovalScope.UI_LIBRARY_ONLY,
            '4': ApprovalScope.SAFE_ONLY
        }
        
        self.console.print("\nApproval Scope:")
        self.console.print("  [1] All - All detected imports")
        self.console.print("  [2] Critical Only - React core and high-confidence imports")
        self.console.print("  [3] UI Library Only - Only UI library imports")
        self.console.print("  [4] Safe Only - Only high-confidence imports")
        
        scope_choice = Prompt.ask("Choose scope", choices=['1', '2', '3', '4'], default='1')
        self.preferences.scope = scope_choices[scope_choice]
        
        # Other preferences
        self.preferences.show_reasoning = Confirm.ask("Show reasoning for import suggestions?", default=True)
        self.preferences.show_line_numbers = Confirm.ask("Show line numbers where imports are used?", default=False)
        self.preferences.remember_choices = Confirm.ask("Remember these preferences?", default=True)
        
        # Save preferences
        if self.preferences.remember_choices:
            self._save_preferences()
            self.console.print("\n[green]✅ Preferences saved to project[/green]")
        
        return True