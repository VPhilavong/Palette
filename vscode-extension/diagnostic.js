// Diagnostic script to check extension activation
// This can be run in VS Code's Developer Console

console.log('=== Palette Extension Diagnostic ===');

// Check if extension is loaded
const extension = vscode.extensions.getExtension('sail-project.code-palette');
if (extension) {
    console.log('✅ Extension found:', extension.id);
    console.log('Extension state:', {
        isActive: extension.isActive,
        packageJSON: {
            version: extension.packageJSON.version,
            main: extension.packageJSON.main,
            activationEvents: extension.packageJSON.activationEvents,
            commands: extension.packageJSON.contributes?.commands?.map(cmd => cmd.command)
        }
    });
    
    // Try to activate the extension
    if (!extension.isActive) {
        console.log('🔄 Activating extension...');
        extension.activate().then(() => {
            console.log('✅ Extension activated successfully');
            
            // Check commands after activation
            vscode.commands.getCommands(true).then(commands => {
                const paletteCommands = commands.filter(cmd => cmd.startsWith('palette.'));
                console.log('Palette commands after activation:', paletteCommands);
            });
        }).catch(err => {
            console.log('❌ Extension activation failed:', err);
        });
    } else {
        console.log('✅ Extension already active');
        
        // Check commands
        vscode.commands.getCommands(true).then(commands => {
            const paletteCommands = commands.filter(cmd => cmd.startsWith('palette.'));
            console.log('Available palette commands:', paletteCommands);
        });
    }
} else {
    console.log('❌ Extension not found');
}