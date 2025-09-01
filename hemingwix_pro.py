#!/usr/bin/env python3
"""
Hemingwix Orchestrator Interface
Primary interaction with orchestrator agent + specialist swarm coordination
"""

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, send_from_directory
import sqlite3
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
import uuid
from werkzeug.utils import secure_filename
from anthropic import Anthropic
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs('uploads', exist_ok=True)

# Initialize Anthropic client
anthropic_client = Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

def init_database():
    """Initialize SQLite database for conversation storage"""
    conn = sqlite3.connect('hemingwix.db')
    cursor = conn.cursor()
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            agent_type TEXT NOT NULL DEFAULT 'orchestrator',
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Messages table  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            agent_source TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    
    # Agent interactions table (for tracking orchestrator delegations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            task_description TEXT,
            agent_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id),
            FOREIGN KEY (message_id) REFERENCES messages (id)
        )
    ''')
    
    # Files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_hash TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_type TEXT,
            description TEXT,
            document_category TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_conversations():
    """Get all conversations with latest message info"""
    conn = sqlite3.connect('hemingwix.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.agent_type, c.title, c.updated_at,
               (SELECT COUNT(*) FROM messages WHERE conversation_id = c.id) as message_count
        FROM conversations c
        ORDER BY c.updated_at DESC
        LIMIT 20
    ''')
    conversations = cursor.fetchall()
    conn.close()
    return conversations

def get_conversation_messages(conversation_id):
    """Get all messages for a conversation with agent source info"""
    conn = sqlite3.connect('hemingwix.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sender, content, timestamp, agent_source 
        FROM messages 
        WHERE conversation_id = ? 
        ORDER BY timestamp ASC
    ''', (conversation_id,))
    messages = cursor.fetchall()
    conn.close()
    return messages

def save_message(conversation_id, sender, content, agent_source=None):
    """Save a message to the database"""
    conn = sqlite3.connect('hemingwix.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (conversation_id, sender, content, agent_source)
        VALUES (?, ?, ?, ?)
    ''', (conversation_id, sender, content, agent_source))
    
    message_id = cursor.lastrowid
    
    # Update conversation timestamp
    cursor.execute('''
        UPDATE conversations SET updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (conversation_id,))
    
    conn.commit()
    conn.close()
    return message_id

def create_conversation(agent_type, title):
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    conn = sqlite3.connect('hemingwix.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (id, agent_type, title)
        VALUES (?, ?, ?)
    ''', (conversation_id, agent_type, title))
    conn.commit()
    conn.close()
    return conversation_id

def log_agent_interaction(conversation_id, message_id, agent_name, task, response):
    """Log orchestrator's interaction with specialist agents"""
    conn = sqlite3.connect('hemingwix.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO agent_interactions (conversation_id, message_id, agent_name, task_description, agent_response)
        VALUES (?, ?, ?, ?, ?)
    ''', (conversation_id, message_id, agent_name, task, response))
    conn.commit()
    conn.close()

# Main dashboard with orchestrator focus
@app.route('/')
def dashboard():
    conversations = get_conversations()
    return render_template_string(ORCHESTRATOR_DASHBOARD, conversations=conversations)

# Primary orchestrator chat interface
@app.route('/orchestrator')
def orchestrator_chat():
    conversation_id = request.args.get('conversation_id')
    messages = []
    
    if conversation_id:
        messages = get_conversation_messages(conversation_id)
    
    return render_template_string(ORCHESTRATOR_CHAT, 
                                conversation_id=conversation_id,
                                messages=messages)

# Specialist agent access
@app.route('/agents')
def agents():
    return render_template_string(AGENTS_TEMPLATE)

# Individual agent chat
@app.route('/chat/<agent_name>')
def specialist_chat(agent_name):
    conversation_id = request.args.get('conversation_id')
    messages = []
    
    if conversation_id:
        messages = get_conversation_messages(conversation_id)
    
    return render_template_string(SPECIALIST_CHAT, 
                                agent_name=agent_name, 
                                conversation_id=conversation_id,
                                messages=messages)

# API: Start new orchestrator conversation
@app.route('/api/orchestrator/new', methods=['POST'])
def new_orchestrator_conversation():
    data = request.json
    title = data.get('title', "New Writing Session")
    
    conversation_id = create_conversation('orchestrator', title)
    return jsonify({'conversation_id': conversation_id})

# API: Orchestrator chat endpoint with agent delegation
@app.route('/api/orchestrator/chat', methods=['POST'])
def orchestrator_chat_api():
    data = request.json
    message = data.get('message')
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        conversation_id = create_conversation('orchestrator', f"Session: {message[:30]}...")
    
    # Save user message
    save_message(conversation_id, 'user', message)
    
    # Get conversation history for context
    messages = get_conversation_messages(conversation_id)
    
    # Orchestrator processes the request using Anthropic API
    orchestrator_response = orchestrator_process_request_ai(message, messages, conversation_id)
    
    # Save orchestrator response
    message_id = save_message(conversation_id, 'orchestrator', orchestrator_response['response'], 'orchestrator')
    
    # Log agent interactions if any
    for interaction in orchestrator_response.get('agent_interactions', []):
        log_agent_interaction(conversation_id, message_id, 
                            interaction['agent'], 
                            interaction['task'], 
                            interaction['response'])
    
    return jsonify({
        'response': orchestrator_response['response'],
        'conversation_id': conversation_id,
        'agent_interactions': orchestrator_response.get('agent_interactions', [])
    })

# API: Individual agent chat
@app.route('/api/agent/chat', methods=['POST'])
def agent_chat_api():
    data = request.json
    agent = data.get('agent')
    message = data.get('message')
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        conversation_id = create_conversation(agent, f"{agent}: {message[:30]}...")
    
    # Save user message
    save_message(conversation_id, 'user', message)
    
    # Get conversation history for context
    messages = get_conversation_messages(conversation_id)
    
    # Direct agent response using AI
    response = generate_specialist_response_ai(agent, message, messages, conversation_id)
    
    # Save agent response
    save_message(conversation_id, 'agent', response, agent)
    
    return jsonify({
        'response': response,
        'conversation_id': conversation_id
    })

# File upload endpoint
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    category = request.form.get('category', 'general')
    description = request.form.get('description', '')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filename)[1]
        stored_filename = f"{file_id}{file_ext}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
        file.save(file_path)
        
        # Calculate file hash and size
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
            file_size = os.path.getsize(file_path)
        
        # Save file info to database
        conn = sqlite3.connect('hemingwix.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO uploaded_files (id, filename, original_name, file_size, file_hash, file_type, description, document_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (file_id, stored_filename, filename, file_size, file_hash, file_ext, description, category))
        conn.commit()
        conn.close()
        
        return jsonify({
            'file_id': file_id,
            'filename': filename,
            'size': file_size,
            'category': category,
            'message': f'File "{filename}" uploaded successfully to {category}!'
        })

def orchestrator_process_request_ai(user_message: str, conversation_history: List, conversation_id: str) -> Dict[str, Any]:
    """Use Anthropic API to process user request as an AI orchestrator"""
    
    # Build conversation context
    context_messages = []
    for msg in conversation_history[-10:]:  # Last 10 messages for context
        role = "user" if msg[0] == "user" else "assistant"
        context_messages.append(f"{role}: {msg[1]}")
    
    system_prompt = """You are an AI Writing Orchestrator for the novel "Broken Drill". You coordinate multiple specialist agents to provide comprehensive novel writing assistance.

Your specialist agents include:
- Character Development Specialist: Deep character psychology, backstories, motivations, and character arcs
- Plot Structure Specialist: Story architecture, pacing, narrative beats, three-act structure
- Dialogue Specialist: Character voice, subtext, conversation flow, authentic dialogue
- Research Assistant: Fact-checking, world-building details, source verification

When responding:
1. Analyze the user's request to determine which aspects need attention
2. Provide a comprehensive response that addresses multiple angles when relevant
3. Structure your response clearly with sections for different aspects
4. Be specific and actionable in your guidance
5. Reference the "Broken Drill" novel context when applicable

Format your response with clear sections using markdown formatting."""

    try:
        # Create the message for Anthropic API
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Previous conversation:\n{chr(10).join(context_messages[-5:]) if context_messages else 'No previous context'}\n\nCurrent request: {user_message}"
                }
            ]
        )
        
        # Extract the response text
        response_text = response.content[0].text
        
        print("CLAUDE RESPONSE: ", response_text)

        # Simulate agent interactions for UI consistency
        agent_interactions = []
        
        # Determine which "agents" were involved based on content
        if any(word in user_message.lower() for word in ['character', 'protagonist', 'personality']):
            agent_interactions.append({
                'agent': 'character',
                'task': 'Character analysis',
                'response': 'Provided character development insights'
            })
        
        if any(word in user_message.lower() for word in ['plot', 'story', 'structure', 'chapter']):
            agent_interactions.append({
                'agent': 'plot',
                'task': 'Plot structure analysis',
                'response': 'Provided plot structure guidance'
            })
        
        if any(word in user_message.lower() for word in ['dialogue', 'conversation', 'says', 'voice']):
            agent_interactions.append({
                'agent': 'dialogue',
                'task': 'Dialogue crafting',
                'response': 'Provided dialogue expertise'
            })
        
        if any(word in user_message.lower() for word in ['research', 'facts', 'realistic', 'accurate']):
            agent_interactions.append({
                'agent': 'research',
                'task': 'Research and verification',
                'response': 'Provided research assistance'
            })
        
        return {
            'response': response_text,
            'agent_interactions': agent_interactions
        }
        
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        # Fallback response
        return {
            'response': f"I apologize, but I encountered an error while processing your request. Please ensure your ANTHROPIC_API_KEY environment variable is set correctly. Error: {str(e)}",
            'agent_interactions': []
        }

def orchestrator_process_request(user_message, conversation_id):
    """Orchestrator analyzes request and coordinates specialist agents"""
    
    # Analyze the user's request to determine which agents to involve
    analysis = analyze_user_request(user_message)
    
    agent_interactions = []
    
    # Delegate to relevant specialist agents
    for agent_task in analysis['required_agents']:
        agent_name = agent_task['agent']
        task_description = agent_task['task']
        
        # Get response from specialist
        specialist_response = generate_specialist_response(agent_name, task_description, conversation_id)
        
        agent_interactions.append({
            'agent': agent_name,
            'task': task_description,
            'response': specialist_response
        })
    
    # Orchestrator synthesizes responses into cohesive answer
    synthesized_response = synthesize_agent_responses(user_message, agent_interactions, analysis)
    
    return {
        'response': synthesized_response,
        'agent_interactions': agent_interactions
    }

def analyze_user_request(message):
    """Analyze user message to determine which specialist agents to involve"""
    
    # Simple keyword-based analysis (would be more sophisticated in real implementation)
    message_lower = message.lower()
    required_agents = []
    
    # Character-related keywords
    if any(word in message_lower for word in ['character', 'protagonist', 'dialogue', 'motivation', 'personality', 'backstory']):
        if any(word in message_lower for word in ['dialogue', 'conversation', 'says', 'voice', 'speech']):
            required_agents.append({
                'agent': 'dialogue',
                'task': f"Help with dialogue aspects of: {message}"
            })
        else:
            required_agents.append({
                'agent': 'character',
                'task': f"Develop character elements for: {message}"
            })
    
    # Plot-related keywords
    if any(word in message_lower for word in ['plot', 'story', 'structure', 'chapter', 'pacing', 'conflict', 'climax', 'outline']):
        required_agents.append({
            'agent': 'plot',
            'task': f"Analyze plot structure for: {message}"
        })
    
    # Research-related keywords
    if any(word in message_lower for word in ['research', 'facts', 'realistic', 'authentic', 'verify', 'sources', 'accurate']):
        required_agents.append({
            'agent': 'research',
            'task': f"Research requirements for: {message}"
        })
    
    # If no specific agents identified, use character and plot as defaults for novel work
    if not required_agents:
        required_agents = [
            {'agent': 'character', 'task': f"Character perspective on: {message}"},
            {'agent': 'plot', 'task': f"Plot implications of: {message}"}
        ]
    
    return {
        'user_intent': 'novel_writing_assistance',
        'complexity': 'multi_agent' if len(required_agents) > 1 else 'single_agent',
        'required_agents': required_agents
    }

def synthesize_agent_responses(user_message, agent_interactions, analysis):
    """Orchestrator synthesizes specialist responses into cohesive answer"""
    
    if not agent_interactions:
        return "I'm here to help coordinate your novel writing. What aspect of 'Broken Drill' would you like to work on?"
    
    # Build synthesized response
    response_parts = [
        f"I've coordinated with my specialist team to address your question about: '{user_message}'\n"
    ]
    
    if len(agent_interactions) > 1:
        response_parts.append("**Multi-Agent Analysis:**\n")
    
    for interaction in agent_interactions:
        agent_name = interaction['agent'].replace('_', ' ').title()
        response_parts.append(f"**{agent_name} Specialist Input:**")
        response_parts.append(f"{interaction['response']}\n")
    
    # Add orchestrator synthesis
    response_parts.append("\n**Coordinated Recommendation:**")
    
    if analysis['complexity'] == 'multi_agent':
        response_parts.append(
            "Based on input from my specialist team, I recommend approaching this systematically. "
            "The character and plot elements need to work together - character decisions should drive plot events, "
            "and plot pressures should reveal character depth. Would you like me to coordinate a specific aspect further, "
            "or shall we dive deeper into any particular specialist's recommendations?"
        )
    else:
        response_parts.append(
            "My specialist has provided focused guidance above. Would you like me to coordinate with additional "
            "specialists to explore related aspects, or shall we develop this direction further?"
        )
    
    return "\n".join(response_parts)

def generate_specialist_response_ai(agent_name: str, message: str, conversation_history: List, conversation_id: str) -> str:
    """Generate response from specialist agent using Anthropic API"""
    
    # Build conversation context
    context_messages = []
    for msg in conversation_history[-10:]:  # Last 10 messages for context
        role = "user" if msg[0] == "user" else "assistant"
        context_messages.append(f"{role}: {msg[1]}")
    
    # Agent-specific system prompts
    agent_prompts = {
        'character': """You are a Character Development Specialist for the novel "Broken Drill". You provide deep expertise in:
- Character psychology and internal motivations
- Backstory development and character history
- Character arcs and transformational journeys
- Personality traits and behavioral patterns
- Internal conflicts and contradictions
- Relationship dynamics between characters

Focus on psychological depth, authentic motivations, and how characters drive the narrative through their choices and growth.""",
        
        'plot': """You are a Plot Structure Specialist for the novel "Broken Drill". You provide expertise in:
- Three-act structure and story architecture
- Narrative pacing and tension building
- Plot points, beats, and turning points
- Conflict escalation and resolution
- Subplot integration and parallel narratives
- Cause-and-effect story logic
- Climax construction and payoffs

Focus on structural integrity, narrative momentum, and how plot serves both entertainment and thematic purposes.""",
        
        'dialogue': """You are a Dialogue Specialist for the novel "Broken Drill". You provide expertise in:
- Unique character voices and speech patterns
- Subtext and what characters don't say
- Dialogue that reveals character and advances plot
- Natural conversation flow and interruptions
- Regional dialects and professional jargon
- Emotional undertones in conversation
- Power dynamics through dialogue

Focus on authentic voices, meaningful subtext, and dialogue that serves multiple narrative purposes simultaneously.""",
        
        'research': """You are a Research Assistant for the novel "Broken Drill". You provide expertise in:
- Fact-checking and verification strategies
- Historical and cultural accuracy
- Technical and professional details
- World-building consistency
- Source credibility assessment
- Research methodologies for fiction
- Balancing accuracy with dramatic needs

Focus on enhancing authenticity, finding credible sources, and knowing when accuracy serves the story versus when dramatic license is appropriate."""
    }
    
    system_prompt = agent_prompts.get(agent_name, f"You are a {agent_name.replace('_', ' ').title()} Specialist for the novel 'Broken Drill'. Provide focused expertise in your area of specialization.")
    
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Previous conversation:\n{chr(10).join(context_messages[-3:]) if context_messages else 'No previous context'}\n\nCurrent request: {message}"
                }
            ]
        )
        
        return response.content[0].text
        
    except Exception as e:
        print(f"Error calling Anthropic API for {agent_name}: {e}")
        return f"I apologize, but I encountered an error while processing your request. Please ensure your ANTHROPIC_API_KEY environment variable is set correctly."

def generate_specialist_response(agent_name, message, conversation_id):
    """Generate response from individual specialist agent"""
    
    # Get conversation context
    messages = get_conversation_messages(conversation_id) if conversation_id else []
    context = f"Based on our conversation history ({len(messages)} messages)"
    
    responses = {
        'character': f"""**Character Development Analysis ({context}):**

For your "Broken Drill" character work around '{message}':

**Psychological Foundation:**
- What core wound or desire drives this character?
- How do their past experiences shape current decision-making?
- What internal contradictions create complexity?

**Character Arc Integration:**
- Where is this character at the story's beginning vs. end?
- What beliefs must they challenge or abandon?
- How do external plot events trigger internal change?

**Voice and Behavior Patterns:**
- What unique speech patterns or mannerisms distinguish them?
- How do they react under pressure vs. in comfort?
- What do they hide, and what do they reveal unconsciously?

**For "Broken Drill" specifically:** Consider how this character's development serves your story's central themes. How do their personal struggles mirror or contrast with the main conflict?

Next steps: Define their primary goal and the internal obstacle preventing them from achieving it.""",
        
        'plot': f"""**Plot Structure Analysis ({context}):**

Analyzing '{message}' within your "Broken Drill" narrative architecture:

**Three-Act Positioning:**
- **Act I (Setup):** How does this element establish stakes and character motivations?
- **Act II (Confrontation):** What escalating conflicts does this create or resolve?
- **Act III (Resolution):** How does this drive toward your climactic sequence?

**Narrative Beats:**
- **Inciting Incident:** What change does this represent?
- **Plot Points:** How does this shift the story's direction?
- **Midpoint:** Does this raise or lower the stakes?

**Pacing Considerations:**
- Does this moment accelerate or decelerate your narrative rhythm?
- How does it serve tension building vs. resolution?
- What questions does it answer, and what new questions does it raise?

**"Broken Drill" Integration:** Ensure this plot element serves your story's central conflict while advancing character development. Every scene should either advance plot or develop character—ideally both.

Recommendation: Map how this connects to your next three story beats.""",
        
        'dialogue': f"""**Dialogue Craft Analysis ({context}):**

Examining dialogue elements in '{message}' for your "Broken Drill" characters:

**Character Voice Distinctiveness:**
- Does each character sound unique based on background, education, emotional state?
- Are their speech patterns consistent with established personality?
- How do they communicate differently under stress vs. relaxed states?

**Subtext and Tension:**
- What are characters NOT saying directly?
- How does underlying conflict drive the conversation?
- What hidden motivations influence their word choices?

**Dialogue Functions:**
- Does this conversation reveal character while advancing plot?
- How does it establish or shift relationships between characters?
- What information is conveyed naturally vs. forced exposition?

**Technical Craft:**
- Are dialogue tags minimal and effective?
- Does the rhythm match each character's speaking style?
- How do interruptions, pauses, and overlaps create realism?

**"Broken Drill" Application:** Each character should have a distinct speaking pattern that reflects their role in your story. How does their dialogue reveal their relationship to the central conflict?

Next: Share a specific dialogue passage for detailed voice refinement.""",
        
        'research': f"""**Research Strategy ({context}):**

Research approach for '{message}' to enhance "Broken Drill" authenticity:

**Authenticity Priorities:**
- What specific details need factual accuracy for reader credibility?
- Which elements can use dramatic license vs. strict realism?
- How do setting, time period, and character backgrounds affect research needs?

**Source Verification Strategy:**
- **Primary Sources:** Firsthand accounts, official documents, expert interviews
- **Secondary Analysis:** Academic papers, professional publications
- **Cross-Reference:** Multiple reliable sources to confirm details
- **Expert Consultation:** When specialized knowledge is crucial

**Research Categories:**
- **Technical/Professional:** How things actually work in your story's world
- **Cultural/Social:** Authentic behavior, language, customs for your setting
- **Historical:** Time period accuracy if relevant
- **Geographic:** Setting details that affect plot and character decisions

**"Broken Drill" Focus:** What specific research questions would strengthen your story's believability? Consider both major plot elements and small details that create immersion.

Priority: Identify your top 3 research questions and I'll guide you to credible source strategies."""
    }
    
    return responses.get(agent_name, f"As a specialist in {agent_name}, I'm ready to help with '{message}' for your 'Broken Drill' novel. What specific aspect would you like to explore?")

# Templates
ORCHESTRATOR_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hemingwix Novel Assistant - Orchestrator</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px 0;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }
        
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logo-text {
            font-size: 2em;
            font-weight: bold;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .orchestrator-badge {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 500;
        }
        
        .nav-buttons {
            display: flex;
            gap: 15px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            font-size: 1.1em;
            padding: 15px 30px;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            color: #333;
            border: 1px solid rgba(0,0,0,0.1);
        }
        
        .main-layout {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 20px;
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 30px;
            height: calc(100vh - 160px);
        }
        
        .sidebar {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            height: fit-content;
            max-height: 100%;
            overflow-y: auto;
        }
        
        .sidebar-section {
            margin-bottom: 30px;
        }
        
        .sidebar-title {
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .document-link {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px;
            border-radius: 8px;
            background: #f8f9fa;
            margin-bottom: 8px;
            cursor: pointer;
            transition: background 0.2s ease;
            text-decoration: none;
            color: #333;
            border: 1px solid #e9ecef;
        }
        
        .document-link:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        
        .document-icon {
            color: #667eea;
            width: 20px;
            text-align: center;
        }
        
        .main-content {
            display: grid;
            grid-template-rows: auto 1fr;
            gap: 20px;
        }
        
        .orchestrator-intro {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .orchestrator-intro h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.8em;
        }
        
        .orchestrator-intro p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 20px;
        }
        
        .conversation-history {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        
        .history-title {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .conversation-item {
            padding: 15px;
            border-radius: 8px;
            background: #f8f9fa;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid #e9ecef;
        }
        
        .conversation-item:hover {
            background: #e3f2fd;
            border-color: #667eea;
            transform: translateX(5px);
        }
        
        .conversation-title {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .conversation-meta {
            font-size: 0.85em;
            color: #666;
            display: flex;
            justify-content: space-between;
        }
        
        .agent-type-badge {
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75em;
            font-weight: 500;
        }
        
        .orchestrator-badge-small {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }
        
        .specialist-badge {
            background: #e9ecef;
            color: #666;
        }
        
        .empty-state {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 40px;
        }
        
        .specialist-access {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }
        
        .specialist-link {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 6px;
            background: #f8f9fa;
            margin-bottom: 5px;
            cursor: pointer;
            transition: background 0.2s ease;
            text-decoration: none;
            color: #666;
            font-size: 0.9em;
        }
        
        .specialist-link:hover {
            background: #e9ecef;
        }
        
        @media (max-width: 1024px) {
            .main-layout {
                grid-template-columns: 1fr;
                grid-template-rows: auto auto;
            }
            
            .sidebar {
                order: 2;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">
                <div class="logo-text">
                    <i class="fas fa-robot"></i> Hemingwix
                </div>
                <div class="orchestrator-badge">AI Orchestrator</div>
            </div>
            <div class="nav-buttons">
                <a href="/orchestrator" class="btn btn-primary">
                    <i class="fas fa-brain"></i> Start Writing Session
                </a>
                <button class="btn btn-secondary" onclick="uploadFile()">
                    <i class="fas fa-upload"></i> Upload
                </button>
            </div>
        </div>
    </div>
    
    <div class="main-layout">
        <div class="sidebar">
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <i class="fas fa-book"></i> "Broken Drill" Manuscript
                </div>
                <a href="#" class="document-link" onclick="alert('Notion integration coming soon!')">
                    <i class="fas fa-file-alt document-icon"></i>
                    <span>Current Draft</span>
                </a>
                <a href="#" class="document-link" onclick="alert('Notion integration coming soon!')">
                    <i class="fas fa-list document-icon"></i>
                    <span>Chapter Outline</span>
                </a>
                <a href="#" class="document-link" onclick="alert('Notion integration coming soon!')">
                    <i class="fas fa-sitemap document-icon"></i>
                    <span>Story Structure</span>
                </a>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <i class="fas fa-users"></i> Characters & World
                </div>
                <a href="#" class="document-link" onclick="alert('Notion integration coming soon!')">
                    <i class="fas fa-user document-icon"></i>
                    <span>Character Profiles</span>
                </a>
                <a href="#" class="document-link" onclick="alert('Notion integration coming soon!')">
                    <i class="fas fa-globe document-icon"></i>
                    <span>World Building</span>
                </a>
                <a href="#" class="document-link" onclick="alert('Notion integration coming soon!')">
                    <i class="fas fa-map document-icon"></i>
                    <span>Timeline & Events</span>
                </a>
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <i class="fas fa-search"></i> Research & Notes
                </div>
                <a href="#" class="document-link" onclick="alert('Notion integration coming soon!')">
                    <i class="fas fa-bookmark document-icon"></i>
                    <span>Research Notes</span>
                </a>
                <a href="#" class="document-link" onclick="alert('Notion integration coming soon!')">
                    <i class="fas fa-lightbulb document-icon"></i>
                    <span>Ideas & Inspiration</span>
                </a>
            </div>
            
            <div class="sidebar-section specialist-access">
                <div class="sidebar-title" style="font-size: 0.9em; color: #666;">
                    <i class="fas fa-cogs"></i> Direct Agent Access
                </div>
                <a href="/agents" class="specialist-link">
                    <i class="fas fa-tools"></i>
                    <span>Specialist Agents</span>
                </a>
            </div>
        </div>
        
        <div class="main-content">
            <div class="orchestrator-intro">
                <h2><i class="fas fa-brain"></i> AI Writing Orchestrator</h2>
                <p>I coordinate your specialized AI agents to provide comprehensive novel writing assistance. Ask me complex questions about your "Broken Drill" project, and I'll delegate tasks to character development, plot structure, dialogue, and research specialists, then synthesize their insights into cohesive guidance.</p>
                <a href="/orchestrator" class="btn btn-primary">
                    <i class="fas fa-comments"></i> Begin Writing Session
                </a>
            </div>
            
            <div class="conversation-history">
                <h2 class="history-title">
                    <i class="fas fa-history"></i> Recent Writing Sessions
                </h2>
                {% if conversations %}
                    {% for conv in conversations %}
                    <div class="conversation-item" onclick="openConversation('{{conv[1]}}', '{{conv[0]}}')">
                        <div class="conversation-title">{{conv[2]}}</div>
                        <div class="conversation-meta">
                            <span>
                                <span class="agent-type-badge {% if conv[1] == 'orchestrator' %}orchestrator-badge-small{% else %}specialist-badge{% endif %}">
                                    {{conv[1].replace('_', ' ').title()}}
                                </span>
                                <i class="fas fa-comments"></i> {{conv[4]}} messages
                            </span>
                            <span>{{conv[3][:10]}}</span>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-state">
                        <i class="fas fa-comments" style="font-size: 3em; margin-bottom: 15px; opacity: 0.3;"></i>
                        <p>No writing sessions yet. Start a conversation with the orchestrator!</p>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <input type="file" id="fileInput" style="display: none;" onchange="handleFileUpload()" accept=".txt,.doc,.docx,.pdf,.md">
    
    <script>
        function openConversation(agentType, conversationId) {
            if (agentType === 'orchestrator') {
                window.location.href = `/orchestrator?conversation_id=${conversationId}`;
            } else {
                window.location.href = `/chat/${agentType}?conversation_id=${conversationId}`;
            }
        }
        
        function uploadFile() {
            document.getElementById('fileInput').click();
        }
        
        async function handleFileUpload() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('category', 'manuscript');
            formData.append('description', 'Uploaded from dashboard');
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    alert(result.message);
                    location.reload();
                } else {
                    alert('Upload failed: ' + result.error);
                }
            } catch (error) {
                alert('Upload failed: ' + error.message);
            }
        }
    </script>
</body>
</html>
'''

ORCHESTRATOR_CHAT = '''
<!DOCTYPE html>
<html>
<head>
    <title>AI Writing Orchestrator - Hemingwix</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .back-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            text-decoration: none;
            backdrop-filter: blur(10px);
        }
        
        .orchestrator-info h1 {
            font-size: 1.5em;
            margin-bottom: 5px;
        }
        
        .orchestrator-info p {
            opacity: 0.9;
            font-size: 0.9em;
        }
        
        .agent-status {
            margin-left: auto;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .agent-indicator {
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.75em;
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
        }
        
        .chat-layout {
            flex: 1;
            display: grid;
            grid-template-columns: 1fr 300px;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .chat-main {
            display: flex;
            flex-direction: column;
            border-right: 1px solid #e9ecef;
        }
        
        .chat-messages {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            scroll-behavior: smooth;
        }
        
        .message {
            margin-bottom: 20px;
            padding: 15px 20px;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
            line-height: 1.5;
        }
        
        .user-message {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        
        .orchestrator-message {
            background: #f8f9fa;
            color: #333;
            border: 2px solid #667eea;
            border-bottom-left-radius: 4px;
            white-space: pre-line;
        }
        
        .agent-message {
            background: #fff3e0;
            color: #333;
            border: 1px solid #ffb74d;
            border-bottom-left-radius: 4px;
            white-space: pre-line;
            margin-left: 20px;
            max-width: 75%;
        }
        
        .message-time {
            font-size: 0.75em;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .agent-source {
            font-size: 0.8em;
            font-weight: bold;
            margin-bottom: 8px;
            color: #667eea;
        }
        
        .typing-indicator {
            display: none;
            padding: 20px;
            font-style: italic;
            color: #666;
            text-align: center;
        }
        
        .typing-dots::after {
            content: '';
            animation: dots 2s infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: ''; }
            40% { content: '.'; }
            60% { content: '..'; }
            80%, 100% { content: '...'; }
        }
        
        .chat-input-container {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            align-items: flex-end;
        }
        
        .chat-input {
            flex: 1;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 15px 20px;
            font-size: 1em;
            outline: none;
            resize: vertical;
            min-height: 50px;
            max-height: 120px;
            font-family: inherit;
        }
        
        .chat-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .send-button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 15px 25px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            height: 50px;
        }
        
        .send-button:hover:not(:disabled) {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .welcome-message {
            background: linear-gradient(45deg, #e3f2fd, #f3e5f5);
            border: 2px solid #667eea;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .welcome-message h3 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .sidebar-panel {
            background: #f8f9fa;
            padding: 20px;
            overflow-y: auto;
        }
        
        .panel-section {
            margin-bottom: 25px;
        }
        
        .panel-title {
            font-size: 0.9em;
            font-weight: bold;
            color: #666;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .agent-activity {
            font-size: 0.8em;
            color: #666;
            padding: 8px;
            background: white;
            border-radius: 6px;
            margin-bottom: 5px;
        }
        
        .context-info {
            font-size: 0.8em;
            color: #666;
            background: white;
            padding: 10px;
            border-radius: 6px;
        }
        
        @media (max-width: 1024px) {
            .chat-layout {
                grid-template-columns: 1fr;
            }
            
            .sidebar-panel {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="chat-header">
        <a href="/" class="back-btn">
            <i class="fas fa-arrow-left"></i>
        </a>
        <div class="orchestrator-info">
            <h1><i class="fas fa-brain"></i> AI Writing Orchestrator</h1>
            <p>Coordinating specialist agents for your "Broken Drill" novel</p>
        </div>
        <div class="agent-status">
            <div class="agent-indicator">
                <i class="fas fa-robot"></i> 4 Specialists Available
            </div>
        </div>
    </div>
    
    <div class="chat-layout">
        <div class="chat-main">
            <div class="chat-messages" id="chatMessages">
                {% if not messages %}
                <div class="welcome-message">
                    <h3><i class="fas fa-brain"></i> Welcome to your AI Writing Orchestrator!</h3>
                    <p>I coordinate your specialist agents to provide comprehensive novel writing assistance. Ask me complex questions about plot, characters, dialogue, or research - I'll delegate to the right experts and synthesize their insights.</p>
                    <p style="margin-top: 15px; font-size: 0.9em; opacity: 0.8;">Try: "I need help developing a detective character who's struggling with self-doubt while investigating a case that mirrors their own past trauma."</p>
                </div>
                {% else %}
                    {% for message in messages %}
                    <div class="message {% if message[0] == 'user' %}user-message{% elif message[3] == 'orchestrator' %}orchestrator-message{% else %}agent-message{% endif %}">
                        {% if message[3] and message[3] != 'orchestrator' %}
                        <div class="agent-source">{{message[3].replace('_', ' ').title()}} Specialist:</div>
                        {% endif %}
                        {{message[1]}}
                        <div class="message-time">{{message[2]}}</div>
                    </div>
                    {% endfor %}
                {% endif %}
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                <span class="typing-dots">Orchestrator is coordinating with specialists</span>
            </div>
            
            <div class="chat-input-container">
                <textarea 
                    id="chatInput" 
                    class="chat-input" 
                    placeholder="Ask me anything about your novel - I'll coordinate with the right specialists..."
                    onkeypress="handleKeyPress(event)"
                    rows="1"
                ></textarea>
                <button class="send-button" id="sendButton" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
        
        <div class="sidebar-panel">
            <div class="panel-section">
                <div class="panel-title">
                    <i class="fas fa-cogs"></i> Active Specialists
                </div>
                <div class="agent-activity">
                    <i class="fas fa-theater-masks" style="color: #667eea;"></i> Character Development
                </div>
                <div class="agent-activity">
                    <i class="fas fa-book-open" style="color: #667eea;"></i> Plot Structure
                </div>
                <div class="agent-activity">
                    <i class="fas fa-comments" style="color: #667eea;"></i> Dialogue Specialist
                </div>
                <div class="agent-activity">
                    <i class="fas fa-search" style="color: #667eea;"></i> Research Assistant
                </div>
            </div>
            
            <div class="panel-section">
                <div class="panel-title">
                    <i class="fas fa-info-circle"></i> Session Context
                </div>
                <div class="context-info" id="contextInfo">
                    Project: "Broken Drill" Novel<br>
                    Session: New<br>
                    Mode: Orchestrated Multi-Agent
                </div>
            </div>
            
            <div class="panel-section">
                <div class="panel-title">
                    <i class="fas fa-lightbulb"></i> Orchestrator Tips
                </div>
                <div class="context-info">
                    • Ask complex, multi-faceted questions<br>
                    • I'll delegate to relevant specialists<br>
                    • Responses synthesize multiple expert perspectives<br>
                    • For focused work, access specialists directly
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let conversationId = '{{conversation_id}}' || null;
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        const contextInfo = document.getElementById('contextInfo');
        
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function addMessage(text, isUser = false, agentSource = null, timestamp = null) {
            const messageDiv = document.createElement('div');
            let messageClass = 'message ';
            
            if (isUser) {
                messageClass += 'user-message';
            } else if (agentSource === 'orchestrator' || !agentSource) {
                messageClass += 'orchestrator-message';
            } else {
                messageClass += 'agent-message';
            }
            
            messageDiv.className = messageClass;
            
            let content = '';
            if (agentSource && agentSource !== 'orchestrator') {
                content += `<div class="agent-source">${agentSource.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase())} Specialist:</div>`;
            }
            
            content += text.replace(/\\n/g, '<br>');
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = timestamp || new Date().toLocaleTimeString();
            
            messageDiv.innerHTML = content;
            messageDiv.appendChild(timeDiv);
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function showTyping() {
            typingIndicator.style.display = 'block';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function hideTyping() {
            typingIndicator.style.display = 'none';
        }
        
        function updateContextInfo(messageCount) {
            contextInfo.innerHTML = `
                Project: "Broken Drill" Novel<br>
                Messages: ${messageCount}<br>
                Mode: Orchestrated Multi-Agent
            `;
        }
        
        async function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            chatInput.value = '';
            sendButton.disabled = true;
            showTyping();
            
            try {
                const response = await fetch('/api/orchestrator/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: conversationId
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                setTimeout(() => {
                    hideTyping();
                    addMessage(data.response, false, 'orchestrator');
                    conversationId = data.conversation_id;
                    
                    // Update context info
                    const messageCount = chatMessages.querySelectorAll('.message').length;
                    updateContextInfo(messageCount);
                    
                    sendButton.disabled = false;
                    chatInput.focus();
                }, 1500 + Math.random() * 2000);
                
            } catch (error) {
                console.error('Error:', error);
                hideTyping();
                addMessage('Sorry, I encountered an error coordinating with my specialist team. Please try again!', false, 'orchestrator');
                sendButton.disabled = false;
                chatInput.focus();
            }
        }
        
        // Auto-resize textarea
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Focus on input when page loads
        window.addEventListener('load', () => {
            chatInput.focus();
        });
    </script>
</body>
</html>
'''

AGENTS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Specialist Agents - Hemingwix</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 50px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .back-btn {
            position: absolute;
            top: 30px;
            left: 30px;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            text-decoration: none;
            backdrop-filter: blur(10px);
        }
        
        .orchestrator-note {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
            color: white;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
        }
        
        .agent-card {
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .agent-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }
        
        .agent-icon {
            font-size: 3.5em;
            margin-bottom: 15px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .agent-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 12px;
            color: #333;
        }
        
        .agent-description {
            color: #666;
            line-height: 1.5;
            margin-bottom: 20px;
            font-size: 0.95em;
        }
        
        .agent-specialty {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 0.8em;
            color: #667eea;
            font-weight: 500;
            margin-bottom: 20px;
        }
        
        .chat-direct-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.3s ease;
            width: 100%;
        }
        
        .chat-direct-btn:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <a href="/" class="back-btn">
        <i class="fas fa-arrow-left"></i> Back to Dashboard
    </a>
    
    <div class="container">
        <div class="header">
            <h1>Specialist Agent Access</h1>
            <p>Direct access to individual writing specialists</p>
        </div>
        
        <div class="orchestrator-note">
            <p><strong>💡 Tip:</strong> For complex questions involving multiple aspects of your novel, use the <strong>Orchestrator</strong> instead. These specialists are for focused, specific assistance in their areas of expertise.</p>
        </div>
        
        <div class="agents-grid">
            <div class="agent-card" onclick="startDirectChat('character')">
                <div class="agent-icon">
                    <i class="fas fa-theater-masks"></i>
                </div>
                <h3 class="agent-title">Character Development Specialist</h3>
                <div class="agent-specialty">Psychology • Motivation • Character Arcs</div>
                <p class="agent-description">
                    Deep dive into character psychology, backstories, motivations, and development arcs. Creates rich, authentic personalities with internal conflicts.
                </p>
                <button class="chat-direct-btn">Chat Directly</button>
            </div>
            
            <div class="agent-card" onclick="startDirectChat('plot')">
                <div class="agent-icon">
                    <i class="fas fa-book-open"></i>
                </div>
                <h3 class="agent-title">Plot Structure Specialist</h3>
                <div class="agent-specialty">Story Architecture • Pacing • Narrative Beats</div>
                <p class="agent-description">
                    Master story structure, three-act development, pacing control, and narrative beats that create compelling, well-organized storytelling.
                </p>
                <button class="chat-direct-btn">Chat Directly</button>
            </div>
            
            <div class="agent-card" onclick="startDirectChat('dialogue')">
                <div class="agent-icon">
                    <i class="fas fa-comments"></i>
                </div>
                <h3 class="agent-title">Dialogue Specialist</h3>
                <div class="agent-specialty">Character Voice • Subtext • Conversation Flow</div>
                <p class="agent-description">
                    Craft authentic character voices, natural conversation flow, meaningful subtext, and dialogue that reveals character while advancing plot.
                </p>
                <button class="chat-direct-btn">Chat Directly</button>
            </div>
            
            <div class="agent-card" onclick="startDirectChat('research')">
                <div class="agent-icon">
                    <i class="fas fa-search"></i>
                </div>
                <h3 class="agent-title">Research Assistant</h3>
                <div class="agent-specialty">Fact-Checking • World-Building • Source Verification</div>
                <p class="agent-description">
                    Find credible sources, verify facts, research world-building details, and ensure authenticity in technical, historical, or cultural elements.
                </p>
                <button class="chat-direct-btn">Chat Directly</button>
            </div>
        </div>
    </div>
    
    <script>
        function startDirectChat(agent) {
            window.location.href = `/chat/${agent}`;
        }
    </script>
</body>
</html>
'''

SPECIALIST_CHAT = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{agent_name.replace('_', ' ').title()}} Specialist - Hemingwix</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .back-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            text-decoration: none;
            backdrop-filter: blur(10px);
        }
        
        .agent-info h1 {
            font-size: 1.5em;
            margin-bottom: 5px;
        }
        
        .agent-info p {
            opacity: 0.9;
            font-size: 0.9em;
        }
        
        .specialist-badge {
            margin-left: auto;
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            border-radius: 15px;
            font-size: 0.8em;
            backdrop-filter: blur(10px);
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .chat-messages {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            scroll-behavior: smooth;
        }
        
        .message {
            margin-bottom: 20px;
            padding: 15px 20px;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
            line-height: 1.5;
        }
        
        .user-message {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        
        .agent-message {
            background: #fff3e0;
            color: #333;
            border: 1px solid #ffb74d;
            border-bottom-left-radius: 4px;
            white-space: pre-line;
        }
        
        .message-time {
            font-size: 0.75em;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .typing-indicator {
            display: none;
            padding: 20px;
            font-style: italic;
            color: #666;
            text-align: center;
        }
        
        .typing-dots::after {
            content: '';
            animation: dots 2s infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: ''; }
            40% { content: '.'; }
            60% { content: '..'; }
            80%, 100% { content: '...'; }
        }
        
        .chat-input-container {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            align-items: flex-end;
        }
        
        .chat-input {
            flex: 1;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 15px 20px;
            font-size: 1em;
            outline: none;
            resize: vertical;
            min-height: 50px;
            max-height: 120px;
            font-family: inherit;
        }
        
        .chat-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .send-button {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 15px 25px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            height: 50px;
        }
        
        .send-button:hover:not(:disabled) {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .specialist-welcome {
            background: linear-gradient(45deg, #fff3e0, #f3e5f5);
            border: 2px solid #ffb74d;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .specialist-welcome h3 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .orchestrator-suggestion {
            background: #e3f2fd;
            border: 1px solid #667eea;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="chat-header">
        <a href="/agents" class="back-btn">
            <i class="fas fa-arrow-left"></i>
        </a>
        <div class="agent-info">
            <h1><i class="fas fa-user-cog"></i> {{agent_name.replace('_', ' ').title()}} Specialist</h1>
            <p>Direct consultation mode - Focused expertise</p>
        </div>
        <div class="specialist-badge">
            Direct Access
        </div>
    </div>
    
    <div class="chat-container">
        <div class="chat-messages" id="chatMessages">
            {% if not messages %}
            <div class="orchestrator-suggestion">
                <strong>💡 Tip:</strong> For complex questions involving multiple writing aspects, consider using the <a href="/orchestrator">AI Orchestrator</a> instead. I specialize in {{agent_name.replace('_', ' ')}} and provide focused expertise in this area.
            </div>
            
            <div class="specialist-welcome">
                <h3>{{agent_name.replace('_', ' ').title()}} Specialist Ready</h3>
                <p>I provide focused expertise in {{agent_name.replace('_', ' ')}} for your "Broken Drill" novel. Ask me specific questions in my area of specialization.</p>
            </div>
            {% else %}
                {% for message in messages %}
                <div class="message {% if message[0] == 'user' %}user-message{% else %}agent-message{% endif %}">
                    {{message[1]}}
                    <div class="message-time">{{message[2]}}</div>
                </div>
                {% endfor %}
            {% endif %}
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <span class="typing-dots">Specialist is analyzing</span>
        </div>
        
        <div class="chat-input-container">
            <textarea 
                id="chatInput" 
                class="chat-input" 
                placeholder="Ask me specific questions about {{agent_name.replace('_', ' ')}}..."
                onkeypress="handleKeyPress(event)"
                rows="1"
            ></textarea>
            <button class="send-button" id="sendButton" onclick="sendMessage()">
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
    </div>
    
    <script>
        const agentName = '{{agent_name}}';
        let conversationId = '{{conversation_id}}' || null;
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function addMessage(text, isUser = false, timestamp = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'agent-message'}`;
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = timestamp || new Date().toLocaleTimeString();
            
            messageDiv.textContent = text;
            messageDiv.appendChild(timeDiv);
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function showTyping() {
            typingIndicator.style.display = 'block';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function hideTyping() {
            typingIndicator.style.display = 'none';
        }
        
        async function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            chatInput.value = '';
            sendButton.disabled = true;
            showTyping();
            
            try {
                const response = await fetch('/api/agent/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        agent: agentName,
                        message: message,
                        conversation_id: conversationId
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                setTimeout(() => {
                    hideTyping();
                    addMessage(data.response);
                    conversationId = data.conversation_id;
                    sendButton.disabled = false;
                    chatInput.focus();
                }, 1000 + Math.random() * 1500);
                
            } catch (error) {
                console.error('Error:', error);
                hideTyping();
                addMessage('Sorry, I encountered an error. Please try again!');
                sendButton.disabled = false;
                chatInput.focus();
            }
        }
        
        // Auto-resize textarea
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Focus on input when page loads
        window.addEventListener('load', () => {
            chatInput.focus();
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    init_database()
    print("Starting Hemingwix Orchestrator Interface...")
    print("Dashboard: http://localhost:8000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=8000, host='0.0.0.0')