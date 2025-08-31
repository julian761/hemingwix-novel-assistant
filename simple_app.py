from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Main page with agent selection
@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Hemingwix Novel Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .agent-button { background: #4CAF50; color: white; padding: 15px 30px; margin: 10px 0; border: none; border-radius: 5px; cursor: pointer; display: block; width: 100%; text-decoration: none; text-align: center; }
        .agent-button:hover { background: #45a049; }
        h1 { text-align: center; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hemingwix Novel Assistant</h1>
        <p>Click an agent to start chatting:</p>
        <a href="/chat/character" class="agent-button">Character Development Agent</a>
        <a href="/chat/plot" class="agent-button">Plot Structure Agent</a>
        <a href="/chat/dialogue" class="agent-button">Dialogue Specialist</a>
        <a href="/chat/research" class="agent-button">Research Assistant</a>
    </div>
</body>
</html>
'''

# Chat page for each agent
@app.route('/chat/<agent_name>')
def chat_page(agent_name):
    agent_titles = {
        'character': 'Character Development Agent',
        'plot': 'Plot Structure Agent', 
        'dialogue': 'Dialogue Specialist',
        'research': 'Research Assistant'
    }
    
    title = agent_titles.get(agent_name, 'AI Agent')
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Chat with {title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; background: #f5f5f5; }}
        .chat-container {{ max-width: 800px; margin: 20px auto; background: white; border-radius: 10px; height: 80vh; display: flex; flex-direction: column; }}
        .chat-header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .chat-messages {{ flex: 1; padding: 20px; overflow-y: auto; }}
        .message {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
        .user-message {{ background: #e3f2fd; margin-left: 50px; }}
        .agent-message {{ background: #f1f8e9; margin-right: 50px; }}
        .chat-input {{ display: flex; padding: 20px; }}
        .chat-input input {{ flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .chat-input button {{ padding: 10px 20px; margin-left: 10px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }}
        .back-btn {{ background: #666; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px; }}
    </style>
</head>
<body>
    <a href="/" class="back-btn">← Back to Agents</a>
    <div class="chat-container">
        <div class="chat-header">
            <h2>{title}</h2>
            <p>Ask me anything about your novel!</p>
        </div>
        <div class="chat-messages" id="messages">
            <div class="message agent-message">Hello! I'm your {title}. How can I help you with your "Broken Drill" novel today?</div>
        </div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="if(event.key==='Enter') sendMessage()">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const agentName = '{agent_name}';
        
        function sendMessage() {{
            const input = document.getElementById('messageInput');
            const messages = document.getElementById('messages');
            const userMessage = input.value.trim();
            
            if (!userMessage) return;
            
            // Add user message
            const userDiv = document.createElement('div');
            userDiv.className = 'message user-message';
            userDiv.textContent = userMessage;
            messages.appendChild(userDiv);
            
            // Clear input
            input.value = '';
            
            // Send to server and get response
            fetch('/api/chat', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ agent: agentName, message: userMessage }})
            }})
            .then(response => response.json())
            .then(data => {{
                const agentDiv = document.createElement('div');
                agentDiv.className = 'message agent-message';
                agentDiv.textContent = data.response;
                messages.appendChild(agentDiv);
                messages.scrollTop = messages.scrollHeight;
            }});
            
            messages.scrollTop = messages.scrollHeight;
        }}
    </script>
</body>
</html>
'''

# API endpoint to handle chat messages
@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json
    agent = data.get('agent')
    message = data.get('message')
    
    # Simple responses based on agent type
    responses = {
        'character': f"Great question about character development! For '{message}', I suggest focusing on your character's deeper motivations. What drives them? What are they afraid of? This psychological depth will make them more compelling in your 'Broken Drill' story.",
        'plot': f"Regarding plot structure for '{message}', consider how this fits into your three-act structure. Is this part of your setup, confrontation, or resolution? Make sure it serves your story's central conflict.",
        'dialogue': f"For dialogue about '{message}', remember that each character should have a distinct voice. How would this character specifically say this? What's their background, education, emotional state?",
        'research': f"For research on '{message}', I can help you find authentic details. What specific aspects need to feel realistic in your story? I can guide you to credible sources."
    }
    
    response = responses.get(agent, f"I'm here to help with '{message}'. What specific aspect would you like to explore?")
    
    return jsonify({'response': response})

if __name__ == '__main__':
    print("Starting Hemingwix Chat Interface on port 8000...")
    print("Open browser: http://localhost:8000")
    app.run(debug=True, port=8000)