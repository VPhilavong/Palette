// Minimal extension test
exports.activate = function(context) {
    console.log('🔥 MINIMAL TEST EXTENSION ACTIVATED!');
    
    const vscode = require('vscode');
    
    // Register the simplest possible command
    let disposable = vscode.commands.registerCommand('minimal.test', function () {
        vscode.window.showInformationMessage('✅ Minimal test command works!');
        console.log('✅ Minimal test command executed successfully');
    });

    context.subscriptions.push(disposable);
    
    console.log('🔥 Test command registered: minimal.test');
};

exports.deactivate = function() {
    console.log('🔥 MINIMAL TEST EXTENSION DEACTIVATED');
};