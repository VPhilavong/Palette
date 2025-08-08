/**
 * Design System Analyzer
 * Analyzes design systems, UI libraries, and design tokens in the codebase
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { 
    DesignSystemInfo, 
    DesignTokens, 
    DesignSystemComponent,
    DesignPattern,
    ComponentUsage
} from './types';

export class DesignSystemAnalyzer {

    /**
     * Analyze design system in the workspace
     */
    async analyze(workspacePath: string): Promise<DesignSystemInfo> {
        try {
            console.log('🧠 Analyzing design system...');

            const [detectedLibrary, tokens, components, patterns] = await Promise.all([
                this.detectDesignLibrary(workspacePath),
                this.extractDesignTokens(workspacePath),
                this.analyzeDesignSystemComponents(workspacePath),
                this.identifyDesignPatterns(workspacePath)
            ]);

            // Type-safe library assignment
            const library = this.validateLibraryType(detectedLibrary);

            const designSystem: DesignSystemInfo = {
                library,
                tokens,
                components,
                patterns
            };

            // Add theme analysis if available
            if (library) {
                designSystem.theme = await this.analyzeTheme(workspacePath, library);
            }

            console.log(`🧠 Design system analysis complete: ${library || 'No library detected'}`);
            return designSystem;

        } catch (error) {
            console.warn('🧠 Design system analysis failed:', error);
            return this.getDefaultDesignSystem();
        }
    }

    /**
     * Detect which design/UI library is being used
     */
    private async detectDesignLibrary(workspacePath: string): Promise<string | undefined> {
        try {
            const packageJsonPath = vscode.Uri.file(path.join(workspacePath, 'package.json'));
            const content = await vscode.workspace.fs.readFile(packageJsonPath);
            const packageJson = JSON.parse(content.toString());

            const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };

            // Check for popular UI libraries
            const libraryMappings: Record<string, string> = {
                '@radix-ui/react-accordion': 'shadcn/ui',
                'shadcn-ui': 'shadcn/ui',
                '@mui/material': 'material-ui',
                '@material-ui/core': 'material-ui',
                'antd': 'antd',
                '@chakra-ui/react': 'chakra-ui',
                '@mantine/core': 'mantine',
                'react-bootstrap': 'react-bootstrap',
                'semantic-ui-react': 'semantic-ui',
                '@headlessui/react': 'headless-ui',
                'react-aria': 'react-aria',
                'grommet': 'grommet',
                'evergreen-ui': 'evergreen',
                'theme-ui': 'theme-ui'
            };

            // Check direct dependencies
            for (const [dep, library] of Object.entries(libraryMappings)) {
                if (dependencies[dep]) {
                    return library;
                }
            }

            // Special check for shadcn/ui (uses @radix-ui components)
            const radixComponents = Object.keys(dependencies).filter(dep => 
                dep.startsWith('@radix-ui/react-')
            );

            if (radixComponents.length >= 3) {
                // Check for shadcn/ui specific patterns
                const hasShadcnPatterns = await this.checkForShadcnPatterns(workspacePath);
                if (hasShadcnPatterns) {
                    return 'shadcn/ui';
                }
            }

            // Check for Tailwind CSS (often used with headless components)
            if (dependencies.tailwindcss || dependencies['@tailwindcss/forms']) {
                const hasTailwindConfig = await this.checkForTailwindConfig(workspacePath);
                if (hasTailwindConfig) {
                    return 'tailwind + headless';
                }
            }

            return undefined;

        } catch (error) {
            console.warn('🧠 Library detection failed:', error);
            return undefined;
        }
    }

    /**
     * Check for shadcn/ui specific patterns
     */
    private async checkForShadcnPatterns(workspacePath: string): Promise<boolean> {
        try {
            // Check for components.json (shadcn/ui config)
            try {
                const componentsJsonPath = vscode.Uri.file(path.join(workspacePath, 'components.json'));
                await vscode.workspace.fs.stat(componentsJsonPath);
                return true;
            } catch {}

            // Check for lib/utils.ts with cn function (common shadcn/ui pattern)
            try {
                const utilsPath = vscode.Uri.file(path.join(workspacePath, 'lib', 'utils.ts'));
                const content = await vscode.workspace.fs.readFile(utilsPath);
                const text = content.toString();
                
                if (/function cn\(|const cn =|export.*cn/.test(text)) {
                    return true;
                }
            } catch {}

            // Check for typical shadcn/ui component structure
            const componentsPattern = new vscode.RelativePattern(workspacePath, '**/components/ui/*.{tsx,jsx}');
            const uiComponents = await vscode.workspace.findFiles(componentsPattern, '**/node_modules/**', 5);
            
            return uiComponents.length > 0;

        } catch {
            return false;
        }
    }

    /**
     * Check for Tailwind CSS configuration
     */
    private async checkForTailwindConfig(workspacePath: string): Promise<boolean> {
        const configFiles = [
            'tailwind.config.js',
            'tailwind.config.ts',
            'tailwind.config.cjs',
            'tailwind.config.mjs'
        ];

        for (const configFile of configFiles) {
            try {
                const configPath = vscode.Uri.file(path.join(workspacePath, configFile));
                await vscode.workspace.fs.stat(configPath);
                return true;
            } catch {}
        }

        return false;
    }

    /**
     * Extract design tokens from various sources
     */
    private async extractDesignTokens(workspacePath: string): Promise<DesignTokens> {
        const tokens: DesignTokens = {
            colors: {},
            spacing: {},
            typography: {},
            breakpoints: {},
            shadows: {},
            borderRadius: {}
        };

        try {
            // Try to extract from Tailwind config
            const tailwindTokens = await this.extractTailwindTokens(workspacePath);
            if (tailwindTokens) {
                Object.assign(tokens, tailwindTokens);
            }

            // Try to extract from CSS custom properties
            const cssTokens = await this.extractCSSTokens(workspacePath);
            if (cssTokens) {
                this.mergeCSSTokens(tokens, cssTokens);
            }

            // Try to extract from theme files
            const themeTokens = await this.extractThemeTokens(workspacePath);
            if (themeTokens) {
                this.mergeThemeTokens(tokens, themeTokens);
            }

        } catch (error) {
            console.warn('🧠 Token extraction failed:', error);
        }

        return tokens;
    }

    /**
     * Extract design tokens from Tailwind config
     */
    private async extractTailwindTokens(workspacePath: string): Promise<Partial<DesignTokens> | null> {
        try {
            const configFiles = [
                'tailwind.config.js',
                'tailwind.config.ts'
            ];

            for (const configFile of configFiles) {
                try {
                    const configPath = vscode.Uri.file(path.join(workspacePath, configFile));
                    const content = await vscode.workspace.fs.readFile(configPath);
                    const text = content.toString();

                    // Basic parsing - in a real implementation, you'd use a proper JS parser
                    const tokens: Partial<DesignTokens> = {};

                    // Extract colors
                    const colorsMatch = text.match(/colors:\s*{([^}]*)}/s);
                    if (colorsMatch) {
                        tokens.colors = this.parseConfigObject(colorsMatch[1], 'colors');
                    }

                    // Extract spacing
                    const spacingMatch = text.match(/spacing:\s*{([^}]*)}/s);
                    if (spacingMatch) {
                        tokens.spacing = this.parseConfigObject(spacingMatch[1], 'spacing');
                    }

                    // Extract breakpoints (screens in Tailwind)
                    const screensMatch = text.match(/screens:\s*{([^}]*)}/s);
                    if (screensMatch) {
                        tokens.breakpoints = this.parseConfigObject(screensMatch[1], 'screens');
                    }

                    // Extract border radius
                    const borderRadiusMatch = text.match(/borderRadius:\s*{([^}]*)}/s);
                    if (borderRadiusMatch) {
                        tokens.borderRadius = this.parseConfigObject(borderRadiusMatch[1], 'borderRadius');
                    }

                    if (Object.keys(tokens).length > 0) {
                        return tokens;
                    }

                } catch (error) {
                    console.warn(`Failed to parse ${configFile}:`, error);
                }
            }

            return null;
        } catch {
            return null;
        }
    }

    /**
     * Parse configuration object from string (simplified)
     */
    private parseConfigObject(content: string, type: string): Record<string, string> {
        const result: Record<string, string> = {};
        
        // Simple key-value parsing (not a complete JS parser)
        const lines = content.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
            const match = line.match(/['"`]?(\w+)['"`]?\s*:\s*['"`]([^'"`]+)['"`]/);
            if (match) {
                const [, key, value] = match;
                result[key] = value;
            }
        }

        // Add some defaults for common Tailwind values
        if (type === 'colors' && Object.keys(result).length === 0) {
            result['primary'] = 'hsl(var(--primary))';
            result['secondary'] = 'hsl(var(--secondary))';
            result['background'] = 'hsl(var(--background))';
            result['foreground'] = 'hsl(var(--foreground))';
        }

        return result;
    }

    /**
     * Extract design tokens from CSS files
     */
    private async extractCSSTokens(workspacePath: string): Promise<Record<string, Record<string, string>> | null> {
        try {
            const cssPattern = new vscode.RelativePattern(workspacePath, '**/*.{css,scss}');
            const cssFiles = await vscode.workspace.findFiles(cssPattern, '**/node_modules/**', 10);

            const tokens: Record<string, Record<string, string>> = {};

            for (const file of cssFiles) {
                try {
                    const content = await vscode.workspace.fs.readFile(file);
                    const text = content.toString();

                    // Extract CSS custom properties
                    const customProps = text.match(/--[\w-]+:\s*[^;]+;/g);
                    if (customProps) {
                        customProps.forEach(prop => {
                            const [key, value] = prop.split(':').map(s => s.trim());
                            const cleanKey = key.replace('--', '');
                            const cleanValue = value.replace(';', '');

                            // Categorize tokens
                            let category = 'other';
                            if (/color|bg|text|border/.test(cleanKey)) category = 'colors';
                            else if (/space|margin|padding|gap/.test(cleanKey)) category = 'spacing';
                            else if (/font|text|size/.test(cleanKey)) category = 'typography';
                            else if (/shadow/.test(cleanKey)) category = 'shadows';
                            else if (/radius|rounded/.test(cleanKey)) category = 'borderRadius';

                            if (!tokens[category]) tokens[category] = {};
                            tokens[category][cleanKey] = cleanValue;
                        });
                    }

                } catch (error) {
                    console.warn(`Failed to parse CSS file ${file.fsPath}:`, error);
                }
            }

            return Object.keys(tokens).length > 0 ? tokens : null;

        } catch {
            return null;
        }
    }

    /**
     * Extract tokens from theme files
     */
    private async extractThemeTokens(workspacePath: string): Promise<Record<string, any> | null> {
        try {
            const themeFiles = [
                'theme.ts',
                'theme.js',
                'src/theme.ts',
                'src/theme.js',
                'config/theme.ts',
                'config/theme.js'
            ];

            for (const themeFile of themeFiles) {
                try {
                    const themePath = vscode.Uri.file(path.join(workspacePath, themeFile));
                    const content = await vscode.workspace.fs.readFile(themePath);
                    const text = content.toString();

                    // Look for theme objects (simplified parsing)
                    const themeMatch = text.match(/(?:export\s+const|const)\s+theme\s*=\s*{([^}]+)}/s);
                    if (themeMatch) {
                        // This is a simplified extraction - real implementation would use AST
                        return { extracted: true, source: themeFile };
                    }

                } catch {}
            }

            return null;
        } catch {
            return null;
        }
    }

    /**
     * Merge CSS tokens into design tokens
     */
    private mergeCSSTokens(tokens: DesignTokens, cssTokens: Record<string, Record<string, string>>): void {
        Object.entries(cssTokens).forEach(([category, categoryTokens]) => {
            if (category in tokens) {
                Object.assign((tokens as any)[category], categoryTokens);
            }
        });
    }

    /**
     * Merge theme tokens into design tokens
     */
    private mergeThemeTokens(tokens: DesignTokens, themeTokens: Record<string, any>): void {
        // Simplified merging - would be more sophisticated in real implementation
        if (themeTokens.extracted) {
            // Mark that theme tokens were found
        }
    }

    /**
     * Analyze design system components
     */
    private async analyzeDesignSystemComponents(workspacePath: string): Promise<DesignSystemComponent[]> {
        const components: DesignSystemComponent[] = [];

        try {
            // Look for UI component directories
            const uiPatterns = [
                '**/components/ui/*.{tsx,jsx}',
                '**/ui/*.{tsx,jsx}',
                '**/components/*.{tsx,jsx}'
            ];

            for (const pattern of uiPatterns) {
                try {
                    const componentPattern = new vscode.RelativePattern(workspacePath, pattern);
                    const files = await vscode.workspace.findFiles(componentPattern, '**/node_modules/**', 20);

                    for (const file of files) {
                        const component = await this.analyzeDesignComponent(file);
                        if (component) {
                            components.push(component);
                        }
                    }

                } catch (error) {
                    console.warn(`Failed to analyze UI components with pattern ${pattern}:`, error);
                }
            }

        } catch (error) {
            console.warn('🧠 Design component analysis failed:', error);
        }

        return components;
    }

    /**
     * Analyze individual design component
     */
    private async analyzeDesignComponent(fileUri: vscode.Uri): Promise<DesignSystemComponent | null> {
        try {
            const content = await vscode.workspace.fs.readFile(fileUri);
            const text = content.toString();
            
            const fileName = path.basename(fileUri.fsPath, path.extname(fileUri.fsPath));

            // Extract variants (simplified)
            const variants = this.extractComponentVariants(text);

            return {
                name: fileName,
                variants,
                props: this.extractComponentProps(text),
                usage: [] // Would be populated by usage analysis
            };

        } catch (error) {
            console.warn(`Failed to analyze design component ${fileUri.fsPath}:`, error);
            return null;
        }
    }

    /**
     * Extract component variants
     */
    private extractComponentVariants(content: string): string[] {
        const variants: Set<string> = new Set();

        // Look for variant definitions
        const variantPatterns = [
            /variant.*['"`](\w+)['"`]/g,
            /variants\s*:\s*{([^}]+)}/g,
            /'(\w+)'\s*:\s*['"`][^'"`]*['"`]/g
        ];

        variantPatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                const variant = match[1];
                if (variant && variant !== 'string' && variant !== 'default') {
                    variants.add(variant);
                }
            }
        });

        return Array.from(variants);
    }

    /**
     * Extract component props
     */
    private extractComponentProps(content: string): Record<string, any> {
        const props: Record<string, any> = {};

        // Look for props interface
        const propsMatch = content.match(/interface\s+\w*Props\s*{([^}]+)}/s);
        if (propsMatch) {
            const propsContent = propsMatch[1];
            const propLines = propsContent.split('\n').filter(line => line.trim());

            propLines.forEach(line => {
                const propMatch = line.match(/(\w+)(\??):\s*([^;]+)/);
                if (propMatch) {
                    const [, name, optional, type] = propMatch;
                    props[name] = {
                        type: type.trim(),
                        required: !optional,
                        optional: !!optional
                    };
                }
            });
        }

        return props;
    }

    /**
     * Identify design patterns
     */
    private async identifyDesignPatterns(workspacePath: string): Promise<DesignPattern[]> {
        const patterns: DesignPattern[] = [];

        try {
            // Common design patterns to look for
            const patternMappings = [
                { name: 'Card Layout', keywords: ['card', 'container'], description: 'Reusable card components for content display' },
                { name: 'Button Variants', keywords: ['button', 'btn'], description: 'Consistent button styling across the application' },
                { name: 'Form Controls', keywords: ['input', 'form', 'field'], description: 'Standardized form input components' },
                { name: 'Navigation', keywords: ['nav', 'menu', 'navigation'], description: 'Navigation components and patterns' },
                { name: 'Modal/Dialog', keywords: ['modal', 'dialog', 'popup'], description: 'Modal and dialog components for overlays' },
                { name: 'List/Table', keywords: ['list', 'table', 'grid'], description: 'Data display components' }
            ];

            // Search for components matching patterns
            const componentPattern = new vscode.RelativePattern(workspacePath, '**/*.{tsx,jsx}');
            const files = await vscode.workspace.findFiles(componentPattern, '**/node_modules/**', 50);

            for (const patternDef of patternMappings) {
                const matchingComponents: string[] = [];
                let frequency = 0;

                for (const file of files) {
                    const fileName = path.basename(file.fsPath, path.extname(file.fsPath)).toLowerCase();
                    
                    if (patternDef.keywords.some(keyword => fileName.includes(keyword))) {
                        matchingComponents.push(path.basename(file.fsPath));
                        frequency++;
                    }
                }

                if (matchingComponents.length >= 2) {
                    patterns.push({
                        name: patternDef.name,
                        description: patternDef.description,
                        components: matchingComponents,
                        structure: `Multiple components implementing ${patternDef.name.toLowerCase()} pattern`,
                        frequency
                    });
                }
            }

        } catch (error) {
            console.warn('🧠 Design pattern identification failed:', error);
        }

        return patterns;
    }

    /**
     * Analyze theme configuration
     */
    private async analyzeTheme(workspacePath: string, library: string): Promise<any> {
        try {
            switch (library) {
                case 'shadcn/ui':
                    return await this.analyzeShadcnTheme(workspacePath);
                case 'material-ui':
                    return await this.analyzeMuiTheme(workspacePath);
                case 'chakra-ui':
                    return await this.analyzeChakraTheme(workspacePath);
                default:
                    return await this.analyzeGenericTheme(workspacePath);
            }
        } catch (error) {
            console.warn(`🧠 Theme analysis failed for ${library}:`, error);
            return null;
        }
    }

    /**
     * Analyze shadcn/ui theme
     */
    private async analyzeShadcnTheme(workspacePath: string): Promise<any> {
        try {
            // Check for globals.css with CSS variables
            const globalsPath = vscode.Uri.file(path.join(workspacePath, 'app', 'globals.css'));
            
            try {
                const content = await vscode.workspace.fs.readFile(globalsPath);
                const text = content.toString();
                
                const darkModeSupport = text.includes('.dark') && text.includes('--');
                const customVariables = (text.match(/--[\w-]+:/g) || []).length;
                
                return {
                    type: 'shadcn/ui',
                    hasDarkMode: darkModeSupport,
                    customVariables,
                    cssVariables: true
                };
            } catch {
                // Try alternative locations
                const altPaths = ['src/globals.css', 'styles/globals.css'];
                for (const altPath of altPaths) {
                    try {
                        const content = await vscode.workspace.fs.readFile(vscode.Uri.file(path.join(workspacePath, altPath)));
                        return { type: 'shadcn/ui', detected: true };
                    } catch {}
                }
            }

            return { type: 'shadcn/ui', detected: false };
        } catch {
            return null;
        }
    }

    /**
     * Analyze Material-UI theme
     */
    private async analyzeMuiTheme(workspacePath: string): Promise<any> {
        // Look for theme configuration files
        const themeFiles = ['theme.ts', 'theme.js', 'src/theme.ts'];
        
        for (const themeFile of themeFiles) {
            try {
                const content = await vscode.workspace.fs.readFile(
                    vscode.Uri.file(path.join(workspacePath, themeFile))
                );
                const text = content.toString();
                
                if (text.includes('createTheme') || text.includes('createMuiTheme')) {
                    return {
                        type: 'material-ui',
                        hasCustomTheme: true,
                        configFile: themeFile
                    };
                }
            } catch {}
        }

        return { type: 'material-ui', hasCustomTheme: false };
    }

    /**
     * Analyze Chakra UI theme
     */
    private async analyzeChakraTheme(workspacePath: string): Promise<any> {
        try {
            // Look for Chakra theme extension
            const themeFiles = ['theme.ts', 'theme.js', 'chakra-theme.ts'];
            
            for (const themeFile of themeFiles) {
                try {
                    const content = await vscode.workspace.fs.readFile(
                        vscode.Uri.file(path.join(workspacePath, themeFile))
                    );
                    const text = content.toString();
                    
                    if (text.includes('extendTheme') || text.includes('@chakra-ui')) {
                        return {
                            type: 'chakra-ui',
                            hasExtendedTheme: true,
                            configFile: themeFile
                        };
                    }
                } catch {}
            }

            return { type: 'chakra-ui', hasExtendedTheme: false };
        } catch {
            return null;
        }
    }

    /**
     * Analyze generic theme
     */
    private async analyzeGenericTheme(workspacePath: string): Promise<any> {
        try {
            // Look for common theme patterns
            const hasThemeProvider = await this.searchForPattern(workspacePath, 'ThemeProvider');
            const hasCSSVariables = await this.searchForCSSVariables(workspacePath);
            
            return {
                type: 'generic',
                hasThemeProvider,
                hasCSSVariables
            };
        } catch {
            return null;
        }
    }

    /**
     * Search for specific pattern in codebase
     */
    private async searchForPattern(workspacePath: string, pattern: string): Promise<boolean> {
        try {
            const files = await vscode.workspace.findFiles(
                new vscode.RelativePattern(workspacePath, '**/*.{tsx,jsx,ts,js}'),
                '**/node_modules/**',
                20
            );

            for (const file of files) {
                try {
                    const content = await vscode.workspace.fs.readFile(file);
                    if (content.toString().includes(pattern)) {
                        return true;
                    }
                } catch {}
            }

            return false;
        } catch {
            return false;
        }
    }

    /**
     * Search for CSS variables
     */
    private async searchForCSSVariables(workspacePath: string): Promise<boolean> {
        try {
            const cssFiles = await vscode.workspace.findFiles(
                new vscode.RelativePattern(workspacePath, '**/*.{css,scss}'),
                '**/node_modules/**',
                10
            );

            for (const file of cssFiles) {
                try {
                    const content = await vscode.workspace.fs.readFile(file);
                    if (/--[\w-]+\s*:/.test(content.toString())) {
                        return true;
                    }
                } catch {}
            }

            return false;
        } catch {
            return false;
        }
    }

    /**
     * Validate and convert library string to proper type
     */
    private validateLibraryType(library: string | undefined): 'shadcn/ui' | 'material-ui' | 'antd' | 'chakra-ui' | 'mantine' | 'custom' | undefined {
        const validLibraries = ['shadcn/ui', 'material-ui', 'antd', 'chakra-ui', 'mantine'] as const;
        
        if (!library) return undefined;
        
        if (validLibraries.includes(library as any)) {
            return library as 'shadcn/ui' | 'material-ui' | 'antd' | 'chakra-ui' | 'mantine';
        }
        
        // For any other detected library, mark as custom
        return 'custom';
    }

    /**
     * Get default design system when analysis fails
     */
    private getDefaultDesignSystem(): DesignSystemInfo {
        return {
            tokens: {
                colors: {},
                spacing: {},
                typography: {},
                breakpoints: {},
                shadows: {},
                borderRadius: {}
            },
            components: [],
            patterns: []
        };
    }
}