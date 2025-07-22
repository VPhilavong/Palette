#!/usr/bin/env python3
"""
Quick fix script to repair the broken Tailwind classes
"""
import re

# Read the broken component
with open('src/components/Component.jsx', 'r') as f:
    content = f.read()

print("Original content has these broken classes:")
broken_classes = re.findall(r'\b\w+-\w+-\d+-\d+-\d+\b', content)
for cls in set(broken_classes):
    print(f"  - {cls}")

# Fix cascaded classes
fixes = [
    (r'\bbg-gray-100-100-100\b', 'bg-gray-100'),
    (r'\btext-gray-600-600-600\b', 'text-gray-600'),
    (r'\btext-gray-600-600-900\b', 'text-gray-900'),
    (r'\bbg-emerald-600-600-600\b', 'bg-emerald-600'),
    (r'\btext-emerald-600-600-600\b', 'text-emerald-600'),
    (r'\bbg-blue-600-600-600\b', 'bg-blue-600'),
    (r'\btext-blue-600-600-600\b', 'text-blue-600'),
    (r'\bbg-indigo-600-600-600\b', 'bg-indigo-600'),
    (r'\btext-indigo-600-600-600\b', 'text-indigo-600'),
    (r'\bbg-sky-500-500-500\b', 'bg-sky-500'),
    (r'\btext-sky-500-500-500\b', 'text-sky-500'),
    (r'\btext-baseletter-spacing\b', 'text-base'),
]

fixed_content = content
fixes_applied = []

for pattern, replacement in fixes:
    if re.search(pattern, fixed_content):
        fixed_content = re.sub(pattern, replacement, fixed_content)
        fixes_applied.append(f"Fixed {pattern} -> {replacement}")

# Also fix the file extension to .tsx and add 'use client' at the top
if not fixed_content.startswith("'use client'"):
    lines = fixed_content.split('\n')
    # Remove any existing 'use client' from middle
    lines = [line for line in lines if "'use client'" not in line]
    # Add at the top
    fixed_content = "'use client';\n\n" + '\n'.join(lines)
    fixes_applied.append("Added 'use client' at top")

# Write the fixed version as .tsx
with open('src/components/UserProfile.tsx', 'w') as f:
    f.write(fixed_content)

print(f"\nApplied {len(fixes_applied)} fixes:")
for fix in fixes_applied:
    print(f"  ✅ {fix}")

print("\n✅ Fixed component saved as src/components/UserProfile.tsx")