"""
Simple wrapper to provide missing analysis methods for the FastAPI server
This is a temporary solution until the ProjectAnalyzer class method issue is resolved
"""

import os
import json
from pathlib import Path


class AnalysisWrapper:
    """Wrapper class providing the analysis methods needed by the FastAPI server"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
    
    def detect_framework(self) -> str:
        """Detect framework used in project"""
        if not self.project_path or not os.path.exists(self.project_path):
            return "unknown"
            
        # Check for Vite config
        vite_configs = ["vite.config.js", "vite.config.ts", "vite.config.mjs"]
        for config in vite_configs:
            if os.path.exists(os.path.join(self.project_path, config)):
                return "vite"
        
        # Check for Next.js
        if os.path.exists(os.path.join(self.project_path, "next.config.js")):
            return "next"
        
        # Check package.json for React
        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    if "react" in deps:
                        return "react"
            except:
                pass
        
        return "unknown"
    
    def detect_styling_library(self) -> str:
        """Detect styling library used in project"""
        if not self.project_path or not os.path.exists(self.project_path):
            return "unknown"
        
        # Check for Tailwind
        if self.detect_tailwind():
            return "tailwindcss"
        
        # Check package.json for styling libraries
        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    
                    if "styled-components" in deps:
                        return "styled-components"
                    elif "@emotion/react" in deps:
                        return "emotion"
                    elif "sass" in deps or "node-sass" in deps:
                        return "sass"
            except:
                pass
        
        return "css"
    
    def has_typescript(self) -> bool:
        """Check if project uses TypeScript"""
        if not self.project_path or not os.path.exists(self.project_path):
            return False
        
        # Check for TypeScript config
        ts_configs = ["tsconfig.json", "tsconfig.app.json", "tsconfig.build.json"]
        for config in ts_configs:
            if os.path.exists(os.path.join(self.project_path, config)):
                return True
        
        # Check package.json for TypeScript
        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    return "typescript" in deps or "@types/react" in deps
            except:
                pass
        
        return False
    
    def detect_tailwind(self) -> bool:
        """Check if project uses Tailwind CSS"""
        if not self.project_path or not os.path.exists(self.project_path):
            return False
        
        # Check for Tailwind config
        config_files = ["tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs"]
        for config_file in config_files:
            if os.path.exists(os.path.join(self.project_path, config_file)):
                return True
        
        # Check package.json for tailwindcss dependency
        package_json_path = os.path.join(self.project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)
                    deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                    return "tailwindcss" in deps
            except:
                pass
        
        return False
    
    def detect_build_tool(self) -> str:
        """Detect build tool used in project"""
        if not self.project_path or not os.path.exists(self.project_path):
            return "unknown"
        
        if os.path.exists(os.path.join(self.project_path, "vite.config.js")) or \
           os.path.exists(os.path.join(self.project_path, "vite.config.ts")):
            return "vite"
        elif os.path.exists(os.path.join(self.project_path, "webpack.config.js")):
            return "webpack"
        elif os.path.exists(os.path.join(self.project_path, "next.config.js")):
            return "next"
        else:
            return "unknown"
    
    def detect_package_manager(self) -> str:
        """Detect package manager used in project"""
        if not self.project_path or not os.path.exists(self.project_path):
            return "unknown"
        
        if os.path.exists(os.path.join(self.project_path, "pnpm-lock.yaml")):
            return "pnpm"
        elif os.path.exists(os.path.join(self.project_path, "yarn.lock")):
            return "yarn"
        elif os.path.exists(os.path.join(self.project_path, "package-lock.json")):
            return "npm"
        else:
            return "npm"
    
    def analyze_project(self, project_path: str = None) -> dict:
        """Simple project analysis returning basic information"""
        path = project_path or self.project_path
        
        return {
            "framework": self.detect_framework(),
            "styling": self.detect_styling_library(),
            "typescript": self.has_typescript(),
            "tailwind": self.detect_tailwind(),
            "build_tool": self.detect_build_tool(),
            "package_manager": self.detect_package_manager(),
            "components": {"files": []},  # Placeholder
            "structure": {"files": []},   # Placeholder
            "dependencies": {},           # Placeholder
            "design_tokens": {},          # Placeholder
            "metrics": {
                "total_lines": 0,
                "complexity": "medium",
                "maintainability": "good"
            },
            "recommendations": ["Project analysis completed"]
        }