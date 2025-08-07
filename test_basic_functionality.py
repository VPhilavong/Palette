#!/usr/bin/env python3
"""
Basic Functionality Test for Palette
Tests core functionality without requiring server startup
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that core modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        from palette.analysis.context import ProjectAnalyzer
        print("✅ ProjectAnalyzer imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ProjectAnalyzer: {e}")
        return False
    
    try:
        from palette.conversation.conversation_engine import ConversationEngine
        print("✅ ConversationEngine imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ConversationEngine: {e}")
        return False
    
    try:
        from palette.quality.validator import ComponentValidator
        print("✅ ComponentValidator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ComponentValidator: {e}")
        return False
    
    return True

def test_analysis():
    """Test project analysis functionality"""
    print("\n🔍 Testing project analysis...")
    
    try:
        from palette.server.analysis_wrapper import AnalysisWrapper
        
        # Test with the current project
        wrapper = AnalysisWrapper(str(Path(__file__).parent))
        
        framework = wrapper.detect_framework()
        styling = wrapper.detect_styling_library()
        has_ts = wrapper.has_typescript()
        has_tailwind = wrapper.detect_tailwind()
        
        print(f"✅ Framework detection: {framework}")
        print(f"✅ Styling detection: {styling}")
        print(f"✅ TypeScript detection: {has_ts}")
        print(f"✅ Tailwind detection: {has_tailwind}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def test_quality_validation():
    """Test quality validation with sample code"""
    print("\n🔍 Testing quality validation...")
    
    try:
        from palette.quality.validator import ComponentValidator
        
        # Create temporary directory for testing
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = ComponentValidator(temp_dir)
            
            # Test with simple valid component
            simple_component = '''import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
}

export const Button: React.FC<ButtonProps> = ({ children, onClick }) => {
  return (
    <button 
      type="button"
      onClick={onClick}
      className="px-4 py-2 bg-blue-500 text-white rounded"
    >
      {children}
    </button>
  );
};'''
            
            result = validator.validate_code_content(simple_component, "comprehensive")
            
            print(f"✅ Quality validation completed")
            print(f"   Score: {result.get('score', 0)}/100")
            print(f"   Issues: {len(result.get('issues', []))}")
            
            return True
            
    except Exception as e:
        print(f"❌ Quality validation failed: {e}")
        return False

def test_server_modules():
    """Test server module loading"""
    print("\n🔍 Testing server modules...")
    
    try:
        # Test server launcher
        from palette.server.main import app
        print("✅ FastAPI app created successfully")
        
        # Test analysis wrapper
        from palette.server.analysis_wrapper import AnalysisWrapper
        wrapper = AnalysisWrapper("/tmp")
        print("✅ AnalysisWrapper created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Server modules failed: {e}")
        return False

def main():
    """Run basic functionality tests"""
    print("🧪 Palette Basic Functionality Test")
    print("=" * 40)
    
    start_time = time.time()
    
    tests = [
        ("Module Imports", test_imports),
        ("Project Analysis", test_analysis),
        ("Quality Validation", test_quality_validation),
        ("Server Modules", test_server_modules),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 25)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED - {e}")
    
    duration = time.time() - start_time
    
    print("\n" + "=" * 40)
    print("📊 TEST SUMMARY")
    print("=" * 40)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"🎯 Success Rate: {(passed/len(tests)*100):.1f}%")
    print(f"⏱️  Duration: {duration:.2f}s")
    
    if failed == 0:
        print("🎉 All basic functionality tests passed!")
        print("💡 Core Palette modules are working correctly")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed")
        print("💡 Some core functionality issues detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())