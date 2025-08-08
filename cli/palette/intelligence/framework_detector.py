"""
Enhanced Framework Detection with deep analysis capabilities.
Provides sophisticated framework detection with confidence scoring.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ..errors.decorators import handle_errors


class Framework(Enum):
    """Supported frontend frameworks."""
    NEXT_JS = "next.js"
    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"
    ANGULAR = "angular"
    GATSBY = "gatsby"
    REMIX = "remix"
    VITE_REACT = "vite-react"
    CREATE_REACT_APP = "create-react-app"


@dataclass
class FrameworkHint:
    """A hint about detected framework from a specific source."""
    source: str
    framework: Framework
    confidence: float
    evidence: List[str] = field(default_factory=list)


@dataclass
class FrameworkAnalysis:
    """Complete framework analysis results."""
    primary_framework: Framework
    confidence: float
    secondary_frameworks: List[Tuple[Framework, float]] = field(default_factory=list)
    evidence_summary: Dict[str, List[str]] = field(default_factory=dict)
    detection_metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedFrameworkDetector:
    """
    Enhanced framework detector with multiple detection methods.
    Provides deep analysis with confidence scoring and evidence tracking.
    """
    
    def __init__(self):
        self._initialize_detection_patterns()
    
    def _initialize_detection_patterns(self):
        """Initialize framework detection patterns."""
        
        # Package.json dependency patterns
        self.package_patterns = {
            Framework.NEXT_JS: [
                "next", "@next/", "next-auth", "@next/font", "next-themes",
                "next-seo", "next-mdx-remote"
            ],
            Framework.REACT: [
                "react", "react-dom", "react-router", "react-router-dom",
                "@testing-library/react", "react-scripts"
            ],
            Framework.VUE: [
                "vue", "@vue/", "vue-router", "vuex", "pinia", "nuxt"
            ],
            Framework.SVELTE: [
                "svelte", "@sveltejs/", "svelte-kit", "svelte-preprocess"
            ],
            Framework.ANGULAR: [
                "@angular/", "angular", "@ngrx/", "rxjs", "zone.js"
            ],
            Framework.GATSBY: [
                "gatsby", "gatsby-plugin-", "gatsby-source-", "gatsby-transformer-"
            ],
            Framework.REMIX: [
                "@remix-run/", "remix", "@remix-run/node", "@remix-run/react"
            ],
            Framework.VITE_REACT: [
                "vite", "@vitejs/plugin-react", "@vitejs/plugin-react-swc"
            ],
            Framework.CREATE_REACT_APP: [
                "react-scripts", "react-app-polyfill"
            ]
        }
        
        # Configuration file patterns
        self.config_patterns = {
            Framework.NEXT_JS: [
                "next.config.js", "next.config.ts", "next.config.mjs"
            ],
            Framework.VUE: [
                "vue.config.js", "vite.config.js", "nuxt.config.js"
            ],
            Framework.SVELTE: [
                "svelte.config.js", "vite.config.js"
            ],
            Framework.ANGULAR: [
                "angular.json", ".angular-cli.json", "ng-package.json"
            ],
            Framework.GATSBY: [
                "gatsby-config.js", "gatsby-node.js", "gatsby-browser.js"
            ],
            Framework.REMIX: [
                "remix.config.js", "app/entry.client.tsx", "app/entry.server.tsx"
            ],
            Framework.VITE_REACT: [
                "vite.config.js", "vite.config.ts"
            ]
        }
        
        # File structure patterns
        self.structure_patterns = {
            Framework.NEXT_JS: [
                "pages/", "app/", "public/", "styles/", 
                "pages/_app.js", "pages/index.js",
                "app/layout.tsx", "app/page.tsx"
            ],
            Framework.VUE: [
                "src/components/", "src/views/", "src/router/",
                "src/App.vue", "src/main.js"
            ],
            Framework.SVELTE: [
                "src/routes/", "src/lib/", "src/app.html",
                "src/app.svelte"
            ],
            Framework.ANGULAR: [
                "src/app/", "src/environments/", "src/assets/",
                "src/main.ts", "src/app/app.module.ts"
            ],
            Framework.GATSBY: [
                "src/pages/", "src/components/", "src/templates/",
                "static/", "gatsby-config.js"
            ],
            Framework.REMIX: [
                "app/routes/", "app/components/", "app/root.tsx",
                "app/entry.client.tsx", "app/entry.server.tsx"
            ],
            Framework.CREATE_REACT_APP: [
                "src/", "public/", "src/App.js", "src/index.js",
                "public/index.html"
            ]
        }
        
        # Import patterns in code files
        self.import_patterns = {
            Framework.NEXT_JS: [
                re.compile(r'from ["\']next/'),
                re.compile(r'import.*from ["\']next/'),
                re.compile(r'useRouter.*from ["\']next/router'),
                re.compile(r'Image.*from ["\']next/image'),
                re.compile(r'Head.*from ["\']next/head')
            ],
            Framework.REACT: [
                re.compile(r'from ["\']react["\']'),
                re.compile(r'import React'),
                re.compile(r'from ["\']react-dom'),
                re.compile(r'from ["\']react-router')
            ],
            Framework.VUE: [
                re.compile(r'from ["\']vue["\']'),
                re.compile(r'<template>'),
                re.compile(r'<script.*vue'),
                re.compile(r'export default.*defineComponent')
            ],
            Framework.REMIX: [
                re.compile(r'from ["\']@remix-run/'),
                re.compile(r'export.*loader'),
                re.compile(r'export.*action'),
                re.compile(r'useLoaderData')
            ]
        }
    
    @handle_errors(reraise=True)
    def deep_analyze(self, project_path: str) -> FrameworkAnalysis:
        """
        Perform deep framework analysis with multiple detection methods.
        
        Args:
            project_path: Path to the project to analyze
            
        Returns:
            Comprehensive framework analysis with confidence scores
        """
        project_path = Path(project_path)
        
        # Collect hints from all detection methods
        hints = []
        
        # 1. Package.json analysis
        package_hint = self._analyze_package_json(project_path)
        if package_hint:
            hints.append(package_hint)
        
        # 2. Configuration files analysis
        config_hints = self._analyze_config_files(project_path)
        hints.extend(config_hints)
        
        # 3. File structure analysis
        structure_hints = self._analyze_file_structure(project_path)
        hints.extend(structure_hints)
        
        # 4. Import patterns analysis
        import_hints = self._analyze_import_patterns(project_path)
        hints.extend(import_hints)
        
        # 5. Special detection logic
        special_hints = self._special_detection_logic(project_path)
        hints.extend(special_hints)
        
        # Resolve conflicts and determine primary framework
        return self._resolve_framework_conflicts(hints)
    
    def _analyze_package_json(self, project_path: Path) -> Optional[FrameworkHint]:
        """Analyze package.json for framework dependencies."""
        package_json = project_path / "package.json"
        
        if not package_json.exists():
            return None
        
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            all_deps = {}
            all_deps.update(package_data.get('dependencies', {}))
            all_deps.update(package_data.get('devDependencies', {}))
            all_deps.update(package_data.get('peerDependencies', {}))
            
            dep_names = set(all_deps.keys())
            
            # Score each framework based on dependencies
            framework_scores = {}
            evidence = {}
            
            for framework, patterns in self.package_patterns.items():
                matches = []
                for pattern in patterns:
                    matching_deps = [dep for dep in dep_names if pattern in dep]
                    matches.extend(matching_deps)
                
                if matches:
                    # Calculate confidence based on matches and specificity
                    confidence = min(0.9, len(matches) * 0.2 + 0.3)
                    framework_scores[framework] = confidence
                    evidence[framework] = matches
            
            if framework_scores:
                # Return the highest scoring framework
                primary_framework = max(framework_scores.items(), key=lambda x: x[1])
                
                return FrameworkHint(
                    source="package.json",
                    framework=primary_framework[0],
                    confidence=primary_framework[1],
                    evidence=[f"Found {dep}" for dep in evidence[primary_framework[0]]]
                )
        
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            pass
        
        return None
    
    def _analyze_config_files(self, project_path: Path) -> List[FrameworkHint]:
        """Analyze configuration files for framework indicators."""
        hints = []
        
        for framework, config_files in self.config_patterns.items():
            for config_file in config_files:
                config_path = project_path / config_file
                if config_path.exists():
                    hints.append(FrameworkHint(
                        source="config_files",
                        framework=framework,
                        confidence=0.8,  # High confidence for config files
                        evidence=[f"Found {config_file}"]
                    ))
        
        return hints
    
    def _analyze_file_structure(self, project_path: Path) -> List[FrameworkHint]:
        """Analyze project file structure for framework patterns."""
        hints = []
        
        for framework, structure_patterns in self.structure_patterns.items():
            matches = []
            for pattern in structure_patterns:
                path_to_check = project_path / pattern
                if path_to_check.exists():
                    matches.append(pattern)
            
            if matches:
                # Calculate confidence based on matches
                confidence = min(0.7, len(matches) * 0.15 + 0.2)
                hints.append(FrameworkHint(
                    source="file_structure",
                    framework=framework,
                    confidence=confidence,
                    evidence=[f"Found {match}" for match in matches]
                ))
        
        return hints
    
    def _analyze_import_patterns(self, project_path: Path) -> List[FrameworkHint]:
        """Analyze import patterns in source files."""
        hints = []
        
        # Find source files to analyze
        source_files = []
        for pattern in ["**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx", "**/*.vue", "**/*.svelte"]:
            source_files.extend(list(project_path.glob(pattern))[:20])  # Limit for performance
        
        framework_import_counts = {}
        
        for file_path in source_files:
            if 'node_modules' in str(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read first 50 lines for imports
                    lines = f.readlines()[:50]
                    content = ''.join(lines)
                
                for framework, patterns in self.import_patterns.items():
                    for pattern in patterns:
                        matches = pattern.findall(content)
                        if matches:
                            if framework not in framework_import_counts:
                                framework_import_counts[framework] = []
                            framework_import_counts[framework].extend(matches)
            
            except (UnicodeDecodeError, IOError):
                continue
        
        # Convert import counts to hints
        for framework, imports in framework_import_counts.items():
            if imports:
                confidence = min(0.8, len(imports) * 0.1 + 0.3)
                hints.append(FrameworkHint(
                    source="import_patterns",
                    framework=framework,
                    confidence=confidence,
                    evidence=[f"Import patterns: {len(imports)} matches"]
                ))
        
        return hints
    
    def _special_detection_logic(self, project_path: Path) -> List[FrameworkHint]:
        """Special detection logic for edge cases."""
        hints = []
        
        # Detect Vite + React vs Create React App
        vite_config = project_path / "vite.config.js" or project_path / "vite.config.ts"
        package_json = project_path / "package.json"
        
        if vite_config.exists() and package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                
                deps = {}
                deps.update(data.get('dependencies', {}))
                deps.update(data.get('devDependencies', {}))
                
                # If has Vite + React, it's Vite React, not just React
                if 'vite' in deps and 'react' in deps:
                    hints.append(FrameworkHint(
                        source="special_logic",
                        framework=Framework.VITE_REACT,
                        confidence=0.9,
                        evidence=["Vite + React combination detected"]
                    ))
                
                # If has react-scripts, it's likely Create React App
                elif 'react-scripts' in deps:
                    hints.append(FrameworkHint(
                        source="special_logic",
                        framework=Framework.CREATE_REACT_APP,
                        confidence=0.8,
                        evidence=["Create React App detected via react-scripts"]
                    ))
            
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Detect Next.js App Router vs Pages Router
        app_dir = project_path / "app"
        pages_dir = project_path / "pages"
        
        if app_dir.exists() and (app_dir / "layout.tsx").exists():
            hints.append(FrameworkHint(
                source="special_logic",
                framework=Framework.NEXT_JS,
                confidence=0.95,
                evidence=["Next.js App Router detected"]
            ))
        elif pages_dir.exists() and (pages_dir / "_app.js").exists():
            hints.append(FrameworkHint(
                source="special_logic", 
                framework=Framework.NEXT_JS,
                confidence=0.9,
                evidence=["Next.js Pages Router detected"]
            ))
        
        return hints
    
    def _resolve_framework_conflicts(self, hints: List[FrameworkHint]) -> FrameworkAnalysis:
        """Resolve conflicts between framework detection methods."""
        
        if not hints:
            return FrameworkAnalysis(
                primary_framework=Framework.REACT,  # Default fallback
                confidence=0.1,
                evidence_summary={"default": ["No framework detected - using React fallback"]}
            )
        
        # Weight each detection source
        source_weights = {
            "config_files": 0.8,      # High weight - explicit configuration
            "package.json": 0.7,      # High weight - explicit dependencies
            "special_logic": 0.9,     # Highest weight - sophisticated detection
            "import_patterns": 0.5,   # Medium weight - usage patterns
            "file_structure": 0.4     # Lower weight - could be misleading
        }
        
        # Aggregate scores
        framework_scores = {}
        evidence_by_framework = {}
        
        for hint in hints:
            weight = source_weights.get(hint.source, 0.5)
            weighted_confidence = hint.confidence * weight
            
            if hint.framework not in framework_scores:
                framework_scores[hint.framework] = 0
                evidence_by_framework[hint.framework] = []
            
            framework_scores[hint.framework] += weighted_confidence
            evidence_by_framework[hint.framework].extend(hint.evidence)
        
        # Sort by score
        sorted_frameworks = sorted(framework_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_frameworks:
            return FrameworkAnalysis(
                primary_framework=Framework.REACT,
                confidence=0.1,
                evidence_summary={"fallback": ["No valid framework detected"]}
            )
        
        primary_framework, primary_score = sorted_frameworks[0]
        secondary_frameworks = [(fw, score) for fw, score in sorted_frameworks[1:] if score > 0.2]
        
        # Build evidence summary
        evidence_summary = {}
        for hint in hints:
            if hint.source not in evidence_summary:
                evidence_summary[hint.source] = []
            evidence_summary[hint.source].extend(hint.evidence)
        
        # Normalize confidence score
        normalized_confidence = min(1.0, primary_score)
        
        return FrameworkAnalysis(
            primary_framework=primary_framework,
            confidence=normalized_confidence,
            secondary_frameworks=secondary_frameworks,
            evidence_summary=evidence_summary,
            detection_metadata={
                'total_hints': len(hints),
                'sources_analyzed': list(set(hint.source for hint in hints)),
                'confidence_raw': primary_score
            }
        )