# VS Code Extension Debugging

## Current Issue
Chat input gets stuck - can't send messages

## Added Debugging
1. ✅ Added console.log for userMessage reception
2. ✅ Added immediate feedback message 
3. ✅ Added timeout (3 min) to prevent hanging
4. ✅ Added workspace and options logging

## To Debug:
1. Open VS Code Developer Tools (Help > Toggle Developer Tools)
2. Open Palette panel
3. Try to send a message
4. Check console for:
   - "Received userMessage: [text]"
   - "streamGenerate called with options: [options]"
   - "workspaceRoot: [path]"
   - Any error messages

## Possible Issues:
1. **No workspace folder** - Extension needs an open folder
2. **API key missing** - Should show error but might hang
3. **CLI path issues** - Can't find palette command
4. **Promise never resolving** - streamGenerate hangs

## Quick Test:
1. Open a folder in VS Code first
2. Open Palette panel  
3. Send message "test"
4. Should see immediate "Message received" response
5. Check Developer Console for logs