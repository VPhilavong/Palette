// Test script to verify file path parsing
const testBuffer = `
╭───────────────────────────────── Generating ─────────────────────────────────╮
│ 🎨 UI/UX Copilot                                                             │
│ test button                                                                  │
╰──────────────────────────────────────────────────────────────────────────────╯

✅ Generation Complete!

                  Created Files                  
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ File                              ┃ Status    ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ test-output/components/Button.jsx │ ✓ Created │
└───────────────────────────────────┴───────────┘
`;

// Test different parsing approaches
console.log('Testing file path parsing...\n');

// Approach 1: Line by line
const lines = testBuffer.split('\n');
const files1 = [];
for (const line of lines) {
    if (line.includes('✓ Created') || line.includes('✓ created')) {
        const match = line.match(/([\w\/\-\.]+\.(tsx?|jsx?))/);
        if (match) {
            files1.push(match[1]);
        }
    }
}
console.log('Approach 1 (line by line):', files1);

// Approach 2: Direct regex on full buffer
const files2 = [];
const matches = testBuffer.match(/([\w\/\-\.]+\.(tsx?|jsx?))\s*│\s*✓\s*Created/g);
if (matches) {
    for (const match of matches) {
        const fileMatch = match.match(/([\w\/\-\.]+\.(tsx?|jsx?))/);
        if (fileMatch) {
            files2.push(fileMatch[1]);
        }
    }
}
console.log('Approach 2 (regex):', files2);

// Approach 3: Split by table characters
const files3 = [];
const tableLines = testBuffer.split('\n').filter(line => line.includes('│'));
for (const line of tableLines) {
    if (line.includes('✓ Created')) {
        const parts = line.split('│');
        if (parts.length >= 2) {
            const filePath = parts[1].trim();
            if (filePath.match(/\.(tsx?|jsx?)$/)) {
                files3.push(filePath);
            }
        }
    }
}
console.log('Approach 3 (split by │):', files3);