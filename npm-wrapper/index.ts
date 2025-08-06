#!/usr/bin/env node

/**
 * Palette AI CLI - NPM Wrapper
 * 
 * This is a zero-friction npm wrapper for the Palette AI component generator.
 * It handles Python environment setup, dependency management, and provides
 * a seamless CLI experience for developers.
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import inquirer from 'inquirer';
import { spawn, exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import which from 'which';

const execAsync = promisify(exec);

interface PaletteConfig {
  pythonPath?: string;
  paletteInstalled: boolean;
  setupComplete: boolean;
  apiKeys: {
    openai?: string;
    anthropic?: string;
  };
}

class PaletteWrapper {
  private configPath: string;
  private config: PaletteConfig;

  constructor() {
    this.configPath = path.join(os.homedir(), '.palette-npm', 'config.json');
    this.config = this.loadConfig();
  }

  private loadConfig(): PaletteConfig {
    const defaultConfig: PaletteConfig = {
      paletteInstalled: false,
      setupComplete: false,
      apiKeys: {}
    };

    try {
      if (fs.existsSync(this.configPath)) {
        const configData = fs.readFileSync(this.configPath, 'utf8');
        return { ...defaultConfig, ...JSON.parse(configData) };
      }
    } catch (error) {
      console.warn(chalk.yellow('Warning: Could not load config, using defaults'));
    }

    return defaultConfig;
  }

  private saveConfig(): void {
    try {
      const configDir = path.dirname(this.configPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2));
    } catch (error) {
      console.error(chalk.red('Error saving configuration:', error));
    }
  }

  private async checkPython(): Promise<string | null> {
    const pythonCommands = ['python3', 'python'];
    
    for (const cmd of pythonCommands) {
      try {
        const pythonPath = await which(cmd);
        const { stdout } = await execAsync(`${cmd} --version`);
        const version = stdout.trim();
        
        // Check if Python version is 3.9+
        const match = version.match(/Python (\d+)\.(\d+)/);
        if (match) {
          const major = parseInt(match[1]);
          const minor = parseInt(match[2]);
          
          if (major === 3 && minor >= 9) {
            return pythonPath;
          }
        }
      } catch (error) {
        // Command not found, continue to next
      }
    }
    
    return null;
  }

  private async setupEnvironment(): Promise<boolean> {
    const spinner = ora('Setting up Palette AI environment...').start();
    
    try {
      // Check Python
      const pythonPath = await this.checkPython();
      if (!pythonPath) {
        spinner.fail('Python 3.9+ is required but not found');
        console.log(chalk.yellow('\nPlease install Python 3.9+ from https://python.org'));
        console.log(chalk.yellow('Or use a package manager like brew, apt, or chocolatey'));
        return false;
      }

      this.config.pythonPath = pythonPath;
      spinner.text = 'Installing Palette AI package...';

      // Install palette package
      await this.executeCommand(pythonPath, ['-m', 'pip', 'install', 'code-palette'], { 
        stdio: 'pipe' 
      });

      this.config.paletteInstalled = true;
      spinner.succeed('Palette AI installed successfully!');
      
      return true;
    } catch (error) {
      spinner.fail('Failed to set up environment');
      console.error(chalk.red('Setup error:', error));
      return false;
    }
  }

  private async setupApiKeys(): Promise<void> {
    console.log(chalk.blue('\n🔑 API Key Setup'));
    console.log('Palette AI requires API keys for AI providers. You can skip this for now.');
    
    const { setupKeys } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'setupKeys',
        message: 'Would you like to configure API keys now?',
        default: false
      }
    ]);

    if (!setupKeys) return;

    const questions = [
      {
        type: 'password',
        name: 'openai',
        message: 'OpenAI API Key (optional):',
        mask: '*'
      },
      {
        type: 'password',
        name: 'anthropic',
        message: 'Anthropic API Key (optional):',
        mask: '*'
      }
    ];

    const answers = await inquirer.prompt(questions);
    
    if (answers.openai) this.config.apiKeys.openai = answers.openai;
    if (answers.anthropic) this.config.apiKeys.anthropic = answers.anthropic;
    
    console.log(chalk.green('✅ API keys configured!'));
  }

  private async firstTimeSetup(): Promise<boolean> {
    console.log(chalk.blue('\n🎨 Welcome to Palette AI!'));
    console.log('This is your first time using Palette. Let\'s get you set up.\n');

    const setupSuccess = await this.setupEnvironment();
    if (!setupSuccess) return false;

    await this.setupApiKeys();
    
    this.config.setupComplete = true;
    this.saveConfig();
    
    console.log(chalk.green('\n🎉 Setup complete! You can now use the `palette` command.'));
    console.log(chalk.cyan('\nTry: palette generate "hero section with gradient background"'));
    
    return true;
  }

  private async executeCommand(command: string, args: string[], options: any = {}): Promise<void> {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        stdio: 'inherit',
        env: {
          ...process.env,
          ...(this.config.apiKeys.openai && { OPENAI_API_KEY: this.config.apiKeys.openai }),
          ...(this.config.apiKeys.anthropic && { ANTHROPIC_API_KEY: this.config.apiKeys.anthropic })
        },
        ...options
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Command failed with code ${code}`));
        }
      });

      child.on('error', (error) => {
        reject(error);
      });
    });
  }

  private async runPalette(args: string[]): Promise<void> {
    if (!this.config.setupComplete) {
      const setupSuccess = await this.firstTimeSetup();
      if (!setupSuccess) process.exit(1);
    }

    if (!this.config.pythonPath) {
      console.error(chalk.red('Python path not configured. Please run setup again.'));
      process.exit(1);
    }

    try {
      await this.executeCommand(this.config.pythonPath, ['-m', 'palette.cli.main', ...args]);
    } catch (error) {
      console.error(chalk.red('Error running Palette:'), error);
      process.exit(1);
    }
  }

  public async checkStatus(): Promise<void> {
    console.log(chalk.blue('\n📊 Palette AI Status'));
    console.log('━━━━━━━━━━━━━━━━━━━━━━');
    
    // Check Python
    const pythonPath = await this.checkPython();
    console.log(`Python 3.9+: ${pythonPath ? chalk.green('✅ Found') : chalk.red('❌ Not found')}`);
    if (pythonPath) console.log(`  Path: ${pythonPath}`);
    
    // Check Palette installation
    console.log(`Palette installed: ${this.config.paletteInstalled ? chalk.green('✅ Yes') : chalk.red('❌ No')}`);
    
    // Check API keys
    const hasOpenAI = !!this.config.apiKeys.openai;
    const hasAnthropic = !!this.config.apiKeys.anthropic;
    console.log(`OpenAI API Key: ${hasOpenAI ? chalk.green('✅ Configured') : chalk.yellow('⚠️ Not set')}`);
    console.log(`Anthropic API Key: ${hasAnthropic ? chalk.green('✅ Configured') : chalk.yellow('⚠️ Not set')}`);
    
    // Check setup status
    console.log(`Setup complete: ${this.config.setupComplete ? chalk.green('✅ Yes') : chalk.red('❌ No')}`);
    
    if (!this.config.setupComplete) {
      console.log(chalk.cyan('\nRun `palette setup` to complete initial setup.'));
    } else if (!hasOpenAI && !hasAnthropic) {
      console.log(chalk.yellow('\n⚠️ No API keys configured. Some features may not work.'));
      console.log(chalk.cyan('Run `palette config` to set up API keys.'));
    }
  }

  public async configure(): Promise<void> {
    console.log(chalk.blue('\n⚙️ Configuration'));
    
    const { action } = await inquirer.prompt([
      {
        type: 'list',
        name: 'action',
        message: 'What would you like to configure?',
        choices: [
          { name: 'Set API Keys', value: 'api-keys' },
          { name: 'Reset Python Path', value: 'python-path' },
          { name: 'Reinstall Palette', value: 'reinstall' },
          { name: 'Reset Everything', value: 'reset' }
        ]
      }
    ]);

    switch (action) {
      case 'api-keys':
        await this.setupApiKeys();
        break;
        
      case 'python-path':
        this.config.pythonPath = undefined;
        console.log(chalk.green('Python path reset. It will be auto-detected on next run.'));
        break;
        
      case 'reinstall':
        await this.setupEnvironment();
        break;
        
      case 'reset':
        const { confirm } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'confirm',
            message: 'This will reset all configuration. Continue?',
            default: false
          }
        ]);
        
        if (confirm) {
          this.config = { paletteInstalled: false, setupComplete: false, apiKeys: {} };
          console.log(chalk.green('Configuration reset. Run `palette setup` to reconfigure.'));
        }
        break;
    }
    
    this.saveConfig();
  }

  public async run(): Promise<void> {
    const program = new Command();
    
    program
      .name('palette')
      .description('Palette AI - Zero-friction React component generator')
      .version('1.0.0');

    program
      .command('status')
      .description('Check installation and configuration status')
      .action(() => this.checkStatus());

    program
      .command('setup')
      .description('Run initial setup')
      .action(async () => {
        const success = await this.firstTimeSetup();
        process.exit(success ? 0 : 1);
      });

    program
      .command('config')
      .description('Configure Palette settings')
      .action(() => this.configure());

    program
      .command('generate')
      .description('Generate a React component')
      .argument('<description>', 'Component description')
      .option('-f, --framework <framework>', 'Framework (react, nextjs)')
      .option('-o, --output <path>', 'Output path')
      .option('--ui <library>', 'UI library (tailwind, chakra, material)')
      .action(async (description, options) => {
        const args = ['generate', description];
        if (options.framework) args.push('--framework', options.framework);
        if (options.output) args.push('--output', options.output);
        if (options.ui) args.push('--ui', options.ui);
        
        await this.runPalette(args);
      });

    program
      .command('analyze')
      .description('Analyze current project')
      .action(() => this.runPalette(['analyze']));

    // Forward any other commands to the Python CLI
    program
      .command('*')
      .description('Forward command to Palette CLI')
      .action(() => {
        const args = process.argv.slice(2);
        this.runPalette(args);
      });

    // If no command specified, show help or forward to Python CLI
    if (process.argv.length === 2) {
      program.help();
    } else {
      await program.parseAsync();
    }
  }
}

// Main entry point
if (require.main === module) {
  const wrapper = new PaletteWrapper();
  wrapper.run().catch((error) => {
    console.error(chalk.red('Unexpected error:'), error);
    process.exit(1);
  });
}

export default PaletteWrapper;