import * as fs from 'fs';
import * as path from 'path';
import {
    ComponentInfo,
    ComponentAST,
    ComponentCluster,
    ComponentNode,
    DependencyEdge,
    GraphMetrics,
    NamingConventions,
    StylePatterns,
    LayerInfo,
    HierarchyInfo,
    DataFlowInfo,
    ComponentCategory
} from './types';

export class AnalyzerUtils {
    
    /**
     * Find all React component files in the project with better detection
     */
    static async findComponentFiles(rootPath: string): Promise<string[]> {
        const componentFiles: string[] = [];
        const extensions = ['.tsx', '.jsx', '.ts', '.js'];
        
        async function scanDirectory(dirPath: string) {
            try {
                const entries = fs.readdirSync(dirPath, { withFileTypes: true });
                
                for (const entry of entries) {
                    const fullPath = path.join(dirPath, entry.name);
                    
                    if (entry.isDirectory()) {
                        // Skip node_modules and other non-source directories
                        if (!['node_modules', '.git', 'dist', 'build', '.next', 'coverage', '.vscode'].includes(entry.name)) {
                            await scanDirectory(fullPath);
                        }
                    } else if (entry.isFile()) {
                        const ext = path.extname(entry.name);
                        if (extensions.includes(ext)) {
                            const fileName = path.basename(entry.name, ext);
                            
                            // Enhanced component detection criteria
                            const startsWithCapital = /^[A-Z]/.test(fileName);
                            const isInComponentsDir = fullPath.includes('/components/') || fullPath.includes('\\components\\');
                            const isPages = fullPath.includes('/pages/') || fullPath.includes('\\pages\\') || fullPath.includes('/routes/') || fullPath.includes('\\routes\\');
                            const hasReactExtension = ext === '.tsx' || ext === '.jsx';
                            const isLikelyComp = AnalyzerUtils.isLikelyComponent(fullPath);
                            
                            // MORE INCLUSIVE: Include ALL .tsx/.jsx files first (user reported 49 tsx files)
                            if (hasReactExtension) {
                                componentFiles.push(fullPath);
                            }
                            // Then add other likely components that aren't .tsx/.jsx
                            else if (startsWithCapital || isInComponentsDir || isPages || isLikelyComp) {
                                componentFiles.push(fullPath);
                            }
                        }
                    }
                }
            } catch (error) {
                console.warn(`Error scanning directory ${dirPath}:`, error);
            }
        }
        
        await scanDirectory(rootPath);
        
        // Remove duplicates and log for debugging
        const uniqueFiles = [...new Set(componentFiles)];
        console.log(`🔍 Component detection summary:`);
        console.log(`  - Total files found: ${uniqueFiles.length}`);
        console.log(`  - .tsx files: ${uniqueFiles.filter(f => f.endsWith('.tsx')).length}`);
        console.log(`  - .jsx files: ${uniqueFiles.filter(f => f.endsWith('.jsx')).length}`);
        console.log(`  - .ts files: ${uniqueFiles.filter(f => f.endsWith('.ts')).length}`);
        console.log(`  - .js files: ${uniqueFiles.filter(f => f.endsWith('.js')).length}`);
        
        return uniqueFiles;
    }
    
    /**
     * Check if a file is likely a React component
     */
    private static isLikelyComponent(filePath: string): boolean {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            
            // Look for React patterns (more flexible)
            const hasReactImport = /import.*react/i.test(content);
            const hasJSX = /<[A-Z]/.test(content) || /<[a-z]+[^>]*>/.test(content) || /jsx/i.test(content);
            const hasComponentExport = /export\s+(default\s+)?(function|const|class)/.test(content);
            const hasReturnJSX = /return\s*\(?\s*</.test(content);
            
            // More lenient: if it has JSX or React patterns, consider it a component
            return hasJSX || hasReturnJSX || (hasReactImport && hasComponentExport);
        } catch {
            return false;
        }
    }
    
    /**
     * Generate descriptive text for a component based on AST analysis
     */
    static generateComponentDescription(ast: ComponentAST): string {
        const parts: string[] = [];
        
        // Basic type
        parts.push(`${ast.type} component`);
        
        // Props information
        if (ast.props.length > 0) {
            parts.push(`with ${ast.props.length} props`);
        }
        
        // Hook usage
        if (ast.hooks.length > 0) {
            const hookTypes = [...new Set(ast.hooks.map(h => h.type))];
            parts.push(`using ${hookTypes.join(', ')} hooks`);
        }
        
        // Complexity
        if (ast.complexity.cyclomaticComplexity > 5) {
            parts.push('(complex logic)');
        }
        
        // Patterns
        if (ast.jsx.patterns.length > 0) {
            parts.push(`implementing ${ast.jsx.patterns.join(', ')}`);
        }
        
        // Styling
        if (ast.styling.approach && ast.styling.approach !== 'unknown') {
            parts.push(`styled with ${ast.styling.approach}`);
        }
        
        // Accessibility
        if (ast.jsx.accessibility.score > 70) {
            parts.push('(accessible)');
        }
        
        return parts.join(' ');
    }
    
    /**
     * Format props array into a readable string
     */
    static formatPropsString(props: ComponentAST['props']): string {
        if (props.length === 0) return '';
        
        return props
            .map(prop => `${prop.name}${prop.optional ? '?' : ''}: ${prop.type}`)
            .join(', ');
    }
    
    /**
     * Categorize component complexity
     */
    static categorizeComplexity(ast: ComponentAST): 'simple' | 'medium' | 'complex' {
        const { cyclomaticComplexity, cognitiveComplexity, linesOfCode } = ast.complexity;
        const hookCount = ast.hooks.length;
        const propCount = ast.props.length;
        
        // Calculate weighted complexity score
        const complexityScore = 
            (cyclomaticComplexity * 0.3) +
            (cognitiveComplexity * 0.25) +
            (Math.min(linesOfCode / 50, 10) * 0.2) +
            (hookCount * 0.15) +
            (propCount * 0.1);
        
        if (complexityScore < 3) return 'simple';
        if (complexityScore < 8) return 'medium';
        return 'complex';
    }
    
    /**
     * Calculate node weight for dependency graph
     */
    static calculateNodeWeight(component: ComponentInfo): number {
        let weight = 1;
        
        // Increase weight based on complexity
        if (component.complexity === 'complex') weight += 2;
        else if (component.complexity === 'medium') weight += 1;
        
        // Increase weight based on number of props
        if (component.ast?.props.length) {
            weight += Math.min(component.ast.props.length * 0.1, 1);
        }
        
        // Increase weight for certain categories
        if (component.category === 'layout' || component.category === 'page') {
            weight += 1.5;
        }
        
        return weight;
    }
    
    /**
     * Identify component clusters based on dependencies and similarity
     */
    static identifyComponentClusters(nodes: ComponentNode[], edges: DependencyEdge[]): ComponentCluster[] {
        const clusters: ComponentCluster[] = [];
        const visited = new Set<string>();
        
        // Group by category first
        const categoryGroups = new Map<ComponentCategory, ComponentNode[]>();
        nodes.forEach(node => {
            if (!categoryGroups.has(node.type)) {
                categoryGroups.set(node.type, []);
            }
            categoryGroups.get(node.type)!.push(node);
        });
        
        // Create clusters for each category
        categoryGroups.forEach((categoryNodes, category) => {
            if (categoryNodes.length > 1) {
                const cohesion = AnalyzerUtils.calculateClusterCohesion(categoryNodes, edges);
                
                clusters.push({
                    id: `cluster-${category}`,
                    components: categoryNodes.map(n => n.id),
                    category,
                    cohesion
                });
                
                categoryNodes.forEach(node => visited.add(node.id));
            }
        });
        
        // Find additional clusters based on strong dependencies
        const remainingNodes = nodes.filter(n => !visited.has(n.id));
        const dependencyClusters = AnalyzerUtils.findDependencyClusters(remainingNodes, edges);
        clusters.push(...dependencyClusters);
        
        return clusters;
    }
    
    /**
     * Calculate cluster cohesion based on internal connections
     */
    static calculateClusterCohesion(nodes: ComponentNode[], edges: DependencyEdge[]): number {
        const nodeIds = new Set(nodes.map(n => n.id));
        const internalEdges = edges.filter(e => nodeIds.has(e.from) && nodeIds.has(e.to));
        const maxPossibleEdges = nodes.length * (nodes.length - 1);
        
        return maxPossibleEdges > 0 ? internalEdges.length / maxPossibleEdges : 0;
    }
    
    /**
     * Find clusters based on dependency relationships
     */
    static findDependencyClusters(nodes: ComponentNode[], edges: DependencyEdge[]): ComponentCluster[] {
        const clusters: ComponentCluster[] = [];
        const visited = new Set<string>();
        
        nodes.forEach(node => {
            if (visited.has(node.id)) return;
            
            const cluster = AnalyzerUtils.findConnectedComponents(node.id, nodes, edges, visited);
            if (cluster.length > 1) {
                const cohesion = AnalyzerUtils.calculateClusterCohesion(
                    cluster.map(id => nodes.find(n => n.id === id)!),
                    edges
                );
                
                clusters.push({
                    id: `dependency-cluster-${clusters.length}`,
                    components: cluster,
                    category: 'utility', // Default category for dependency clusters
                    cohesion
                });
            }
        });
        
        return clusters;
    }
    
    /**
     * Find connected components using DFS
     */
    static findConnectedComponents(
        startId: string,
        nodes: ComponentNode[],
        edges: DependencyEdge[],
        visited: Set<string>
    ): string[] {
        const component: string[] = [];
        const stack = [startId];
        
        while (stack.length > 0) {
            const nodeId = stack.pop()!;
            if (visited.has(nodeId)) continue;
            
            visited.add(nodeId);
            component.push(nodeId);
            
            // Find connected nodes
            const connectedEdges = edges.filter(e => e.from === nodeId || e.to === nodeId);
            connectedEdges.forEach(edge => {
                const connectedId = edge.from === nodeId ? edge.to : edge.from;
                if (!visited.has(connectedId)) {
                    stack.push(connectedId);
                }
            });
        }
        
        return component;
    }
    
    /**
     * Calculate graph metrics
     */
    static calculateGraphMetrics(nodes: ComponentNode[], edges: DependencyEdge[]): GraphMetrics {
        const nodeCount = nodes.length;
        const edgeCount = edges.length;
        const maxPossibleEdges = nodeCount * (nodeCount - 1);
        
        // Graph density
        const density = maxPossibleEdges > 0 ? edgeCount / maxPossibleEdges : 0;
        
        // Calculate centrality scores (simplified PageRank-like algorithm)
        const centralityScores: Record<string, number> = {};
        nodes.forEach(node => {
            const incomingEdges = edges.filter(e => e.to === node.id).length;
            const outgoingEdges = edges.filter(e => e.from === node.id).length;
            centralityScores[node.id] = (incomingEdges * 2 + outgoingEdges) / Math.max(edgeCount, 1);
        });
        
        // Average path length (simplified)
        const avgPathLength = nodeCount > 1 ? Math.log(nodeCount) : 0;
        
        // Modularity (simplified)
        const modularity = density > 0 ? 1 - density : 0;
        
        return {
            density,
            modularity,
            avgPathLength,
            centralityScores
        };
    }
    
    /**
     * Analyze naming conventions across components
     */
    static analyzeNamingConventions(components: ComponentInfo[]): NamingConventions {
        let pascalCaseComponents = 0;
        let camelCaseComponents = 0;
        let pascalCaseFiles = 0;
        let kebabCaseFiles = 0;
        let camelCaseFiles = 0;
        
        components.forEach(component => {
            // Analyze component names
            if (/^[A-Z][a-zA-Z0-9]*$/.test(component.name)) {
                pascalCaseComponents++;
            } else if (/^[a-z][a-zA-Z0-9]*$/.test(component.name)) {
                camelCaseComponents++;
            }
            
            // Analyze file names
            const fileName = path.basename(component.path, path.extname(component.path));
            if (/^[A-Z][a-zA-Z0-9]*$/.test(fileName)) {
                pascalCaseFiles++;
            } else if (/^[a-z]+(-[a-z]+)*$/.test(fileName)) {
                kebabCaseFiles++;
            } else if (/^[a-z][a-zA-Z0-9]*$/.test(fileName)) {
                camelCaseFiles++;
            }
        });
        
        return {
            components: pascalCaseComponents > camelCaseComponents ? 'PascalCase' : 'camelCase',
            files: pascalCaseFiles > kebabCaseFiles && pascalCaseFiles > camelCaseFiles ? 'PascalCase' :
                   kebabCaseFiles > camelCaseFiles ? 'kebab-case' : 'camelCase',
            props: 'camelCase', // React convention
            constants: 'UPPER_CASE' // Common convention
        };
    }
    
    /**
     * Analyze style patterns across components
     */
    static analyzeStylePatterns(components: ComponentInfo[]): StylePatterns {
        const stylingApproaches = components
            .map(c => c.ast?.styling.approach)
            .filter(Boolean);
        
        const classNamingPatterns = components
            .flatMap(c => c.ast?.styling.classes || [])
            .map(cls => {
                if (cls.includes('__') || cls.includes('--')) return 'BEM';
                if (cls.includes('-') && cls.length < 20) return 'utility';
                return 'semantic';
            });
        
        // Determine dominant patterns
        const classNaming = AnalyzerUtils.getMostCommon(classNamingPatterns) || 'semantic';
        
        let organization: StylePatterns['organization'] = 'component-based';
        if (stylingApproaches.some(a => a?.includes('tailwind'))) {
            organization = 'utility-first';
        } else if (stylingApproaches.some(a => a?.includes('atomic'))) {
            organization = 'atomic';
        }
        
        // Check for responsive patterns
        const hasResponsiveClasses = components.some(c => 
            c.ast?.styling.responsive || 
            c.ast?.styling.classes.some(cls => /^(sm|md|lg|xl):/i.test(cls))
        );
        
        const responsiveStrategy: StylePatterns['responsiveStrategy'] = 
            hasResponsiveClasses ? 'mobile-first' : 'desktop-first';
        
        return {
            classNaming: classNaming as StylePatterns['classNaming'],
            organization,
            responsiveStrategy
        };
    }
    
    /**
     * Get most common item from array
     */
    static getMostCommon<T>(arr: T[]): T | null {
        if (arr.length === 0) return null;
        
        const counts = new Map<T, number>();
        arr.forEach(item => {
            counts.set(item, (counts.get(item) || 0) + 1);
        });
        
        let mostCommon = arr[0];
        let maxCount = 0;
        
        counts.forEach((count, item) => {
            if (count > maxCount) {
                maxCount = count;
                mostCommon = item;
            }
        });
        
        return mostCommon;
    }
}