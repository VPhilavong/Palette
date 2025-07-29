#!/usr/bin/env python3
"""
Demo of the new File Search knowledge base system.
Shows how it replaces the complex MCP architecture with a simpler approach.
"""

import os
import sys
from pathlib import Path

# Add Palette to path
palette_dir = Path(__file__).parent.parent
sys.path.insert(0, str(palette_dir))

from src.palette.knowledge import PaletteKnowledgeBase, KnowledgeEnhancedGenerator


def demo_knowledge_base():
    """Demonstrate the knowledge base functionality."""
    print("🧠 Palette Knowledge Base Demo")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        return
    
    # Initialize knowledge base
    print("\n1. Initializing knowledge base...")
    kb = PaletteKnowledgeBase()
    
    # Create core knowledge base (this would be done once)
    print("\n2. Setting up core knowledge base...")
    try:
        core_kb_id = kb.create_core_knowledge_base()
        print(f"   Core knowledge base ID: {core_kb_id}")
    except Exception as e:
        print(f"   ❌ Failed to create knowledge base: {e}")
        return
    
    # Demo knowledge search
    print("\n3. Testing knowledge search...")
    context = {
        'framework': 'react',
        'styling': 'tailwind',
        'component_library': 'none',
        'typescript': True
    }
    
    # Search for form patterns
    print("   🔍 Searching for form best practices...")
    search_result = kb.search_knowledge(
        query="login form with validation patterns",
        context=context
    )
    
    if search_result["success"]:
        print(f"   ✅ Found {len(search_result['knowledge'])} knowledge items")
        print(f"   📚 Citations: {len(search_result['citations'])}")
        
        # Show first knowledge item
        if search_result['knowledge']:
            first_knowledge = search_result['knowledge'][0]
            content = first_knowledge.get('content', '')[:200]
            print(f"   📖 Sample knowledge: {content}...")
    else:
        print(f"   ❌ Search failed: {search_result.get('error')}")
    
    # Demo enhanced generation
    print("\n4. Testing enhanced generation...")
    generator = KnowledgeEnhancedGenerator(kb)
    
    enhanced_prompt, citations = generator.enhance_prompt_with_knowledge(
        prompt="create a login form with email and password fields",
        context=context
    )
    
    print(f"   ✅ Enhanced prompt length: {len(enhanced_prompt)} characters")
    print(f"   📚 Citations included: {len(citations)}")
    
    # Show available knowledge bases
    print("\n5. Available knowledge bases:")
    bases = kb.get_available_knowledge_bases()
    for base in bases:
        status = "✅" if base["status"] == "active" else "❌"
        print(f"   {status} {base['name']}: {base['id']}")
    
    print("\n" + "=" * 50)
    print("✅ Knowledge base demo completed!")
    print("\nThis system replaces the complex MCP architecture with:")
    print("- Simple OpenAI API calls")
    print("- No async context issues") 
    print("- Hosted infrastructure")
    print("- Transparent citations")
    print("- Scalable knowledge management")


if __name__ == "__main__":
    demo_knowledge_base()