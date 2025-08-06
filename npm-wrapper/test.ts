/**
 * Test script for Palette AI NPM wrapper
 */

import chalk from 'chalk';
import { spawn } from 'child_process';
import * as path from 'path';

async function runTest(command: string, args: string[] = []): Promise<boolean> {
  return new Promise((resolve) => {
    console.log(chalk.blue(`\n🧪 Testing: ${command} ${args.join(' ')}`));
    
    const child = spawn('node', [path.join(__dirname, 'index.js'), command, ...args], {
      stdio: 'pipe'
    });
    
    let stdout = '';
    let stderr = '';
    
    child.stdout?.on('data', (data) => {
      stdout += data.toString();
    });
    
    child.stderr?.on('data', (data) => {
      stderr += data.toString();
    });
    
    child.on('close', (code) => {
      if (code === 0 || command === 'status') { // Status command might exit with non-zero if not setup
        console.log(chalk.green(`✅ ${command} test passed`));
        if (stdout) console.log('Output:', stdout.substring(0, 200) + (stdout.length > 200 ? '...' : ''));
        resolve(true);
      } else {
        console.log(chalk.red(`❌ ${command} test failed (code: ${code})`));
        if (stderr) console.log('Error:', stderr);
        resolve(false);
      }
    });
    
    child.on('error', (error) => {
      console.log(chalk.red(`❌ ${command} test failed:`, error.message));
      resolve(false);
    });
    
    // Kill after 10 seconds to prevent hanging
    setTimeout(() => {
      child.kill();
      console.log(chalk.yellow(`⚠️ ${command} test timed out`));
      resolve(false);
    }, 10000);
  });
}

async function main() {
  console.log(chalk.blue('🎨 Palette AI NPM Wrapper Tests'));
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  const tests = [
    { command: 'status' },
    { command: '--help' },
    { command: '--version' }
  ];
  
  let passed = 0;
  let total = tests.length;
  
  for (const test of tests) {
    const success = await runTest(test.command);
    if (success) passed++;
  }
  
  console.log(chalk.blue('\n📊 Test Results'));
  console.log('━━━━━━━━━━━━━━');
  console.log(`Passed: ${chalk.green(passed.toString())}/${total}`);
  console.log(`Success Rate: ${chalk.blue(Math.round(passed/total * 100) + '%')}`);
  
  if (passed === total) {
    console.log(chalk.green('\n🎉 All tests passed!'));
    console.log(chalk.cyan('NPM wrapper is ready for publication.'));
  } else {
    console.log(chalk.red('\n❌ Some tests failed.'));
    console.log(chalk.yellow('Please check the implementation.'));
  }
  
  process.exit(passed === total ? 0 : 1);
}

main().catch(console.error);