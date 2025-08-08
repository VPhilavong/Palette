/**
 * Component Relationship Analyzer
 * Maps dependencies, relationships, and patterns between components in the project
 */

import * as vscode from 'vscode';
import { ProjectStructure, ComponentInfo, ComponentType } from './typescript-project-analyzer';

export interface ComponentRelationship {
    source: string;
    target: string;
    type: 'imports' | 'extends' | 'uses' | 'renders' | 'wraps';
    strength: number; // 1-10, how tightly coupled
    description: string;
}

export interface ComponentCluster {
    name: string;
    components: string[];
    description: string;
    type: 'feature' | 'ui-library' | 'pages' | 'utilities';
    cohesion: number; // How related components are within cluster
}

export interface DependencyNode {
    componentName: string;
    filePath: string;
    dependencies: string[];
    dependents: string[];
    depth: number;
    isLeaf: boolean;
    isRoot: boolean;
    cyclicDependencies: string[];
}

export interface RelationshipAnalysis {
    relationships: ComponentRelationship[];
    clusters: ComponentCluster[];
    dependencyGraph: DependencyNode[];
    patterns: ComponentPattern[];
    recommendations: RelationshipRecommendation[];
    metrics: {
        averageCoupling: number;
        cyclicDependenciesCount: number;
        orphanedComponents: number;
        mostUsedComponents: string[];
        leastUsedComponents: string[];
    };
}

export interface ComponentPattern {
    name: string;
    description: string;
    components: string[];
    confidence: number;
    examples: string[];
}

export interface RelationshipRecommendation {
    type: 'refactor' | 'extract' | 'merge' | 'decouple';
    priority: 'high' | 'medium' | 'low';
    components: string[];
    message: string;
    action: string;
}

export class ComponentRelationshipAnalyzer {
    private projectStructure: ProjectStructure | null = null;
    private components: ComponentInfo[] = [];

    /**
     * Analyze component relationships and dependencies
     */
    async analyzeRelationships(projectStructure: ProjectStructure): Promise<RelationshipAnalysis> {
        console.log('🔗 Analyzing component relationships...');
        
        this.projectStructure = projectStructure;
        this.components = projectStructure.components;

        const relationships = this.extractRelationships();
        const dependencyGraph = this.buildDependencyGraph();
        const clusters = this.identifyComponentClusters();
        const patterns = this.detectComponentPatterns();
        const recommendations = this.generateRelationshipRecommendations(relationships, dependencyGraph, clusters);
        const metrics = this.calculateRelationshipMetrics(relationships, dependencyGraph);

        return {
            relationships,
            clusters,
            dependencyGraph,
            patterns,
            recommendations,
            metrics
        };
    }

    /**
     * Extract relationships between components
     */
    private extractRelationships(): ComponentRelationship[] {
        const relationships: ComponentRelationship[] = [];

        this.components.forEach(sourceComponent => {
            sourceComponent.imports.forEach(importPath => {
                const targetComponent = this.findComponentByImport(importPath);
                if (targetComponent) {
                    const relationship = this.createRelationship(
                        sourceComponent.name,
                        targetComponent.name,
                        importPath,
                        sourceComponent
                    );
                    if (relationship) {
                        relationships.push(relationship);
                    }
                }
            });
        });

        return this.deduplicateRelationships(relationships);
    }

    /**
     * Create a relationship object based on import analysis
     */
    private createRelationship(
        source: string,
        target: string,
        importPath: string,
        sourceComponent: ComponentInfo
    ): ComponentRelationship | null {
        // Determine relationship type based on import path and content
        let type: ComponentRelationship['type'] = 'imports';
        let strength = 1;
        let description = `${source} imports ${target}`;

        // Analyze import usage to determine relationship strength and type
        const sourceContent = this.getComponentContent(sourceComponent.filePath);
        if (sourceContent) {
            const targetUsageCount = this.countComponentUsage(sourceContent, target);
            strength = Math.min(10, Math.max(1, targetUsageCount));

            // Determine relationship type
            if (this.isComponentRendered(sourceContent, target)) {
                type = 'renders';
                description = `${source} renders ${target} component`;
                strength += 2;
            } else if (this.isComponentWrapped(sourceContent, target)) {
                type = 'wraps';
                description = `${source} wraps ${target} component`;
                strength += 1;
            } else if (this.isComponentExtended(sourceContent, target)) {
                type = 'extends';
                description = `${source} extends ${target}`;
                strength += 3;
            } else if (this.isUtilityUsed(sourceContent, target)) {
                type = 'uses';
                description = `${source} uses ${target} utility`;
            }
        }

        return {
            source,
            target,
            type,
            strength: Math.min(10, strength),
            description
        };
    }

    /**
     * Build dependency graph
     */
    private buildDependencyGraph(): DependencyNode[] {
        const nodes: Map<string, DependencyNode> = new Map();

        // Initialize nodes
        this.components.forEach(component => {
            nodes.set(component.name, {
                componentName: component.name,
                filePath: component.filePath,
                dependencies: [],
                dependents: [],
                depth: 0,
                isLeaf: false,
                isRoot: false,
                cyclicDependencies: []
            });
        });

        // Build dependency relationships
        this.components.forEach(component => {
            const node = nodes.get(component.name)!;
            
            component.dependencies.forEach(depName => {
                const targetComponent = this.findComponentByName(depName);
                if (targetComponent) {
                    node.dependencies.push(targetComponent.name);
                    const targetNode = nodes.get(targetComponent.name)!;
                    targetNode.dependents.push(component.name);
                }
            });
        });

        // Calculate depths and identify roots/leaves
        const nodeArray = Array.from(nodes.values());
        this.calculateNodeDepths(nodeArray);
        this.identifyRootsAndLeaves(nodeArray);
        this.detectCyclicDependencies(nodeArray);

        return nodeArray;
    }

    /**
     * Identify component clusters based on usage patterns
     */
    private identifyComponentClusters(): ComponentCluster[] {
        const clusters: ComponentCluster[] = [];

        // Cluster by component type
        const typeGroups = this.groupComponentsByType();
        Object.entries(typeGroups).forEach(([type, components]) => {
            if (components.length > 1) {
                clusters.push({
                    name: `${type.replace('_', ' ')} Components`,
                    components: components.map(c => c.name),
                    description: `Components of type: ${type}`,
                    type: this.mapComponentTypeToClusterType(type as ComponentType),
                    cohesion: this.calculateClusterCohesion(components)
                });
            }
        });

        // Cluster by file location
        const locationGroups = this.groupComponentsByLocation();
        locationGroups.forEach(group => {
            if (group.components.length > 2) {
                clusters.push({
                    name: `${group.path} Module`,
                    components: group.components.map(c => c.name),
                    description: `Components in ${group.path}`,
                    type: 'feature',
                    cohesion: this.calculateLocationCohesion(group.components)
                });
            }
        });

        // Cluster by dependency relationships
        const dependencyClusters = this.identifyDependencyClusters();
        clusters.push(...dependencyClusters);

        return this.deduplicateClusters(clusters);
    }

    /**
     * Detect common component patterns
     */
    private detectComponentPatterns(): ComponentPattern[] {
        const patterns: ComponentPattern[] = [];

        // Provider Pattern
        const providerPattern = this.detectProviderPattern();
        if (providerPattern) patterns.push(providerPattern);

        // HOC Pattern
        const hocPattern = this.detectHOCPattern();
        if (hocPattern) patterns.push(hocPattern);

        // Compound Component Pattern
        const compoundPattern = this.detectCompoundComponentPattern();
        if (compoundPattern) patterns.push(compoundPattern);

        // Container/Presenter Pattern
        const containerPattern = this.detectContainerPresenterPattern();
        if (containerPattern) patterns.push(containerPattern);

        // Custom Hook Pattern
        const hookPattern = this.detectCustomHookPattern();
        if (hookPattern) patterns.push(hookPattern);

        return patterns;
    }

    /**
     * Generate recommendations based on analysis
     */
    private generateRelationshipRecommendations(
        relationships: ComponentRelationship[],
        dependencyGraph: DependencyNode[],
        clusters: ComponentCluster[]
    ): RelationshipRecommendation[] {
        const recommendations: RelationshipRecommendation[] = [];

        // High coupling recommendations
        const highCouplingPairs = relationships.filter(r => r.strength > 7);
        if (highCouplingPairs.length > 0) {
            recommendations.push({
                type: 'decouple',
                priority: 'high',
                components: highCouplingPairs.map(r => `${r.source}-${r.target}`),
                message: 'High coupling detected between components',
                action: 'Consider extracting shared logic or using composition'
            });
        }

        // Cyclic dependency recommendations
        const cyclicComponents = dependencyGraph.filter(n => n.cyclicDependencies.length > 0);
        if (cyclicComponents.length > 0) {
            recommendations.push({
                type: 'refactor',
                priority: 'high',
                components: cyclicComponents.map(c => c.componentName),
                message: 'Cyclic dependencies detected',
                action: 'Refactor to remove circular imports'
            });
        }

        // Large cluster recommendations
        const largeClusters = clusters.filter(c => c.components.length > 10);
        if (largeClusters.length > 0) {
            largeClusters.forEach(cluster => {
                recommendations.push({
                    type: 'extract',
                    priority: 'medium',
                    components: cluster.components,
                    message: `Large cluster detected: ${cluster.name}`,
                    action: 'Consider breaking into smaller, focused modules'
                });
            });
        }

        return recommendations;
    }

    /**
     * Calculate relationship metrics
     */
    private calculateRelationshipMetrics(
        relationships: ComponentRelationship[],
        dependencyGraph: DependencyNode[]
    ): RelationshipAnalysis['metrics'] {
        const totalStrength = relationships.reduce((sum, r) => sum + r.strength, 0);
        const averageCoupling = relationships.length > 0 ? totalStrength / relationships.length : 0;

        const cyclicDependenciesCount = dependencyGraph.reduce(
            (count, node) => count + node.cyclicDependencies.length, 0
        );

        const orphanedComponents = dependencyGraph
            .filter(node => node.dependencies.length === 0 && node.dependents.length === 0)
            .length;

        const componentUsage = new Map<string, number>();
        dependencyGraph.forEach(node => {
            componentUsage.set(node.componentName, node.dependents.length);
        });

        const sortedByUsage = Array.from(componentUsage.entries())
            .sort((a, b) => b[1] - a[1]);

        const mostUsedComponents = sortedByUsage
            .slice(0, 5)
            .map(([name]) => name);

        const leastUsedComponents = sortedByUsage
            .slice(-5)
            .map(([name]) => name);

        return {
            averageCoupling,
            cyclicDependenciesCount,
            orphanedComponents,
            mostUsedComponents,
            leastUsedComponents
        };
    }

    // Helper methods (implementation details)
    
    private findComponentByImport(importPath: string): ComponentInfo | null {
        // Logic to find component by import path
        return this.components.find(c => 
            importPath.includes(c.name.toLowerCase()) ||
            c.filePath.includes(importPath)
        ) || null;
    }

    private findComponentByName(name: string): ComponentInfo | null {
        return this.components.find(c => c.name === name) || null;
    }

    private getComponentContent(filePath: string): string | null {
        // In a real implementation, this would read the file content
        // For now, return null as we don't have direct file access in this context
        return null;
    }

    private countComponentUsage(content: string, componentName: string): number {
        const regex = new RegExp(`<${componentName}\\s*[^>]*>|${componentName}\\(`, 'g');
        const matches = content.match(regex);
        return matches ? matches.length : 0;
    }

    private isComponentRendered(content: string, componentName: string): boolean {
        return content.includes(`<${componentName}`) || content.includes(`{${componentName}`);
    }

    private isComponentWrapped(content: string, componentName: string): boolean {
        return content.includes(`<${componentName}`) && content.includes(`{children}`);
    }

    private isComponentExtended(content: string, componentName: string): boolean {
        return content.includes(`extends ${componentName}`) || content.includes(`...${componentName}`);
    }

    private isUtilityUsed(content: string, utilityName: string): boolean {
        return content.includes(`${utilityName}(`) && !content.includes(`<${utilityName}`);
    }

    private deduplicateRelationships(relationships: ComponentRelationship[]): ComponentRelationship[] {
        const seen = new Set<string>();
        return relationships.filter(rel => {
            const key = `${rel.source}-${rel.target}-${rel.type}`;
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    }

    private groupComponentsByType(): Record<string, ComponentInfo[]> {
        return this.components.reduce((groups, component) => {
            const type = component.componentType;
            if (!groups[type]) groups[type] = [];
            groups[type].push(component);
            return groups;
        }, {} as Record<string, ComponentInfo[]>);
    }

    private groupComponentsByLocation(): Array<{path: string, components: ComponentInfo[]}> {
        const groups = new Map<string, ComponentInfo[]>();
        
        this.components.forEach(component => {
            const dir = component.filePath.split('/').slice(0, -1).join('/');
            if (!groups.has(dir)) groups.set(dir, []);
            groups.get(dir)!.push(component);
        });

        return Array.from(groups.entries()).map(([path, components]) => ({
            path,
            components
        }));
    }

    private calculateClusterCohesion(components: ComponentInfo[]): number {
        // Simple cohesion calculation based on shared dependencies
        const allDeps = components.flatMap(c => c.dependencies);
        const uniqueDeps = new Set(allDeps);
        return allDeps.length > 0 ? uniqueDeps.size / allDeps.length : 0;
    }

    private calculateLocationCohesion(components: ComponentInfo[]): number {
        // Calculate cohesion based on file proximity and shared patterns
        return Math.random() * 0.3 + 0.7; // Placeholder implementation
    }

    private identifyDependencyClusters(): ComponentCluster[] {
        // Identify clusters based on dependency relationships
        return []; // Placeholder implementation
    }

    private deduplicateClusters(clusters: ComponentCluster[]): ComponentCluster[] {
        const seen = new Set<string>();
        return clusters.filter(cluster => {
            const key = cluster.components.sort().join('-');
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    }

    private mapComponentTypeToClusterType(type: ComponentType): ComponentCluster['type'] {
        switch (type) {
            case ComponentType.UI_LIBRARY: return 'ui-library';
            case ComponentType.PAGE: return 'pages';
            case ComponentType.UTILITY:
            case ComponentType.HOOK: return 'utilities';
            default: return 'feature';
        }
    }

    private calculateNodeDepths(nodes: DependencyNode[]): void {
        // Calculate depth in dependency tree
        nodes.forEach(node => {
            node.depth = this.calculateDepth(node, nodes, new Set());
        });
    }

    private calculateDepth(node: DependencyNode, allNodes: DependencyNode[], visited: Set<string>): number {
        if (visited.has(node.componentName)) return 0; // Avoid infinite recursion
        visited.add(node.componentName);

        if (node.dependencies.length === 0) return 0;

        const depthsOfDependencies = node.dependencies.map(depName => {
            const depNode = allNodes.find(n => n.componentName === depName);
            return depNode ? this.calculateDepth(depNode, allNodes, visited) + 1 : 0;
        });

        return Math.max(...depthsOfDependencies);
    }

    private identifyRootsAndLeaves(nodes: DependencyNode[]): void {
        nodes.forEach(node => {
            node.isRoot = node.dependents.length === 0;
            node.isLeaf = node.dependencies.length === 0;
        });
    }

    private detectCyclicDependencies(nodes: DependencyNode[]): void {
        nodes.forEach(node => {
            node.cyclicDependencies = this.findCyclicDeps(node, nodes, []);
        });
    }

    private findCyclicDeps(node: DependencyNode, allNodes: DependencyNode[], path: string[]): string[] {
        if (path.includes(node.componentName)) {
            return [node.componentName];
        }

        const newPath = [...path, node.componentName];
        const cyclicDeps: string[] = [];

        node.dependencies.forEach(depName => {
            const depNode = allNodes.find(n => n.componentName === depName);
            if (depNode) {
                const result = this.findCyclicDeps(depNode, allNodes, newPath);
                cyclicDeps.push(...result);
            }
        });

        return cyclicDeps;
    }

    // Pattern detection methods
    private detectProviderPattern(): ComponentPattern | null {
        const providers = this.components.filter(c => 
            c.name.includes('Provider') || c.name.includes('Context')
        );
        
        if (providers.length > 0) {
            return {
                name: 'Provider Pattern',
                description: 'Components using React Context Provider pattern',
                components: providers.map(c => c.name),
                confidence: 0.8,
                examples: [`${providers[0]?.name}Provider`]
            };
        }
        return null;
    }

    private detectHOCPattern(): ComponentPattern | null {
        const hocs = this.components.filter(c => 
            c.name.startsWith('with') || c.name.includes('HOC')
        );
        
        if (hocs.length > 0) {
            return {
                name: 'Higher-Order Component Pattern',
                description: 'Components using HOC pattern for code reuse',
                components: hocs.map(c => c.name),
                confidence: 0.7,
                examples: [`with${hocs[0]?.name}`]
            };
        }
        return null;
    }

    private detectCompoundComponentPattern(): ComponentPattern | null {
        // Look for components that have multiple exports (compound components)
        const compoundComponents = this.components.filter(c => c.exports.length > 2);
        
        if (compoundComponents.length > 0) {
            return {
                name: 'Compound Component Pattern',
                description: 'Components using compound component pattern',
                components: compoundComponents.map(c => c.name),
                confidence: 0.6,
                examples: [`${compoundComponents[0]?.name}.Item`]
            };
        }
        return null;
    }

    private detectContainerPresenterPattern(): ComponentPattern | null {
        const containers = this.components.filter(c => c.name.includes('Container'));
        const presenters = this.components.filter(c => c.name.includes('Presenter') || c.name.includes('View'));
        
        if (containers.length > 0 && presenters.length > 0) {
            return {
                name: 'Container/Presenter Pattern',
                description: 'Separation of logic and presentation components',
                components: [...containers.map(c => c.name), ...presenters.map(c => c.name)],
                confidence: 0.8,
                examples: [`${containers[0]?.name} + ${presenters[0]?.name}`]
            };
        }
        return null;
    }

    private detectCustomHookPattern(): ComponentPattern | null {
        const hooks = this.components.filter(c => 
            c.componentType === ComponentType.HOOK && c.name.startsWith('use')
        );
        
        if (hooks.length > 1) {
            return {
                name: 'Custom Hook Pattern',
                description: 'Reusable custom React hooks for shared logic',
                components: hooks.map(c => c.name),
                confidence: 0.9,
                examples: hooks.slice(0, 2).map(c => c.name)
            };
        }
        return null;
    }
}

// Factory function
export function createComponentRelationshipAnalyzer(): ComponentRelationshipAnalyzer {
    return new ComponentRelationshipAnalyzer();
}