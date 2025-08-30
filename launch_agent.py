#!/usr/bin/env python3
"""
Hemingwix Agent Launcher
Quick access to specialized agents for novel creation assistance
"""

import sys
import json
from pathlib import Path

def show_available_agents():
    """Display all available agents"""
    try:
        with open("agent_registry.json", "r") as f:
            registry = json.load(f)
        
        print("🤖 Available Hemingwix Agents:")
        print("=" * 40)
        
        for category, count in registry["metadata"]["categories"].items():
            print(f"\n📂 {category.replace('_', ' ').title()} ({count} agents)")
            
            for agent_name, agent_data in registry["agents"].items():
                if agent_data["category"] == category:
                    print(f"   • {agent_name.replace('_', ' ').title()}")
                    print(f"     {agent_data['specialty']}")
        
        print(f"\n📊 Total: {registry['metadata']['total_agents']} agents")
        print("\nUsage: python launch_agent.py <agent_name>")
        print("Example: python launch_agent.py character_development")
        
    except FileNotFoundError:
        print("❌ Agent registry not found. Run: python agents/agent_registry.py")

def launch_agent(agent_name: str):
    """Launch a specific agent"""
    try:
        with open("agent_registry.json", "r") as f:
            registry = json.load(f)
        
        # Find agent
        agent_data = None
        for name, data in registry["agents"].items():
            if name == agent_name or name.replace("_", " ").lower() == agent_name.replace("_", " ").lower():
                agent_data = data
                break
        
        if not agent_data:
            print(f"❌ Agent '{agent_name}' not found.")
            show_available_agents()
            return
        
        print(f"🚀 Launching {agent_data['name'].replace('_', ' ').title()} Agent")
        print("=" * 50)
        print(f"**Specialty**: {agent_data['specialty']}")
        print(f"**Category**: {agent_data['category'].replace('_', ' ').title()}")
        print("\n**Ready to assist with:**")
        for capability in agent_data['capabilities'][:5]:  # Show first 5 capabilities
            print(f"  • {capability}")
        
        if len(agent_data['capabilities']) > 5:
            print(f"  • ... and {len(agent_data['capabilities']) - 5} more capabilities")
        
        print(f"\n**Agent Prompt Template**:")
        print("```")
        print(agent_data['prompt_template'][:500] + "..." if len(agent_data['prompt_template']) > 500 else agent_data['prompt_template'])
        print("```")
        
        print(f"\n📋 **Usage Examples**:")
        for example in agent_data['usage_examples'][:3]:
            print(f"  {example}")
        
        print(f"\n🔗 **Full Configuration**: {agent_data['file_path']}")
        print("\n✅ **Agent is ready for specialized assistance!**")
        print("\nYou can now ask questions specific to this agent's expertise.")
        
    except Exception as e:
        print(f"❌ Error launching agent: {e}")

def main():
    """Main launcher function"""
    if len(sys.argv) < 2:
        show_available_agents()
        return
    
    agent_name = sys.argv[1].lower().replace("-", "_")
    launch_agent(agent_name)

if __name__ == "__main__":
    main()