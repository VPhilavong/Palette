#!/usr/bin/env python3
"""
Basic integration test for critical framework detection fixes.
Tests the StylingSystemAnalyzer and ChakraUIGenerationStrategy.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from palette.intelligence.styling_analyzer import StylingSystemAnalyzer, StylingSystem
from palette.intelligence.configuration_hub import ConfigurationIntelligenceHub
from palette.generation.strategies.registry import get_strategy_registry
from palette.generation.strategies.chakra_ui_strategy import ChakraUIGenerationStrategy


def create_test_chakra_project(temp_dir: Path):
    """Create a test Chakra UI project structure."""
    
    # Create package.json with Chakra UI dependencies
    package_json = {
        "name": "test-chakra-project",
        "version": "1.0.0",
        "dependencies": {
            "react": "^18.0.0",
            "react-dom": "^18.0.0",
            "@chakra-ui/react": "^2.8.0",
            "@emotion/react": "^11.0.0",
            "@emotion/styled": "^11.0.0"
        },
        "devDependencies": {
            "typescript": "^5.0.0",
            "@types/react": "^18.0.0"
        }
    }
    
    with open(temp_dir / "package.json", 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # Create a sample component using Chakra UI
    component_dir = temp_dir / "src" / "components"
    component_dir.mkdir(parents=True, exist_ok=True)
    
    sample_component = '''import React from 'react';
import { Box, Button, Text, Flex } from '@chakra-ui/react';

interface ButtonComponentProps {
  children: React.ReactNode;
  colorScheme?: string;
  variant?: string;
}

const ButtonComponent: React.FC<ButtonComponentProps> = ({ 
  children, 
  colorScheme = "blue", 
  variant = "solid" 
}) => {
  return (
    <Flex direction="column" p={4}>
      <Text fontSize="lg" mb={4}>
        Chakra UI Button Component
      </Text>
      <Button colorScheme={colorScheme} variant={variant}>
        {children}
      </Button>
    </Flex>
  );
};

export default ButtonComponent;
'''
    
    with open(component_dir / "ButtonComponent.tsx", 'w') as f:
        f.write(sample_component)
    
    return str(temp_dir)


def test_styling_system_analyzer():
    """Test the StylingSystemAnalyzer with Chakra UI project."""
    print("🧪 Testing StylingSystemAnalyzer...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_test_chakra_project(temp_path)
        
        # Initialize analyzer
        analyzer = StylingSystemAnalyzer()
        
        # Analyze the project
        result = analyzer.comprehensive_scan(project_path)
        
        # Verify results
        print(f"   Primary System: {result.primary_system.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Conflicts: {len(result.conflicts_detected)}")
        print(f"   Recommendations: {len(result.recommendations)}")
        
        # Assert Chakra UI is detected
        assert result.primary_system == StylingSystem.CHAKRA_UI, f"Expected Chakra UI, got {result.primary_system}"
        assert result.confidence > 0.5, f"Low confidence: {result.confidence}"
        
        print("   ✅ StylingSystemAnalyzer test passed!")
        return result


def test_configuration_intelligence_hub():
    """Test the ConfigurationIntelligenceHub."""
    print("🧪 Testing ConfigurationIntelligenceHub...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_test_chakra_project(temp_path)
        
        # Initialize hub
        hub = ConfigurationIntelligenceHub()
        
        # Analyze configuration
        config = hub.analyze_configuration(project_path)
        
        print(f"   Framework: {config.framework.value}")
        print(f"   Styling System: {config.styling_system.value}")
        print(f"   Component Library: {config.component_library.value}")
        print(f"   TypeScript: {config.typescript}")
        print(f"   Confidence: {config.confidence_score:.2f}")
        print(f"   Strategy: {config.generation_strategy}")
        
        # Verify results
        assert config.styling_system == StylingSystem.CHAKRA_UI, f"Expected Chakra UI, got {config.styling_system}"
        assert config.typescript == True, "TypeScript should be detected"
        assert "ChakraUI" in config.generation_strategy, f"Expected ChakraUI-related strategy, got {config.generation_strategy}"
        
        print("   ✅ ConfigurationIntelligenceHub test passed!")
        return config


def test_strategy_registry():
    """Test the GenerationStrategyRegistry."""
    print("🧪 Testing GenerationStrategyRegistry...")
    
    registry = get_strategy_registry()
    
    # Test strategy listing
    strategies = registry.list_strategies()
    print(f"   Registered strategies: {len(strategies)}")
    
    for strategy in strategies:
        print(f"   - {strategy['name']}: {strategy['supported_styling_systems']}")
    
    # Test coverage analysis
    coverage = registry.validate_strategy_coverage()
    print(f"   Coverage: {coverage['coverage_percentage']:.1f}%")
    print(f"   Covered: {coverage['covered_combinations']}/{coverage['total_combinations']}")
    
    # Test recommendations
    recommendations = registry.recommend_strategy_implementation()
    print(f"   Implementation recommendations: {len(recommendations)}")
    for rec in recommendations[:3]:
        print(f"   - {rec}")
    
    print("   ✅ GenerationStrategyRegistry test passed!")


def test_chakra_ui_strategy():
    """Test the ChakraUIGenerationStrategy."""
    print("🧪 Testing ChakraUIGenerationStrategy...")
    
    strategy = ChakraUIGenerationStrategy()
    
    # Test basic component generation (without LLM)
    prompt = "Create a simple button component"
    context = {
        'project_path': '/test',
        'styling_system': 'chakra-ui',
        'framework': 'react'
    }
    
    # This will use the mock generation since no LLM client is provided
    result = strategy.generate_component(prompt, context)
    
    print(f"   Strategy: {result.strategy_used}")
    print(f"   Quality Score: {result.quality_score:.2f}")
    print(f"   Validation Issues: {len(result.validation_issues)}")
    print(f"   Auto Fixes: {len(result.auto_fixes_applied)}")
    
    # Verify the generated code doesn't contain Tailwind classes
    assert 'bg-blue-500' not in result.code, "Tailwind classes found in Chakra UI code!"
    assert '@chakra-ui/react' in result.code, "Missing Chakra UI imports!"
    assert 'Button' in result.code, "Missing Chakra UI Button component!"
    
    print("   ✅ ChakraUIGenerationStrategy test passed!")
    return result


def test_integration():
    """Test full integration of all components."""
    print("🧪 Testing Full Integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_path = create_test_chakra_project(temp_path)
        
        # Step 1: Analyze configuration
        hub = ConfigurationIntelligenceHub()
        config = hub.analyze_configuration(project_path)
        
        # Step 2: Get appropriate strategy
        registry = get_strategy_registry()
        strategy = registry.get_strategy(config)
        
        assert strategy is not None, "No strategy found for configuration!"
        assert isinstance(strategy, ChakraUIGenerationStrategy), f"Wrong strategy type: {type(strategy)}"
        
        # Step 3: Generate component with strategy
        prompt = "Create a responsive card component with title and description"
        context = {
            'project_path': project_path,
            'styling_system': config.styling_system.value,
            'framework': config.framework.value
        }
        
        result = strategy.generate_component(prompt, context)
        
        print(f"   Generated component with {result.strategy_used} strategy")
        print(f"   Quality score: {result.quality_score:.2f}")
        print(f"   Issues resolved: {len(result.auto_fixes_applied)}")
        
        # Verify no Tailwind classes in Chakra UI code
        assert 'className="bg-' not in result.code, "CRITICAL: Tailwind classes in Chakra UI code!"
        assert 'className="text-' not in result.code, "CRITICAL: Tailwind classes in Chakra UI code!"
        assert 'className="p-' not in result.code, "CRITICAL: Tailwind classes in Chakra UI code!"
        
        # Verify Chakra UI patterns
        assert '@chakra-ui/react' in result.code, "Missing Chakra UI imports!"
        assert any(comp in result.code for comp in ['Box', 'Button', 'Text']), "Missing Chakra UI components!"
        
        print("   ✅ Full integration test passed!")
        print("   🎉 CRITICAL FIXES WORKING: No Tailwind classes in Chakra UI code!")
        
        return result


def main():
    """Run all tests."""
    print("🚀 Starting Critical Fixes Integration Tests")
    print("=" * 60)
    
    try:
        # Test individual components
        test_styling_system_analyzer()
        print()
        
        test_configuration_intelligence_hub()
        print()
        
        test_strategy_registry() 
        print()
        
        test_chakra_ui_strategy()
        print()
        
        # Test full integration
        test_integration()
        print()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Critical framework detection fixes are working correctly")
        print("✅ Chakra UI strategy prevents Tailwind class generation")
        print("✅ Configuration intelligence provides accurate analysis")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()