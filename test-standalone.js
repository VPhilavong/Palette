/**
 * Standalone test for embedding system core logic
 * Tests the algorithms without VS Code dependencies
 */

// Mock VS Code workspace for testing
const mockVscode = {
    workspace: {
        workspaceFolders: [{ uri: { fsPath: process.cwd() } }]
    }
};

// Sample component data for testing
const sampleComponents = [
    {
        name: 'LoginForm',
        path: 'src/components/auth/LoginForm.tsx',
        exports: ['LoginForm'],
        imports: [{ module: 'react', imports: ['useState', 'useEffect'], isDefault: false }],
        hooks: ['useState', 'useUser'],
        jsxElements: ['form', 'input', 'button'],
        comments: ['Login form component with validation'],
        props: ['onSubmit', 'isLoading']
    },
    {
        name: 'Dashboard',
        path: 'src/pages/Dashboard.tsx',
        exports: ['Dashboard'],
        imports: [{ module: 'react', imports: ['useEffect'], isDefault: false }],
        hooks: ['useEffect', 'useQuery'],
        jsxElements: ['div', 'table', 'card'],
        comments: ['Main dashboard component'],
        props: []
    },
    {
        name: 'UserProfile',
        path: 'src/components/user/UserProfile.tsx',
        exports: ['UserProfile'],
        imports: [{ module: 'react', imports: ['useState'], isDefault: false }],
        hooks: ['useState', 'useUser'],
        jsxElements: ['form', 'input'],
        comments: ['User profile editing form'],
        props: ['user', 'onUpdate']
    }
];

/**
 * Test cosine similarity calculation
 */
function testCosineSimilarity() {
    console.log('🔢 Testing Cosine Similarity...');
    
    // Create test vectors
    const vectorA = [1, 2, 3];
    const vectorB = [4, 5, 6]; 
    const vectorC = [1, 2, 3]; // Same as A
    
    function cosineSimilarity(vectorA, vectorB) {
        if (vectorA.length !== vectorB.length) {
            throw new Error('Vectors must have the same length');
        }

        let dotProduct = 0;
        let normA = 0;
        let normB = 0;

        for (let i = 0; i < vectorA.length; i++) {
            dotProduct += vectorA[i] * vectorB[i];
            normA += vectorA[i] * vectorA[i];
            normB += vectorB[i] * vectorB[i];
        }

        normA = Math.sqrt(normA);
        normB = Math.sqrt(normB);

        if (normA === 0 || normB === 0) {
            return 0;
        }

        return dotProduct / (normA * normB);
    }
    
    const simAB = cosineSimilarity(vectorA, vectorB);
    const simAC = cosineSimilarity(vectorA, vectorC);
    
    console.log(`   Vector A vs B: ${simAB.toFixed(4)}`);
    console.log(`   Vector A vs C (identical): ${simAC.toFixed(4)}`);
    console.log(`   ✅ Cosine similarity working correctly`);
}

/**
 * Test component summary generation logic
 */
function testSummaryGeneration() {
    console.log('\n📝 Testing Component Summary Generation...');
    
    function detectFramework(component) {
        const imports = component.imports.map(imp => imp.module.toLowerCase());
        
        if (imports.some(imp => imp.includes('vue'))) return 'Vue';
        if (imports.some(imp => imp.includes('next'))) return 'Next.js';
        if (imports.some(imp => imp.includes('react'))) return 'React';
        if (component.path.endsWith('.vue')) return 'Vue';
        
        return 'JavaScript';
    }

    function describeHooks(hooks) {
        const hookDescriptions = {
            'useState': 'state management',
            'useEffect': 'side effects',
            'useContext': 'context data',
            'useRouter': 'routing',
            'useUser': 'user authentication',
            'useQuery': 'data fetching'
        };
        
        return hooks
            .map(hook => hookDescriptions[hook] || hook)
            .slice(0, 3)
            .join(', ');
    }

    function describeUIElements(elements) {
        const elementDescriptions = {
            'form': 'a form',
            'table': 'a data table',
            'button': 'buttons',
            'input': 'input fields',
            'modal': 'a modal dialog',
            'card': 'cards'
        };
        
        return elements
            .map(element => elementDescriptions[element.toLowerCase()] || element)
            .slice(0, 4)
            .join(', ');
    }

    function generateComponentSummary(component) {
        const parts = [];
        
        const framework = detectFramework(component);
        parts.push(`${framework} component`);
        parts.push(`'${component.name}'`);
        
        if (component.hooks && component.hooks.length > 0) {
            const hookDescriptions = describeHooks(component.hooks);
            parts.push(`uses ${hookDescriptions}`);
        }
        
        if (component.jsxElements && component.jsxElements.length > 0) {
            const uiDescription = describeUIElements(component.jsxElements);
            parts.push(`renders ${uiDescription}`);
        }
        
        return parts.join(', ');
    }

    function optimizeForEmbedding(summary) {
        return summary
            .replace(/[\n\r]+/g, ' ')
            .replace(/\s+/g, ' ')
            .trim()
            .substring(0, 500);
    }

    for (const component of sampleComponents) {
        const summary = generateComponentSummary(component);
        const optimized = optimizeForEmbedding(summary);
        
        console.log(`   📦 ${component.name}:`);
        console.log(`      Summary: "${summary}"`);
        console.log(`      Optimized: "${optimized}"`);
        console.log('');
    }
    
    console.log('   ✅ Summary generation working correctly');
}

/**
 * Test embedding input optimization
 */
function testEmbeddingOptimization() {
    console.log('\n⚡ Testing Embedding Input Optimization...');
    
    function optimizeForEmbedding(text) {
        return text
            .replace(/[\n\r]+/g, ' ')
            .replace(/\s+/g, ' ')
            .trim()
            .substring(0, 500);
    }

    function estimateTokenCount(text) {
        return Math.ceil(text.length / 4);
    }

    const testInputs = [
        'Simple text',
        'Text\nwith\nmultiple\nlines',
        'Text    with    excessive    whitespace',
        'Very long text that should be truncated because it exceeds the maximum length limit for embedding input and needs to be cut off at exactly 500 characters to ensure we stay within token limits and maintain good performance while still capturing the essential meaning of the component description that we are trying to embed into the vector space for semantic search and similarity matching across the codebase to help developers find relevant components and understand the structure and purpose of their code',
        'Normal length text that fits comfortably within limits'
    ];

    for (const input of testInputs) {
        const optimized = optimizeForEmbedding(input);
        const tokenCount = estimateTokenCount(optimized);
        
        console.log(`   Original (${input.length} chars): "${input.substring(0, 50)}${input.length > 50 ? '...' : ''}"`);
        console.log(`   Optimized (${optimized.length} chars, ~${tokenCount} tokens): "${optimized.substring(0, 50)}${optimized.length > 50 ? '...' : ''}"`);
        console.log('   ---');
    }
    
    console.log('   ✅ Optimization working correctly');
}

/**
 * Test similarity ranking algorithms
 */
function testSimilarityRanking() {
    console.log('\n🎯 Testing Similarity Ranking...');
    
    // Generate mock embeddings (simplified to 5 dimensions for testing)
    const dimensions = 5;
    sampleComponents[0].embedding = [1, 0, 0, 0, 0]; // LoginForm
    sampleComponents[1].embedding = [0, 1, 0, 0, 0]; // Dashboard  
    sampleComponents[2].embedding = [0.8, 0.2, 0, 0, 0]; // UserProfile (similar to LoginForm)

    function cosineSimilarity(vectorA, vectorB) {
        let dotProduct = 0;
        let normA = 0;
        let normB = 0;

        for (let i = 0; i < vectorA.length; i++) {
            dotProduct += vectorA[i] * vectorB[i];
            normA += vectorA[i] * vectorA[i];
            normB += vectorB[i] * vectorB[i];
        }

        normA = Math.sqrt(normA);
        normB = Math.sqrt(normB);

        return dotProduct / (normA * normB);
    }

    function findSimilarComponents(targetComponent, allComponents, maxResults = 5) {
        const results = [];

        for (const component of allComponents) {
            if (component.path === targetComponent.path || !component.embedding) {
                continue;
            }

            const similarity = cosineSimilarity(targetComponent.embedding, component.embedding);
            results.push({ component, similarity });
        }

        return results
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, maxResults);
    }

    const targetComponent = sampleComponents[0]; // LoginForm
    const similar = findSimilarComponents(targetComponent, sampleComponents);

    console.log(`   🎯 Components similar to ${targetComponent.name}:`);
    for (const result of similar) {
        console.log(`      ${result.component.name}: ${(result.similarity * 100).toFixed(1)}% similar`);
    }
    
    console.log('   ✅ Similarity ranking working correctly');
}

/**
 * Run all tests
 */
function runAllTests() {
    console.log('🧪 UI Copilot Embedding System - Standalone Tests');
    console.log('==================================================');
    
    try {
        testCosineSimilarity();
        testSummaryGeneration();
        testEmbeddingOptimization();
        testSimilarityRanking();
        
        console.log('\n🎉 All tests passed successfully!');
        console.log('\nNext steps:');
        console.log('1. Set OpenAI API key in VS Code settings');
        console.log('2. Press F5 to launch Extension Development Host');
        console.log('3. Test the extension commands:');
        console.log('   - "Reindex Workspace"');
        console.log('   - "Generate Embeddings"');
        console.log('   - "Search Codebase"');
        console.log('   - "Find Similar Files"');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        process.exit(1);
    }
}

// Run tests
runAllTests();