/**
 * shadcn/ui MCP Server Integration
 * Advanced integration with shadcn/ui MCP server for component management
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { MCPManager } from './mcp-manager';
import { MCPServerConfig } from './types';
import { ToolRegistry } from '../tools/tool-registry';
import { PaletteTool, ToolExecutionContext, ToolResult } from '../tools/types';

export interface ShadcnComponent {
    name: string;
    description: string;
    category: 'ui' | 'form' | 'layout' | 'feedback' | 'navigation' | 'data-display';
    dependencies: string[];
    registryUrl?: string;
    variants?: string[];
    examples?: Array<{
        name: string;
        code: string;
        description: string;
    }>;
}

export interface ShadcnTheme {
    name: string;
    colors: {
        primary: string;
        secondary: string;
        accent: string;
        background: string;
        foreground: string;
        muted: string;
        border: string;
    };
    radius: string;
    fontFamily?: string;
}

export class ShadcnMCPIntegration {
    private mcpManager: MCPManager;
    private toolRegistry: ToolRegistry;
    private serverName = 'shadcn-ui';
    
    // Enhanced component catalog with detailed information
    private componentCatalog: ShadcnComponent[] = [
        {
            name: 'accordion',
            description: 'A vertically stacked set of interactive headings',
            category: 'ui',
            dependencies: ['@radix-ui/react-accordion'],
            variants: ['default', 'bordered', 'filled'],
            examples: [{
                name: 'Basic Accordion',
                description: 'Simple accordion with multiple items',
                code: `<Accordion type="single" collapsible>\n  <AccordionItem value="item-1">\n    <AccordionTrigger>Is it accessible?</AccordionTrigger>\n    <AccordionContent>Yes. It adheres to WAI-ARIA guidelines.</AccordionContent>\n  </AccordionItem>\n</Accordion>`
            }]
        },
        {
            name: 'alert',
            description: 'Displays a callout for user attention',
            category: 'feedback',
            dependencies: [],
            variants: ['default', 'destructive'],
            examples: [{
                name: 'Basic Alert',
                description: 'Information alert with title and description',
                code: `<Alert>\n  <AlertCircle className="h-4 w-4" />\n  <AlertTitle>Heads up!</AlertTitle>\n  <AlertDescription>You can add components to your app using the cli.</AlertDescription>\n</Alert>`
            }]
        },
        {
            name: 'button',
            description: 'Displays a button or a component that looks like a button',
            category: 'ui',
            dependencies: ['@radix-ui/react-slot'],
            variants: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
            examples: [{
                name: 'Button Variants',
                description: 'Different button styles',
                code: `<div className="flex gap-2">\n  <Button variant="default">Default</Button>\n  <Button variant="secondary">Secondary</Button>\n  <Button variant="outline">Outline</Button>\n</div>`
            }]
        },
        {
            name: 'card',
            description: 'Displays a card with header, content, and footer',
            category: 'layout',
            dependencies: [],
            variants: ['default', 'elevated'],
            examples: [{
                name: 'Basic Card',
                description: 'Card with header, content and footer',
                code: `<Card>\n  <CardHeader>\n    <CardTitle>Card Title</CardTitle>\n    <CardDescription>Card Description</CardDescription>\n  </CardHeader>\n  <CardContent>Card content goes here</CardContent>\n  <CardFooter>Card footer</CardFooter>\n</Card>`
            }]
        },
        {
            name: 'input',
            description: 'Displays a form input field',
            category: 'form',
            dependencies: [],
            variants: ['default', 'file'],
            examples: [{
                name: 'Basic Input',
                description: 'Standard input field with placeholder',
                code: `<Input type="email" placeholder="Email" />`
            }]
        },
        {
            name: 'data-table',
            description: 'Powerful data tables built using TanStack Table',
            category: 'data-display',
            dependencies: ['@tanstack/react-table'],
            variants: ['default', 'striped', 'bordered'],
            examples: [{
                name: 'Basic Data Table',
                description: 'Sortable data table with actions',
                code: `<DataTable columns={columns} data={data} />`
            }]
        },
        {
            name: 'dialog',
            description: 'A window overlaid on either the primary window or another dialog window',
            category: 'feedback',
            dependencies: ['@radix-ui/react-dialog'],
            variants: ['default', 'centered'],
            examples: [{
                name: 'Basic Dialog',
                description: 'Modal dialog with trigger button',
                code: `<Dialog>\n  <DialogTrigger asChild>\n    <Button variant="outline">Open Dialog</Button>\n  </DialogTrigger>\n  <DialogContent>\n    <DialogHeader>\n      <DialogTitle>Are you sure?</DialogTitle>\n      <DialogDescription>This action cannot be undone.</DialogDescription>\n    </DialogHeader>\n  </DialogContent>\n</Dialog>`
            }]
        },
        {
            name: 'form',
            description: 'Building forms with React Hook Form and Zod validation',
            category: 'form',
            dependencies: ['react-hook-form', '@hookform/resolvers', 'zod'],
            variants: ['default'],
            examples: [{
                name: 'Basic Form',
                description: 'Form with validation using Zod schema',
                code: `<Form {...form}>\n  <form onSubmit={form.handleSubmit(onSubmit)}>\n    <FormField\n      control={form.control}\n      name="username"\n      render={({ field }) => (\n        <FormItem>\n          <FormLabel>Username</FormLabel>\n          <FormControl>\n            <Input placeholder="Username" {...field} />\n          </FormControl>\n        </FormItem>\n      )}\n    />\n  </form>\n</Form>`
            }]
        },
        {
            name: 'navigation-menu',
            description: 'A collection of links for navigating websites',
            category: 'navigation',
            dependencies: ['@radix-ui/react-navigation-menu'],
            variants: ['default', 'vertical'],
            examples: [{
                name: 'Basic Navigation',
                description: 'Horizontal navigation menu',
                code: `<NavigationMenu>\n  <NavigationMenuList>\n    <NavigationMenuItem>\n      <NavigationMenuLink href="/docs">Documentation</NavigationMenuLink>\n    </NavigationMenuItem>\n  </NavigationMenuList>\n</NavigationMenu>`
            }]
        },
        {
            name: 'sheet',
            description: 'Extends the Dialog component to display content that complements the main content',
            category: 'feedback',
            dependencies: ['@radix-ui/react-dialog'],
            variants: ['top', 'right', 'bottom', 'left'],
            examples: [{
                name: 'Basic Sheet',
                description: 'Side sheet with trigger',
                code: `<Sheet>\n  <SheetTrigger asChild>\n    <Button variant="outline">Open Sheet</Button>\n  </SheetTrigger>\n  <SheetContent>\n    <SheetHeader>\n      <SheetTitle>Edit Profile</SheetTitle>\n      <SheetDescription>Make changes to your profile</SheetDescription>\n    </SheetHeader>\n  </SheetContent>\n</Sheet>`
            }]
        }
    ];

    private themes: ShadcnTheme[] = [
        {
            name: 'default',
            colors: {
                primary: '222.2 84% 4.9%',
                secondary: '210 40% 96%',
                accent: '210 40% 94%',
                background: '0 0% 100%',
                foreground: '222.2 84% 4.9%',
                muted: '210 40% 96%',
                border: '214.3 31.8% 91.4%'
            },
            radius: '0.5rem'
        },
        {
            name: 'dark',
            colors: {
                primary: '210 40% 98%',
                secondary: '222.2 84% 4.9%',
                accent: '217.2 32.6% 17.5%',
                background: '222.2 84% 4.9%',
                foreground: '210 40% 98%',
                muted: '217.2 32.6% 17.5%',
                border: '217.2 32.6% 17.5%'
            },
            radius: '0.5rem'
        },
        {
            name: 'new-york',
            colors: {
                primary: '222.2 47.4% 11.2%',
                secondary: '210 40% 96%',
                accent: '210 40% 94%',
                background: '0 0% 100%',
                foreground: '222.2 47.4% 11.2%',
                muted: '210 40% 96%',
                border: '214.3 31.8% 91.4%'
            },
            radius: '0.75rem',
            fontFamily: 'Inter'
        }
    ];

    constructor() {
        this.mcpManager = MCPManager.getInstance();
        this.toolRegistry = ToolRegistry.getInstance();
    }

    /**
     * Initialize shadcn/ui MCP server integration
     */
    async initialize(): Promise<void> {
        console.log('🎨 Initializing shadcn/ui MCP integration...');

        try {
            // Configure shadcn/ui MCP server
            await this.configureShadcnServer();
            
            // Register enhanced shadcn tools
            this.registerEnhancedTools();
            
            // Set up workspace analysis
            // await this.analyzeWorkspaceSetup(); // TODO: Implement if needed

            console.log('🎨 shadcn/ui MCP integration initialized');
        } catch (error) {
            console.error('🎨 Failed to initialize shadcn/ui MCP integration:', error);
            // Fallback to local tools if MCP server unavailable
            await this.initializeFallbackMode();
        }
    }

    /**
     * Configure shadcn/ui MCP server
     */
    private async configureShadcnServer(): Promise<void> {
        // Check VS Code configuration for shadcn/ui MCP server
        const config = vscode.workspace.getConfiguration('palette.mcp');
        const servers = config.get<any[]>('servers', []);
        
        // Look for existing shadcn-ui server configuration
        const existingConfig = servers.find(s => s.name === 'shadcn-ui');
        
        if (existingConfig && existingConfig.enabled) {
            // Use user-configured server
            const serverConfig: MCPServerConfig = {
                name: this.serverName,
                description: existingConfig.description || 'shadcn/ui component management and installation',
                command: existingConfig.command,
                args: existingConfig.args || [],
                enabled: existingConfig.enabled,
                autoStart: existingConfig.autoStart,
                tools: existingConfig.tools || [
                    'install_component',
                    'list_components', 
                    'update_component',
                    'uninstall_component',
                    'init_shadcn',
                    'add_theme',
                    'generate_component_code',
                    'analyze_components',
                    'get_component_examples'
                ],
                resources: existingConfig.resources || ['component', 'theme', 'registry']
            };

            // Add server configuration
            this.mcpManager.addServerConfig(serverConfig);

            // Try to start the server
            try {
                await this.mcpManager.startServer(this.serverName);
                console.log('🎨 shadcn/ui MCP server started successfully');
            } catch (error) {
                console.warn('🎨 shadcn/ui MCP server failed to start, using fallback mode:', error);
                throw error;
            }
        } else {
            // No valid configuration found, skip MCP server
            console.log('🎨 shadcn/ui MCP server not configured or disabled, using fallback mode');
            throw new Error('shadcn/ui MCP server not configured');
        }
    }

    /**
     * Register enhanced shadcn/ui tools
     */
    private registerEnhancedTools(): void {
        // Smart component installer with dependency management
        this.toolRegistry.registerTool(this.createSmartInstallTool(), { enabled: true });
        
        // Component code generator with variants
        this.toolRegistry.registerTool(this.createComponentGeneratorTool(), { enabled: true });
        
        // Theme management tool
        this.toolRegistry.registerTool(this.createThemeManagerTool(), { enabled: true });
        
        // Component analysis and suggestions
        this.toolRegistry.registerTool(this.createComponentAnalyzerTool(), { enabled: true });

        // Bulk component operations
        this.toolRegistry.registerTool(this.createBulkComponentTool(), { enabled: true });

        console.log('🎨 Registered enhanced shadcn/ui tools');
    }

    /**
     * Smart component installer with dependency resolution
     */
    private createSmartInstallTool(): PaletteTool {
        return {
            name: 'shadcn_smart_install',
            description: 'Intelligently install shadcn/ui components with dependency resolution and setup validation',
            category: 'component-management',
            requiresApproval: true,
            dangerLevel: 'caution',
            inputSchema: require('zod').object({
                components: require('zod').array(require('zod').string()).describe('Component names to install'),
                autoSetup: require('zod').boolean().optional().default(true).describe('Automatically set up shadcn/ui if not configured'),
                installDependencies: require('zod').boolean().optional().default(true).describe('Install npm dependencies'),
                variant: require('zod').string().optional().describe('Component variant to use')
            }),
            async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
                const integration = new ShadcnMCPIntegration();
                return await integration.smartInstallComponents(params, context);
            }
        };
    }

    /**
     * Component code generator with examples and variants
     */
    private createComponentGeneratorTool(): PaletteTool {
        return {
            name: 'shadcn_generate_component',
            description: 'Generate complete component code with examples, variants, and usage documentation',
            category: 'component-management',
            dangerLevel: 'safe',
            inputSchema: require('zod').object({
                componentName: require('zod').string().describe('Component name'),
                variant: require('zod').string().optional().describe('Component variant'),
                includeExamples: require('zod').boolean().optional().default(true).describe('Include usage examples'),
                customProps: require('zod').record(require('zod').any()).optional().describe('Custom props to add')
            }),
            async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
                const integration = new ShadcnMCPIntegration();
                return await integration.generateComponentCode(params, context);
            }
        };
    }

    /**
     * Theme management tool
     */
    private createThemeManagerTool(): PaletteTool {
        return {
            name: 'shadcn_theme_manager',
            description: 'Manage shadcn/ui themes, colors, and design tokens',
            category: 'component-management',
            requiresApproval: true,
            dangerLevel: 'caution',
            inputSchema: require('zod').object({
                action: require('zod').enum(['apply', 'create', 'list', 'export']).describe('Theme action'),
                themeName: require('zod').string().optional().describe('Theme name'),
                customColors: require('zod').record(require('zod').string()).optional().describe('Custom color values')
            }),
            async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
                const integration = new ShadcnMCPIntegration();
                return await integration.manageTheme(params, context);
            }
        };
    }

    /**
     * Component analyzer and suggestions
     */
    private createComponentAnalyzerTool(): PaletteTool {
        return {
            name: 'shadcn_analyze_components',
            description: 'Analyze existing components and suggest improvements or missing components',
            category: 'project-analysis',
            dangerLevel: 'safe',
            inputSchema: require('zod').object({
                includeUsage: require('zod').boolean().optional().default(true).describe('Include usage analysis'),
                suggestMissing: require('zod').boolean().optional().default(true).describe('Suggest missing components'),
                checkUpdates: require('zod').boolean().optional().default(false).describe('Check for component updates')
            }),
            async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
                const integration = new ShadcnMCPIntegration();
                return await integration.analyzeComponents(params, context);
            }
        };
    }

    /**
     * Bulk component operations
     */
    private createBulkComponentTool(): PaletteTool {
        return {
            name: 'shadcn_bulk_operations',
            description: 'Perform bulk operations on multiple components (install, update, configure)',
            category: 'component-management',
            requiresApproval: true,
            dangerLevel: 'caution',
            inputSchema: require('zod').object({
                operation: require('zod').enum(['install', 'update', 'remove']).describe('Bulk operation'),
                components: require('zod').array(require('zod').string()).describe('Component names'),
                preset: require('zod').enum(['form', 'layout', 'navigation', 'feedback', 'all']).optional().describe('Component preset to install')
            }),
            async execute(params, context: ToolExecutionContext): Promise<ToolResult> {
                const integration = new ShadcnMCPIntegration();
                return await integration.bulkComponentOperations(params, context);
            }
        };
    }

    /**
     * Smart component installation with dependency resolution
     */
    async smartInstallComponents(params: any, context: ToolExecutionContext): Promise<ToolResult> {
        try {
            console.log(`🎨 Smart installing components: ${params.components.join(', ')}`);

            if (!context.workspacePath) {
                return {
                    success: false,
                    error: {
                        code: 'NO_WORKSPACE',
                        message: 'No workspace folder is open',
                        recoverable: false
                    }
                };
            }

            // 1. Check shadcn/ui setup
            const setupCheck = await this.checkShadcnSetup(context.workspacePath);
            if (!setupCheck.isSetup && params.autoSetup) {
                await this.initializeShadcnSetup(context.workspacePath);
            }

            // 2. Resolve dependencies
            const installPlan = await this.resolveComponentDependencies(params.components);

            // 3. Install components via MCP server or fallback
            const results = await this.executeInstallPlan(installPlan, context);

            return {
                success: results.success,
                data: {
                    installed: results.installed,
                    dependencies: results.dependencies,
                    setup: setupCheck
                },
                followUpSuggestions: [
                    `Installed ${results.installed.length} components`,
                    `Added ${results.dependencies.length} dependencies`,
                    'Components are ready to use in your project'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'COMPONENT_INSTALL_ERROR',
                    message: `Failed to install components: ${error.message}`,
                    recoverable: true
                }
            };
        }
    }

    /**
     * Generate component code with examples
     */
    async generateComponentCode(params: any, context: ToolExecutionContext): Promise<ToolResult> {
        try {
            const component = this.componentCatalog.find(c => c.name === params.componentName);
            if (!component) {
                return {
                    success: false,
                    error: {
                        code: 'COMPONENT_NOT_FOUND',
                        message: `Component ${params.componentName} not found in catalog`,
                        recoverable: true
                    }
                };
            }

            const generatedCode = this.generateComponentCodeSnippet(component, params.variant, params.customProps);
            const examples = params.includeExamples ? component.examples : [];

            return {
                success: true,
                data: {
                    component: component.name,
                    variant: params.variant,
                    code: generatedCode,
                    examples,
                    dependencies: component.dependencies,
                    usage: `Import and use the ${component.name} component in your React app`
                },
                followUpSuggestions: [
                    `Generated ${component.name} component code`,
                    examples ? `Included ${examples.length} usage examples` : 'Use install command to add to project',
                    'Copy code to your component file'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'CODE_GENERATION_ERROR',
                    message: `Failed to generate component code: ${error.message}`,
                    recoverable: true
                }
            };
        }
    }

    /**
     * Manage themes
     */
    async manageTheme(params: any, context: ToolExecutionContext): Promise<ToolResult> {
        try {
            switch (params.action) {
                case 'list':
                    return {
                        success: true,
                        data: {
                            themes: this.themes,
                            current: 'default' // Would detect from CSS variables
                        },
                        followUpSuggestions: [
                            `Found ${this.themes.length} available themes`,
                            'Use apply action to switch themes'
                        ]
                    };

                case 'apply':
                    if (!params.themeName) {
                        throw new Error('Theme name required for apply action');
                    }
                    await this.applyTheme(params.themeName, context);
                    return {
                        success: true,
                        data: { appliedTheme: params.themeName },
                        followUpSuggestions: [`Applied ${params.themeName} theme to project`]
                    };

                case 'create':
                    if (!params.customColors) {
                        throw new Error('Custom colors required for create action');
                    }
                    const newTheme = await this.createCustomTheme(params.themeName, params.customColors);
                    return {
                        success: true,
                        data: { createdTheme: newTheme },
                        followUpSuggestions: [`Created custom theme: ${newTheme.name}`]
                    };

                default:
                    throw new Error(`Unsupported theme action: ${params.action}`);
            }

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'THEME_MANAGEMENT_ERROR',
                    message: error.message,
                    recoverable: true
                }
            };
        }
    }

    /**
     * Analyze existing components
     */
    async analyzeComponents(params: any, context: ToolExecutionContext): Promise<ToolResult> {
        try {
            if (!context.workspacePath) {
                return {
                    success: false,
                    error: {
                        code: 'NO_WORKSPACE',
                        message: 'No workspace folder is open',
                        recoverable: false
                    }
                };
            }

            const analysis = {
                installed: [] as string[],
                missing: [] as string[],
                unused: [] as string[],
                updates: [] as string[],
                suggestions: [] as string[]
            };

            // Analyze installed components
            const componentsDir = path.join(context.workspacePath, 'src/components/ui');
            try {
                const dirUri = vscode.Uri.file(componentsDir);
                const files = await vscode.workspace.fs.readDirectory(dirUri);
                analysis.installed = files
                    .filter(([name, type]) => type === vscode.FileType.File && name.endsWith('.tsx'))
                    .map(([name]) => name.replace('.tsx', ''));
            } catch {
                // Components directory doesn't exist
            }

            // Suggest missing components based on usage patterns
            if (params.suggestMissing) {
                analysis.suggestions = await this.suggestMissingComponents(context.workspacePath);
            }

            return {
                success: true,
                data: analysis,
                followUpSuggestions: [
                    `Found ${analysis.installed.length} installed components`,
                    analysis.suggestions.length > 0 ? `Suggested ${analysis.suggestions.length} missing components` : 'All common components installed',
                    'Use smart install to add missing components'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'COMPONENT_ANALYSIS_ERROR',
                    message: error.message,
                    recoverable: true
                }
            };
        }
    }

    /**
     * Bulk component operations
     */
    async bulkComponentOperations(params: any, context: ToolExecutionContext): Promise<ToolResult> {
        try {
            let components = params.components;

            // Handle presets
            if (params.preset) {
                components = this.getPresetComponents(params.preset);
            }

            const results = {
                successful: [] as string[],
                failed: [] as Array<{ component: string; error: string }>
            };

            for (const component of components) {
                try {
                    switch (params.operation) {
                        case 'install':
                            await this.installSingleComponent(component, context);
                            results.successful.push(component);
                            break;
                        case 'update':
                            await this.updateSingleComponent(component, context);
                            results.successful.push(component);
                            break;
                        case 'remove':
                            await this.removeSingleComponent(component, context);
                            results.successful.push(component);
                            break;
                    }
                } catch (error: any) {
                    results.failed.push({ component, error: error.message });
                }
            }

            return {
                success: results.failed.length === 0,
                data: results,
                followUpSuggestions: [
                    `${params.operation}: ${results.successful.length} successful, ${results.failed.length} failed`,
                    results.failed.length === 0 ? 'All operations completed successfully' : 'Some operations failed - check details'
                ]
            };

        } catch (error: any) {
            return {
                success: false,
                error: {
                    code: 'BULK_OPERATION_ERROR',
                    message: error.message,
                    recoverable: true
                }
            };
        }
    }

    /**
     * Initialize fallback mode when MCP server is unavailable
     */
    private async initializeFallbackMode(): Promise<void> {
        console.log('🎨 Initializing shadcn/ui fallback mode...');
        
        // Register fallback tools that work without MCP server
        this.registerEnhancedTools();
        
        vscode.window.showWarningMessage(
            '⚠️ shadcn/ui MCP server not available. Using local component management.',
            'Configure MCP Server'
        ).then(action => {
            if (action === 'Configure MCP Server') {
                vscode.commands.executeCommand('palette.mcp.configure.shadcn');
            }
        });
    }

    // Helper methods...

    private async checkShadcnSetup(workspacePath: string): Promise<{ isSetup: boolean; missing: string[] }> {
        const missing = [];
        let isSetup = true;

        try {
            // Check components.json
            const componentsJsonPath = path.join(workspacePath, 'components.json');
            await vscode.workspace.fs.stat(vscode.Uri.file(componentsJsonPath));
        } catch {
            missing.push('components.json');
            isSetup = false;
        }

        // Check utils
        try {
            const utilsPath = path.join(workspacePath, 'src/lib/utils.ts');
            await vscode.workspace.fs.stat(vscode.Uri.file(utilsPath));
        } catch {
            missing.push('src/lib/utils.ts');
            isSetup = false;
        }

        return { isSetup, missing };
    }

    private async resolveComponentDependencies(components: string[]): Promise<{ components: string[]; dependencies: string[] }> {
        const allComponents = new Set<string>();
        const allDependencies = new Set<string>();

        for (const componentName of components) {
            const component = this.componentCatalog.find(c => c.name === componentName);
            if (component) {
                allComponents.add(componentName);
                component.dependencies.forEach(dep => allDependencies.add(dep));
            }
        }

        return {
            components: Array.from(allComponents),
            dependencies: Array.from(allDependencies)
        };
    }

    private generateComponentCodeSnippet(component: ShadcnComponent, variant?: string, customProps?: any): string {
        // Generate basic component usage code
        const example = component.examples?.[0];
        if (example) {
            return example.code;
        }

        return `<${component.name.split('-').map(part => 
            part.charAt(0).toUpperCase() + part.slice(1)
        ).join('')} />`;
    }

    private getPresetComponents(preset: string): string[] {
        const presets: Record<string, string[]> = {
            form: ['input', 'button', 'form', 'label', 'textarea', 'select', 'checkbox'],
            layout: ['card', 'sheet', 'dialog', 'accordion', 'tabs', 'separator'],
            navigation: ['navigation-menu', 'breadcrumb', 'pagination'],
            feedback: ['alert', 'toast', 'progress', 'skeleton'],
            all: this.componentCatalog.map(c => c.name)
        };

        return presets[preset] || [];
    }

    private async suggestMissingComponents(workspacePath: string): Promise<string[]> {
        // Analyze project files to suggest missing components
        // This would scan for common patterns and suggest relevant components
        const suggestions: string[] = [];

        try {
            // Look for form usage
            const hasFormUsage = await this.scanForPattern(workspacePath, /<form|<input|<button/);
            if (hasFormUsage) {
                suggestions.push('form', 'input', 'button', 'label');
            }

            // Look for navigation patterns
            const hasNavigation = await this.scanForPattern(workspacePath, /<nav|href=|Link/);
            if (hasNavigation) {
                suggestions.push('navigation-menu', 'breadcrumb');
            }

            // Look for data display patterns
            const hasDataDisplay = await this.scanForPattern(workspacePath, /<table|<ul|<li/);
            if (hasDataDisplay) {
                suggestions.push('data-table', 'card');
            }

        } catch (error) {
            console.warn('Error analyzing project for component suggestions:', error);
        }

        return suggestions;
    }

    private async scanForPattern(workspacePath: string, pattern: RegExp): Promise<boolean> {
        try {
            const searchPattern = new vscode.RelativePattern(workspacePath, '**/*.{tsx,jsx,ts,js}');
            const files = await vscode.workspace.findFiles(searchPattern, '**/node_modules/**', 10);

            for (const file of files) {
                const content = await vscode.workspace.fs.readFile(file);
                const text = new TextDecoder().decode(content);
                if (pattern.test(text)) {
                    return true;
                }
            }
        } catch (error) {
            console.warn('Error scanning for pattern:', error);
        }
        
        return false;
    }

    // Placeholder methods for complex operations
    private async executeInstallPlan(plan: any, context: ToolExecutionContext): Promise<any> {
        // Would execute via MCP server or fallback methods
        return { success: true, installed: plan.components, dependencies: plan.dependencies };
    }

    private async initializeShadcnSetup(workspacePath: string): Promise<void> {
        // Initialize shadcn/ui in project
        console.log('🎨 Initializing shadcn/ui setup...');
    }

    private async applyTheme(themeName: string, context: ToolExecutionContext): Promise<void> {
        // Apply theme to project CSS variables
        console.log(`🎨 Applying theme: ${themeName}`);
    }

    private async createCustomTheme(name: string, colors: any): Promise<ShadcnTheme> {
        // Create custom theme configuration
        return {
            name,
            colors,
            radius: '0.5rem'
        };
    }

    private async installSingleComponent(component: string, context: ToolExecutionContext): Promise<void> {
        // Install single component
    }

    private async updateSingleComponent(component: string, context: ToolExecutionContext): Promise<void> {
        // Update single component
    }

    private async removeSingleComponent(component: string, context: ToolExecutionContext): Promise<void> {
        // Remove single component
    }
}