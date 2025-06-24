import * as fs from 'fs';
import * as path from 'path';
import {
    DesignSystemAnalysis,
    ThemeStructure,
    ThemeVariable,
    ColorPalette,
    SpacingSystem,
    TypographySystem,
    IconSystem,
    DesignToken,
    ComponentInfo
} from './types';

export class DesignSystemAnalyzer {
    
    /**
     * Analyze design system patterns in the codebase
     */
    async analyzeDesignSystem(components: ComponentInfo[], rootPath: string): Promise<DesignSystemAnalysis> {
        console.log('🎨 Analyzing design system patterns...');
        
        const analysis: DesignSystemAnalysis = {};
        
        // Detect component library
        analysis.componentLibrary = await this.detectComponentLibrary(rootPath);
        
        // Analyze theme structure
        analysis.themeStructure = await this.analyzeThemeStructure(rootPath);
        
        // Analyze color patterns
        analysis.colorPalette = await this.analyzeColorPalette(components, rootPath);
        
        // Analyze spacing patterns
        analysis.spacingSystem = await this.analyzeSpacingSystem(components, rootPath);
        
        // Analyze typography
        analysis.typographySystem = await this.analyzeTypographySystem(components, rootPath);
        
        // Analyze icon usage
        analysis.iconSystem = await this.analyzeIconSystem(components, rootPath);
        
        // Extract design tokens
        analysis.designTokens = await this.extractDesignTokens(rootPath);
        
        return analysis;
    }
    
    /**
     * Detect component library being used
     */
    private async detectComponentLibrary(rootPath: string): Promise<string | undefined> {
        try {
            const packageJsonPath = path.join(rootPath, 'package.json');
            if (fs.existsSync(packageJsonPath)) {
                const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
                const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
                
                // Check for popular component libraries
                const libraries = {
                    '@mui/material': 'Material-UI',
                    '@chakra-ui/react': 'Chakra UI',
                    'antd': 'Ant Design',
                    '@mantine/core': 'Mantine',
                    'react-bootstrap': 'React Bootstrap',
                    '@headlessui/react': 'Headless UI',
                    '@radix-ui/react-dialog': 'Radix UI',
                    'semantic-ui-react': 'Semantic UI React'
                };
                
                for (const [pkg, name] of Object.entries(libraries)) {
                    if (pkg in allDeps) {
                        return name;
                    }
                }
            }
        } catch (error) {
            console.warn('Error detecting component library:', error);
        }
        
        return undefined;
    }
    
    /**
     * Analyze theme structure
     */
    private async analyzeThemeStructure(rootPath: string): Promise<ThemeStructure | undefined> {
        const themeFiles = await this.findThemeFiles(rootPath);
        if (themeFiles.length === 0) return undefined;
        
        const themeStructure: ThemeStructure = {
            provider: 'unknown',
            variables: [],
            breakpoints: {},
            darkMode: false
        };
        
        for (const themeFile of themeFiles) {
            const content = fs.readFileSync(themeFile, 'utf8');
            
            // Detect theme provider
            if (content.includes('ThemeProvider')) {
                themeStructure.provider = 'styled-components';
            } else if (content.includes('ChakraProvider')) {
                themeStructure.provider = 'chakra-ui';
            } else if (content.includes('MuiThemeProvider')) {
                themeStructure.provider = 'material-ui';
            }
            
            // Extract theme variables
            const variables = this.extractThemeVariables(content);
            themeStructure.variables.push(...variables);
            
            // Extract breakpoints
            const breakpoints = this.extractBreakpoints(content);
            Object.assign(themeStructure.breakpoints, breakpoints);
            
            // Check for dark mode
            if (content.includes('dark') || content.includes('darkMode')) {
                themeStructure.darkMode = true;
            }
            
            themeStructure.themePath = themeFile;
        }
        
        return themeStructure;
    }
    
    /**
     * Analyze color palette from components
     */
    private async analyzeColorPalette(components: ComponentInfo[], rootPath: string): Promise<ColorPalette | undefined> {
        const allClasses = this.getAllClassNames(components);
        const colorClasses = allClasses.filter(cls => this.isColorClass(cls));
        
        if (colorClasses.length === 0) return undefined;
        
        const palette: ColorPalette = {
            primary: [],
            secondary: [],
            semantic: {},
            neutral: []
        };
        
        // Categorize colors
        colorClasses.forEach(cls => {
            if (cls.includes('primary')) {
                palette.primary.push(cls);
            } else if (cls.includes('secondary')) {
                palette.secondary.push(cls);
            } else if (cls.includes('success') || cls.includes('error') || cls.includes('warning')) {
                const type = cls.includes('success') ? 'success' : 
                           cls.includes('error') ? 'error' : 'warning';
                if (!palette.semantic[type]) palette.semantic[type] = [];
                palette.semantic[type].push(cls);
            } else if (cls.includes('gray') || cls.includes('neutral')) {
                palette.neutral.push(cls);
            }
        });
        
        return palette;
    }
    
    /**
     * Analyze spacing system
     */
    private async analyzeSpacingSystem(components: ComponentInfo[], rootPath: string): Promise<SpacingSystem | undefined> {
        const allClasses = this.getAllClassNames(components);
        const spacingClasses = allClasses.filter(cls => this.isSpacingClass(cls));
        
        if (spacingClasses.length === 0) return undefined;
        
        // Detect spacing unit (Tailwind uses rem/px)
        const unit = spacingClasses.some(cls => cls.match(/p-\d+|m-\d+/)) ? 'rem' : 'px';
        
        // Extract spacing scale
        const scale: Record<string, string> = {};
        const scalePattern = /(?:p|m|px|py|mx|my)-(\d+|\w+)/g;
        
        spacingClasses.forEach(cls => {
            const match = cls.match(scalePattern);
            if (match) {
                const value = cls.split('-').pop();
                if (value) {
                    scale[value] = this.convertSpacingValue(value, unit);
                }
            }
        });
        
        return {
            unit,
            scale,
            customValues: this.extractCustomSpacingValues(spacingClasses)
        };
    }
    
    /**
     * Analyze typography system
     */
    private async analyzeTypographySystem(components: ComponentInfo[], rootPath: string): Promise<TypographySystem | undefined> {
        const allClasses = this.getAllClassNames(components);
        const typographyClasses = allClasses.filter(cls => this.isTypographyClass(cls));
        
        if (typographyClasses.length === 0) return undefined;
        
        const typography: TypographySystem = {
            fontFamilies: {},
            fontSizes: {},
            fontWeights: {},
            lineHeights: {}
        };
        
        // Extract font families
        const fontFamilyClasses = typographyClasses.filter(cls => cls.includes('font-'));
        fontFamilyClasses.forEach(cls => {
            const family = cls.replace('font-', '');
            typography.fontFamilies[family] = this.resolveFontFamily(family);
        });
        
        // Extract font sizes
        const fontSizeClasses = typographyClasses.filter(cls => cls.match(/text-(xs|sm|base|lg|xl|\d+xl)/));
        fontSizeClasses.forEach(cls => {
            const size = cls.replace('text-', '');
            typography.fontSizes[size] = this.resolveFontSize(size);
        });
        
        // Extract font weights
        const fontWeightClasses = typographyClasses.filter(cls => cls.match(/font-(thin|light|normal|medium|semibold|bold|extrabold|black|\d+)/));
        fontWeightClasses.forEach(cls => {
            const weight = cls.replace('font-', '');
            typography.fontWeights[weight] = this.resolveFontWeight(weight);
        });
        
        return typography;
    }
    
    /**
     * Analyze icon system
     */
    private async analyzeIconSystem(components: ComponentInfo[], rootPath: string): Promise<IconSystem | undefined> {
        // Check for icon libraries in package.json
        const packageJsonPath = path.join(rootPath, 'package.json');
        let library = 'unknown';
        
        if (fs.existsSync(packageJsonPath)) {
            const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
            const allDeps = { ...packageJson.dependencies, ...packageJson.devDependencies };
            
            if ('react-icons' in allDeps) library = 'react-icons';
            else if ('lucide-react' in allDeps) library = 'lucide-react';
            else if ('heroicons' in allDeps) library = 'heroicons';
            else if ('@heroicons/react' in allDeps) library = 'heroicons';
        }
        
        // Analyze icon usage in components
        const iconUsage = this.extractIconUsage(components);
        
        return {
            library,
            usage: iconUsage,
            customIcons: this.hasCustomIcons(rootPath)
        };
    }
    
    /**
     * Extract design tokens
     */
    private async extractDesignTokens(rootPath: string): Promise<DesignToken[] | undefined> {
        const tokenFiles = await this.findDesignTokenFiles(rootPath);
        if (tokenFiles.length === 0) return undefined;
        
        const tokens: DesignToken[] = [];
        
        for (const tokenFile of tokenFiles) {
            const content = fs.readFileSync(tokenFile, 'utf8');
            
            // Parse different token formats
            if (tokenFile.endsWith('.json')) {
                tokens.push(...this.parseJsonTokens(content));
            } else if (tokenFile.endsWith('.js') || tokenFile.endsWith('.ts')) {
                tokens.push(...this.parseJsTokens(content));
            }
        }
        
        return tokens;
    }
    
    // Helper methods
    
    private async findThemeFiles(rootPath: string): Promise<string[]> {
        const themeFiles: string[] = [];
        const possiblePaths = [
            'src/theme',
            'src/styles/theme',
            'theme',
            'styles/theme'
        ];
        
        for (const possiblePath of possiblePaths) {
            const fullPath = path.join(rootPath, possiblePath);
            if (fs.existsSync(fullPath)) {
                this.findFilesRecursively(fullPath, themeFiles, /\.(js|ts|json)$/);
            }
        }
        
        return themeFiles;
    }
    
    private extractThemeVariables(content: string): ThemeVariable[] {
        const variables: ThemeVariable[] = [];
        
        // Extract CSS custom properties
        const cssVarMatches = content.match(/--[\w-]+:\s*[^;]+/g);
        if (cssVarMatches) {
            cssVarMatches.forEach(match => {
                const [name, value] = match.split(':').map(s => s.trim());
                variables.push({
                    name: name.replace('--', ''),
                    value: value.replace(';', ''),
                    category: this.categorizeVariable(name),
                    usage: []
                });
            });
        }
        
        // Extract JavaScript object properties
        const jsVarMatches = content.match(/(\w+):\s*['"`]([^'"`]+)['"`]/g);
        if (jsVarMatches) {
            jsVarMatches.forEach(match => {
                const [, name, value] = match.match(/(\w+):\s*['"`]([^'"`]+)['"`]/) || [];
                if (name && value) {
                    variables.push({
                        name,
                        value,
                        category: this.categorizeVariable(name),
                        usage: []
                    });
                }
            });
        }
        
        return variables;
    }
    
    private extractBreakpoints(content: string): Record<string, string> {
        const breakpoints: Record<string, string> = {};
        
        // Common breakpoint patterns
        const bpPatterns = [
            /breakpoints?\s*:\s*{([^}]+)}/,
            /screens?\s*:\s*{([^}]+)}/
        ];
        
        bpPatterns.forEach(pattern => {
            const match = content.match(pattern);
            if (match) {
                const bpContent = match[1];
                const bpMatches = bpContent.match(/(\w+):\s*['"`]([^'"`]+)['"`]/g);
                if (bpMatches) {
                    bpMatches.forEach(bpMatch => {
                        const [, name, value] = bpMatch.match(/(\w+):\s*['"`]([^'"`]+)['"`]/) || [];
                        if (name && value) {
                            breakpoints[name] = value;
                        }
                    });
                }
            }
        });
        
        return breakpoints;
    }
    
    private getAllClassNames(components: ComponentInfo[]): string[] {
        const allClasses: string[] = [];
        
        components.forEach(component => {
            if (component.ast?.styling?.classes) {
                allClasses.push(...component.ast.styling.classes);
            }
        });
        
        return [...new Set(allClasses)];
    }
    
    private isColorClass(cls: string): boolean {
        return /^(bg-|text-|border-|from-|to-|via-)/.test(cls) &&
               /(red|blue|green|yellow|purple|pink|gray|indigo|primary|secondary|success|error|warning)/.test(cls);
    }
    
    private isSpacingClass(cls: string): boolean {
        return /^(p|m|px|py|pl|pr|pt|pb|mx|my|ml|mr|mt|mb)-/.test(cls);
    }
    
    private isTypographyClass(cls: string): boolean {
        return /^(text-|font-|leading-|tracking-)/.test(cls);
    }
    
    private convertSpacingValue(value: string, unit: string): string {
        // Convert Tailwind spacing to actual values
        const spacingMap: Record<string, string> = {
            '0': '0',
            '1': '0.25rem',
            '2': '0.5rem',
            '3': '0.75rem',
            '4': '1rem',
            '5': '1.25rem',
            '6': '1.5rem',
            '8': '2rem',
            '10': '2.5rem',
            '12': '3rem',
            '16': '4rem',
            '20': '5rem',
            '24': '6rem',
            '32': '8rem'
        };
        
        return spacingMap[value] || `${value}${unit}`;
    }
    
    private extractCustomSpacingValues(spacingClasses: string[]): string[] {
        return spacingClasses
            .filter(cls => !cls.match(/^(p|m|px|py|pl|pr|pt|pb|mx|my|ml|mr|mt|mb)-\d+$/))
            .map(cls => cls.split('-').pop())
            .filter(Boolean) as string[];
    }
    
    private resolveFontFamily(family: string): string {
        const fontMap: Record<string, string> = {
            'sans': 'system-ui, sans-serif',
            'serif': 'Georgia, serif',
            'mono': 'Menlo, Monaco, monospace'
        };
        
        return fontMap[family] || family;
    }
    
    private resolveFontSize(size: string): string {
        const sizeMap: Record<string, string> = {
            'xs': '0.75rem',
            'sm': '0.875rem',
            'base': '1rem',
            'lg': '1.125rem',
            'xl': '1.25rem',
            '2xl': '1.5rem',
            '3xl': '1.875rem',
            '4xl': '2.25rem'
        };
        
        return sizeMap[size] || size;
    }
    
    private resolveFontWeight(weight: string): string {
        const weightMap: Record<string, string> = {
            'thin': '100',
            'light': '300',
            'normal': '400',
            'medium': '500',
            'semibold': '600',
            'bold': '700',
            'extrabold': '800',
            'black': '900'
        };
        
        return weightMap[weight] || weight;
    }
    
    private extractIconUsage(components: ComponentInfo[]) {
        // Implementation for extracting icon usage patterns
        return [];
    }
    
    private hasCustomIcons(rootPath: string): boolean {
        const iconDirs = ['src/icons', 'src/assets/icons', 'assets/icons'];
        return iconDirs.some(dir => fs.existsSync(path.join(rootPath, dir)));
    }
    
    private async findDesignTokenFiles(rootPath: string): Promise<string[]> {
        const tokenFiles: string[] = [];
        const possibleFiles = [
            'tokens.json',
            'design-tokens.json',
            'src/tokens.js',
            'src/design-tokens.js',
            'theme/tokens.json'
        ];
        
        possibleFiles.forEach(file => {
            const fullPath = path.join(rootPath, file);
            if (fs.existsSync(fullPath)) {
                tokenFiles.push(fullPath);
            }
        });
        
        return tokenFiles;
    }
    
    private parseJsonTokens(content: string): DesignToken[] {
        try {
            const tokens = JSON.parse(content);
            return this.flattenTokens(tokens);
        } catch {
            return [];
        }
    }
    
    private parseJsTokens(content: string): DesignToken[] {
        // Basic parsing for JS token files
        const tokens: DesignToken[] = [];
        const matches = content.match(/(\w+):\s*['"`]([^'"`]+)['"`]/g);
        
        if (matches) {
            matches.forEach(match => {
                const [, name, value] = match.match(/(\w+):\s*['"`]([^'"`]+)['"`]/) || [];
                if (name && value) {
                    tokens.push({
                        name,
                        value,
                        type: this.inferTokenType(name, value)
                    });
                }
            });
        }
        
        return tokens;
    }
    
    private flattenTokens(tokens: any, prefix = ''): DesignToken[] {
        const flattened: DesignToken[] = [];
        
        Object.entries(tokens).forEach(([key, value]) => {
            const tokenName = prefix ? `${prefix}-${key}` : key;
            
            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                flattened.push(...this.flattenTokens(value, tokenName));
            } else {
                flattened.push({
                    name: tokenName,
                    value: String(value),
                    type: this.inferTokenType(tokenName, String(value))
                });
            }
        });
        
        return flattened;
    }
    
    private inferTokenType(name: string, value: string): string {
        if (name.includes('color') || value.match(/^#|rgb|hsl/)) return 'color';
        if (name.includes('spacing') || value.match(/^\d+(\.\d+)?(px|rem|em)$/)) return 'spacing';
        if (name.includes('font') || name.includes('typography')) return 'typography';
        if (name.includes('shadow')) return 'shadow';
        if (name.includes('border')) return 'border';
        return 'other';
    }
    
    private categorizeVariable(name: string): 'color' | 'spacing' | 'typography' | 'shadow' | 'border' | 'other' {
        if (name.includes('color')) return 'color';
        if (name.includes('spacing') || name.includes('gap') || name.includes('margin') || name.includes('padding')) return 'spacing';
        if (name.includes('font') || name.includes('text')) return 'typography';
        if (name.includes('shadow')) return 'shadow';
        if (name.includes('border')) return 'border';
        return 'other';
    }
    
    private findFilesRecursively(dirPath: string, files: string[], pattern: RegExp): void {
        try {
            const entries = fs.readdirSync(dirPath, { withFileTypes: true });
            entries.forEach(entry => {
                const fullPath = path.join(dirPath, entry.name);
                if (entry.isDirectory()) {
                    this.findFilesRecursively(fullPath, files, pattern);
                } else if (entry.isFile() && pattern.test(entry.name)) {
                    files.push(fullPath);
                }
            });
        } catch (error) {
            // Ignore errors accessing directories
        }
    }
}