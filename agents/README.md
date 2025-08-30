# Hemingwix Specialized Agent System

A comprehensive suite of AI specialists for novel creation, technical implementation, and project management.

## 🤖 Available Agents

### 📚 Novel Writing Specialists

#### **Character Development Agent**
- **Specialty**: Character psychology, backstories, motivations, voice development
- **Use for**: Creating complex characters, consistency checking, relationship dynamics
- **File**: `novel_writing/character_development_agent.md`

#### **Plot Structure Agent** 
- **Specialty**: Story beats, three-act structure, pacing, plot points
- **Use for**: Story architecture, tension building, scene transitions
- **File**: `novel_writing/plot_structure_agent.md`

#### **Dialogue Specialist Agent**
- **Specialty**: Character voice, conversation writing, subtext
- **Use for**: Natural dialogue, character voice consistency, exposition through speech
- **File**: `novel_writing/dialogue_specialist_agent.md`

#### **Research Assistant Agent**
- **Specialty**: World-building research, fact-checking, source verification
- **Use for**: Historical accuracy, technical details, cultural authenticity
- **File**: `novel_writing/research_assistant_agent.md`

### 🔧 Technical Specialists

#### **MCP Integration Specialist**
- **Specialty**: Notion MCP server, API integration, AI workflows
- **Use for**: Technical support, server configuration, troubleshooting
- **File**: `technical/mcp_integration_specialist.md`

#### **Database Design Agent**
- **Specialty**: PostgreSQL/ChromaDB optimization, schema design
- **Use for**: Database performance, query optimization, data modeling
- **File**: `technical/database_design_agent.md`

#### **Code Review Agent**
- **Specialty**: Python code quality, security, architecture review
- **Use for**: Code improvements, security audits, best practices
- **File**: `technical/code_review_agent.md`

#### **DevOps Agent**
- **Specialty**: Deployment, infrastructure, monitoring, operations
- **Use for**: Production deployment, scaling, monitoring setup
- **File**: `technical/devops_agent.md`

### 📋 Project Management

#### **Novel Planning Agent**
- **Specialty**: Strategic planning, timelines, workflow optimization
- **Use for**: Project timelines, writing schedules, milestone planning
- **File**: `project_management/novel_planning_agent.md`

#### **Content Organization Agent**
- **Specialty**: File management, content structure, version control
- **Use for**: File organization, content workflows, system optimization
- **File**: `project_management/content_organization_agent.md`

## 🚀 How to Use Agents

### Quick Access via Registry

```python
from agents.agent_registry import HemingwixAgentRegistry, create_agent_launcher

# Initialize registry
registry = HemingwixAgentRegistry("/path/to/project")

# Launch an agent
launcher = create_agent_launcher()
result = launcher("character_development", "Help me develop Ned's character arc")

print(result["launch_message"])
print("Specialty:", result["specialty"])
```

### Direct Agent Access

Each agent has a dedicated markdown file with:
- **Agent Prompt**: Ready-to-use system prompt
- **Capabilities**: Detailed skill list
- **Usage Examples**: Common use cases
- **Integration Points**: How it connects with Hemingwix systems

### Agent Categories by Use Case

**📝 Writing New Content**
- Character Development Agent → Plot Structure Agent → Dialogue Specialist

**🔍 Improving Existing Content** 
- Research Assistant → Character Development → Dialogue Specialist

**🛠️ Technical Issues**
- MCP Integration Specialist → Database Design Agent → DevOps Agent

**📊 Project Management**
- Novel Planning Agent → Content Organization Agent

## 🎯 Agent Selection Guide

### For Story Development
- **Characters feeling flat?** → Character Development Agent
- **Plot not working?** → Plot Structure Agent  
- **Dialogue sounds artificial?** → Dialogue Specialist Agent
- **Need factual accuracy?** → Research Assistant Agent

### For Technical Issues
- **MCP server problems?** → MCP Integration Specialist
- **Database performance issues?** → Database Design Agent
- **Code quality concerns?** → Code Review Agent
- **Deployment challenges?** → DevOps Agent

### For Project Management
- **Behind schedule?** → Novel Planning Agent
- **Files disorganized?** → Content Organization Agent

## 🔄 Agent Workflows

### Collaborative Agent Chains

**New Chapter Workflow:**
1. Novel Planning Agent → Plan chapter goals and structure
2. Research Assistant → Gather necessary background information
3. Character Development Agent → Review character arcs for chapter
4. Plot Structure Agent → Confirm plot beats and pacing
5. Dialogue Specialist → Review character voice and conversations

**Technical Issue Resolution:**
1. Code Review Agent → Identify issues and improvements
2. Database Design Agent → Optimize data structures if needed
3. DevOps Agent → Implement deployment and monitoring solutions

## 📊 Registry Statistics

- **Total Agents**: 10 specialized assistants
- **Novel Writing**: 4 agents
- **Technical**: 4 agents  
- **Project Management**: 2 agents
- **Total Capabilities**: 50+ specialized skills
- **Integration Points**: Full Hemingwix system coverage

## 🛠️ Maintenance

### Adding New Agents
1. Create agent markdown file in appropriate category directory
2. Follow the established template format
3. Run `agent_registry.py` to update the registry
4. Test agent integration with existing systems

### Updating Agents
1. Modify the agent's markdown file
2. Update capabilities or integration points as needed
3. Regenerate registry with `agent_registry.py`

## 🎮 Quick Commands

```bash
# View all agents
python agents/agent_registry.py

# Export registry
python -c "from agents.agent_registry import HemingwixAgentRegistry; r = HemingwixAgentRegistry('.'); r.export_registry()"

# Search for agents
python -c "from agents.agent_registry import HemingwixAgentRegistry; r = HemingwixAgentRegistry('.'); print([a.name for a in r.search_agents('character')])"
```

---

**🎉 Your complete AI agent team is ready to assist with every aspect of your novel creation process!**