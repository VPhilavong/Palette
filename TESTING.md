# 🧪 Palette Testing Guide

This guide provides comprehensive testing procedures for the unified Palette AI design prototyping system. Palette transforms natural language descriptions into complete, interactive pages and features you can see immediately.

## 📋 Overview

Palette is a **design prototyping tool** (like Vercel v0) that generates complete, visible pages and features - not individual components. The system routes between:
- **AI SDK** (simple requests) - Fast generation using AI SDK
- **Python Intelligence Layer** (complex requests) - Advanced analysis + quality assurance

## 🚀 Quick Start Testing

### Prerequisites

1. **Environment Setup**
   ```bash
   # Ensure you're in the Palette project root
   cd /path/to/Palette
   
   # Python environment
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   
   # VS Code extension
   cd vscode-extension
   npm install
   npm run compile
   ```

2. **API Keys** (Set one or both)
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   ```

3. **Test Project Setup**
   ```bash
   # Create a test Vite + React + shadcn/ui project
   npm create vite@latest test-palette-project -- --template react-ts
   cd test-palette-project
   npm install
   
   # Add shadcn/ui
   npx shadcn-ui@latest init
   npx shadcn-ui@latest add button card input
   ```

## 🎯 Testing Scenarios

### 1. Python Backend Testing

#### 1.1 Server Health Check
```bash
# Start the Python intelligence server
cd src/palette/server
python3 main.py

# In another terminal, test health
curl http://127.0.0.1:8765/health
```
**Expected:** Status 200 with server info

#### 1.2 Project Analysis Testing
```bash
# Test analysis endpoint
curl -X POST http://127.0.0.1:8765/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "projectPath": "/path/to/test-palette-project",
    "analysisType": "quick"
  }'
```
**Expected:** Framework detection (vite), styling (tailwindcss), TypeScript status

#### 1.3 Quality Validation Testing
```bash
# Create test component file
echo 'import React from "react";
export const TestButton = () => <button>Test</button>;' > /tmp/test-component.tsx

# Test quality validation
curl -X POST http://127.0.0.1:8765/api/quality/validate \
  -H "Content-Type: application/json" \
  -d '{
    "projectPath": "/tmp",
    "filePaths": ["/tmp/test-component.tsx"],
    "validationType": "comprehensive"
  }'
```
**Expected:** Quality score, issues list, suggestions

### 2. VS Code Extension Testing

#### 2.1 Extension Installation & Activation
1. Open VS Code
2. Press `F5` to launch Extension Development Host
3. In new window, open test project: `File → Open Folder → test-palette-project`
4. Press `Ctrl+Shift+P` → type "Palette" → should see commands

#### 2.2 Unified Panel Testing
1. Run command: `Palette: Open Unified Interface`
2. **Expected:** Webview panel opens with chat interface
3. **Check:** Status shows "Connected to unified intelligence layer"

#### 2.3 Simple Generation Testing (AI SDK Route)
**Prompt:** `Create a simple login form with email and password`
**Expected Behavior:**
- Request classified as "simple"
- Routed to AI SDK (fast response)
- Generates single form component
- No quality validation (simple route)

#### 2.4 Complex Generation Testing (Python Backend Route)
**Prompt:** `Create a complete dashboard page with sidebar navigation, user profile header, data charts, and a data table with sorting`
**Expected Behavior:**
- Request classified as "complex"
- Routed to Python backend
- Shows streaming phases:
  1. "Analyzing project structure..."
  2. "Complex request detected - enabling multi-file generation"
  3. "Generating your design..."
  4. "Validating generated code quality..." (if enabled)
- Generates multiple files
- Quality score displayed

### 3. Generation Pipeline Testing

#### 3.1 Multi-File Generation
**Test Prompt:** `Create a complete e-commerce product page with product gallery, details, reviews section, and add to cart functionality`

**Expected Outputs:**
- `ProductPage.tsx` - Main page component
- `ProductGallery.tsx` - Image carousel component
- `ProductDetails.tsx` - Product info component
- `ReviewsSection.tsx` - Reviews display component
- `AddToCartButton.tsx` - Cart functionality

**Validation Points:**
- All files created in correct directories
- Proper import/export structure
- Consistent styling (Tailwind + shadcn/ui)
- TypeScript types properly defined

#### 3.2 Quality Assurance Integration
**Test with Poor Quality Prompt:** `make a bad component with duplicate imports and console.log`

**Expected Quality Issues Detected:**
- Duplicate React imports
- Console.log statements present
- Missing accessibility attributes
- Invalid CSS classes

**Expected Auto-fix Suggestions:**
- Consolidate duplicate imports
- Remove console.log statements
- Add alt attributes to images
- Fix invalid Tailwind classes

#### 3.3 MCP Enhancement Testing
**Test Prompt:** `Create a pricing page using shadcn/ui components with three tiers`

**Expected MCP Features:**
- Automatic detection of available shadcn/ui components
- Enhanced prompts with component-specific guidance
- Proper shadcn/ui import patterns
- Preview URL generation (if enabled)

## 🔧 Advanced Testing Scenarios

### 4. Streaming & Real-Time Features

#### 4.1 Server-Sent Events Testing
```bash
# Test SSE streaming endpoint
curl -N http://127.0.0.1:8765/api/generate/stream/test-id
```
**Expected:** Continuous stream of events until completion

#### 4.2 VS Code Real-Time Updates
1. Submit complex generation request
2. **Monitor:** Real-time streaming in VS Code panel
3. **Check:** Status updates appear progressively
4. **Verify:** Files appear in explorer as they're generated

### 5. Error Handling & Recovery

#### 5.1 Python Server Unavailable
1. Stop Python server
2. Submit request in VS Code
3. **Expected:** Automatic fallback to AI SDK
4. **Message:** "Python backend unavailable, using AI SDK fallback"

#### 5.2 API Key Missing
1. Remove all API keys
2. Submit request
3. **Expected:** Clear error message
4. **Guidance:** Instructions to set API keys

#### 5.3 Invalid Project Path
1. Set invalid project path in analysis request
2. **Expected:** Proper error handling
3. **Response:** Clear error message, no system crash

### 6. Performance Testing

#### 6.1 Large Project Analysis
- Test with project containing 100+ files
- **Expected:** Analysis completes within 30 seconds
- **Memory:** No memory leaks during analysis

#### 6.2 Concurrent Requests
- Submit 5 generation requests simultaneously
- **Expected:** All complete without conflicts
- **Check:** Proper stream isolation

## 🐛 Troubleshooting Guide

### Common Issues & Solutions

#### Python Server Won't Start
**Symptoms:** Import errors, module not found
**Solutions:**
```bash
# Check Python path
export PYTHONPATH="/path/to/Palette/src:$PYTHONPATH"

# Verify dependencies
pip install -r requirements.txt

# Check FastAPI installation
python3 -c "import fastapi; print('FastAPI OK')"
```

#### VS Code Extension Not Loading
**Symptoms:** Commands not appearing, panel not opening
**Solutions:**
1. Reload VS Code window (`Ctrl+Shift+P` → "Reload Window")
2. Check VS Code Output panel (View → Output → "Code Palette")
3. Reinstall extension: `npm run compile` in vscode-extension folder

#### Generation Requests Timing Out
**Symptoms:** No response after 2+ minutes
**Solutions:**
1. Check API key validity
2. Monitor VS Code Output panel for errors
3. Verify Python server is running (`curl http://127.0.0.1:8765/health`)
4. Check network connectivity

#### Quality Validation Failing
**Symptoms:** Quality scores always 0, validation errors
**Solutions:**
1. Verify ComponentValidator imports working
2. Check temporary file permissions
3. Ensure TypeScript compiler available (`npx tsc --version`)

#### Files Not Being Created
**Symptoms:** Generation completes but no files appear
**Solutions:**
1. Check workspace folder is opened in VS Code
2. Verify write permissions in target directory
3. Monitor VS Code Output panel for file operation errors

### Debug Mode Activation
```bash
# Enable verbose logging
export PALETTE_DEBUG=1

# Python server debug
python3 -c "import logging; logging.basicConfig(level=logging.DEBUG)"

# VS Code extension debug
# Check Developer Console (Help → Toggle Developer Tools)
```

## 📊 Expected Performance Metrics

| Test Scenario | Expected Duration | Success Criteria |
|---------------|------------------|------------------|
| Simple component (AI SDK) | < 10 seconds | Component generated, compiles |
| Complex page (Python) | 30-60 seconds | Multiple files, quality validated |
| Project analysis | < 15 seconds | Framework/styling detected |
| Quality validation | < 5 seconds | Score generated, issues listed |
| Server startup | < 10 seconds | Health check returns 200 |

## 📈 Success Criteria

### ✅ Passing Tests Should Show:
- **Intelligent Routing:** Simple → AI SDK, Complex → Python backend
- **Complete Pages:** Generate full, visible, interactive pages (not isolated components)
- **Quality Assurance:** Automatic validation with scoring and suggestions
- **Real-time Streaming:** Progressive updates in VS Code panel
- **Multi-file Generation:** Create multiple related files for complex features
- **Error Recovery:** Graceful fallbacks when services unavailable
- **Project Integration:** Proper analysis and context-aware generation

### ❌ Common Test Failures:
- Generated components that can't be viewed/used immediately
- No streaming updates in VS Code panel
- Quality validation not running on complex requests
- Files created in wrong directories
- Import/export errors preventing compilation
- API rate limiting or timeout issues

## 🔄 Continuous Testing

### Automated Test Run
```bash
# Run all backend tests
python3 test_generation_pipeline.py

# Run quality validation tests
python3 test_quality_workflow.py

# Run VS Code integration tests
npm test  # In vscode-extension folder
```

### Test Project Templates
Pre-configured test projects are available in `test_projects/`:
- `vite-react-ts/` - Basic Vite + React + TypeScript
- `next-shadcn/` - Next.js + shadcn/ui setup
- `legacy-project/` - Non-Vite project for fallback testing

---

## 🎯 Remember: Design Prototyping Focus

Palette generates **complete, visible pages and features** - not individual components:
- ✅ Generate: Landing pages, dashboards, e-commerce sites, admin panels
- ❌ Don't generate: Isolated buttons, cards, or UI elements
- ✅ Think: "What will the user see on screen?"
- ✅ Goal: Rapid prototyping of complete user experiences

Happy testing! 🚀