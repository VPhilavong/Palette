#!/usr/bin/env python3
"""
Fix the double backslashes in the validator regex patterns
"""

# Read the validator file
with open('src/palette/quality/validator.py', 'r') as f:
    content = f.read()

# Fix double backslashes in regex patterns
fixes = [
    (r'r\'\\\\b', r'r\'\b'),  # Fix \\b -> \b
]

for old, new in fixes:
    content = content.replace(old, new)

# Also fix the specific patterns manually
patterns_to_fix = [
    "r'\\\\bbg-gray-100-100-100\\\\b'",
    "r'\\\\btext-gray-600-600-600\\\\b'", 
    "r'\\\\btext-gray-600-600-900\\\\b'",
    "r'\\\\bbg-emerald-600-600-600\\\\b'",
    "r'\\\\btext-emerald-600-600-600\\\\b'",
    "r'\\\\bbg-blue-600-600-600\\\\b'",
    "r'\\\\btext-blue-600-600-600\\\\b'",
    "r'\\\\bbg-indigo-600-600-600\\\\b'",
    "r'\\\\btext-indigo-600-600-600\\\\b'",
    "r'\\\\bbg-sky-500-500-500\\\\b'",
    "r'\\\\btext-baseletter-spacing\\\\b'",
    "r'\\\\bbaseline-height\\\\b'",
    "r'\\\\bsmline-height\\\\b'",
]

for pattern in patterns_to_fix:
    fixed_pattern = pattern.replace('\\\\b', '\\b')
    content = content.replace(pattern, fixed_pattern)

# Also fix the rf patterns
content = content.replace("rf'\\\\b{re.escape(invalid_class)}(?!-[0-9])\\\\b'", "rf'\\b{re.escape(invalid_class)}(?!-[0-9])\\b'")
content = content.replace("rf'\\\\b{re.escape(invalid_class)}\\\\b'", "rf'\\b{re.escape(invalid_class)}\\b'")

# Write back the fixed file
with open('src/palette/quality/validator.py', 'w') as f:
    f.write(content)

print("✅ Fixed double backslashes in regex patterns")