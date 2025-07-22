#!/usr/bin/env python3
"""
Test regex patterns for Tailwind class fixing
"""
import re

# Test code with invalid classes
test_code = '''
<div className="bg-gray text-blue baseline-height smline-height border-gray">
  <p className="text-gray">Hello</p>
</div>
'''

print("Test code:")
print(test_code)
print()

# Test patterns
patterns = [
    (r'\bbaseline-height\b', 'leading-normal'),
    (r'\bsmline-height\b', 'text-sm'),
    (r'\bbg-gray(?!-[0-9])\b', 'bg-gray-100'),
    (r'\btext-gray(?!-[0-9])\b', 'text-gray-600'),
    (r'\bborder-gray(?!-[0-9])\b', 'border-gray-300'),
    (r'\btext-blue(?!-[0-9])\b', 'text-blue-600'),
]

fixed_code = test_code
for pattern, replacement in patterns:
    if re.search(pattern, fixed_code):
        print(f"✅ Found and fixing: {pattern} -> {replacement}")
        fixed_code = re.sub(pattern, replacement, fixed_code)
    else:
        print(f"❌ Not found: {pattern}")

print("\nFixed code:")
print(fixed_code)