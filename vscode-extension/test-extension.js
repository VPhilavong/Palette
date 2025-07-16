#!/usr/bin/env node

/**
 * Test script for Code Palette VS Code Extension
 * Simulates the extension calling the palette CLI
 */

const { exec } = require('child_process');
const path = require('path');

async function testPaletteCLI() {
    console.log('🧪 Testing Code Palette CLI integration...\n');
    
    // Test 1: Check if palette CLI is available
    console.log('1️⃣ Testing CLI availability...');
    try {
        const { stdout } = await execAsync('palette --help');
        console.log('✅ Palette CLI is accessible');
    } catch (error) {
        console.log('❌ Palette CLI not found');
        console.log('   Run: pip install -e /path/to/code-palette');
        return false;
    }
    
    // Test 2: Test project analysis
    console.log('\n2️⃣ Testing project analysis...');
    try {
        const testProjectPath = '../test_projects/nextjs-test';
        const { stdout } = await execAsync('palette analyze', { cwd: testProjectPath });
        console.log('✅ Project analysis works');
        console.log('   Detected:', stdout.split('\n').find(line => line.includes('Framework:')));
    } catch (error) {
        console.log('❌ Project analysis failed:', error.message);
        return false;
    }
    
    // Test 3: Test component preview
    console.log('\n3️⃣ Testing component preview...');
    try {
        const testProjectPath = '../test_projects/nextjs-test';
        const { stdout } = await execAsync('palette preview "simple button"', { 
            cwd: testProjectPath,
            timeout: 15000 
        });
        console.log('✅ Component preview works');
        const hasReactCode = stdout.includes('interface') && stdout.includes('React');
        console.log(`   Generated React component: ${hasReactCode ? '✅' : '❌'}`);
    } catch (error) {
        console.log('❌ Component preview failed:', error.message);
        if (error.message.includes('API key')) {
            console.log('   Make sure OPENAI_API_KEY is set');
        }
        return false;
    }
    
    console.log('\n🎉 All tests passed! Extension should work correctly.');
    return true;
}

function execAsync(command, options = {}) {
    return new Promise((resolve, reject) => {
        exec(command, options, (error, stdout, stderr) => {
            if (error) {
                reject(error);
            } else {
                resolve({ stdout, stderr });
            }
        });
    });
}

// Run tests
testPaletteCLI().then(success => {
    if (success) {
        console.log('\n🚀 Ready to install VS Code extension!');
        console.log('   Run: ./install.sh');
    } else {
        console.log('\n❌ Please fix the issues above before installing the extension.');
        process.exit(1);
    }
}).catch(error => {
    console.error('Test failed:', error);
    process.exit(1);
});