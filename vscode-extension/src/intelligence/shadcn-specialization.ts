/**
 * shadcn/ui Specialization System
 * Provides intelligent shadcn/ui component detection, suggestions, and integration
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { ProjectStructure, ComponentInfo } from './typescript-project-analyzer';

export interface ShadcnComponent {
    name: string;
    description: string;
    category: 'form' | 'navigation' | 'feedback' | 'overlay' | 'data-display' | 'layout' | 'input';
    dependencies: string[];
    props: ShadcnProp[];
    variants?: ShadcnVariant[];
    examples: ShadcnExample[];
    installCommand?: string;
    isInstalled: boolean;
}

export interface ShadcnProp {
    name: string;
    type: string;
    description: string;
    required: boolean;
    defaultValue?: string;
}

export interface ShadcnVariant {
    name: string;
    values: string[];
    description: string;
}

export interface ShadcnExample {
    title: string;
    code: string;
    description: string;
}

export interface ShadcnAnalysis {
    isConfigured: boolean;
    configFile?: string;
    installedComponents: string[];
    availableComponents: ShadcnComponent[];
    missingDependencies: string[];
    recommendations: ShadcnRecommendation[];
}

export interface ShadcnRecommendation {
    type: 'install' | 'update' | 'configure' | 'usage';
    component?: string;
    message: string;
    action: string;
    priority: 'high' | 'medium' | 'low';
}

export class ShadcnSpecialist {
    private static instance: ShadcnSpecialist;
    private workspaceFolder: vscode.WorkspaceFolder | null = null;
    private componentsRegistry: Map<string, ShadcnComponent> = new Map();

    private constructor() {
        this.initializeComponentsRegistry();
    }

    static getInstance(): ShadcnSpecialist {
        if (!ShadcnSpecialist.instance) {
            ShadcnSpecialist.instance = new ShadcnSpecialist();
        }
        return ShadcnSpecialist.instance;
    }

    /**
     * Analyze the project's shadcn/ui setup and usage
     */
    async analyzeShadcnSetup(projectStructure?: ProjectStructure): Promise<ShadcnAnalysis> {
        this.workspaceFolder = vscode.workspace.workspaceFolders?.[0] || null;
        if (!this.workspaceFolder) {
            throw new Error('No workspace folder found');
        }

        console.log('🎨 Analyzing shadcn/ui setup...');

        const isConfigured = await this.isShadcnConfigured();
        const configFile = await this.findConfigFile();
        const installedComponents = await this.getInstalledComponents();
        const availableComponents = this.getAvailableComponents();
        const missingDependencies = await this.findMissingDependencies();
        const recommendations = await this.generateRecommendations(
            isConfigured, 
            installedComponents, 
            projectStructure
        );

        // Update component installation status
        availableComponents.forEach(component => {
            component.isInstalled = installedComponents.includes(component.name);
        });

        return {
            isConfigured,
            configFile,
            installedComponents,
            availableComponents,
            missingDependencies,
            recommendations
        };
    }

    /**
     * Suggest relevant shadcn/ui components based on user intent
     */
    suggestComponentsForIntent(intent: string, currentContent?: string): ShadcnComponent[] {
        const suggestions: ShadcnComponent[] = [];
        const intentLower = intent.toLowerCase();

        // Form-related suggestions
        if (intentLower.includes('form') || intentLower.includes('input') || intentLower.includes('submit')) {
            suggestions.push(
                ...this.getComponentsByCategory('form'),
                ...this.getComponentsByCategory('input')
            );
        }

        // Navigation suggestions
        if (intentLower.includes('menu') || intentLower.includes('nav') || intentLower.includes('tab')) {
            suggestions.push(...this.getComponentsByCategory('navigation'));
        }

        // Data display suggestions
        if (intentLower.includes('table') || intentLower.includes('list') || intentLower.includes('card')) {
            suggestions.push(...this.getComponentsByCategory('data-display'));
        }

        // Feedback suggestions
        if (intentLower.includes('toast') || intentLower.includes('alert') || intentLower.includes('dialog')) {
            suggestions.push(...this.getComponentsByCategory('feedback'));
        }

        // Layout suggestions
        if (intentLower.includes('layout') || intentLower.includes('grid') || intentLower.includes('container')) {
            suggestions.push(...this.getComponentsByCategory('layout'));
        }

        // Overlay suggestions
        if (intentLower.includes('modal') || intentLower.includes('popup') || intentLower.includes('dropdown')) {
            suggestions.push(...this.getComponentsByCategory('overlay'));
        }

        return suggestions.slice(0, 5); // Limit to top 5 suggestions
    }

    /**
     * Generate enhanced prompt context for shadcn/ui
     */
    buildShadcnContext(analysis: ShadcnAnalysis, userIntent: string): string {
        const installedComponents = analysis.installedComponents;
        const suggestions = this.suggestComponentsForIntent(userIntent);

        let context = '';

        if (analysis.isConfigured) {
            context += `\n**shadcn/ui Configuration:**
- Configured: Yes (${analysis.configFile})
- Installed Components: ${installedComponents.length > 0 ? installedComponents.join(', ') : 'None'}
`;

            if (installedComponents.length > 0) {
                context += `
**Available shadcn/ui Components:**
Use these installed components with proper imports:
${installedComponents.slice(0, 10).map(comp => `- ${comp}: import { ${this.capitalizeFirst(comp)} } from "@/components/ui/${comp}"`).join('\n')}
${installedComponents.length > 10 ? `... and ${installedComponents.length - 10} more` : ''}
`;
            }
        } else {
            context += `\n**shadcn/ui Setup:**
- Not configured yet
- Recommendation: Set up shadcn/ui for better component library support
`;
        }

        if (suggestions.length > 0) {
            context += `\n**Recommended Components for your request:**
${suggestions.map(comp => `- **${comp.name}**: ${comp.description} ${!comp.isInstalled ? '(Not installed - suggest installation)' : ''}`).join('\n')}
`;
        }

        if (analysis.recommendations.length > 0) {
            const highPriorityRecs = analysis.recommendations.filter(r => r.priority === 'high');
            if (highPriorityRecs.length > 0) {
                context += `\n**Important Recommendations:**
${highPriorityRecs.map(rec => `- ${rec.message} (${rec.action})`).join('\n')}
`;
            }
        }

        return context;
    }

    /**
     * Generate installation commands for missing components
     */
    generateInstallCommands(componentNames: string[]): string[] {
        const commands: string[] = [];
        
        componentNames.forEach(name => {
            const component = this.componentsRegistry.get(name);
            if (component && !component.isInstalled) {
                commands.push(`npx shadcn-ui@latest add ${name}`);
            }
        });

        return commands;
    }

    /**
     * Enhance generated code with shadcn/ui best practices
     */
    enhanceCodeWithShadcnPatterns(code: string, usedComponents: string[]): string {
        let enhancedCode = code;

        // Add cn utility import if shadcn components are used
        if (usedComponents.length > 0 && !code.includes('import { cn }')) {
            enhancedCode = `import { cn } from "@/lib/utils";\n${enhancedCode}`;
        }

        // Add proper shadcn component imports
        const missingImports: string[] = [];
        usedComponents.forEach(componentName => {
            const importPattern = new RegExp(`import.*${this.capitalizeFirst(componentName)}.*from.*components/ui/${componentName}`);
            if (!importPattern.test(code)) {
                missingImports.push(`import { ${this.capitalizeFirst(componentName)} } from "@/components/ui/${componentName}"`);
            }
        });

        if (missingImports.length > 0) {
            enhancedCode = `${missingImports.join('\n')}\n${enhancedCode}`;
        }

        return enhancedCode;
    }

    /**
     * Private methods for analysis
     */
    private async isShadcnConfigured(): Promise<boolean> {
        if (!this.workspaceFolder) return false;
        
        const configFile = path.join(this.workspaceFolder.uri.fsPath, 'components.json');
        try {
            await vscode.workspace.fs.stat(vscode.Uri.file(configFile));
            return true;
        } catch {
            return false;
        }
    }

    private async findConfigFile(): Promise<string | undefined> {
        if (!this.workspaceFolder) return undefined;

        const possibleConfigs = ['components.json', 'ui.config.json', 'shadcn.config.json'];
        
        for (const config of possibleConfigs) {
            const configPath = path.join(this.workspaceFolder.uri.fsPath, config);
            try {
                await vscode.workspace.fs.stat(vscode.Uri.file(configPath));
                return config;
            } catch {
                continue;
            }
        }
        
        return undefined;
    }

    private async getInstalledComponents(): Promise<string[]> {
        if (!this.workspaceFolder) return [];

        const uiComponentsPath = path.join(this.workspaceFolder.uri.fsPath, 'src', 'components', 'ui');
        
        try {
            const stat = await vscode.workspace.fs.stat(vscode.Uri.file(uiComponentsPath));
            if (stat.type !== vscode.FileType.Directory) return [];

            const entries = await vscode.workspace.fs.readDirectory(vscode.Uri.file(uiComponentsPath));
            
            return entries
                .filter(([name, type]) => type === vscode.FileType.File && name.endsWith('.tsx'))
                .map(([name]) => name.replace('.tsx', ''));
        } catch {
            return [];
        }
    }

    private getAvailableComponents(): ShadcnComponent[] {
        return Array.from(this.componentsRegistry.values());
    }

    private async findMissingDependencies(): Promise<string[]> {
        if (!this.workspaceFolder) return [];

        const packageJsonPath = path.join(this.workspaceFolder.uri.fsPath, 'package.json');
        
        try {
            const content = await vscode.workspace.fs.readFile(vscode.Uri.file(packageJsonPath));
            const packageJson = JSON.parse(Buffer.from(content).toString());
            
            const requiredDeps = [
                'class-variance-authority',
                'clsx',
                'tailwind-merge',
                '@radix-ui/react-slot',
                'lucide-react'
            ];

            const allDeps = {
                ...packageJson.dependencies,
                ...packageJson.devDependencies
            };

            return requiredDeps.filter(dep => !allDeps[dep]);
        } catch {
            return [];
        }
    }

    private async generateRecommendations(
        isConfigured: boolean,
        installedComponents: string[],
        projectStructure?: ProjectStructure
    ): Promise<ShadcnRecommendation[]> {
        const recommendations: ShadcnRecommendation[] = [];

        if (!isConfigured) {
            recommendations.push({
                type: 'configure',
                message: 'shadcn/ui is not configured in this project',
                action: 'Run: npx shadcn-ui@latest init',
                priority: 'high'
            });
        }

        if (installedComponents.length === 0 && isConfigured) {
            recommendations.push({
                type: 'install',
                message: 'No shadcn/ui components are installed',
                action: 'Consider installing common components like Button, Card, Input',
                priority: 'medium'
            });
        }

        // Analyze project structure for component recommendations
        if (projectStructure) {
            const hasFormComponents = projectStructure.components.some(c => 
                c.name.toLowerCase().includes('form') || 
                c.filePath.toLowerCase().includes('form')
            );

            if (hasFormComponents && !installedComponents.includes('button')) {
                recommendations.push({
                    type: 'install',
                    component: 'button',
                    message: 'Forms detected but Button component not installed',
                    action: 'Install Button component for better form UX',
                    priority: 'medium'
                });
            }
        }

        return recommendations;
    }

    private getComponentsByCategory(category: string): ShadcnComponent[] {
        return Array.from(this.componentsRegistry.values())
            .filter(component => component.category === category);
    }

    private capitalizeFirst(str: string): string {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    /**
     * Initialize the shadcn/ui components registry
     */
    private initializeComponentsRegistry(): void {
        const components: ShadcnComponent[] = [
            // Form Components
            {
                name: 'button',
                description: 'Displays a button or a component that looks like a button',
                category: 'form',
                dependencies: ['@radix-ui/react-slot', 'class-variance-authority'],
                props: [
                    { name: 'variant', type: '"default" | "destructive" | "outline" | "secondary" | "ghost" | "link"', description: 'Button style variant', required: false, defaultValue: 'default' },
                    { name: 'size', type: '"default" | "sm" | "lg" | "icon"', description: 'Button size', required: false, defaultValue: 'default' },
                    { name: 'asChild', type: 'boolean', description: 'Render as child component', required: false }
                ],
                variants: [
                    { name: 'variant', values: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'], description: 'Visual style variants' },
                    { name: 'size', values: ['default', 'sm', 'lg', 'icon'], description: 'Size variants' }
                ],
                examples: [
                    {
                        title: 'Basic Button',
                        code: '<Button>Click me</Button>',
                        description: 'Default button with text'
                    },
                    {
                        title: 'Button Variants',
                        code: '<Button variant="outline">Outline</Button>\n<Button variant="destructive">Delete</Button>',
                        description: 'Different button styles'
                    }
                ],
                isInstalled: false
            },
            {
                name: 'input',
                description: 'Displays a form input field',
                category: 'input',
                dependencies: [],
                props: [
                    { name: 'type', type: 'string', description: 'Input type', required: false, defaultValue: 'text' },
                    { name: 'placeholder', type: 'string', description: 'Placeholder text', required: false },
                    { name: 'disabled', type: 'boolean', description: 'Disable the input', required: false }
                ],
                examples: [
                    {
                        title: 'Basic Input',
                        code: '<Input placeholder="Enter your name" />',
                        description: 'Text input with placeholder'
                    }
                ],
                isInstalled: false
            },
            // Navigation Components
            {
                name: 'navigation-menu',
                description: 'A collection of links for navigating websites',
                category: 'navigation',
                dependencies: ['@radix-ui/react-navigation-menu'],
                props: [],
                examples: [
                    {
                        title: 'Basic Navigation',
                        code: '<NavigationMenu>\n  <NavigationMenuList>\n    <NavigationMenuItem>\n      <NavigationMenuTrigger>Item One</NavigationMenuTrigger>\n    </NavigationMenuItem>\n  </NavigationMenuList>\n</NavigationMenu>',
                        description: 'Basic navigation menu'
                    }
                ],
                isInstalled: false
            },
            // Data Display Components
            {
                name: 'card',
                description: 'Displays a card with header, content, and footer',
                category: 'data-display',
                dependencies: [],
                props: [],
                examples: [
                    {
                        title: 'Basic Card',
                        code: '<Card>\n  <CardHeader>\n    <CardTitle>Card Title</CardTitle>\n  </CardHeader>\n  <CardContent>\n    <p>Card content goes here.</p>\n  </CardContent>\n</Card>',
                        description: 'Basic card layout'
                    }
                ],
                isInstalled: false
            },
            {
                name: 'table',
                description: 'A responsive table component',
                category: 'data-display',
                dependencies: [],
                props: [],
                examples: [
                    {
                        title: 'Basic Table',
                        code: '<Table>\n  <TableHeader>\n    <TableRow>\n      <TableHead>Name</TableHead>\n      <TableHead>Email</TableHead>\n    </TableRow>\n  </TableHeader>\n  <TableBody>\n    <TableRow>\n      <TableCell>John Doe</TableCell>\n      <TableCell>john@example.com</TableCell>\n    </TableRow>\n  </TableBody>\n</Table>',
                        description: 'Basic data table'
                    }
                ],
                isInstalled: false
            },
            // Feedback Components
            {
                name: 'toast',
                description: 'A succinct message that is displayed temporarily',
                category: 'feedback',
                dependencies: ['@radix-ui/react-toast'],
                props: [],
                examples: [
                    {
                        title: 'Toast Notification',
                        code: 'const { toast } = useToast()\n\ntoast({\n  title: "Success!",\n  description: "Your changes have been saved.",\n})',
                        description: 'Show toast notification'
                    }
                ],
                isInstalled: false
            },
            {
                name: 'alert',
                description: 'Displays a callout for user attention',
                category: 'feedback',
                dependencies: [],
                props: [],
                examples: [
                    {
                        title: 'Alert Message',
                        code: '<Alert>\n  <AlertCircle className="h-4 w-4" />\n  <AlertTitle>Heads up!</AlertTitle>\n  <AlertDescription>\n    You can add components to your app using the cli.\n  </AlertDescription>\n</Alert>',
                        description: 'Information alert'
                    }
                ],
                isInstalled: false
            },
            // Overlay Components
            {
                name: 'dialog',
                description: 'A window overlaid on either the primary window or another dialog window',
                category: 'overlay',
                dependencies: ['@radix-ui/react-dialog'],
                props: [],
                examples: [
                    {
                        title: 'Basic Dialog',
                        code: '<Dialog>\n  <DialogTrigger asChild>\n    <Button>Open Dialog</Button>\n  </DialogTrigger>\n  <DialogContent>\n    <DialogHeader>\n      <DialogTitle>Are you sure?</DialogTitle>\n      <DialogDescription>\n        This action cannot be undone.\n      </DialogDescription>\n    </DialogHeader>\n  </DialogContent>\n</Dialog>',
                        description: 'Modal dialog'
                    }
                ],
                isInstalled: false
            }
        ];

        // Populate the registry
        components.forEach(component => {
            this.componentsRegistry.set(component.name, component);
        });

        console.log('🎨 Initialized shadcn/ui components registry with', components.length, 'components');
    }
}

// Factory function for easy access
export function getShadcnSpecialist(): ShadcnSpecialist {
    return ShadcnSpecialist.getInstance();
}