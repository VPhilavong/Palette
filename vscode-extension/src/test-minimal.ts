// Minimal test for PaletteService
import { PaletteService } from './paletteService';

async function test() {
    console.log('Testing minimal palette service...');
    
    const service = new PaletteService();
    
    // Test stream generation
    await service.streamGenerate(
        { prompt: 'simple button' },
        (data) => {
            console.log('[DATA]:', data);
        },
        (error) => {
            console.error('[ERROR]:', error);
        }
    );
    
    console.log('Test complete');
}

// Run if called directly
if (require.main === module) {
    test().catch(console.error);
}