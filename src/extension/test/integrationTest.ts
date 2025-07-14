/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Palette Team. All rights reserved.
 *  Licensed under the MIT License.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { WCAGValidator } from '../accessibility/wcagValidator';
import { WorkspacePatternSearch } from '../search/workspacePatternSearch';
import { ComponentAnalyzer } from '../../codebase/componentAnalyzer';
import { VectorStore } from '../../embeddings/vectorStore';
import { ConsoleLogService } from '../../platform/log/node/consoleLogService';
import { LogLevel } from '../../platform/log/common/logService';

/**
 * Integration tests to validate the Palette UI Agent functionality
 */
export class IntegrationTest {
	private logService = new ConsoleLogService(LogLevel.Info);

	async runAllTests(): Promise<{ passed: number; failed: number; results: string[] }> {
		const results: string[] = [];
		let passed = 0;
		let failed = 0;

		const tests = [
			{ name: 'WCAG Validator', test: () => this.testWCAGValidator() },
			{ name: 'Vector Store', test: () => this.testVectorStore() },
			{ name: 'Pattern Search', test: () => this.testPatternSearch() },
			{ name: 'Component Analyzer', test: () => this.testComponentAnalyzer() }
		];

		for (const { name, test } of tests) {
			try {
				const result = await test();
				if (result.success) {
					passed++;
					results.push(`✅ ${name}: ${result.message}`);
				} else {
					failed++;
					results.push(`❌ ${name}: ${result.message}`);
				}
			} catch (error) {
				failed++;
				results.push(`❌ ${name}: Error - ${error instanceof Error ? error.message : 'Unknown error'}`);
			}
		}

		return { passed, failed, results };
	}

	private async testWCAGValidator(): Promise<{ success: boolean; message: string }> {
		const validator = new WCAGValidator(this.logService);

		// Create a test component with accessibility issues
		const testComponent = {
			name: 'TestComponent',
			path: '/test/TestComponent.tsx',
			exports: ['TestComponent'],
			imports: [],
			props: ['title'],
			hooks: ['useState'],
			jsxElements: ['div', 'img', 'button']
		};

		// Mock the workspace text document
		const mockContent = `
import React from 'react';

export const TestComponent = ({ title }: { title: string }) => {
  return (
    <div onClick={() => alert('clicked')}>
      <img src="test.jpg" />
      <h1>{title}</h1>
      <button>Click me</button>
    </div>
  );
};`;

		// Since we can't easily mock vscode.workspace.openTextDocument in tests,
		// we'll test the validator logic with a mock component
		try {
			// This would normally call validateComponent but we'll test the core logic
			const issues = validator['checkNonTextContent'](mockContent, mockContent.split('\\n'));
			
			if (issues.length > 0) {
				return { success: true, message: `Found ${issues.length} accessibility issues as expected` };
			} else {
				return { success: false, message: 'Expected to find accessibility issues but found none' };
			}
		} catch (error) {
			return { success: false, message: `WCAG validation failed: ${error}` };
		}
	}

	private async testVectorStore(): Promise<{ success: boolean; message: string }> {
		const vectorStore = new VectorStore();

		// Test basic vector operations
		const testEmbedding = [0.1, 0.2, 0.3, 0.4, 0.5];
		const testMetadata = { type: 'component', name: 'Button' };

		// Store a vector
		vectorStore.store('test-1', testEmbedding, testMetadata);

		// Check if it was stored
		if (!vectorStore.has('test-1')) {
			return { success: false, message: 'Vector was not stored correctly' };
		}

		// Test similarity search
		const queryEmbedding = [0.15, 0.25, 0.35, 0.45, 0.55]; // Similar to test embedding
		const results = vectorStore.findSimilar(queryEmbedding, 1);

		if (results.length === 0) {
			return { success: false, message: 'Similarity search returned no results' };
		}

		if (results[0].id !== 'test-1') {
			return { success: false, message: 'Similarity search returned wrong result' };
		}

		// Test vector store size
		if (vectorStore.size() !== 1) {
			return { success: false, message: `Expected size 1, got ${vectorStore.size()}` };
		}

		return { success: true, message: 'Vector store operations working correctly' };
	}

	private async testPatternSearch(): Promise<{ success: boolean; message: string }> {
		const patternSearch = new WorkspacePatternSearch(this.logService);

		// Create test components
		const testComponents = [
			{
				name: 'Button',
				path: '/test/Button.tsx',
				exports: ['Button'],
				imports: [],
				props: ['variant', 'size'],
				hooks: [],
				jsxElements: ['button']
			},
			{
				name: 'Card',
				path: '/test/Card.tsx',
				exports: ['Card'],
				imports: [],
				props: ['title', 'content'],
				hooks: [],
				jsxElements: ['div', 'h2', 'p']
			}
		];

		// Test pattern search
		try {
			const results = await patternSearch.searchDesignPatterns('button component', testComponents);
			
			if (results.components.length === 0) {
				return { success: false, message: 'Pattern search did not find relevant components' };
			}

			const foundButton = results.components.find(c => c.name === 'Button');
			if (!foundButton) {
				return { success: false, message: 'Pattern search did not find Button component' };
			}

			return { success: true, message: `Found ${results.components.length} relevant components` };
		} catch (error) {
			return { success: false, message: `Pattern search failed: ${error}` };
		}
	}

	private async testComponentAnalyzer(): Promise<{ success: boolean; message: string }> {
		const analyzer = new ComponentAnalyzer();

		// Test component stats generation
		const testComponents = [
			{
				name: 'FunctionalComponent',
				path: '/test/FC.tsx',
				exports: ['FunctionalComponent'],
				imports: [],
				props: ['data'],
				hooks: ['useState', 'useEffect'],
				jsxElements: ['div']
			},
			{
				name: 'SimpleComponent',
				path: '/test/SC.tsx',
				exports: ['SimpleComponent'],
				imports: [],
				props: [],
				hooks: [],
				jsxElements: ['span']
			}
		];

		try {
			const stats = analyzer.getComponentStats(testComponents);
			
			if (stats.totalComponents !== 2) {
				return { success: false, message: `Expected 2 components, got ${stats.totalComponents}` };
			}

			if (stats.hooksUsage['useState'] !== 1) {
				return { success: false, message: 'Hook usage tracking not working correctly' };
			}

			return { success: true, message: 'Component analysis working correctly' };
		} catch (error) {
			return { success: false, message: `Component analyzer failed: ${error}` };
		}
	}
}

/**
 * VS Code command to run integration tests
 */
export async function runIntegrationTests(): Promise<void> {
	const testRunner = new IntegrationTest();
	
	try {
		vscode.window.showInformationMessage('🧪 Running Palette UI Agent integration tests...');
		
		const results = await testRunner.runAllTests();
		
		const summary = `Tests completed: ${results.passed} passed, ${results.failed} failed`;
		const details = results.results.join('\\n');
		
		if (results.failed === 0) {
			vscode.window.showInformationMessage(`✅ All tests passed! ${summary}`);
		} else {
			vscode.window.showWarningMessage(`⚠️ Some tests failed. ${summary}`);
		}
		
		// Show detailed results in output channel
		const outputChannel = vscode.window.createOutputChannel('Palette UI Agent Tests');
		outputChannel.clear();
		outputChannel.appendLine('=== Palette UI Agent Integration Tests ===\\n');
		outputChannel.appendLine(summary + '\\n');
		outputChannel.appendLine('Detailed Results:');
		outputChannel.appendLine(details);
		outputChannel.show();
		
	} catch (error) {
		vscode.window.showErrorMessage(`❌ Test execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
	}
}