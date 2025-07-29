"""
Component Pattern Analyzer using Remote MCP (DeepWiki)
Learns from popular UI libraries to generate better components
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI
import json


@dataclass
class ComponentPattern:
    """Represents a component pattern learned from repositories."""
    component_type: str
    repository: str
    patterns: List[str]
    best_practices: List[str]
    code_examples: Optional[str] = None


class PatternAnalyzer:
    """Analyzes component patterns from popular UI libraries using DeepWiki."""
    
    # Repository mappings for different component types
    COMPONENT_REPOS = {
        "button": [
            "shadcn/ui",
            "mui/material-ui", 
            "ant-design/ant-design",
            "chakra-ui/chakra-ui",
            "tailwindlabs/headlessui"
        ],
        "form": [
            "react-hook-form/react-hook-form",
            "formik/formik",
            "shadcn/ui",
            "ant-design/ant-design"
        ],
        "modal": [
            "tailwindlabs/headlessui",
            "radix-ui/primitives",
            "mui/material-ui",
            "arco-design/arco-design"
        ],
        "table": [
            "tanstack/table",
            "ag-grid/ag-grid",
            "ant-design/ant-design",
            "shadcn/ui"
        ],
        "navigation": [
            "vercel/next.js",
            "remix-run/remix",
            "shadcn/ui",
            "ant-design/ant-design"
        ],
        "card": [
            "shadcn/ui",
            "mui/material-ui",
            "tailwindlabs/tailwindui-react",
            "mantine-dev/mantine"
        ],
        "dropdown": [
            "radix-ui/primitives",
            "tailwindlabs/headlessui", 
            "react-select/react-select",
            "downshift-js/downshift"
        ]
    }
    
    # Design system repositories from major companies
    DESIGN_SYSTEMS = {
        "google": "material-components/material-components-web",
        "microsoft": "microsoft/fluentui",
        "adobe": "adobe/spectrum-web-components", 
        "ibm": "carbon-design-system/carbon",
        "shopify": "Shopify/polaris",
        "atlassian": "atlassian/atlassian-frontend",
        "github": "primer/react",
        "uber": "uber/baseweb",
        "airbnb": "airbnb/lunar"
    }
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client or OpenAI()
    
    def analyze_component_patterns(
        self, 
        component_type: str,
        specific_repos: Optional[List[str]] = None
    ) -> List[ComponentPattern]:
        """Analyze how top libraries implement a specific component."""
        
        repos = specific_repos or self.COMPONENT_REPOS.get(component_type, ["shadcn/ui"])
        patterns = []
        
        for repo in repos:
            try:
                # Query DeepWiki about this component in this repo
                query = f"""
                Analyze the {component_type} component implementation in {repo}.
                Focus on:
                1. Component structure and composition
                2. Props/API design
                3. Styling approach
                4. Accessibility features
                5. State management patterns
                6. Best practices and patterns used
                """
                
                response = self._query_deepwiki(repo, query)
                
                # Parse the response to extract patterns
                pattern = self._parse_pattern_response(
                    component_type, repo, response
                )
                patterns.append(pattern)
                
            except Exception as e:
                print(f"Failed to analyze {repo}: {e}")
                continue
        
        return patterns
    
    def learn_design_system(self, company: str) -> Dict[str, Any]:
        """Learn design principles and patterns from a company's design system."""
        
        if company not in self.DESIGN_SYSTEMS:
            available = ", ".join(self.DESIGN_SYSTEMS.keys())
            raise ValueError(f"Unknown company. Available: {available}")
        
        repo = self.DESIGN_SYSTEMS[company]
        
        query = f"""
        Analyze the design system and component library of {repo}.
        Extract:
        1. Core design principles
        2. Component naming conventions
        3. Theming and styling approach
        4. Accessibility standards
        5. Component composition patterns
        6. Documentation patterns
        """
        
        response = self._query_deepwiki(repo, query)
        
        return {
            "company": company,
            "repository": repo,
            "principles": self._extract_principles(response),
            "patterns": self._extract_patterns(response),
            "recommendations": self._extract_recommendations(response)
        }
    
    def find_best_implementation(
        self, 
        component_type: str,
        requirements: List[str]
    ) -> Dict[str, Any]:
        """Find the best implementation based on specific requirements."""
        
        # Analyze all relevant repos
        patterns = self.analyze_component_patterns(component_type)
        
        # Score each implementation based on requirements
        scored_patterns = []
        for pattern in patterns:
            score = self._score_pattern(pattern, requirements)
            scored_patterns.append({
                "pattern": pattern,
                "score": score,
                "matching_requirements": self._match_requirements(pattern, requirements)
            })
        
        # Sort by score
        scored_patterns.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "best_match": scored_patterns[0] if scored_patterns else None,
            "all_matches": scored_patterns,
            "recommendation": self._generate_recommendation(scored_patterns, requirements)
        }
    
    def _query_deepwiki(self, repo: str, query: str) -> str:
        """Query DeepWiki about a specific repository."""
        
        response = self.client.responses.create(
            model="gpt-4o",
            tools=[{
                "type": "mcp",
                "server_label": "deepwiki",
                "server_url": "https://mcp.deepwiki.com/mcp",
                "require_approval": "never"
            }],
            input=f"Repository: {repo}\n\n{query}"
        )
        
        return response.output_text
    
    def _parse_pattern_response(
        self, 
        component_type: str,
        repo: str,
        response: str
    ) -> ComponentPattern:
        """Parse DeepWiki response into structured pattern data."""
        
        # Extract patterns using GPT to structure the response
        structured_response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": "Extract component patterns and best practices from the analysis."
            }, {
                "role": "user", 
                "content": f"Component: {component_type}\nRepository: {repo}\n\nAnalysis:\n{response}\n\nExtract: patterns (list), best_practices (list), code_example (optional)"
            }],
            response_format={
                "type": "json_object"
            }
        )
        
        data = json.loads(structured_response.choices[0].message.content)
        
        return ComponentPattern(
            component_type=component_type,
            repository=repo,
            patterns=data.get("patterns", []),
            best_practices=data.get("best_practices", []),
            code_examples=data.get("code_example")
        )
    
    def _score_pattern(
        self,
        pattern: ComponentPattern,
        requirements: List[str]
    ) -> float:
        """Score a pattern based on how well it matches requirements."""
        
        score = 0.0
        pattern_text = " ".join(pattern.patterns + pattern.best_practices)
        
        for req in requirements:
            if req.lower() in pattern_text.lower():
                score += 1.0
        
        # Bonus for popular libraries
        if "shadcn" in pattern.repository:
            score += 0.5
        elif "mui" in pattern.repository or "ant-design" in pattern.repository:
            score += 0.3
            
        return score
    
    def _match_requirements(
        self,
        pattern: ComponentPattern,
        requirements: List[str]
    ) -> List[str]:
        """Find which requirements are matched by this pattern."""
        
        matched = []
        pattern_text = " ".join(pattern.patterns + pattern.best_practices)
        
        for req in requirements:
            if req.lower() in pattern_text.lower():
                matched.append(req)
                
        return matched
    
    def _generate_recommendation(
        self,
        scored_patterns: List[Dict[str, Any]],
        requirements: List[str]
    ) -> str:
        """Generate a recommendation based on analysis."""
        
        if not scored_patterns:
            return "No patterns found for this component type."
        
        best = scored_patterns[0]
        
        return f"""
Based on your requirements: {', '.join(requirements)}

Recommended approach: {best['pattern'].repository}
- Matches {len(best['matching_requirements'])} of {len(requirements)} requirements
- Key patterns: {', '.join(best['pattern'].patterns[:3])}
- Best practices: {', '.join(best['pattern'].best_practices[:3])}

Consider combining patterns from multiple libraries for the best result.
"""
    
    def _extract_principles(self, response: str) -> List[str]:
        """Extract design principles from response."""
        # Simplified extraction - in real implementation, use GPT
        lines = response.split('\n')
        principles = [line.strip('- ') for line in lines if 'principle' in line.lower()]
        return principles[:5] if principles else ["Modern", "Accessible", "Composable"]
    
    def _extract_patterns(self, response: str) -> List[str]:
        """Extract patterns from response."""
        lines = response.split('\n')
        patterns = [line.strip('- ') for line in lines if 'pattern' in line.lower()]
        return patterns[:5] if patterns else ["Component composition", "Prop forwarding"]
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response."""
        lines = response.split('\n')
        recs = [line.strip('- ') for line in lines if any(word in line.lower() for word in ['recommend', 'should', 'best'])]
        return recs[:3] if recs else ["Follow accessibility guidelines"]


# Example usage
if __name__ == "__main__":
    analyzer = PatternAnalyzer()
    
    # Example 1: Analyze button patterns
    print("🔍 Analyzing Button Patterns")
    print("="*60)
    
    button_patterns = analyzer.analyze_component_patterns("button", ["shadcn/ui", "mui/material-ui"])
    for pattern in button_patterns:
        print(f"\n📦 {pattern.repository}")
        print(f"Patterns: {', '.join(pattern.patterns[:3])}")
        print(f"Best Practices: {', '.join(pattern.best_practices[:3])}")
    
    # Example 2: Find best implementation
    print("\n\n🎯 Finding Best Modal Implementation")
    print("="*60)
    
    requirements = ["accessible", "animated", "backdrop", "keyboard navigation"]
    best = analyzer.find_best_implementation("modal", requirements)
    print(best["recommendation"])
    
    # Example 3: Learn from a design system
    print("\n\n🎨 Learning from Google's Material Design")
    print("="*60)
    
    google_patterns = analyzer.learn_design_system("google")
    print(f"Principles: {', '.join(google_patterns['principles'])}")
    print(f"Patterns: {', '.join(google_patterns['patterns'])}")