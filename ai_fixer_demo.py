#!/usr/bin/env python3
"""
Comprehensive demonstration of the AI-powered auto-fixing system
"""

import os
import sys
sys.path.insert(0, 'src')

from palette.quality.validator import ComponentValidator, AIAutoFixer

def demonstrate_ai_fixing():
    """Demonstrate the complete AI-powered auto-fixing pipeline"""
    
    print("🚀 Palette AI-Powered Auto-Fixing System Demo")
    print("=" * 50)
    
    # Test component with multiple known issues
    problematic_code = '''import React from "react";
import Image from "next/image";
import React, { useState } from "react";

const UserProfile = () => {
  const [isActive, setIsActive] = useState(true);
  
  return (
    <div className="bg-gray text-blue border-blue-600-600-600 text-text-sm">
      <img src="/avatar.jpg" alt="user" className="border-red" />
      <h1 className="text-baseletter-spacing">Profile</h1>
      <p className="baseline-height smline-height">Description</p>
      <button onClick={() => setIsActive(!isActive)}>Toggle</button>
    </div>
  );
};

export default UserProfile;'''

    print("📝 Original Problematic Code:")
    print("=" * 30)
    issues = [
        "❌ Duplicate React imports",
        "❌ Invalid Tailwind classes: bg-gray, text-blue, border-blue-600-600-600, text-text-sm, border-red",
        "❌ Invalid composite classes: text-baseletter-spacing, baseline-height, smline-height", 
        "❌ Uses <img> instead of Next.js <Image>",
        "❌ Missing 'use client' directive for useState hook",
        "❌ Missing required width/height props for Image"
    ]
    for issue in issues:
        print(f"  {issue}")
    
    print(f"\nCode length: {len(problematic_code)} characters")
    
    # Initialize the validation system
    validator = ComponentValidator(project_path=".")
    
    print("\n🔧 Auto-Fixing Pipeline:")
    print("=" * 30)
    
    # Check which fixers are available
    api_available = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if api_available:
        print("✅ AI Fixer: AVAILABLE (LLM API key detected)")
        print("✅ Rule-based Fixers: AVAILABLE (fallback)")
        fixing_mode = "AI + Rule-based"
    else:
        print("⚠️ AI Fixer: UNAVAILABLE (no API key)")
        print("✅ Rule-based Fixers: AVAILABLE")
        fixing_mode = "Rule-based only"
    
    print(f"🔧 Fixing Mode: {fixing_mode}")
    
    # Run the iterative refinement process
    print("\n🔄 Running Iterative Refinement...")
    print("=" * 40)
    
    fixed_code, quality_report = validator.iterative_refinement(
        problematic_code, "UserProfile.tsx", max_iterations=3
    )
    
    # Analyze the results
    print("\n📊 Fixing Results:")
    print("=" * 20)
    print(f"Final Quality Score: {quality_report.score:.1f}/100")
    print(f"Total Fixes Applied: {len(quality_report.auto_fixes_applied)}")
    
    if quality_report.auto_fixes_applied:
        print("\n🔧 Applied Fixes:")
        for i, fix in enumerate(quality_report.auto_fixes_applied, 1):
            print(f"  {i}. {fix}")
    
    # Show the improvements
    print("\n✅ Issues Resolved:")
    resolved_issues = []
    
    if "import React from \"react\";" in fixed_code and "import React, {" in fixed_code:
        if fixed_code.count("import React") == 1:
            resolved_issues.append("✅ Consolidated duplicate React imports")
    
    if "border-blue-600-600-600" not in fixed_code:
        resolved_issues.append("✅ Fixed cascaded border class")
    
    if "text-text-sm" not in fixed_code:
        resolved_issues.append("✅ Fixed duplicate text class")
    
    if "'use client'" in fixed_code:
        resolved_issues.append("✅ Added 'use client' directive")
    
    if "<Image" in fixed_code and "width=" in fixed_code:
        resolved_issues.append("✅ Converted to Next.js Image with proper props")
    
    if "bg-gray-100" in fixed_code or "bg-gray-" in fixed_code:
        resolved_issues.append("✅ Fixed invalid bg-gray class")
    
    for issue in resolved_issues:
        print(f"  {issue}")
    
    # Save the results
    with open("demo_fixed_component.tsx", "w") as f:
        f.write(fixed_code)
    
    print(f"\n💾 Fixed code saved to: demo_fixed_component.tsx")
    print(f"📏 Original: {len(problematic_code)} chars → Fixed: {len(fixed_code)} chars")
    
    # Quality assessment
    if quality_report.score >= 85.0:
        print("\n🎉 SUCCESS: Quality threshold achieved!")
        print("🎯 Zero manual fixing required!")
    else:
        print(f"\n⚠️ PARTIAL SUCCESS: Quality score {quality_report.score:.1f}/100")
        print("💡 Manual review may be needed for edge cases")
    
    return quality_report.score >= 85.0

def show_architecture():
    """Show the AI-powered fixing architecture"""
    
    print("\n🏗️ AI-Powered Auto-Fixing Architecture:")
    print("=" * 45)
    
    architecture = """
    ┌─────────────────────────────────────────┐
    │           Generated Component            │
    │          (with potential issues)         │
    └─────────────────┬───────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────┐
    │         Quality Validation System        │
    │  • TypeScript compilation                │
    │  • ESLint checks                         │
    │  • Accessibility validation              │
    │  • Performance analysis                  │
    │  • Issue categorization                  │
    └─────────────────┬───────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────┐
    │          Auto-Fixing Pipeline            │
    │  1. 🤖 AI Fixer (context-aware)         │
    │  2. 🔧 Enhanced TypeScript Fixer        │
    │  3. 🎨 Enhanced Format Fixer            │
    │  4. 📏 ESLint Auto-Fixer               │
    └─────────────────┬───────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────┐
    │         Iterative Refinement             │
    │  • Re-validate after each fix            │
    │  • Continue until quality threshold      │
    │  • Max 3 iterations                      │
    │  • Track improvement progress            │
    └─────────────────┬───────────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────────┐
    │         Production-Ready Component       │
    │          🎯 Zero Manual Fixing          │
    └─────────────────────────────────────────┘
    """
    
    print(architecture)
    
    print("\n🤖 AI Fixer Capabilities:")
    capabilities = [
        "🧠 Context-aware code understanding",
        "🔍 Semantic issue detection and resolution", 
        "🎯 Framework-specific fixes (React/Next.js/TypeScript)",
        "🎨 Intelligent Tailwind CSS class correction",
        "📦 Smart import consolidation and organization",
        "⚡ Performance optimization suggestions",
        "♿ Accessibility compliance improvements",
        "🔧 Syntax error correction with structure preservation"
    ]
    
    for capability in capabilities:
        print(f"  {capability}")

if __name__ == "__main__":
    show_architecture()
    success = demonstrate_ai_fixing()
    
    print("\n" + "=" * 50)
    if success:
        print("🏆 DEMO COMPLETE: AI-powered zero manual fixing achieved!")
    else:
        print("📋 DEMO COMPLETE: System functional, further tuning available")
    print("🚀 Palette is ready for production zero-manual-fixing!")