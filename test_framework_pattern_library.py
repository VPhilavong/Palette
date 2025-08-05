#!/usr/bin/env python3
"""
Test suite for FrameworkPatternLibrary with modular knowledge system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from palette.generation.framework_pattern_library import (
    FrameworkPatternLibrary,
    PatternSearchQuery,
    PatternType,
    PatternComplexity
)
from palette.intelligence.framework_detector import Framework
from palette.intelligence.styling_analyzer import StylingSystem


def test_pattern_library_initialization():
    """Test that the pattern library initializes correctly."""
    print("🧪 Testing FrameworkPatternLibrary initialization...")
    
    library = FrameworkPatternLibrary()
    
    # Verify patterns were loaded
    assert len(library.patterns) > 0, "Should load built-in patterns"
    
    # Verify indices were built
    assert len(library.framework_index) > 0, "Should build framework index"
    assert Framework.REACT in library.framework_index, "Should index React patterns"
    
    # Print stats
    stats = library.get_library_stats()
    print(f"   Loaded {stats['total_patterns']} patterns")
    print(f"   Frameworks: {list(stats['frameworks'].keys())}")
    print(f"   Pattern types: {list(stats['pattern_types'].keys())}")
    
    print("   ✅ Pattern library initialization test passed!")


def test_pattern_search():
    """Test pattern search functionality."""
    print("🧪 Testing pattern search...")
    
    library = FrameworkPatternLibrary()
    
    # Test 1: Search for React + Chakra UI patterns
    query = PatternSearchQuery(
        framework=Framework.REACT,
        styling_system=StylingSystem.CHAKRA_UI,
        pattern_types=[PatternType.COMPONENT]
    )
    
    results = library.search_patterns(query)
    assert len(results) > 0, "Should find React + Chakra UI component patterns"
    
    chakra_button = next((p for p in results if 'button' in p.id), None)
    assert chakra_button is not None, "Should find Chakra UI button pattern"
    assert chakra_button.framework == Framework.REACT, "Should match framework"
    assert chakra_button.styling_system == StylingSystem.CHAKRA_UI, "Should match styling system"
    
    print(f"   Found {len(results)} React + Chakra UI component patterns")
    print(f"   Button pattern: {chakra_button.name}")
    
    # Test 2: Search for form patterns
    form_query = PatternSearchQuery(
        pattern_types=[PatternType.FORM],
        keywords=['validation']
    )
    
    form_results = library.search_patterns(form_query)
    assert len(form_results) > 0, "Should find form patterns with validation"
    
    print(f"   Found {len(form_results)} form patterns with validation")
    
    # Test 3: Search by tags
    tag_query = PatternSearchQuery(tags={'button', 'chakra'})
    tag_results = library.search_patterns(tag_query)
    assert len(tag_results) > 0, "Should find patterns by tags"
    
    print(f"   Found {len(tag_results)} patterns with 'button' and 'chakra' tags")
    
    print("   ✅ Pattern search test passed!")


def test_pattern_recommendations():
    """Test pattern recommendation system."""
    print("🧪 Testing pattern recommendations...")
    
    library = FrameworkPatternLibrary()
    
    # Test 1: Button recommendation
    button_recommendations = library.get_recommended_patterns(
        user_request="Create a button component with loading state",
        framework=Framework.REACT,
        styling_system=StylingSystem.CHAKRA_UI,
        max_results=3
    )
    
    assert len(button_recommendations) > 0, "Should recommend button patterns"
    
    # Should prioritize Chakra UI button pattern
    top_recommendation = button_recommendations[0]
    assert 'button' in top_recommendation.id.lower(), "Top recommendation should be button-related"
    
    print(f"   Button recommendations: {len(button_recommendations)}")
    print(f"   Top recommendation: {top_recommendation.name}")
    
    # Test 2: Form recommendation
    form_recommendations = library.get_recommended_patterns(
        user_request="I need a login form with validation",
        framework=Framework.REACT,
        styling_system=StylingSystem.CHAKRA_UI,
        max_results=3
    )
    
    assert len(form_recommendations) > 0, "Should recommend form patterns"
    
    # Should include form patterns
    has_form_pattern = any('form' in p.id.lower() for p in form_recommendations)
    assert has_form_pattern, "Should recommend form patterns for form request"
    
    print(f"   Form recommendations: {len(form_recommendations)}")
    
    # Test 3: Hook recommendation
    hook_recommendations = library.get_recommended_patterns(
        user_request="Custom hook for data fetching",
        framework=Framework.REACT,
        max_results=3
    )
    
    assert len(hook_recommendations) > 0, "Should recommend hook patterns"
    
    # Should include hook patterns
    has_hook_pattern = any(p.pattern_type == PatternType.HOOK for p in hook_recommendations)
    assert has_hook_pattern, "Should recommend hook patterns for hook request"
    
    print(f"   Hook recommendations: {len(hook_recommendations)}")
    
    print("   ✅ Pattern recommendations test passed!")


def test_framework_specific_patterns():
    """Test framework-specific pattern retrieval."""
    print("🧪 Testing framework-specific patterns...")
    
    library = FrameworkPatternLibrary()
    
    # Test React patterns
    react_patterns = library.get_patterns_by_framework(Framework.REACT)
    assert len(react_patterns) > 0, "Should have React patterns"
    
    # Verify all patterns are React-based
    for pattern in react_patterns:
        assert pattern.framework == Framework.REACT, "All patterns should be React-based"
    
    print(f"   React patterns: {len(react_patterns)}")
    
    # Test Next.js patterns
    nextjs_patterns = library.get_patterns_by_framework(Framework.NEXT_JS)
    assert len(nextjs_patterns) > 0, "Should have Next.js patterns"
    
    # Should include API route pattern
    has_api_pattern = any('api' in p.id.lower() for p in nextjs_patterns)
    assert has_api_pattern, "Should have API route patterns for Next.js"
    
    print(f"   Next.js patterns: {len(nextjs_patterns)}")
    
    print("   ✅ Framework-specific patterns test passed!")


def test_styling_system_patterns():
    """Test styling system specific patterns."""
    print("🧪 Testing styling system patterns...")
    
    library = FrameworkPatternLibrary()
    
    # Test Chakra UI patterns
    chakra_patterns = library.get_patterns_by_styling_system(StylingSystem.CHAKRA_UI)
    assert len(chakra_patterns) > 0, "Should have Chakra UI patterns"
    
    # Verify all patterns use Chakra UI
    for pattern in chakra_patterns:
        assert pattern.styling_system == StylingSystem.CHAKRA_UI, "All patterns should use Chakra UI"
    
    print(f"   Chakra UI patterns: {len(chakra_patterns)}")
    
    # Test Tailwind patterns
    tailwind_patterns = library.get_patterns_by_styling_system(StylingSystem.TAILWIND)
    assert len(tailwind_patterns) > 0, "Should have Tailwind patterns"
    
    # Verify all patterns use Tailwind
    for pattern in tailwind_patterns:
        assert pattern.styling_system == StylingSystem.TAILWIND, "All patterns should use Tailwind"
    
    print(f"   Tailwind patterns: {len(tailwind_patterns)}")
    
    print("   ✅ Styling system patterns test passed!")


def test_pattern_content_quality():
    """Test that patterns contain high-quality content."""
    print("🧪 Testing pattern content quality...")
    
    library = FrameworkPatternLibrary()
    
    # Test Chakra button pattern quality
    chakra_button = library.get_pattern_by_id("react_chakra_button")
    assert chakra_button is not None, "Should find Chakra button pattern"
    
    # Verify pattern completeness
    assert len(chakra_button.examples) > 0, "Should have code examples"
    assert len(chakra_button.best_practices) > 0, "Should have best practices"
    assert len(chakra_button.common_mistakes) > 0, "Should have common mistakes"
    assert len(chakra_button.tags) > 0, "Should have tags"
    
    # Verify example quality
    example = chakra_button.examples[0]
    assert len(example.code) > 100, "Code example should be substantial"
    assert 'React.FC' in example.code, "Should use TypeScript React patterns"
    assert '@chakra-ui/react' in example.dependencies, "Should specify Chakra UI dependency"
    
    print(f"   Button pattern has {len(chakra_button.examples)} examples")
    print(f"   Best practices: {len(chakra_button.best_practices)}")
    print(f"   Common mistakes: {len(chakra_button.common_mistakes)}")
    
    # Test form pattern quality
    chakra_form = library.get_pattern_by_id("react_chakra_form")
    assert chakra_form is not None, "Should find Chakra form pattern"
    assert chakra_form.complexity == PatternComplexity.INTERMEDIATE, "Form should be intermediate complexity"
    
    form_example = chakra_form.examples[0]
    assert 'useForm' in form_example.code, "Form should use react-hook-form"
    assert 'FormControl' in form_example.code, "Should use Chakra UI form components"
    assert 'validation' in form_example.description.lower(), "Should mention validation"
    
    print(f"   Form pattern complexity: {chakra_form.complexity.value}")
    print(f"   Form example length: {len(form_example.code)} characters")
    
    print("   ✅ Pattern content quality test passed!")


def test_pattern_integration():
    """Test pattern library integration with other components."""
    print("🧪 Testing pattern library integration...")
    
    library = FrameworkPatternLibrary()
    
    # Simulate integration with configuration system
    configuration_frameworks = [Framework.REACT, Framework.NEXT_JS]
    configuration_styling = [StylingSystem.CHAKRA_UI, StylingSystem.TAILWIND]
    
    for framework in configuration_frameworks:
        for styling in configuration_styling:
            if styling == StylingSystem.CHAKRA_UI and framework == Framework.NEXT_JS:
                continue  # Skip incompatible combinations for this test
                
            # Get patterns for this configuration
            query = PatternSearchQuery(
                framework=framework,
                styling_system=styling,
                pattern_types=[PatternType.COMPONENT]
            )
            
            patterns = library.search_patterns(query)
            
            if framework == Framework.REACT and styling == StylingSystem.CHAKRA_UI:
                assert len(patterns) >= 1, f"Should have patterns for {framework.value} + {styling.value}"
            
            print(f"   {framework.value} + {styling.value}: {len(patterns)} patterns")
    
    # Test recommendation integration - only test for patterns that exist
    test_requests = [
        "Create a responsive button component",
        "Build a form with validation", 
        "Custom hook for API calls"
    ]
    
    for request in test_requests:
        # Use different styling system for hook requests since hooks are framework-agnostic
        styling = None if 'hook' in request.lower() else StylingSystem.CHAKRA_UI
        
        recommendations = library.get_recommended_patterns(
            user_request=request,
            framework=Framework.REACT,
            styling_system=styling,
            max_results=2
        )
        
        assert len(recommendations) > 0, f"Should provide recommendations for: {request}"
        print(f"   '{request}': {len(recommendations)} recommendations")
    
    print("   ✅ Pattern library integration test passed!")


def main():
    """Run all framework pattern library tests."""
    print("🚀 Starting Framework Pattern Library Tests")
    print("=" * 70)
    
    try:
        test_pattern_library_initialization()
        test_pattern_search()
        test_pattern_recommendations() 
        test_framework_specific_patterns()
        test_styling_system_patterns()
        test_pattern_content_quality()
        test_pattern_integration()
        
        print("=" * 70)
        print("🎉 ALL FRAMEWORK PATTERN LIBRARY TESTS PASSED!")
        print("✅ Pattern library loads built-in patterns correctly")
        print("✅ Search functionality works with multiple criteria")
        print("✅ Recommendation engine provides contextual suggestions")
        print("✅ Framework and styling system filtering working")
        print("✅ Pattern content meets quality standards")
        print("✅ Integration with configuration system verified")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()