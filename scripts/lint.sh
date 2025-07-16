#!/bin/bash

# Comprehensive Python linting and code quality check
# Run this script to validate the entire codebase

set -e  # Exit on any error

echo "🔍 Starting comprehensive code quality checks..."
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo "----------------------------------------"
}

# Function to run command and capture results
run_check() {
    local cmd="$1"
    local description="$2"
    
    echo -e "${YELLOW}Running: $description${NC}"
    
    if eval "$cmd"; then
        echo -e "${GREEN}✓ $description passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $description failed${NC}"
        return 1
    fi
}

# Change to project root
cd "$(dirname "$0")/.."

# Initialize counters
total_checks=0
passed_checks=0

print_section "1. Black - Code Formatting Check"
total_checks=$((total_checks + 1))
if run_check "black --check --diff src/ palette.py" "Black formatting check"; then
    passed_checks=$((passed_checks + 1))
fi

print_section "2. isort - Import Sorting Check"
total_checks=$((total_checks + 1))
if run_check "isort --check-only --diff src/ palette.py" "Import sorting check"; then
    passed_checks=$((passed_checks + 1))
fi

print_section "3. Flake8 - Style Guide Enforcement"
total_checks=$((total_checks + 1))
if run_check "flake8 src/ palette.py" "Flake8 style check"; then
    passed_checks=$((passed_checks + 1))
fi

print_section "4. MyPy - Static Type Checking"
total_checks=$((total_checks + 1))
if run_check "mypy src/" "MyPy type checking"; then
    passed_checks=$((passed_checks + 1))
fi

print_section "5. Pylint - Comprehensive Code Analysis"
total_checks=$((total_checks + 1))
if run_check "pylint src/ --score=y" "Pylint code analysis"; then
    passed_checks=$((passed_checks + 1))
fi

print_section "6. Bandit - Security Linting"
total_checks=$((total_checks + 1))
if run_check "bandit -r src/ -f json -o bandit-report.json || bandit -r src/" "Security analysis"; then
    passed_checks=$((passed_checks + 1))
fi

print_section "7. Basic Import Tests"
total_checks=$((total_checks + 1))
if run_check "python3 -c 'import sys; sys.path.insert(0, \"src\"); import palette.cli.main; print(\"✓ Main imports work\")'" "Import validation"; then
    passed_checks=$((passed_checks + 1))
fi

print_section "8. CLI Functionality Test"
total_checks=$((total_checks + 1))
if run_check "python3 palette.py --help > /dev/null" "CLI help command"; then
    passed_checks=$((passed_checks + 1))
fi

# Final summary
echo -e "\n================================================="
echo -e "${BLUE}FINAL SUMMARY${NC}"
echo "================================================="

if [ $passed_checks -eq $total_checks ]; then
    echo -e "${GREEN}🎉 All checks passed! ($passed_checks/$total_checks)${NC}"
    echo -e "${GREEN}Your code is ready for production!${NC}"
    exit 0
else
    failed_checks=$((total_checks - passed_checks))
    echo -e "${RED}❌ Some checks failed: $passed_checks/$total_checks passed${NC}"
    echo -e "${RED}$failed_checks checks need attention${NC}"
    
    echo -e "\n${YELLOW}💡 To auto-fix formatting issues, run:${NC}"
    echo "  black src/ palette.py"
    echo "  isort src/ palette.py"
    
    exit 1
fi
