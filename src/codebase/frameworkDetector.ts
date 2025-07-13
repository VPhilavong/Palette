/**
 * Framework Detector
 * 
 * This file detects and analyzes the project's framework and technology stack:
 * - Identifies React, Vue, Angular, and other frontend frameworks
 * - Detects UI libraries (Material-UI, Ant Design, Chakra UI, etc.)
 * - Analyzes package.json for dependencies and versions
 * - Identifies state management solutions (Redux, Zustand, etc.)
 * - Detects TypeScript usage and configuration
 * - Provides confidence scores for framework detection
 * 
 * Essential for generating framework-appropriate code.
 */

import * as vscode from 'vscode';
import { Framework, ProjectMetadata } from '../types';

export class FrameworkDetector {
    async detectProjectFrameworks(): Promise<ProjectMetadata> {
        const metadata: ProjectMetadata = {
            frameworks: [],
            dependencies: {},
            devDependencies: {},
            hasTypeScript: false,
            uiLibraries: [],
            stateManagement: [],
            rootPath: ''
        };

        // Step 1: Analyze package.json
        await this.analyzePackageJson(metadata);

        // Step 2: Analyze imports in code files
        await this.analyzeCodeImports(metadata);

        // Step 3: Detect TypeScript
        metadata.hasTypeScript = await this.detectTypeScript();

        return metadata;
    }

    private async analyzePackageJson(metadata: ProjectMetadata): Promise<void> {
        if (!vscode.workspace.workspaceFolders) {
            return;
        }

        // Try to find package.json in any workspace folder
        for (const workspaceFolder of vscode.workspace.workspaceFolders) {
            try {
                const packageJsonUri = vscode.Uri.joinPath(workspaceFolder.uri, 'package.json');
                const content = await vscode.workspace.fs.readFile(packageJsonUri);
                const packageJson = JSON.parse(content.toString());

                metadata.dependencies = packageJson.dependencies || {};
                metadata.devDependencies = packageJson.devDependencies || {};

                // Detect frameworks based on dependencies
                this.detectFrameworksFromDependencies(metadata);
                this.detectUILibraries(metadata);
                this.detectStateManagement(metadata);

                console.log(`Found package.json in ${workspaceFolder.name}, detected ${metadata.frameworks.length} frameworks`);
                return; // Found one, we're done
            } catch (error) {
                // Try next workspace folder
                continue;
            }
        }

        console.log('No package.json found in any workspace folder, relying on code analysis');
    }

    private detectFrameworksFromDependencies(metadata: ProjectMetadata): void {
        const allDeps = { ...metadata.dependencies, ...metadata.devDependencies };

        const frameworkMap: Record<string, Framework> = {
            'react': { name: 'React', version: allDeps['react'], detected: false, confidence: 0 },
            'next': { name: 'Next.js', version: allDeps['next'], detected: false, confidence: 0 },
            'vue': { name: 'Vue', version: allDeps['vue'], detected: false, confidence: 0 },
            'nuxt': { name: 'Nuxt', version: allDeps['nuxt'], detected: false, confidence: 0 },
            'angular': { name: 'Angular', version: allDeps['@angular/core'], detected: false, confidence: 0 },
            'svelte': { name: 'Svelte', version: allDeps['svelte'], detected: false, confidence: 0 }
        };

        for (const framework of Object.values(frameworkMap)) {
            if (framework.version) {
                framework.detected = true;
                framework.confidence = 1.0;
                metadata.frameworks.push(framework);
            }
        }
    }

    private detectUILibraries(metadata: ProjectMetadata): void {
        const allDeps = { ...metadata.dependencies, ...metadata.devDependencies };

        const uiLibraryPatterns = [
            'tailwindcss',
            '@mui/material',
            '@chakra-ui/react',
            'antd',
            'react-bootstrap',
            'semantic-ui-react',
            '@mantine/core',
            'styled-components',
            '@emotion/react',
            'lucide-react',
            'react-icons'
        ];

        metadata.uiLibraries = uiLibraryPatterns.filter(lib => lib in allDeps);
    }

    private detectStateManagement(metadata: ProjectMetadata): void {
        const allDeps = { ...metadata.dependencies, ...metadata.devDependencies };

        const stateManagementPatterns = [
            'redux',
            '@reduxjs/toolkit',
            'zustand',
            'jotai',
            'recoil',
            'mobx',
            'valtio'
        ];

        metadata.stateManagement = stateManagementPatterns.filter(lib => lib in allDeps);
    }

    private async analyzeCodeImports(metadata: ProjectMetadata): Promise<void> {
        // Find React/JSX files to analyze imports
        const files = await vscode.workspace.findFiles(
            '**/*.{js,jsx,ts,tsx}',
            '{node_modules,dist,build}/**',
            50 // Limit for performance
        );

        const importCounts: Record<string, number> = {};
        const jsxUsage = { count: 0, files: 0 };

        for (const file of files.slice(0, 20)) { // Sample more files for better detection
            try {
                const content = await vscode.workspace.fs.readFile(file);
                const text = content.toString();
                
                // Simple regex to find imports
                const importRegex = /import\s+(?:[\w\s{},*]+\s+from\s+)?['"]([^'"]+)['"]/g;
                let match;

                while ((match = importRegex.exec(text)) !== null) {
                    const module = match[1];
                    importCounts[module] = (importCounts[module] || 0) + 1;
                }

                // Check for JSX usage
                if (text.includes('<') && text.includes('/>') || text.includes('</')) {
                    jsxUsage.count += (text.match(/<[A-Z][^>]*>/g) || []).length;
                    jsxUsage.files++;
                }
            } catch (error) {
                // Skip files that can't be read
            }
        }

        // Detect frameworks from imports even without package.json
        this.detectFrameworksFromImports(metadata, importCounts, jsxUsage);

        // Boost confidence for frameworks found in imports
        for (const framework of metadata.frameworks) {
            const frameworkKey = framework.name.toLowerCase();
            if (importCounts[frameworkKey] || importCounts[`${frameworkKey}/`]) {
                framework.confidence = Math.min(framework.confidence + 0.3, 1.0);
            }
        }
    }

    private detectFrameworksFromImports(metadata: ProjectMetadata, importCounts: Record<string, number>, jsxUsage: {count: number, files: number}): void {
        // React detection - be more strict to avoid false positives
        if (importCounts['react'] || (jsxUsage.files > 0 && !importCounts['vue'])) {
            // Only detect React if we have actual React imports OR JSX without Vue
            const hasReactImports = importCounts['react'] > 0;
            const hasJSXWithoutVue = jsxUsage.files > 0 && !importCounts['vue'] && !importCounts['vitepress'];
            
            if (hasReactImports || hasJSXWithoutVue) {
                const reactFramework: Framework = {
                    name: 'React',
                    detected: true,
                    confidence: hasReactImports ? 0.9 : 0.6
                };
                
                if (!metadata.frameworks.some(f => f.name === 'React')) {
                    metadata.frameworks.push(reactFramework);
                }
            }
        }

        // Next.js detection
        if (importCounts['next'] || importCounts['next/'] || importCounts['next/router'] || importCounts['next/head']) {
            const nextFramework: Framework = {
                name: 'Next.js',
                detected: true,
                confidence: 0.8
            };
            
            if (!metadata.frameworks.some(f => f.name === 'Next.js')) {
                metadata.frameworks.push(nextFramework);
            }
        }

        // Vue detection
        if (importCounts['vue'] || importCounts['@vue/'] || 
            Object.keys(importCounts).some(imp => imp.includes('vitepress'))) {
            const vueFramework: Framework = {
                name: 'Vue',
                detected: true,
                confidence: importCounts['vue'] ? 0.9 : 0.8
            };
            
            if (!metadata.frameworks.some(f => f.name === 'Vue')) {
                metadata.frameworks.push(vueFramework);
            }
        }

        // VitePress detection
        if (importCounts['vitepress'] || Object.keys(importCounts).some(imp => imp.includes('vitepress'))) {
            const vitepressFramework: Framework = {
                name: 'VitePress',
                detected: true,
                confidence: 0.9
            };
            
            if (!metadata.frameworks.some(f => f.name === 'VitePress')) {
                metadata.frameworks.push(vitepressFramework);
            }
        }

        // UI Library detection from imports
        const uiLibraryImports = [
            { pattern: '@mui/', name: 'Material-UI' },
            { pattern: '@chakra-ui/', name: 'Chakra UI' },
            { pattern: 'antd', name: 'Ant Design' },
            { pattern: 'react-bootstrap', name: 'React Bootstrap' },
            { pattern: '@mantine/', name: 'Mantine' },
            { pattern: 'styled-components', name: 'Styled Components' },
            { pattern: '@emotion/', name: 'Emotion' },
            { pattern: 'lucide-react', name: 'Lucide React' }
        ];

        for (const lib of uiLibraryImports) {
            const hasImport = Object.keys(importCounts).some(imp => imp.includes(lib.pattern));
            if (hasImport && !metadata.uiLibraries.includes(lib.name)) {
                metadata.uiLibraries.push(lib.name);
            }
        }

        console.log(`Code analysis: JSX in ${jsxUsage.files} files, ${Object.keys(importCounts).length} unique imports`);
    }

    private async detectTypeScript(): Promise<boolean> {
        try {
            const tsconfigUri = vscode.Uri.joinPath(
                vscode.workspace.workspaceFolders![0].uri,
                'tsconfig.json'
            );
            await vscode.workspace.fs.stat(tsconfigUri);
            return true;
        } catch {
            // Check for .ts/.tsx files
            const tsFiles = await vscode.workspace.findFiles('**/*.{ts,tsx}', 'node_modules/**', 1);
            return tsFiles.length > 0;
        }
    }
}