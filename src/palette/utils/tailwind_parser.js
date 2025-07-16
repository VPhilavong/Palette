#!/usr/bin/env node

/**
 * Tailwind Config Parser
 * 
 * This Node.js script safely executes a tailwind.config.js file and extracts
 * the resolved theme object, outputting it as JSON for Python consumption.
 * 
 * Usage: node tailwind_parser.js <path_to_tailwind_config>
 * Output: JSON object with theme configuration
 */

const fs = require('fs');
const path = require('path');

function parseConfig(configPath) {
    try {
        // Check if config file exists
        if (!fs.existsSync(configPath)) {
            throw new Error(`Config file not found: ${configPath}`);
        }

        // Clear the require cache to ensure fresh imports
        delete require.cache[require.resolve(configPath)];
        
        // Require the config file
        const config = require(configPath);
        
        // Extract theme from config
        const theme = config.theme || {};
        
        // Return the theme object with default Tailwind values merged
        return {
            colors: theme.colors || {},
            spacing: theme.spacing || {},
            fontSize: theme.fontSize || {},
            fontFamily: theme.fontFamily || {},
            fontWeight: theme.fontWeight || {},
            borderRadius: theme.borderRadius || {},
            boxShadow: theme.boxShadow || {},
            screens: theme.screens || {},
            extend: theme.extend || {}
        };
        
    } catch (error) {
        // If there's an error, return a basic structure with the error
        return {
            error: error.message,
            colors: {},
            spacing: {},
            fontSize: {},
            fontFamily: {},
            fontWeight: {},
            borderRadius: {},
            boxShadow: {},
            screens: {},
            extend: {}
        };
    }
}

function main() {
    // Get config path from command line arguments
    const configPath = process.argv[2];
    
    if (!configPath) {
        console.error(JSON.stringify({
            error: "Please provide a path to the tailwind.config.js file",
            usage: "node tailwind_parser.js <path_to_tailwind_config>"
        }));
        process.exit(1);
    }
    
    // Resolve the absolute path
    const absolutePath = path.resolve(configPath);
    
    // Parse the config and output as JSON
    const result = parseConfig(absolutePath);
    console.log(JSON.stringify(result, null, 2));
}

// Only run if this script is called directly
if (require.main === module) {
    main();
}

module.exports = { parseConfig };