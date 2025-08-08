#!/usr/bin/env node
/**
 * React Router MCP Server
 * Provides tools for automatic React Router route management with TypeScript AST manipulation
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { Project, SyntaxKind, SourceFile } from 'ts-morph';
import * as fs from 'fs-extra';
import * as path from 'path';
import { glob } from 'glob';

interface RouteInfo {
  path: string;
  component: string;
  importName: string;
  filePath: string;
  label?: string;
}

interface NavigationItem {
  path: string;
  label: string;
}

class ReactRouterMCPServer {
  private server: Server;
  private tsProject: Project;
  private projectPath: string;

  constructor() {
    this.server = new Server({
      name: 'react-router-mcp-server',
      version: '1.0.0',
    }, {
      capabilities: {
        tools: {},
      },
    });

    this.tsProject = new Project({
      tsConfigFilePath: undefined,
      useInMemoryFileSystem: false,
    });

    this.projectPath = process.cwd();
    this.setupToolHandlers();
  }

  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'analyze_routes',
          description: 'Analyze existing React Router routes in the project',
          inputSchema: {
            type: 'object',
            properties: {
              appPath: {
                type: 'string',
                description: 'Path to App.tsx file',
                default: 'src/App.tsx'
              }
            }
          }
        },
        {
          name: 'add_route',
          description: 'Add a new route to React Router configuration',
          inputSchema: {
            type: 'object',
            properties: {
              route: {
                type: 'string',
                description: 'Route path (e.g., "/dashboard")',
              },
              component: {
                type: 'string', 
                description: 'Component name (e.g., "Dashboard")',
              },
              importPath: {
                type: 'string',
                description: 'Import path for the component (e.g., "./pages/Dashboard")',
              },
              appPath: {
                type: 'string',
                description: 'Path to App.tsx file',
                default: 'src/App.tsx'
              },
              index: {
                type: 'boolean',
                description: 'Whether this is an index route',
                default: false
              }
            },
            required: ['route', 'component', 'importPath']
          }
        },
        {
          name: 'update_navigation',
          description: 'Update navigation component with new route',
          inputSchema: {
            type: 'object',
            properties: {
              route: {
                type: 'string',
                description: 'Route path (e.g., "/dashboard")',
              },
              label: {
                type: 'string',
                description: 'Display label for navigation (e.g., "Dashboard")',
              },
              navigationPath: {
                type: 'string',
                description: 'Path to Navigation component',
                default: 'src/components/Navigation.tsx'
              }
            },
            required: ['route', 'label']
          }
        },
        {
          name: 'remove_route',
          description: 'Remove a route from React Router configuration',
          inputSchema: {
            type: 'object',
            properties: {
              route: {
                type: 'string',
                description: 'Route path to remove (e.g., "/dashboard")',
              },
              appPath: {
                type: 'string',
                description: 'Path to App.tsx file',
                default: 'src/App.tsx'
              },
              removeFromNavigation: {
                type: 'boolean',
                description: 'Also remove from navigation component',
                default: true
              },
              navigationPath: {
                type: 'string',
                description: 'Path to Navigation component',
                default: 'src/components/Navigation.tsx'
              }
            },
            required: ['route']
          }
        },
        {
          name: 'generate_route_config',
          description: 'Generate complete route configuration based on page files',
          inputSchema: {
            type: 'object',
            properties: {
              pagesDir: {
                type: 'string',
                description: 'Directory containing page components',
                default: 'src/pages'
              },
              appPath: {
                type: 'string',
                description: 'Path to App.tsx file',  
                default: 'src/App.tsx'
              },
              navigationPath: {
                type: 'string',
                description: 'Path to Navigation component',
                default: 'src/components/Navigation.tsx'
              }
            }
          }
        }
      ] as Tool[]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;

        switch (name) {
          case 'analyze_routes':
            return { content: [{ type: 'text', text: JSON.stringify(await this.analyzeRoutes((args as any)?.appPath || 'src/App.tsx'), null, 2) }] };
            
          case 'add_route':
            return { content: [{ type: 'text', text: JSON.stringify(await this.addRoute(args || {}), null, 2) }] };
            
          case 'update_navigation':
            return { content: [{ type: 'text', text: JSON.stringify(await this.updateNavigation(args || {}), null, 2) }] };
            
          case 'remove_route':
            return { content: [{ type: 'text', text: JSON.stringify(await this.removeRoute(args || {}), null, 2) }] };
            
          case 'generate_route_config':
            return { content: [{ type: 'text', text: JSON.stringify(await this.generateRouteConfig(args || {}), null, 2) }] };
            
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{ 
            type: 'text', 
            text: JSON.stringify({ 
              error: error instanceof Error ? error.message : 'Unknown error',
              success: false 
            }, null, 2) 
          }],
          isError: true
        };
      }
    });
  }

  private async analyzeRoutes(appPath: string = 'src/App.tsx'): Promise<any> {
    const fullPath = path.resolve(this.projectPath, appPath);
    
    if (!await fs.pathExists(fullPath)) {
      throw new Error(`App.tsx not found at ${fullPath}`);
    }

    const sourceFile = this.tsProject.addSourceFileAtPath(fullPath);
    const routes: RouteInfo[] = [];
    const imports: string[] = [];

    // Find all import declarations
    sourceFile.getImportDeclarations().forEach(importDecl => {
      const moduleSpecifier = importDecl.getModuleSpecifier().getLiteralValue();
      const namedImports = importDecl.getNamedImports().map(ni => ni.getName());
      const defaultImport = importDecl.getDefaultImport()?.getText();
      
      imports.push({
        module: moduleSpecifier,
        named: namedImports,
        default: defaultImport
      } as any);
    });

    // Find Route elements in JSX
    sourceFile.forEachDescendantAsArray().forEach(node => {
      if (node.getKind() === SyntaxKind.JsxElement || node.getKind() === SyntaxKind.JsxSelfClosingElement) {
        const tagName = node.getFirstChild()?.getFirstChild()?.getText();
        
        if (tagName === 'Route') {
          const attributes: any = {};
          node.forEachChild(child => {
            if (child.getKind() === SyntaxKind.JsxAttributes) {
              child.forEachChild(attr => {
                if (attr.getKind() === SyntaxKind.JsxAttribute) {
                  const name = attr.getFirstChild()?.getText();
                  const value = attr.getLastChild()?.getText();
                  if (name && value) {
                    attributes[name] = value.replace(/['"]/g, '');
                  }
                }
              });
            }
          });

          if (attributes.path || attributes.index) {
            routes.push({
              path: attributes.path || '/',
              component: attributes.element?.replace(/[<>]/g, '') || 'Unknown',
              importName: attributes.element?.match(/^<(\w+)/)?.[1] || 'Unknown',
              filePath: appPath,
              index: attributes.index === 'true'
            } as any);
          }
        }
      }
    });

    return {
      success: true,
      appPath: fullPath,
      routes,
      imports,
      totalRoutes: routes.length
    };
  }

  private async addRoute(args: any): Promise<any> {
    const { route, component, importPath, appPath = 'src/App.tsx', index = false } = args;
    const fullPath = path.resolve(this.projectPath, appPath);

    if (!await fs.pathExists(fullPath)) {
      throw new Error(`App.tsx not found at ${fullPath}`);
    }

    const sourceFile = this.tsProject.addSourceFileAtPath(fullPath);

    // Add import statement
    const existingImport = sourceFile.getImportDeclaration(decl => 
      decl.getModuleSpecifier().getLiteralValue() === importPath
    );

    if (!existingImport) {
      sourceFile.addImportDeclaration({
        moduleSpecifier: importPath,
        defaultImport: component
      });
    }

    // Find the Routes component and add new Route
    let routeAdded = false;
    const newRouteText = index 
      ? `<Route index element={<${component} />} />`
      : `<Route path="${route}" element={<${component} />} />`;
    
    // Simple text-based insertion for now
    const currentText = sourceFile.getFullText();
    if (currentText.includes('<Routes>') && currentText.includes('</Routes>')) {
      const newText = currentText.replace('</Routes>', `          ${newRouteText}\n        </Routes>`);
      sourceFile.replaceWithText(newText);
      routeAdded = true;
    }

    if (!routeAdded) {
      throw new Error('Could not find Routes component to add route to');
    }

    // Save the file
    await sourceFile.save();

    return {
      success: true,
      message: `Added route ${route} with component ${component}`,
      route: {
        path: route,
        component,
        importPath,
        index
      }
    };
  }

  private async updateNavigation(args: any): Promise<any> {
    const { route, label, navigationPath = 'src/components/Navigation.tsx' } = args;
    const fullPath = path.resolve(this.projectPath, navigationPath);

    if (!await fs.pathExists(fullPath)) {
      throw new Error(`Navigation component not found at ${fullPath}`);
    }

    const sourceFile = this.tsProject.addSourceFileAtPath(fullPath);

    // Find navItems array and add new item using text replacement
    let navUpdated = false;
    const currentText = sourceFile.getFullText();
    const newItem = `    { path: '${route}', label: '${label}' },`;
    
    // Look for the navItems array and insert before the closing bracket
    if (currentText.includes('const navItems = [') || currentText.includes('const navItems=[')) {
      // Find the closing bracket of the array
      const navItemsMatch = currentText.match(/const navItems\s*=\s*\[([\s\S]*?)\]/);
      if (navItemsMatch && navItemsMatch[1]) {
        const arrayContent = navItemsMatch[1];
        const newArrayContent = arrayContent.trimEnd() + '\n    ' + newItem;
        const newText = currentText.replace(
          /const navItems\s*=\s*\[([\s\S]*?)\]/,
          `const navItems = [\n${newArrayContent}\n  ]`
        );
        sourceFile.replaceWithText(newText);
        navUpdated = true;
      }
    }

    if (!navUpdated) {
      throw new Error('Could not find navItems array to update');
    }

    // Save the file
    await sourceFile.save();

    return {
      success: true,
      message: `Added navigation item for ${route}`,
      navigationItem: {
        path: route,
        label
      }
    };
  }

  private async removeRoute(args: any): Promise<any> {
    const { 
      route, 
      appPath = 'src/App.tsx', 
      removeFromNavigation = true, 
      navigationPath = 'src/components/Navigation.tsx' 
    } = args;
    
    const results: string[] = [];

    // Remove from App.tsx using text replacement
    const fullAppPath = path.resolve(this.projectPath, appPath);
    if (await fs.pathExists(fullAppPath)) {
      const sourceFile = this.tsProject.addSourceFileAtPath(fullAppPath);
      let currentText = sourceFile.getFullText();
      
      // Remove route using regex
      const routeRegex = new RegExp(`\\s*<Route\\s+path=["']${route}["'][^>]*\\/?>\n?`, 'g');
      const newText = currentText.replace(routeRegex, '');
      
      if (newText !== currentText) {
        sourceFile.replaceWithText(newText);
        await sourceFile.save();
        results.push(`Removed route ${route} from App.tsx`);
      }
    }

    // Remove from Navigation.tsx using text replacement
    if (removeFromNavigation) {
      const fullNavPath = path.resolve(this.projectPath, navigationPath);
      if (await fs.pathExists(fullNavPath)) {
        const navSourceFile = this.tsProject.addSourceFileAtPath(fullNavPath);
        let currentText = navSourceFile.getFullText();
        
        // Remove navigation item using regex
        const navItemRegex = new RegExp(`\\s*{\\s*path:\\s*['"]${route}['"][^}]*},?\n?`, 'g');
        const newText = currentText.replace(navItemRegex, '');
        
        if (newText !== currentText) {
          navSourceFile.replaceWithText(newText);
          await navSourceFile.save();
          results.push(`Removed navigation item for ${route}`);
        }
      }
    }

    return {
      success: true,
      results,
      removedRoute: route
    };
  }

  private async generateRouteConfig(args: any): Promise<any> {
    const { 
      pagesDir = 'src/pages', 
      appPath = 'src/App.tsx',
      navigationPath = 'src/components/Navigation.tsx'
    } = args;

    const pagesDirPath = path.resolve(this.projectPath, pagesDir);
    
    if (!await fs.pathExists(pagesDirPath)) {
      throw new Error(`Pages directory not found at ${pagesDirPath}`);
    }

    // Find all page files
    const pageFiles = await glob('**/*.{tsx,ts,jsx,js}', { 
      cwd: pagesDirPath,
      ignore: ['**/*.test.*', '**/*.spec.*', '**/index.*']
    });

    const routes: RouteInfo[] = [];
    const navItems: NavigationItem[] = [];

    // Generate routes from page files
    for (const pageFile of pageFiles) {
      const fileName = path.basename(pageFile, path.extname(pageFile));
      const componentName = fileName;
      const routePath = fileName.toLowerCase() === 'home' ? '/' : `/${fileName.toLowerCase()}`;
      const importPath = `./pages/${pageFile.replace(/\.(tsx?|jsx?)$/, '')}`;
      const label = fileName.charAt(0).toUpperCase() + fileName.slice(1);

      routes.push({
        path: routePath,
        component: componentName,
        importName: componentName,
        filePath: path.join(pagesDir, pageFile),
        label
      });

      navItems.push({
        path: routePath,
        label
      });
    }

    return {
      success: true,
      pagesFound: pageFiles.length,
      routes,
      navigationItems: navItems,
      generatedConfig: {
        routes: routes.map(r => ({
          path: r.path,
          component: r.component,
          import: `import ${r.component} from '${r.importName}'`
        })),
        navigation: navItems
      }
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('React Router MCP server running on stdio');
  }
}

const server = new ReactRouterMCPServer();
server.run().catch(console.error);