export interface FileMetadata {
    path: string;
    name: string;
    extension: string;
    size: number;
    lastModified: Date;
    isComponent?: boolean;
}

export interface Framework {
    name: string;
    version?: string;
    detected: boolean;
    confidence: number;
}

export interface ProjectMetadata {
    frameworks: Framework[];
    dependencies: Record<string, string>;
    devDependencies: Record<string, string>;
    hasTypeScript: boolean;
    uiLibraries: string[];
    stateManagement: string[];
}

export interface ComponentInfo {
    name: string;
    path: string;
    exports: string[];
    imports: ImportInfo[];
    props?: string[];
    hooks?: string[];
}

export interface ImportInfo {
    module: string;
    imports: string[];
    isDefault: boolean;
}

export interface WorkspaceIndex {
    files: FileMetadata[];
    components: ComponentInfo[];
    project: ProjectMetadata;
    lastUpdated: Date;
}