#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Hemingwix Novel Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .agent-button { background: #4CAF50; color: white; padding: 15px 30px; margin: 10px 0; border: none; border-radius: 5px; cursor: pointer; display: block; width: 100%; font-size: 16px; }
        .agent-button:hover { background: #45a049; transform: translateY(-2px); }
        h1 { text-align: center; color: #333; margin-bottom: 10px; }
        p { text-align: center; color: #666; margin-bottom: 30px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Hemingwix Novel Assistant</h1>
        <p>Your AI-powered writing team for "Broken Drill"</p>
        <button class="agent-button" onclick="alert('Character Development Agent ready! Ask me about creating complex characters with psychological depth.')">Character Development Agent</button>
        <button class="agent-button" onclick="alert('Plot Structure Agent ready! Let me help you with story architecture and narrative beats.')">Plot Structure Agent</button>
        <button class="agent-button" onclick="alert('Dialogue Specialist ready! I can help make your character voices authentic and distinct.')">Dialogue Specialist</button>
        <button class="agent-button" onclick="alert('Research Assistant ready! I will help you find facts and sources for your novel.')">Research Assistant</button>
        <button class="agent-button" onclick="alert('MCP Integration Specialist ready! I can help with your Notion database connection.')">MCP Integration Specialist</button>
    </div>
</body>
</html>
    '''

if __name__ == '__main__':
    print("Starting Hemingwix Web Interface...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, port=5000, host='0.0.0.0')