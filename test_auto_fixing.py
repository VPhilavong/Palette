#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'src')

from palette.quality.validator import ComponentValidator

# Test code with obvious issues that should be auto-fixed
test_code = '''import React from "react";

const TestComponent = () => {
  return (
    <button className="bg-blue text-smline-height">
      Test
    </button>
  );
};

export default TestComponent;'''

print("🧪 Testing Auto-Fixing System")
print("=" * 50)

# Initialize validator
project_path = "/home/vphilavong/Projects/Palette/test/test_repo/landing_page"
validator = ComponentValidator(project_path)

print(f"📁 Project path: {project_path}")
print(f"📄 Test code has invalid classes: bg-blue, text-smline-height")
print()

# Run validation
report = validator.validate_component(test_code, "components/Test.tsx")

print(f"📊 Quality Score: {report.score:.1f}/100")
print(f"🔍 Issues found: {len(report.issues)}")

for i, issue in enumerate(report.issues[:5], 1):  # Show first 5 issues
    print(f"  {i}. [{issue.level.value}] {issue.category}: {issue.message}")
    if hasattr(issue, 'auto_fixable'):
        print(f"     Auto-fixable: {issue.auto_fixable}")

print()

# Test auto-fixing
print("🔧 Testing Auto-Fixing:")
fixed_code, fixes_applied = validator.auto_fix_component(test_code, report)

print(f"✅ Fixes applied: {len(fixes_applied)}")
for fix in fixes_applied:
    print(f"  • {fix}")

if fixes_applied:
    print()
    print("📝 Fixed code:")
    print("-" * 30)
    print(fixed_code)
    print("-" * 30)
else:
    print()
    print("❌ No fixes were applied - this is the problem!")
    
    print("\n🔍 Debugging Auto-Fixers:")
    
    # Test individual auto-fixers
    from palette.quality.validator import TypeScriptAutoFixer, FormatAutoFixer, ImportAutoFixer, ESLintAutoFixer
    
    fixers = [
        ("TypeScript", TypeScriptAutoFixer(project_path)),
        ("Format", FormatAutoFixer(project_path)), 
        ("Import", ImportAutoFixer(project_path)),
        ("ESLint", ESLintAutoFixer())
    ]
    
    for name, fixer in fixers:
        can_fix = fixer.can_fix_issues(report.issues)
        print(f"  {name}AutoFixer can_fix_issues: {can_fix}")
        
        if can_fix:
            try:
                code, applied = fixer.fix(test_code, report.issues)
                print(f"    -> Applied {len(applied)} fixes: {applied}")
            except Exception as e:
                print(f"    -> Error: {e}")