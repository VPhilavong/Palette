import * as vscode from 'vscode';
import { parse } from '@babel/parser';
import traverse, { NodePath } from '@babel/traverse';
import * as t from '@babel/types';
import { ComponentInfo, ImportInfo } from './types';

export class ASTParser {
    async parseComponentsFromFiles(files: vscode.Uri[]): Promise<ComponentInfo[]> {
        const components: ComponentInfo[] = [];
        
        for (const file of files) {
            try {
                const componentInfo = await this.parseFile(file);
                if (componentInfo) {
                    components.push(componentInfo);
                }
            } catch (error) {
                console.warn(`Failed to parse ${file.fsPath}:`, error);
            }
        }
        
        return components;
    }

    private async parseFile(fileUri: vscode.Uri): Promise<ComponentInfo | null> {
        try {
            const content = await vscode.workspace.fs.readFile(fileUri);
            const code = content.toString();
            
            // Skip files that are too large or don't look like components
            if (code.length > 50000 || !this.looksLikeComponent(code)) {
                return null;
            }

            const ast = parse(code, {
                sourceType: 'module',
                allowImportExportEverywhere: true,
                allowReturnOutsideFunction: true,
                plugins: [
                    'jsx',
                    'typescript',
                    'decorators-legacy',
                    'classProperties',
                    'objectRestSpread',
                    'asyncGenerators',
                    'functionBind',
                    'exportDefaultFrom',
                    'exportNamespaceFrom',
                    'dynamicImport'
                ]
            });

            const componentInfo: ComponentInfo = {
                name: this.getFileBaseName(fileUri),
                path: vscode.workspace.asRelativePath(fileUri),
                exports: [],
                imports: [],
                props: [],
                hooks: []
            };

            traverse(ast, {
                // Extract imports
                ImportDeclaration: (path: NodePath<t.ImportDeclaration>) => {
                    const importInfo: ImportInfo = {
                        module: path.node.source.value,
                        imports: [],
                        isDefault: false
                    };

                    path.node.specifiers.forEach((spec: t.ImportSpecifier | t.ImportDefaultSpecifier | t.ImportNamespaceSpecifier) => {
                        if (t.isImportDefaultSpecifier(spec)) {
                            importInfo.imports.push(spec.local.name);
                            importInfo.isDefault = true;
                        } else if (t.isImportSpecifier(spec)) {
                            importInfo.imports.push(spec.imported.type === 'Identifier' ? spec.imported.name : spec.imported.value);
                        } else if (t.isImportNamespaceSpecifier(spec)) {
                            importInfo.imports.push(`* as ${spec.local.name}`);
                        }
                    });

                    componentInfo.imports.push(importInfo);
                },

                // Extract function components
                FunctionDeclaration: (path: NodePath<t.FunctionDeclaration>) => {
                    if (this.isReactComponent(path.node)) {
                        componentInfo.exports.push(path.node.id?.name || 'Anonymous');
                        this.extractPropsFromFunction(path.node, componentInfo);
                    }
                },

                // Extract arrow function components
                VariableDeclarator: (path: NodePath<t.VariableDeclarator>) => {
                    if (t.isArrowFunctionExpression(path.node.init) || t.isFunctionExpression(path.node.init)) {
                        if (this.isReactComponent(path.node.init)) {
                            const name = t.isIdentifier(path.node.id) ? path.node.id.name : 'Anonymous';
                            componentInfo.exports.push(name);
                            this.extractPropsFromFunction(path.node.init, componentInfo);
                        }
                    }
                },

                // Extract class components
                ClassDeclaration: (path: NodePath<t.ClassDeclaration>) => {
                    if (this.isReactClassComponent(path.node)) {
                        componentInfo.exports.push(path.node.id?.name || 'Anonymous');
                    }
                },

                // Extract default exports
                ExportDefaultDeclaration: (path: NodePath<t.ExportDefaultDeclaration>) => {
                    if (t.isIdentifier(path.node.declaration)) {
                        componentInfo.exports.push(`default:${path.node.declaration.name}`);
                    } else if (t.isFunctionDeclaration(path.node.declaration)) {
                        const name = path.node.declaration.id?.name || 'default';
                        componentInfo.exports.push(`default:${name}`);
                    }
                },

                // Extract named exports
                ExportNamedDeclaration: (path: NodePath<t.ExportNamedDeclaration>) => {
                    if (path.node.specifiers) {
                        path.node.specifiers.forEach((spec) => {
                            if (t.isExportSpecifier(spec)) {
                                const exportName = spec.exported.type === 'Identifier' ? spec.exported.name : spec.exported.value;
                                componentInfo.exports.push(exportName);
                            }
                        });
                    }
                },

                // Extract React hooks usage
                CallExpression: (path: NodePath<t.CallExpression>) => {
                    if (t.isIdentifier(path.node.callee) && path.node.callee.name.startsWith('use')) {
                        const hookName = path.node.callee.name;
                        if (!componentInfo.hooks!.includes(hookName)) {
                            componentInfo.hooks!.push(hookName);
                        }
                    }
                }
            });

            // Only return if we found exports (indicating it's likely a component file)
            return componentInfo.exports.length > 0 ? componentInfo : null;

        } catch (error) {
            console.warn(`AST parsing failed for ${fileUri.fsPath}:`, error);
            return null;
        }
    }

    private looksLikeComponent(code: string): boolean {
        // Quick heuristics to identify component files
        const componentIndicators = [
            /export\s+(default\s+)?function\s+[A-Z]/,  // Exported function starting with capital
            /export\s+(default\s+)?const\s+[A-Z]/,     // Exported const starting with capital
            /class\s+[A-Z]\w*\s+extends\s+.*Component/, // Class component
            /<[A-Z][^>]*>/,                             // JSX with capital letter tag
            /useState|useEffect|useContext/,            // React hooks
            /import.*from\s+['"]react['"]/              // React import
        ];

        return componentIndicators.some(pattern => pattern.test(code));
    }

    private isReactComponent(node: t.Function): boolean {
        // Check if function returns JSX
        let returnsJSX = false;
        
        // Use a simple visitor without scope
        const visitor = {
            ReturnStatement(path: NodePath<t.ReturnStatement>) {
                if (path.node.argument) {
                    if (t.isJSXElement(path.node.argument) || t.isJSXFragment(path.node.argument)) {
                        returnsJSX = true;
                    }
                }
            }
        };
        
        traverse({ type: 'Program', body: [node] } as any, visitor);

        return returnsJSX;
    }

    private isReactClassComponent(node: t.ClassDeclaration): boolean {
        if (!node.superClass) return false;
        
        // Check if extends Component or PureComponent
        if (t.isIdentifier(node.superClass)) {
            return ['Component', 'PureComponent'].includes(node.superClass.name);
        }
        
        if (t.isMemberExpression(node.superClass)) {
            const obj = node.superClass.object;
            const prop = node.superClass.property;
            if (t.isIdentifier(obj) && t.isIdentifier(prop)) {
                return obj.name === 'React' && ['Component', 'PureComponent'].includes(prop.name);
            }
        }
        
        return false;
    }

    private extractPropsFromFunction(node: t.Function, componentInfo: ComponentInfo): void {
        // Extract props from function parameters
        if (node.params.length > 0) {
            const firstParam = node.params[0];
            
            if (t.isObjectPattern(firstParam)) {
                // Destructured props: function Component({ prop1, prop2 })
                firstParam.properties.forEach(prop => {
                    if (t.isObjectProperty(prop) && t.isIdentifier(prop.key)) {
                        componentInfo.props!.push(prop.key.name);
                    }
                });
            } else if (t.isIdentifier(firstParam)) {
                // Props object: function Component(props)
                componentInfo.props!.push(firstParam.name);
            }
        }
    }

    private getFileBaseName(uri: vscode.Uri): string {
        const fileName = uri.fsPath.split('/').pop() || '';
        return fileName.replace(/\.(js|jsx|ts|tsx)$/, '');
    }
}