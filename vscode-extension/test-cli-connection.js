#!/usr/bin/env node

// Simple test script to verify CLI connection
const { spawn } = require('child_process');
const path = require('path');

const palettePath = path.join(__dirname, '..', 'venv', 'bin', 'palette');

console.log('🔍 Testing Palette CLI connection...');
console.log(`CLI Path: ${palettePath}`);

// Test 1: Check if CLI exists and runs
const testVersion = spawn(palettePath, ['--version'], {
    stdio: 'pipe'
});

testVersion.stdout.on('data', (data) => {
    console.log(`✅ CLI Version: ${data.toString().trim()}`);
});

testVersion.stderr.on('data', (data) => {
    console.error(`CLI Error: ${data.toString()}`);
});

testVersion.on('close', (code) => {
    if (code === 0) {
        console.log('✅ CLI executable test passed');
        
        // Test 2: Check help command
        console.log('\n🔍 Testing help command...');
        const testHelp = spawn(palettePath, ['--help'], {
            stdio: 'pipe'
        });
        
        testHelp.stdout.on('data', (data) => {
            console.log('✅ Help command works');
        });
        
        testHelp.on('close', (helpCode) => {
            if (helpCode === 0) {
                console.log('🎉 CLI connection test passed!');
                console.log('\nNext: Test from VS Code extension by opening the Palette panel');
            } else {
                console.log('❌ Help command failed');
            }
        });
        
    } else {
        console.log(`❌ CLI executable test failed with code ${code}`);
    }
});

testVersion.on('error', (err) => {
    console.error(`❌ CLI execution failed: ${err.message}`);
    console.log(`Make sure the CLI is installed at: ${palettePath}`);
});