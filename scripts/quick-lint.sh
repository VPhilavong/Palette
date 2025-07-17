#!/bin/bash

# Simplified linting check with pass/fail summary
# Run this for a quick overview of code quality

cd "$(dirname "$0")/.."

echo "🔍 Quick Code Quality Check"
echo "=========================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

passed=0
total=0

# Test 1: Black formatting
total=$((total + 1))
echo -n "📐 Code formatting (Black): "
if black --check --quiet src/ palette.py 2>/dev/null; then
    echo -e "${GREEN}PASS${NC}"
    passed=$((passed + 1))
else
    echo -e "${RED}FAIL${NC} - Run: black src/ palette.py"
fi

# Test 2: Import ordering
total=$((total + 1))
echo -n "📦 Import ordering (isort): "
if isort --check-only --quiet src/ palette.py 2>/dev/null; then
    echo -e "${GREEN}PASS${NC}"
    passed=$((passed + 1))
else
    echo -e "${RED}FAIL${NC} - Run: isort src/ palette.py"
fi

# Test 3: Basic syntax check
total=$((total + 1))
echo -n "🐍 Python syntax check: "
if python3 -m py_compile src/palette/**/*.py src/palette/*.py palette.py 2>/dev/null; then
    echo -e "${GREEN}PASS${NC}"
    passed=$((passed + 1))
else
    echo -e "${RED}FAIL${NC} - Check syntax errors"
fi

# Test 4: Import validation
total=$((total + 1))
echo -n "📥 Import validation: "
if python3 -c "import sys; sys.path.insert(0, 'src'); import palette.cli.main" 2>/dev/null; then
    echo -e "${GREEN}PASS${NC}"
    passed=$((passed + 1))
else
    echo -e "${RED}FAIL${NC} - Import errors detected"
fi

# Test 5: CLI functionality
total=$((total + 1))
echo -n "⚡ CLI functionality: "
if python3 palette.py --help >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
    passed=$((passed + 1))
else
    echo -e "${RED}FAIL${NC} - CLI not working"
fi

echo ""
echo "=========================="
if [ $passed -eq $total ]; then
    echo -e "${GREEN}✅ All checks passed ($passed/$total)${NC}"
    echo -e "${GREEN}Your code is ready!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some issues found ($passed/$total passed)${NC}"
    echo -e "${BLUE}💡 Run ./scripts/lint.sh for detailed analysis${NC}"
    exit 1
fi
