// Simple test to check if extension commands are properly registered
const fs = require('fs');
const path = require('path');

// Read the package.json to see what commands should be available
const packagePath = path.join(__dirname, 'package.json');
const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));

console.log('🔍 Extension Commands from package.json:');
console.log('================================================');

if (packageData.contributes && packageData.contributes.commands) {
    packageData.contributes.commands.forEach((command, index) => {
        console.log(`${index + 1}. Command: ${command.command}`);
        console.log(`   Title: ${command.title}`);
        console.log(`   Category: ${command.category || 'None'}`);
        console.log('');
    });
}

console.log('🔍 Commands in Command Palette Menu:');
console.log('=====================================');

if (packageData.contributes && packageData.contributes.menus && packageData.contributes.menus.commandPalette) {
    packageData.contributes.menus.commandPalette.forEach((menuItem, index) => {
        const command = packageData.contributes.commands.find(cmd => cmd.command === menuItem.command);
        console.log(`${index + 1}. ${menuItem.command}`);
        if (command) {
            console.log(`   → Shows as: "${command.title}"`);
        }
        console.log('');
    });
}

console.log('✅ The command "palette.openUnified" should show as:');
console.log('   "🎨 Palette: Open Unified System"');
console.log('');
console.log('🔧 If you don\'t see this command, try:');
console.log('   1. Press F5 to test in Extension Development Host');
console.log('   2. Check VS Code Output → "Code Palette" for errors');
console.log('   3. Try "Developer: Reload Window" in VS Code');
console.log('   4. Ensure the extension is properly installed/activated');