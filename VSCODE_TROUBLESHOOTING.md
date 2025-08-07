# VS Code Extension Troubleshooting

## Issue 1: "Palette: Open Unified Interface" Not Showing in Command Palette

### ✅ **The command exists but is named differently**

**Actual Command**: `🎨 Palette: Open Unified System`

### How to Fix:

1. **Reload VS Code Extension**:
   ```
   Ctrl+Shift+P → "Developer: Reload Window"
   ```

2. **Search for the correct command**:
   ```
   Ctrl+Shift+P → Type "Palette: Open Unified" or "🎨 Palette"
   ```

3. **If still not showing, reinstall the extension**:
   ```bash
   cd vscode-extension
   npm run compile
   # Then press F5 to test in Extension Development Host
   ```

## Issue 2: "Python backend: Starting..." Gets Stuck

### 🔍 **Root Cause**: 
VS Code extension is trying to start Python server using `uvicorn palette.server.main:app` but the module import fails.

### ✅ **Quick Fix**: Use our working server launcher

1. **Update VS Code settings** (`Ctrl+,`):
   ```json
   {
     "palette.serverUrl": "http://127.0.0.1:8765",
     "palette.pythonPath": "/path/to/your/python3",
     "palette.projectPath": "/home/vphilavong/Projects/Palette"
   }
   ```

2. **Start server manually** (recommended for now):
   ```bash
   cd /home/vphilavong/Projects/Palette
   python3 run_server.py
   ```
   
   You should see:
   ```
   🎨 Starting Palette Intelligence Server...
   INFO:     Uvicorn running on http://127.0.0.1:8765
   ```

3. **Then use VS Code extension**:
   ```
   Ctrl+Shift+P → "🎨 Palette: Open Unified System"
   ```

## Issue 3: Extension Commands Not Working

### 📋 **Available Commands** (check these work):

1. `🎨 Palette: Open Unified System` - Main interface
2. `Palette: Generate Component` - Quick generation
3. `Palette: Analyze Project` - Project analysis  
4. `Palette: Open Chat` - Streaming chat
5. `Palette: Open AI Agent (AI SDK)` - AI SDK version

### ✅ **Test Each Command**:
```
Ctrl+Shift+P → Type each command name above
```

## Manual Testing Workflow

### 1. **Test Server Independently**:
```bash
# Terminal 1: Start server
python3 run_server.py

# Terminal 2: Test server
curl http://127.0.0.1:8765/health
```

### 2. **Test VS Code Extension**:
```
Ctrl+Shift+P → "🎨 Palette: Open Unified System"
```

### 3. **Test Generation**:
Use any of these test messages:
- `"Create a button component with primary and secondary variants"`
- `"Create a todo list app with add, complete, delete functionality"`
- `"Create a complete dashboard with sidebar and charts"`

## Debug Information

### Check Extension Status:
```
Ctrl+Shift+P → "Developer: Show Running Extensions"
Look for "code-palette" or "Palette AI (Bundled)"
```

### Check Output Logs:
```
View → Output → Select "Code Palette" from dropdown
```

### Check Console:
```
Help → Toggle Developer Tools → Console tab
Look for Palette-related errors
```

## Working Configuration Example

**Settings.json**:
```json
{
  "palette.serverUrl": "http://127.0.0.1:8765",
  "palette.openaiApiKey": "your-openai-key-here",
  "palette.projectPath": "/home/vphilavong/Projects/Palette",
  "palette.enableQualityAssurance": true,
  "palette.preferredProvider": "python_backend"
}
```

## Expected Behavior

✅ **When Working Correctly**:
1. `🎨 Palette: Open Unified System` opens a webview panel
2. You can type messages and get AI responses
3. Server status shows "Connected" or "Ready"
4. Generation completes within 30-180 seconds

❌ **When Broken**:
1. Commands not showing in palette
2. "Python backend: Starting..." never progresses
3. Webview shows connection errors
4. No response to messages

## Quick Test

**1-Minute Test**:
```bash
# Start server manually
python3 run_server.py &

# Test server
curl http://127.0.0.1:8765/health

# Open VS Code
# Ctrl+Shift+P → "🎨 Palette: Open Unified System"
# Type: "Create a simple button component"
```

If this works, your core functionality is fine - just the automatic server startup in the extension needs fixing.