# VS Code Extension Testing Guide

This guide provides step-by-step instructions to test different versions of the Palette extension to identify and fix the root issues.

## Option 1: Test Ultra-Minimal Diagnostic Extension

### Step 1: Switch to Diagnostic Configuration

1. **Backup current package.json:**
   ```bash
   cp package.json package.json.backup
   ```

2. **Switch to diagnostic configuration:**
   ```bash
   cp package-diagnostic.json package.json
   ```

3. **Test the diagnostic extension:**
   - Press `F5` in VS Code (should open Extension Development Host)
   - In the new window, open Command Palette (`Ctrl+Shift+P`)
   - Look for commands starting with "🩺 Palette"
   - Try both:
     - `🩺 Palette: Test Basic Function`
     - `🩺 Palette: Open Diagnostic Webview`

### Expected Results:
- ✅ Extension should activate without errors
- ✅ Test command should show success message
- ✅ Diagnostic webview should open with interactive form
- ✅ Message sending/receiving should work

### If Diagnostic Extension Works:
This confirms the issue is with complex dependencies or command conflicts. Proceed to Option 2.

### If Diagnostic Extension Fails:
Check VS Code Developer Console (`Help > Toggle Developer Tools > Console`) for errors.

---

## Option 2: Test Cleaned-Up Minimal Extension

### Step 1: Switch to Minimal Configuration

1. **Switch to minimal configuration:**
   ```bash
   cp package-minimal.json package.json
   ```

2. **Test the minimal extension:**
   - Press `F5` in VS Code
   - In Extension Development Host, open Command Palette
   - Look for:
     - `🎨 Palette: Open Unified System`
     - `🧪 Palette: Test Extension`

### Expected Results:
- ✅ Extension should activate
- ✅ Commands should appear in Command Palette
- ✅ Unified System should open with AI chat interface
- ✅ Message input should be functional

---

## Option 3: Debug Current Extension

### Step 1: Restore Original Configuration

1. **Restore original package.json:**
   ```bash
   cp package.json.backup package.json
   ```

2. **Debug with Console Open:**
   - Open VS Code Developer Tools before testing
   - Press `F5` to launch Extension Development Host
   - Watch Console tab for errors
   - Try opening command palette and look for Palette commands

---

## Debugging Checklist

### In Extension Development Host:

1. **Check Command Palette:**
   - Open with `Ctrl+Shift+P`
   - Type "Palette" to filter commands
   - Note which commands appear vs. what's expected

2. **Check VS Code Console:**
   - Open Developer Tools (`Help > Toggle Developer Tools`)
   - Look for:
     - Extension activation messages
     - Error messages
     - Import/dependency failures

3. **Check Extension Status:**
   - Go to Extensions view (`Ctrl+Shift+X`)
   - Look for the Palette extension
   - Check if it shows as "Activated" or has error indicators

### Common Issues to Look For:

- ❌ "Cannot resolve module" errors
- ❌ Command registration failures  
- ❌ Extension activation timeout
- ❌ PaletteService import failures
- ❌ Zod dependency conflicts

## Testing Protocol

### Test Each Version in Order:

1. **Diagnostic Extension** (most likely to work)
2. **Minimal Extension** (should work if diagnostic works)
3. **Full Extension** (may fail due to dependencies)

### For Each Test:

1. Note activation success/failure
2. Check available commands
3. Test webview functionality
4. Record any console errors
5. Document what works vs. what doesn't

## Next Steps Based on Results

### If Diagnostic Works:
- ✅ VS Code extension basics are functional
- Issue is with complex dependencies or command conflicts
- Progressively add features to diagnostic version

### If Minimal Works:
- ✅ Basic Palette functionality works
- Issue is with unused commands in full package.json
- Clean up original package.json

### If Nothing Works:
- Check VS Code version compatibility
- Try creating completely new extension from scratch
- Consider alternative implementation approaches

## Alternative Approaches

If all versions fail:
1. **Sidebar Webview** instead of panel
2. **Terminal Integration** instead of webview
3. **Language Server Protocol** integration
4. **Standalone Web App** with VS Code API

## Success Criteria

The extension is working when:
- ✅ Extension activates without console errors
- ✅ Commands appear in Command Palette
- ✅ Webview opens and displays content
- ✅ Message input accepts text and triggers responses
- ✅ Basic echo functionality works