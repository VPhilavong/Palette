#!/usr/bin/env python3
"""
Enhanced auto-fixers that can actually fix the issues being generated.
This will replace the basic auto-fixers in validator.py
"""
import re
import subprocess
import tempfile
import os
from typing import Dict, List, Optional, Tuple, Any

# Auto-fixer implementations
class TypeScriptAutoFixer:
    """Automatically fixes TypeScript issues with advanced import resolution and interface generation."""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
    
    def can_fix_issues(self, issues: List) -> bool:
        return True  # Always try to fix TypeScript issues
    
    def fix(self, code: str, issues: List) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # 1. Fix duplicate imports
        fixed_code, duplicate_fixes = self._fix_duplicate_imports(fixed_code)
        fixes_applied.extend(duplicate_fixes)
        
        # 2. Convert to client component if using hooks
        if self._uses_client_features(fixed_code) and not self._is_client_component(fixed_code):
            fixed_code = self._add_use_client(fixed_code)
            fixes_applied.append("Added 'use client' directive for client-side features")
        
        # 3. Add missing Next.js Image import
        if self._needs_next_image_import(fixed_code):
            fixed_code = self._add_next_image_import(fixed_code)
            fixes_applied.append("Added Next.js Image import")
        
        # 4. Remove any types (simple fix)
        if re.search(r':\s*any\b', fixed_code):
            fixed_code = re.sub(r':\s*any\b', '', fixed_code)
            fixes_applied.append("Removed 'any' type annotations")
        
        return fixed_code, fixes_applied
    
    def _fix_duplicate_imports(self, code: str) -> Tuple[str, List[str]]:
        """Fix duplicate import statements."""
        fixes_applied = []
        lines = code.split('\n')
        
        # Find all import lines
        import_lines = []
        non_import_start = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import'):
                import_lines.append(line.strip())
            elif line.strip() and not line.strip().startswith('import'):
                if non_import_start == 0:
                    non_import_start = i
                break
        
        if len(import_lines) <= 1:
            return code, fixes_applied
        
        # Check for duplicate React imports
        react_imports = [line for line in import_lines if "from 'react'" in line or 'from "react"' in line]
        
        if len(react_imports) > 1:
            # Consolidate React imports
            all_imports = set()
            has_default_react = False
            
            for imp in react_imports:
                if 'React,' in imp or imp.strip().startswith('import React '):
                    has_default_react = True
                
                # Extract named imports
                if '{' in imp and '}' in imp:
                    named_part = imp[imp.find('{')+1:imp.find('}')]
                    for item in named_part.split(','):
                        item = item.strip()
                        if item and item != 'React':
                            all_imports.add(item)
            
            # Create consolidated import
            if has_default_react and all_imports:
                new_import = f"import React, {{ {', '.join(sorted(all_imports))} }} from 'react';"
            elif has_default_react:
                new_import = "import React from 'react';"
            else:
                new_import = f"import {{ {', '.join(sorted(all_imports))} }} from 'react';"
            
            # Replace all React imports with consolidated one
            new_import_lines = []
            for line in import_lines:
                if not ("from 'react'" in line or 'from "react"' in line):
                    new_import_lines.append(line)
            
            new_import_lines.insert(0, new_import)
            
            # Rebuild code
            new_lines = new_import_lines + [''] + lines[non_import_start:]
            code = '\n'.join(new_lines)
            fixes_applied.append(f"Consolidated {len(react_imports)} React import statements")
        
        return code, fixes_applied
    
    def _uses_client_features(self, code: str) -> bool:
        """Check if code uses client-side features like useState, useEffect, etc."""
        client_features = ['useState', 'useEffect', 'useCallback', 'useMemo', 'useRef', 'useContext']
        return any(feature in code for feature in client_features)
    
    def _is_client_component(self, code: str) -> bool:
        """Check if component already has 'use client' directive."""
        return "'use client'" in code or '"use client"' in code
    
    def _add_use_client(self, code: str) -> str:
        """Add 'use client' directive at the top of the file."""
        return "'use client';\n\n" + code
    
    def _needs_next_image_import(self, code: str) -> bool:
        """Check if Next.js Image import is needed."""
        has_img_tag = '<img' in code
        has_image_import = 'from "next/image"' in code or "from 'next/image'" in code
        return has_img_tag and not has_image_import
    
    def _add_next_image_import(self, code: str) -> str:
        """Add Next.js Image import."""
        lines = code.split('\n')
        
        # Find where to insert the import
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import'):
                insert_idx = i + 1
        
        lines.insert(insert_idx, 'import Image from "next/image";')
        return '\n'.join(lines)


class FormatAutoFixer:
    """Automatically fixes formatting and style issues with Tailwind validation."""
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
    
    def can_fix_issues(self, issues: List) -> bool:
        return True  # Can always try to format
    
    def fix(self, code: str, issues: List) -> Tuple[str, List[str]]:
        fixed_code = code
        fixes_applied = []
        
        # 1. Fix invalid Tailwind CSS classes
        fixed_code, tailwind_fixes = self._fix_tailwind_classes(fixed_code)
        fixes_applied.extend(tailwind_fixes)
        
        # 2. Replace img tags with Next.js Image components
        fixed_code, image_fixes = self._fix_image_tags(fixed_code)
        fixes_applied.extend(image_fixes)
        
        # 3. Basic formatting fixes
        if re.search(r'\n\s*\n\s*\n', fixed_code):
            fixed_code = re.sub(r'\n\s*\n\s*\n', '\n\n', fixed_code)
            fixes_applied.append("Removed extra blank lines")
        
        return fixed_code, fixes_applied
    
    def _fix_tailwind_classes(self, code: str) -> Tuple[str, List[str]]:
        """Fix common invalid Tailwind CSS classes."""
        fixes_applied = []
        
        # Common invalid class mappings
        class_fixes = {
            'text-smline-height': 'text-sm',
            'text-baseline-height': 'text-base',
            'bg-gray': 'bg-gray-100',
            'text-gray': 'text-gray-600',
            'text-black': 'text-gray-900',
            'bg-sky': 'bg-sky-500',
            'text-blue': 'text-blue-600',
            'bg-blue': 'bg-blue-600',
            'text-indigo': 'text-indigo-600',
            'bg-indigo': 'bg-indigo-600',
            'text-emerald': 'text-emerald-600',
            'bg-emerald': 'bg-emerald-600',
            'border-sky': 'border-sky-500',
            'border-blue': 'border-blue-600',
            'border-emerald': 'border-emerald-600',
            'border-gray': 'border-gray-300',
            'bg-sky/10': 'bg-sky-500/10',
            'bg-sky/20': 'bg-sky-500/20',
        }
        
        for invalid_class, valid_class in class_fixes.items():
            if invalid_class in code:
                code = code.replace(invalid_class, valid_class)
                fixes_applied.append(f"Fixed invalid Tailwind class '{invalid_class}' to '{valid_class}'")
        
        return code, fixes_applied
    
    def _fix_image_tags(self, code: str) -> Tuple[str, List[str]]:
        """Replace img tags with Next.js Image components."""
        fixes_applied = []
        
        # Replace <img> with <Image> if Next.js Image is imported
        if '<img' in code and 'next/image' in code:
            img_pattern = r'<img([^>]*?)>'
            
            def replace_img(match):
                attrs = match.group(1)
                # Add width and height if missing (required for Next.js Image)
                if 'width=' not in attrs:
                    attrs += ' width={200}'
                if 'height=' not in attrs:
                    attrs += ' height={200}'
                return f'<Image{attrs} />'
            
            new_code = re.sub(img_pattern, replace_img, code)
            if new_code != code:
                fixes_applied.append("Replaced img tags with Next.js Image components")
                code = new_code
        
        return code, fixes_applied


# Test the enhanced auto-fixers on your problem code
if __name__ == "__main__":
    test_code = '''import { useState } from 'react';
import React, { useState } from "react";

interface UserProfileProps {
  name: string;
  role: string;
  email: string;
  bio?: string;
}

const UserProfile: React.FC<UserProfileProps> = ({ name, role, email, bio }) => {
  const [avatarError, setAvatarError] = useState(false);

  return (
    <main className="w-full min-h-screen flex flex-col items-center bg-sky/10 py-8">
      <div className="bg-gray text-black">
        <h1 className="text-lg font-bold text-black">{name}</h1>
        <p className="text-smline-height text-gray">{bio}</p>
        <img
          src="test.jpg"
          alt="avatar"
          className="w-32 h-32"
        />
      </div>
    </main>
  );
};

export default UserProfile;'''

    print("🧪 Testing Enhanced Auto-Fixers")
    print("=" * 50)
    print("Original code has these issues:")
    print("- Duplicate React imports")
    print("- useState in server component")
    print("- Invalid Tailwind classes: bg-gray, text-gray, bg-sky/10, text-smline-height")
    print("- img tag instead of Next.js Image")
    print()
    
    # Test TypeScript auto-fixer
    ts_fixer = TypeScriptAutoFixer()
    fixed_code, ts_fixes = ts_fixer.fix(test_code, [])
    
    print("🔧 TypeScript Auto-Fixer:")
    for fix in ts_fixes:
        print(f"  ✅ {fix}")
    print()
    
    # Test Format auto-fixer
    format_fixer = FormatAutoFixer()
    fixed_code, format_fixes = format_fixer.fix(fixed_code, [])
    
    print("🎨 Format Auto-Fixer:")
    for fix in format_fixes:
        print(f"  ✅ {fix}")
    print()
    
    print("📝 Fixed Code:")
    print("-" * 50)
    print(fixed_code)
    print("-" * 50)