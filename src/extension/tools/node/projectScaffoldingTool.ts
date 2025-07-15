/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import * as path from 'path';
import { ILogService } from '../../../platform/log/common/logService';
import { FileOperationsTool, FileModification } from './fileOperationsTool';
import { TerminalOperationsTool } from './terminalOperationsTool';

export interface ProjectTemplate {
    name: string;
    description: string;
    files: { [path: string]: string };
    directories: string[];
    dependencies?: string[];
    devDependencies?: string[];
    scripts?: { [name: string]: string };
    postInstallCommands?: string[];
}

export interface ComponentScaffoldOptions {
    componentName: string;
    componentType: 'functional' | 'class';
    includeTypes: boolean;
    includeTests: boolean;
    includeStorybook: boolean;
    includeStyles: boolean;
    styleType: 'css' | 'scss' | 'module.css' | 'styled-components' | 'tailwind';
    directory?: string;
}

export interface FeatureScaffoldOptions {
    featureName: string;
    includeApi: boolean;
    includeComponents: boolean;
    includeHooks: boolean;
    includeTypes: boolean;
    includeTests: boolean;
    apiType?: 'rest' | 'graphql';
}

export class ProjectScaffoldingTool {
    private fileOps: FileOperationsTool;
    private terminalOps: TerminalOperationsTool;

    constructor(private readonly logService: ILogService) {
        this.fileOps = new FileOperationsTool(logService);
        this.terminalOps = new TerminalOperationsTool(logService);
    }

    async scaffoldComponent(options: ComponentScaffoldOptions): Promise<{ success: boolean; files: string[]; error?: string }> {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                throw new Error('No workspace found');
            }

            const { componentName, directory = 'src/components' } = options;
            const componentDir = path.join(workspaceRoot, directory, componentName);
            const files: string[] = [];

            // Create component structure
            const componentFiles = this.generateComponentFiles(options);
            const modifications: FileModification[] = [];

            // Create all files
            for (const [fileName, content] of Object.entries(componentFiles)) {
                const filePath = path.join(componentDir, fileName);
                modifications.push({
                    type: 'create',
                    filePath,
                    content
                });
                files.push(filePath);
            }

            // Execute file operations
            const results = await this.fileOps.modifyFiles(modifications);
            const failedOps = results.filter(r => !r.success);

            if (failedOps.length > 0) {
                throw new Error(`Failed to create files: ${failedOps.map(r => r.error).join(', ')}`);
            }

            // Install dependencies if needed
            if (options.styleType === 'styled-components') {
                await this.terminalOps.installPackages(['styled-components', '@types/styled-components'], false);
            }

            this.logService.info(`ProjectScaffoldingTool: Component ${componentName} scaffolded successfully`);

            return { success: true, files };
        } catch (error) {
            this.logService.error('ProjectScaffoldingTool: Error scaffolding component', error);
            return {
                success: false,
                files: [],
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    async scaffoldFeature(options: FeatureScaffoldOptions): Promise<{ success: boolean; files: string[]; error?: string }> {
        try {
            const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspaceRoot) {
                throw new Error('No workspace found');
            }

            const { featureName } = options;
            const featureDir = path.join(workspaceRoot, 'src/features', featureName);
            const files: string[] = [];

            // Create feature structure
            const featureFiles = this.generateFeatureFiles(options);
            const modifications: FileModification[] = [];

            // Create all files
            for (const [fileName, content] of Object.entries(featureFiles)) {
                const filePath = path.join(featureDir, fileName);
                modifications.push({
                    type: 'create',
                    filePath,
                    content
                });
                files.push(filePath);
            }

            // Execute file operations
            const results = await this.fileOps.modifyFiles(modifications);
            const failedOps = results.filter(r => !r.success);

            if (failedOps.length > 0) {
                throw new Error(`Failed to create files: ${failedOps.map(r => r.error).join(', ')}`);
            }

            // Install dependencies if needed
            const dependencies: string[] = [];
            if (options.includeApi && options.apiType === 'graphql') {
                dependencies.push('@apollo/client', 'graphql');
            }

            if (dependencies.length > 0) {
                await this.terminalOps.installPackages(dependencies, false);
            }

            this.logService.info(`ProjectScaffoldingTool: Feature ${featureName} scaffolded successfully`);

            return { success: true, files };
        } catch (error) {
            this.logService.error('ProjectScaffoldingTool: Error scaffolding feature', error);
            return {
                success: false,
                files: [],
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    async scaffoldProject(template: ProjectTemplate, projectPath: string): Promise<{ success: boolean; error?: string }> {
        try {
            // Create directory structure
            const directoryResults = await this.fileOps.createDirectoryStructure(projectPath, template.files);
            const failedOps = directoryResults.filter(r => !r.success);

            if (failedOps.length > 0) {
                throw new Error(`Failed to create project structure: ${failedOps.map(r => r.error).join(', ')}`);
            }

            // Update package.json if it exists
            const packageJsonPath = path.join(projectPath, 'package.json');
            if (template.dependencies || template.devDependencies || template.scripts) {
                await this.terminalOps.updatePackageJson({
                    dependencies: template.dependencies?.reduce((acc, dep) => ({ ...acc, [dep]: 'latest' }), {}),
                    devDependencies: template.devDependencies?.reduce((acc, dep) => ({ ...acc, [dep]: 'latest' }), {}),
                    scripts: template.scripts
                });
            }

            // Install dependencies
            if (template.dependencies && template.dependencies.length > 0) {
                await this.terminalOps.installPackages(template.dependencies, false);
            }

            if (template.devDependencies && template.devDependencies.length > 0) {
                await this.terminalOps.installPackages(template.devDependencies, true);
            }

            // Run post-install commands
            if (template.postInstallCommands) {
                for (const command of template.postInstallCommands) {
                    await this.terminalOps.executeCommand(command);
                }
            }

            this.logService.info(`ProjectScaffoldingTool: Project ${template.name} scaffolded successfully`);

            return { success: true };
        } catch (error) {
            this.logService.error('ProjectScaffoldingTool: Error scaffolding project', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    private generateComponentFiles(options: ComponentScaffoldOptions): { [fileName: string]: string } {
        const { componentName, componentType, includeTypes, includeTests, includeStorybook, includeStyles, styleType } = options;
        const files: { [fileName: string]: string } = {};

        // Main component file
        const componentExt = includeTypes ? 'tsx' : 'jsx';
        files[`${componentName}.${componentExt}`] = this.generateComponentCode(options);

        // Types file
        if (includeTypes) {
            files[`${componentName}.types.ts`] = this.generateComponentTypes(componentName);
        }

        // Styles file
        if (includeStyles && styleType !== 'tailwind' && styleType !== 'styled-components') {
            const styleExt = styleType === 'scss' ? 'scss' : styleType === 'module.css' ? 'module.css' : 'css';
            files[`${componentName}.${styleExt}`] = this.generateComponentStyles(componentName, styleType);
        }

        // Test file
        if (includeTests) {
            files[`${componentName}.test.${componentExt}`] = this.generateComponentTest(componentName, includeTypes);
        }

        // Storybook file
        if (includeStorybook) {
            files[`${componentName}.stories.${componentExt}`] = this.generateComponentStory(componentName, includeTypes);
        }

        // Index file
        files['index.ts'] = `export { default as ${componentName} } from './${componentName}';\n${includeTypes ? `export type * from './${componentName}.types';\n` : ''}`;

        return files;
    }

    private generateFeatureFiles(options: FeatureScaffoldOptions): { [fileName: string]: string } {
        const { featureName, includeApi, includeComponents, includeHooks, includeTypes, includeTests, apiType } = options;
        const files: { [fileName: string]: string } = {};

        // Types
        if (includeTypes) {
            files['types/index.ts'] = this.generateFeatureTypes(featureName);
        }

        // API
        if (includeApi) {
            if (apiType === 'graphql') {
                files['api/queries.ts'] = this.generateGraphQLQueries(featureName);
                files['api/mutations.ts'] = this.generateGraphQLMutations(featureName);
            } else {
                files['api/index.ts'] = this.generateRestAPI(featureName);
            }
        }

        // Components
        if (includeComponents) {
            files[`components/${featureName}List.tsx`] = this.generateFeatureListComponent(featureName);
            files[`components/${featureName}Item.tsx`] = this.generateFeatureItemComponent(featureName);
            files['components/index.ts'] = `export { default as ${featureName}List } from './${featureName}List';\nexport { default as ${featureName}Item } from './${featureName}Item';`;
        }

        // Hooks
        if (includeHooks) {
            files[`hooks/use${featureName}.ts`] = this.generateFeatureHook(featureName, includeApi, apiType);
            files['hooks/index.ts'] = `export { default as use${featureName} } from './use${featureName}';`;
        }

        // Tests
        if (includeTests && includeHooks) {
            files[`hooks/use${featureName}.test.ts`] = this.generateFeatureHookTest(featureName);
        }

        // Main index
        const exports = [];
        if (includeComponents) exports.push(`export * from './components';`);
        if (includeHooks) exports.push(`export * from './hooks';`);
        if (includeApi) exports.push(`export * from './api';`);
        if (includeTypes) exports.push(`export * from './types';`);

        files['index.ts'] = exports.join('\n');

        return files;
    }

    private generateComponentCode(options: ComponentScaffoldOptions): string {
        const { componentName, componentType, includeTypes, styleType } = options;
        const hasTypes = includeTypes;
        const hasStyles = styleType !== 'tailwind';

        let imports = `import React${componentType === 'class' ? ', { Component }' : ''} from 'react';\n`;
        
        if (hasTypes) {
            imports += `import { ${componentName}Props } from './${componentName}.types';\n`;
        }
        
        if (hasStyles && styleType !== 'styled-components') {
            imports += `import './${componentName}.${styleType === 'scss' ? 'scss' : styleType === 'module.css' ? 'module.css' : 'css'}';\n`;
        }

        if (styleType === 'styled-components') {
            imports += `import styled from 'styled-components';\n`;
        }

        let componentCode = '';
        
        if (componentType === 'functional') {
            componentCode = `
interface ${componentName}Props {
  ${hasTypes ? '// Props defined in types file' : 'className?: string;'}
}

const ${componentName}: React.FC<${componentName}Props> = ({ ${hasTypes ? '...props' : 'className'} }) => {
  return (
    <div${styleType === 'tailwind' ? ' className="p-4"' : styleType === 'styled-components' ? '' : ' className="' + componentName.toLowerCase() + '"'}>
      <h1>Welcome to ${componentName}</h1>
      <p>This component was generated by Palette UI Agent.</p>
    </div>
  );
};

export default ${componentName};`;
        } else {
            componentCode = `
interface ${componentName}Props {
  ${hasTypes ? '// Props defined in types file' : 'className?: string;'}
}

interface ${componentName}State {
  // Add state properties here
}

class ${componentName} extends Component<${componentName}Props, ${componentName}State> {
  constructor(props: ${componentName}Props) {
    super(props);
    this.state = {
      // Initialize state here
    };
  }

  render() {
    return (
      <div${styleType === 'tailwind' ? ' className="p-4"' : styleType === 'styled-components' ? '' : ' className="' + componentName.toLowerCase() + '"'}>
        <h1>Welcome to ${componentName}</h1>
        <p>This component was generated by Palette UI Agent.</p>
      </div>
    );
  }
}

export default ${componentName};`;
        }

        if (styleType === 'styled-components') {
            componentCode = `
const StyledContainer = styled.div\`
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 8px;
\`;

interface ${componentName}Props {
  ${hasTypes ? '// Props defined in types file' : 'className?: string;'}
}

const ${componentName}: React.FC<${componentName}Props> = ({ ${hasTypes ? '...props' : 'className'} }) => {
  return (
    <StyledContainer>
      <h1>Welcome to ${componentName}</h1>
      <p>This component was generated by Palette UI Agent.</p>
    </StyledContainer>
  );
};

export default ${componentName};`;
        }

        return imports + componentCode;
    }

    private generateComponentTypes(componentName: string): string {
        return `export interface ${componentName}Props {
  /** Custom CSS class name */
  className?: string;
  /** Custom styles */
  style?: React.CSSProperties;
  /** Component children */
  children?: React.ReactNode;
  /** Disabled state */
  disabled?: boolean;
  /** Click handler */
  onClick?: () => void;
}

export interface ${componentName}State {
  // Add state interface properties here
}`;
    }

    private generateComponentStyles(componentName: string, styleType: string): string {
        const className = componentName.toLowerCase();
        
        if (styleType === 'scss') {
            return `.${className} {
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 8px;
  
  h1 {
    margin: 0 0 0.5rem 0;
    color: #333;
  }
  
  p {
    margin: 0;
    color: #666;
  }
}`;
        } else if (styleType === 'module.css') {
            return `.container {
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.title {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.description {
  margin: 0;
  color: #666;
}`;
        } else {
            return `.${className} {
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.${className} h1 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.${className} p {
  margin: 0;
  color: #666;
}`;
        }
    }

    private generateComponentTest(componentName: string, includeTypes: boolean): string {
        return `import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import ${componentName} from './${componentName}';
${includeTypes ? `import { ${componentName}Props } from './${componentName}.types';` : ''}

describe('${componentName}', () => {
  it('renders without crashing', () => {
    render(<${componentName} />);
    expect(screen.getByText('Welcome to ${componentName}')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const customClass = 'custom-class';
    render(<${componentName} className={customClass} />);
    const component = screen.getByText('Welcome to ${componentName}').closest('div');
    expect(component).toHaveClass(customClass);
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<${componentName} onClick={handleClick} />);
    
    const component = screen.getByText('Welcome to ${componentName}').closest('div');
    component?.click();
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});`;
    }

    private generateComponentStory(componentName: string, includeTypes: boolean): string {
        return `import type { Meta, StoryObj } from '@storybook/react';
import ${componentName} from './${componentName}';
${includeTypes ? `import { ${componentName}Props } from './${componentName}.types';` : ''}

const meta: Meta<typeof ${componentName}> = {
  title: 'Components/${componentName}',
  component: ${componentName},
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    className: {
      control: 'text',
      description: 'Custom CSS class name',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const CustomClassName: Story = {
  args: {
    className: 'custom-styling',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
  },
};`;
    }

    private generateFeatureTypes(featureName: string): string {
        const entityName = featureName.charAt(0).toUpperCase() + featureName.slice(1);
        
        return `export interface ${entityName} {
  id: string;
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ${entityName}CreateInput {
  name: string;
  description?: string;
}

export interface ${entityName}UpdateInput {
  name?: string;
  description?: string;
}

export interface ${entityName}ListResponse {
  data: ${entityName}[];
  total: number;
  page: number;
  limit: number;
}

export interface ${entityName}ApiState {
  loading: boolean;
  error: string | null;
  data: ${entityName}[];
}`;
    }

    private generateRestAPI(featureName: string): string {
        const entityName = featureName.charAt(0).toUpperCase() + featureName.slice(1);
        
        return `import { ${entityName}, ${entityName}CreateInput, ${entityName}UpdateInput, ${entityName}ListResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

export const ${featureName}Api = {
  // Get all items
  getAll: async (): Promise<${entityName}ListResponse> => {
    const response = await fetch(\`\${API_BASE_URL}/${featureName}s\`);
    if (!response.ok) {
      throw new Error('Failed to fetch ${featureName}s');
    }
    return response.json();
  },

  // Get single item
  getById: async (id: string): Promise<${entityName}> => {
    const response = await fetch(\`\${API_BASE_URL}/${featureName}s/\${id}\`);
    if (!response.ok) {
      throw new Error('Failed to fetch ${featureName}');
    }
    return response.json();
  },

  // Create new item
  create: async (data: ${entityName}CreateInput): Promise<${entityName}> => {
    const response = await fetch(\`\${API_BASE_URL}/${featureName}s\`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to create ${featureName}');
    }
    return response.json();
  },

  // Update item
  update: async (id: string, data: ${entityName}UpdateInput): Promise<${entityName}> => {
    const response = await fetch(\`\${API_BASE_URL}/${featureName}s/\${id}\`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to update ${featureName}');
    }
    return response.json();
  },

  // Delete item
  delete: async (id: string): Promise<void> => {
    const response = await fetch(\`\${API_BASE_URL}/${featureName}s/\${id}\`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete ${featureName}');
    }
  },
};`;
    }

    private generateGraphQLQueries(featureName: string): string {
        const entityName = featureName.charAt(0).toUpperCase() + featureName.slice(1);
        
        return `import { gql } from '@apollo/client';

export const GET_${featureName.toUpperCase()}S = gql\`
  query Get${entityName}s($limit: Int, $offset: Int) {
    ${featureName}s(limit: $limit, offset: $offset) {
      id
      name
      description
      createdAt
      updatedAt
    }
  }
\`;

export const GET_${featureName.toUpperCase()} = gql\`
  query Get${entityName}($id: ID!) {
    ${featureName}(id: $id) {
      id
      name
      description
      createdAt
      updatedAt
    }
  }
\`;`;
    }

    private generateGraphQLMutations(featureName: string): string {
        const entityName = featureName.charAt(0).toUpperCase() + featureName.slice(1);
        
        return `import { gql } from '@apollo/client';

export const CREATE_${featureName.toUpperCase()} = gql\`
  mutation Create${entityName}($input: ${entityName}CreateInput!) {
    create${entityName}(input: $input) {
      id
      name
      description
      createdAt
      updatedAt
    }
  }
\`;

export const UPDATE_${featureName.toUpperCase()} = gql\`
  mutation Update${entityName}($id: ID!, $input: ${entityName}UpdateInput!) {
    update${entityName}(id: $id, input: $input) {
      id
      name
      description
      createdAt
      updatedAt
    }
  }
\`;

export const DELETE_${featureName.toUpperCase()} = gql\`
  mutation Delete${entityName}($id: ID!) {
    delete${entityName}(id: $id)
  }
\`;`;
    }

    private generateFeatureListComponent(featureName: string): string {
        const entityName = featureName.charAt(0).toUpperCase() + featureName.slice(1);
        
        return `import React from 'react';
import { ${entityName} } from '../types';
import ${entityName}Item from './${entityName}Item';

interface ${entityName}ListProps {
  items: ${entityName}[];
  loading?: boolean;
  onItemClick?: (item: ${entityName}) => void;
  onItemDelete?: (id: string) => void;
}

const ${entityName}List: React.FC<${entityName}ListProps> = ({
  items,
  loading = false,
  onItemClick,
  onItemDelete,
}) => {
  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="text-center p-8 text-gray-500">
        <p>No ${featureName}s found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item) => (
        <${entityName}Item
          key={item.id}
          item={item}
          onClick={() => onItemClick?.(item)}
          onDelete={() => onItemDelete?.(item.id)}
        />
      ))}
    </div>
  );
};

export default ${entityName}List;`;
    }

    private generateFeatureItemComponent(featureName: string): string {
        const entityName = featureName.charAt(0).toUpperCase() + featureName.slice(1);
        
        return `import React from 'react';
import { ${entityName} } from '../types';

interface ${entityName}ItemProps {
  item: ${entityName};
  onClick?: () => void;
  onDelete?: () => void;
}

const ${entityName}Item: React.FC<${entityName}ItemProps> = ({
  item,
  onClick,
  onDelete,
}) => {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start">
        <div className="flex-1 cursor-pointer" onClick={onClick}>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {item.name}
          </h3>
          {item.description && (
            <p className="text-gray-600 mb-3">{item.description}</p>
          )}
          <div className="text-sm text-gray-500">
            Created: {new Date(item.createdAt).toLocaleDateString()}
          </div>
        </div>
        <div className="flex gap-2 ml-4">
          <button
            onClick={onClick}
            className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default ${entityName}Item;`;
    }

    private generateFeatureHook(featureName: string, includeApi: boolean, apiType?: string): string {
        const entityName = featureName.charAt(0).toUpperCase() + featureName.slice(1);
        
        if (includeApi && apiType === 'graphql') {
            return `import { useState } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { GET_${featureName.toUpperCase()}S, GET_${featureName.toUpperCase()} } from '../api/queries';
import { CREATE_${featureName.toUpperCase()}, UPDATE_${featureName.toUpperCase()}, DELETE_${featureName.toUpperCase()} } from '../api/mutations';
import { ${entityName}, ${entityName}CreateInput, ${entityName}UpdateInput } from '../types';

export const use${entityName} = () => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Queries
  const { data: items, loading: loadingList, refetch: refetchList } = useQuery(GET_${featureName.toUpperCase()}S);
  const { data: selectedItem, loading: loadingItem } = useQuery(GET_${featureName.toUpperCase()}, {
    variables: { id: selectedId },
    skip: !selectedId,
  });

  // Mutations
  const [create${entityName}] = useMutation(CREATE_${featureName.toUpperCase()});
  const [update${entityName}] = useMutation(UPDATE_${featureName.toUpperCase()});
  const [delete${entityName}] = useMutation(DELETE_${featureName.toUpperCase()});

  const create = async (input: ${entityName}CreateInput) => {
    await create${entityName}({
      variables: { input },
      refetchQueries: [GET_${featureName.toUpperCase()}S],
    });
  };

  const update = async (id: string, input: ${entityName}UpdateInput) => {
    await update${entityName}({
      variables: { id, input },
      refetchQueries: [GET_${featureName.toUpperCase()}S, GET_${featureName.toUpperCase()}],
    });
  };

  const remove = async (id: string) => {
    await delete${entityName}({
      variables: { id },
      refetchQueries: [GET_${featureName.toUpperCase()}S],
    });
  };

  return {
    // Data
    items: items?.${featureName}s || [],
    selectedItem: selectedItem?.${featureName},
    
    // Loading states
    loadingList,
    loadingItem,
    
    // Actions
    setSelectedId,
    create,
    update,
    remove,
    refetchList,
  };
};

export default use${entityName};`;
        } else {
            return `import { useState, useEffect } from 'react';
import { ${entityName}, ${entityName}CreateInput, ${entityName}UpdateInput, ${entityName}ApiState } from '../types';
${includeApi ? `import { ${featureName}Api } from '../api';` : ''}

export const use${entityName} = () => {
  const [state, setState] = useState<${entityName}ApiState>({
    loading: false,
    error: null,
    data: [],
  });
  const [selectedItem, setSelectedItem] = useState<${entityName} | null>(null);

  const setLoading = (loading: boolean) => {
    setState(prev => ({ ...prev, loading }));
  };

  const setError = (error: string | null) => {
    setState(prev => ({ ...prev, error }));
  };

  const setData = (data: ${entityName}[]) => {
    setState(prev => ({ ...prev, data }));
  };

  const fetchAll = async () => {
    try {
      setLoading(true);
      setError(null);
      ${includeApi ? `
      const response = await ${featureName}Api.getAll();
      setData(response.data);` : `
      // TODO: Implement API call
      setData([]);`}
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const fetchById = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      ${includeApi ? `
      const item = await ${featureName}Api.getById(id);
      setSelectedItem(item);` : `
      // TODO: Implement API call
      setSelectedItem(null);`}
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const create = async (input: ${entityName}CreateInput) => {
    try {
      setLoading(true);
      setError(null);
      ${includeApi ? `
      const newItem = await ${featureName}Api.create(input);
      setData(prev => [...prev, newItem]);
      return newItem;` : `
      // TODO: Implement API call
      return null;`}
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const update = async (id: string, input: ${entityName}UpdateInput) => {
    try {
      setLoading(true);
      setError(null);
      ${includeApi ? `
      const updatedItem = await ${featureName}Api.update(id, input);
      setData(prev => prev.map(item => item.id === id ? updatedItem : item));
      if (selectedItem?.id === id) {
        setSelectedItem(updatedItem);
      }
      return updatedItem;` : `
      // TODO: Implement API call
      return null;`}
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      ${includeApi ? `
      await ${featureName}Api.delete(id);
      setData(prev => prev.filter(item => item.id !== id));
      if (selectedItem?.id === id) {
        setSelectedItem(null);
      }` : `
      // TODO: Implement API call`}
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, []);

  return {
    // State
    ...state,
    selectedItem,
    
    // Actions
    fetchAll,
    fetchById,
    create,
    update,
    remove,
    setSelectedItem,
  };
};

export default use${entityName};`;
        }
    }

    private generateFeatureHookTest(featureName: string): string {
        const entityName = featureName.charAt(0).toUpperCase() + featureName.slice(1);
        
        return `import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import use${entityName} from './use${entityName}';

// Mock the API
vi.mock('../api', () => ({
  ${featureName}Api: {
    getAll: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('use${entityName}', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => use${entityName}());
    
    expect(result.current.data).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.selectedItem).toBe(null);
  });

  it('should fetch all items on mount', async () => {
    const mockData = [
      { id: '1', name: 'Test ${entityName}', createdAt: new Date(), updatedAt: new Date() },
    ];
    
    const { ${featureName}Api } = await import('../api');
    (${featureName}Api.getAll as any).mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => use${entityName}());
    
    // Wait for the effect to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.data).toEqual(mockData);
    expect(${featureName}Api.getAll).toHaveBeenCalledTimes(1);
  });

  it('should handle create operation', async () => {
    const newItem = { id: '2', name: 'New ${entityName}', createdAt: new Date(), updatedAt: new Date() };
    const input = { name: 'New ${entityName}' };
    
    const { ${featureName}Api } = await import('../api');
    (${featureName}Api.create as any).mockResolvedValue(newItem);

    const { result } = renderHook(() => use${entityName}());
    
    await act(async () => {
      await result.current.create(input);
    });

    expect(${featureName}Api.create).toHaveBeenCalledWith(input);
    expect(result.current.data).toContain(newItem);
  });
});`;
    }
}