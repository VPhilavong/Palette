export interface WorkspaceInfo {
    hasTypeScript: boolean;
    styling: StylingInfo;
    existingComponents: ComponentInfo[];
    projectStructure: string[];
}

export interface StylingInfo {
    hasTailwind: boolean;
    hasStyledComponents: boolean;
    hasCSSModules: boolean;
    hasEmotion: boolean;
}

export interface ComponentInfo {
    name: string;
    path: string;
    description: string;
    props?: string;
}

export interface GenerationContext {
    prompt: string;
    workspaceInfo: WorkspaceInfo;
    selectedCode?: string;
}