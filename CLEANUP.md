# Palette Repository Sanitization

This directory contains scripts to clean up the Palette repository for fresh testing.

## Available Scripts

### 1. Full Sanitization (`sanitize.py`)
**Comprehensive cleanup with detailed reporting**

```bash
python3 sanitize.py
```

**Features:**
- ✅ Removes test projects and temporary directories
- ✅ Cleans all Python cache files (`__pycache__`, `.pyc`)
- ✅ Removes temporary test files
- ✅ Cleans test CSS files (keeps essentials)
- ✅ Removes generated components
- ✅ Cleans node_modules in test directories
- ✅ Git status check and recommendations
- ✅ Detailed progress reporting

### 2. Quick Cleanup (`quick-clean.sh`)
**Fast cleanup for rapid iteration**

```bash
./quick-clean.sh
```

**Features:**
- ⚡ Fast execution
- 🗂️ Removes test projects and temp files
- 🐍 Cleans Python cache
- 📦 Removes test node_modules
- 📋 Usage instructions

## Usage Workflow

### For Testing New Projects:

1. **Clean the workspace:**
   ```bash
   ./quick-clean.sh
   ```

2. **Clone a test project:**
   ```bash
   git clone <repository-url> test-project
   ```

3. **Analyze the project:**
   ```bash
   cd test-project
   PYTHONPATH=/home/vphilavong/Projects/Palette python3 -m src.cli analyze
   ```

4. **Generate components:**
   ```bash
   PYTHONPATH=/home/vphilavong/Projects/Palette python3 -m src.cli generate "your component prompt"
   ```

5. **Repeat for next project:**
   ```bash
   cd .. && ./quick-clean.sh
   ```

## What Gets Cleaned

### Directories Removed:
- `test-project/` - Cloned test repositories
- `test_projects/` - Additional test directories
- `temp/`, `tmp/` - Temporary directories
- `__pycache__/` - Python cache directories (recursive)
- `node_modules/` - In test directories only

### Files Removed:
- `test_aggregated_output.txt`
- `test_output.txt`
- `debug.log`
- `analysis_output.txt`
- `*.pyc` - Python cache files
- Generated test components

### What's Preserved:
- Source code (`src/`)
- Essential test CSS files
- Configuration files
- Virtual environment (`venv/`)
- Git repository data

## Safety Features

- ✅ Only removes test/temporary files
- ✅ Preserves source code and configuration
- ✅ Git status check before completion
- ✅ Error handling for missing files
- ✅ Detailed logging of all actions

## Examples

### Testing Multiple Projects:
```bash
# Clean workspace
./quick-clean.sh

# Test project 1
git clone https://github.com/user/project1.git test-project
cd test-project && PYTHONPATH=.. python3 -m src.cli analyze
cd ..

# Clean and test project 2
./quick-clean.sh
git clone https://github.com/user/project2.git test-project
cd test-project && PYTHONPATH=.. python3 -m src.cli analyze
cd ..
```

### Full Cleanup with Details:
```bash
python3 sanitize.py  # See detailed progress and git status
```

---

🎯 **Goal**: Keep the repository clean and ready for consistent testing across multiple projects.
