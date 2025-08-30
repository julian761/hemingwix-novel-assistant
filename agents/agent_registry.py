#!/usr/bin/env python3
"""
Hemingwix Agent Registry
Manages and provides access to all specialized subagents for the Novel Creation Assistant
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class AgentCategory(Enum):
    NOVEL_WRITING = "novel_writing"
    TECHNICAL = "technical" 
    PROJECT_MANAGEMENT = "project_management"

@dataclass
class AgentConfig:
    """Configuration for a specialized agent"""
    name: str
    category: AgentCategory
    specialty: str
    description: str
    capabilities: List[str]
    file_path: str
    prompt_template: str
    usage_examples: List[str]
    integration_points: List[str]

class HemingwixAgentRegistry:
    """Registry and manager for all Hemingwix specialized agents"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.agents_path = self.base_path / "agents"
        self.agents = self._load_all_agents()
    
    def _load_all_agents(self) -> Dict[str, AgentConfig]:
        """Load all agent configurations from markdown files"""
        agents = {}
        
        # Novel Writing Agents
        agents.update(self._load_category_agents(AgentCategory.NOVEL_WRITING))
        
        # Technical Agents
        agents.update(self._load_category_agents(AgentCategory.TECHNICAL))
        
        # Project Management Agents
        agents.update(self._load_category_agents(AgentCategory.PROJECT_MANAGEMENT))
        
        return agents
    
    def _load_category_agents(self, category: AgentCategory) -> Dict[str, AgentConfig]:
        """Load agents from a specific category directory"""
        category_agents = {}
        category_path = self.agents_path / category.value
        
        if not category_path.exists():
            return category_agents
            
        for agent_file in category_path.glob("*_agent.md"):
            agent_config = self._parse_agent_file(agent_file, category)
            if agent_config:
                category_agents[agent_config.name] = agent_config
                
        return category_agents
    
    def _parse_agent_file(self, file_path: Path, category: AgentCategory) -> Optional[AgentConfig]:
        """Parse agent configuration from markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract key information from markdown
            lines = content.split('\n')
            
            # Parse header information
            name = ""
            specialty = ""
            description = ""
            prompt_template = ""
            capabilities = []
            usage_examples = []
            integration_points = []
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('# ') and not name:
                    name = line[2:].replace(" Agent", "").lower().replace(" ", "_")
                elif line.startswith('**Role**:'):
                    description = line.split(':', 1)[1].strip()
                elif line.startswith('**Specialty**:'):
                    specialty = line.split(':', 1)[1].strip()
                elif line == "### Core Capabilities":
                    current_section = "capabilities"
                elif line == "## Usage Examples":
                    current_section = "examples"
                elif line == "## Integration with Hemingwix Systems":
                    current_section = "integration"
                elif line.startswith('```') and 'You are the' in content[content.find(line):]:
                    # Extract prompt template
                    start = content.find('```', content.find(line)) + 3
                    end = content.find('```', start)
                    prompt_template = content[start:end].strip()
                elif current_section == "capabilities" and line.startswith('- '):
                    capabilities.append(line[2:])
                elif current_section == "examples" and line.startswith('**'):
                    usage_examples.append(line)
                elif current_section == "integration" and line.startswith('- **'):
                    integration_points.append(line[3:])
            
            return AgentConfig(
                name=name,
                category=category,
                specialty=specialty,
                description=description,
                capabilities=capabilities,
                file_path=str(file_path),
                prompt_template=prompt_template,
                usage_examples=usage_examples,
                integration_points=integration_points
            )
            
        except Exception as e:
            print(f"Error parsing agent file {file_path}: {e}")
            return None
    
    def get_agent(self, agent_name: str) -> Optional[AgentConfig]:
        """Get a specific agent configuration"""
        return self.agents.get(agent_name)
    
    def list_agents(self, category: Optional[AgentCategory] = None) -> List[AgentConfig]:
        """List all agents, optionally filtered by category"""
        if category:
            return [agent for agent in self.agents.values() if agent.category == category]
        return list(self.agents.values())
    
    def get_agents_by_capability(self, capability_keyword: str) -> List[AgentConfig]:
        """Find agents that have a specific capability"""
        matching_agents = []
        
        for agent in self.agents.values():
            for cap in agent.capabilities:
                if capability_keyword.lower() in cap.lower():
                    matching_agents.append(agent)
                    break
                    
        return matching_agents
    
    def search_agents(self, query: str) -> List[AgentConfig]:
        """Search agents by name, specialty, or capabilities"""
        query_lower = query.lower()
        matching_agents = []
        
        for agent in self.agents.values():
            if (query_lower in agent.name.lower() or 
                query_lower in agent.specialty.lower() or
                query_lower in agent.description.lower() or
                any(query_lower in cap.lower() for cap in agent.capabilities)):
                matching_agents.append(agent)
                
        return matching_agents
    
    def generate_agent_prompt(self, agent_name: str, context: str = "") -> str:
        """Generate a complete prompt for launching an agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return f"Agent '{agent_name}' not found"
            
        prompt = agent.prompt_template
        if context:
            prompt += f"\n\nAdditional Context:\n{context}"
            
        return prompt
    
    def export_registry(self, output_file: str = "agent_registry.json"):
        """Export complete agent registry to JSON"""
        registry_data = {
            "metadata": {
                "project": "Hemingwix Novel Creation Assistant",
                "total_agents": len(self.agents),
                "categories": {cat.value: len(self.list_agents(cat)) for cat in AgentCategory},
                "created": "2025-08-30",
                "version": "1.0.0"
            },
            "agents": {name: asdict(agent) for name, agent in self.agents.items()}
        }
        
        output_path = self.base_path / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, indent=2, default=str)
            
        return output_path
    
    def print_agent_summary(self):
        """Print a summary of all available agents"""
        print("🤖 Hemingwix Specialized Agent Registry")
        print("=" * 50)
        
        for category in AgentCategory:
            category_agents = self.list_agents(category)
            if category_agents:
                print(f"\n📂 {category.value.replace('_', ' ').title()} ({len(category_agents)} agents)")
                for agent in category_agents:
                    print(f"   • {agent.name.replace('_', ' ').title()}: {agent.specialty}")
        
        print(f"\n📊 Total: {len(self.agents)} specialized agents available")
        print("Use agent_registry.get_agent('agent_name') to access specific agents")

def create_agent_launcher():
    """Create a simple agent launcher function"""
    def launch_agent(agent_name: str, context: str = "", registry_path: str = None):
        """Launch a specialized agent with context"""
        if not registry_path:
            registry_path = "/Users/benitosmac/Limerix_JBP-Local/Novelcrafter Experiment "
            
        registry = HemingwixAgentRegistry(registry_path)
        agent = registry.get_agent(agent_name)
        
        if not agent:
            available = [name.replace('_', ' ').title() for name in registry.agents.keys()]
            return f"Agent '{agent_name}' not found. Available agents: {', '.join(available)}"
        
        prompt = registry.generate_agent_prompt(agent_name, context)
        
        return {
            "agent": agent,
            "prompt": prompt,
            "launch_message": f"🚀 Launching {agent.name.replace('_', ' ').title()} Agent",
            "specialty": agent.specialty,
            "capabilities": agent.capabilities
        }
    
    return launch_agent

if __name__ == "__main__":
    # Initialize and test the registry
    base_path = "/Users/benitosmac/Limerix_JBP-Local/Novelcrafter Experiment "
    registry = HemingwixAgentRegistry(base_path)
    
    # Print summary
    registry.print_agent_summary()
    
    # Export registry
    export_path = registry.export_registry()
    print(f"\n💾 Registry exported to: {export_path}")
    
    # Test agent search
    print(f"\n🔍 Agents with 'character' capability:")
    char_agents = registry.search_agents("character")
    for agent in char_agents:
        print(f"   • {agent.name.replace('_', ' ').title()}")