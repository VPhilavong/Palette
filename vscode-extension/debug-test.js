// Debug test for VS Code extension
const { spawn } = require('child_process');
const path = require('path');

console.log('Testing Palette CLI execution...');

// Test if palette command exists
const testCmd = spawn('which', ['palette']);
testCmd.on('close', (code) => {
  if (code === 0) {
    console.log('✅ Palette CLI found in PATH');
    
    // Now test actual generation
    console.log('Testing palette generate command...');
    
    const genCmd = spawn('palette', ['generate', 'simple button', '--output', '.'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true
    });
    
    let stdout = '';
    let stderr = '';
    
    genCmd.stdout.on('data', (data) => {
      const text = data.toString();
      stdout += text;
      console.log('[STDOUT]:', text);
    });
    
    genCmd.stderr.on('data', (data) => {
      const text = data.toString();
      stderr += text;
      console.log('[STDERR]:', text);
    });
    
    genCmd.on('close', (code) => {
      console.log(`\n=== Command completed with code: ${code} ===`);
      console.log('Total stdout length:', stdout.length);
      console.log('Total stderr length:', stderr.length);
      
      if (code === 0) {
        console.log('✅ Command succeeded');
      } else {
        console.log('❌ Command failed');
        console.log('Error output:', stderr);
      }
    });
    
    genCmd.on('error', (err) => {
      console.log('❌ Failed to start command:', err.message);
    });
    
  } else {
    console.log('❌ Palette CLI not found in PATH');
    console.log('Make sure Palette is installed and accessible from command line');
  }
});

testCmd.on('error', (err) => {
  console.log('❌ Error checking for palette:', err.message);
});