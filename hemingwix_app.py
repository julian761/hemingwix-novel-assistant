#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hemingwix Novel Master</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            overflow: hidden;
        }
        
        .app-container {
            display: flex;
            height: 100vh;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            margin: 20px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
        }
        
        .sidebar {
            width: 320px;
            background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
            border-radius: 20px 0 0 20px;
            padding: 30px 20px;
            box-shadow: inset -5px 0 15px rgba(0, 0, 0, 0.1);
        }
        
        .sidebar-header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .sidebar-title {
            color: #ecf0f1;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .sidebar-subtitle {
            color: #bdc3c7;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .agent-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .agent-button {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 16px 20px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            text-align: left;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .agent-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.4);
            background: linear-gradient(135deg, #2980b9, #3498db);
        }
        
        .agent-button:active {
            transform: translateY(0);
        }
        
        .agent-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        
        .agent-button:hover::before {
            left: 100%;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 40px 50px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 0 20px 20px 0;
        }
        
        .main-header {
            text-align: center;
            margin-bottom: 50px;
        }
        
        .main-title {
            font-size: 48px;
            font-weight: 700;
            background: linear-gradient(135deg, #2c3e50, #3498db);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
        }
        
        .main-subtitle {
            font-size: 18px;
            color: #6c757d;
            font-weight: 400;
        }
        
        .parent-agent-interface {
            flex: 1;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
            display: flex;
            flex-direction: column;
            gap: 30px;
        }
        
        .interface-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            padding: 30px;
            border-radius: 15px;
            border: 2px solid #e9ecef;
            transition: all 0.3s ease;
        }
        
        .interface-section:hover {
            border-color: #3498db;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.1);
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .section-icon {
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, #3498db, #2980b9);
            border-radius: 50%;
        }
        
        .section-content {
            color: #6c757d;
            line-height: 1.6;
        }
        
        .chat-interface {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            min-height: 200px;
            border: 2px dashed #dee2e6;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6c757d;
            font-style: italic;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #27ae60;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        @media (max-width: 768px) {
            .app-container {
                flex-direction: column;
                margin: 10px;
            }
            .sidebar {
                width: 100%;
                border-radius: 20px 20px 0 0;
            }
            .main-content {
                border-radius: 0 0 20px 20px;
            }
            .main-title {
                font-size: 32px;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <aside class="sidebar">
            <div class="sidebar-header">
                <h2 class="sidebar-title">Specialized Agents</h2>
                <p class="sidebar-subtitle">Your Writing Team</p>
            </div>
            <div class="agent-list">
                <button class="agent-button" onclick="activateAgent('character')">
                    📝 Character Development Agent
                </button>
                <button class="agent-button" onclick="activateAgent('plot')">
                    📚 Plot Structure Agent
                </button>
                <button class="agent-button" onclick="activateAgent('dialogue')">
                    💬 Dialogue Specialist
                </button>
                <button class="agent-button" onclick="activateAgent('research')">
                    🔍 Research Assistant
                </button>
                <button class="agent-button" onclick="activateAgent('mcp')">
                    🔗 MCP Integration Specialist
                </button>
            </div>
        </aside>
        
        <main class="main-content">
            <div class="main-header">
                <h1 class="main-title">Hemingwix Novel Master</h1>
                <p class="main-subtitle">Your AI-powered novel writing command center</p>
            </div>
            
            <div class="parent-agent-interface">
                <div class="interface-section">
                    <h3 class="section-title">
                        <div class="section-icon"></div>
                        Master Agent Status
                    </h3>
                    <div class="section-content">
                        <span class="status-indicator"></span>
                        Ready to orchestrate your writing process. Select a specialized agent from the sidebar or interact directly with the master agent below.
                    </div>
                </div>
                
                <div class="interface-section">
                    <h3 class="section-title">
                        <div class="section-icon"></div>
                        Direct Communication
                    </h3>
                    <div class="chat-interface">
                        Chat interface will be implemented here for direct parent agent interaction
                    </div>
                </div>
                
                <div class="interface-section">
                    <h3 class="section-title">
                        <div class="section-icon"></div>
                        Current Project
                    </h3>
                    <div class="section-content">
                        Working on: <strong>"Broken Drill"</strong> - Your novel project with integrated character development, plot structuring, and research capabilities.
                    </div>
                </div>
            </div>
        </main>
    </div>
    
    <script>
        function activateAgent(agentType) {
            const agents = {
                character: 'Character Development Agent ready! Ask me about creating complex characters with psychological depth.',
                plot: 'Plot Structure Agent ready! Let me help you with story architecture and narrative beats.',
                dialogue: 'Dialogue Specialist ready! I can help make your character voices authentic and distinct.',
                research: 'Research Assistant ready! I will help you find facts and sources for your novel.',
                mcp: 'MCP Integration Specialist ready! I can help with your Notion database connection.'
            };
            
            // Future: Replace with actual agent communication
            alert(agents[agentType]);
            
            // Visual feedback
            const button = event.target;
            const originalBg = button.style.background;
            button.style.background = 'linear-gradient(135deg, #27ae60, #2ecc71)';
            setTimeout(() => {
                button.style.background = originalBg;
            }, 1000);
        }
        
        // Add some interactive elements
        document.addEventListener('DOMContentLoaded', function() {
            const interfaceSections = document.querySelectorAll('.interface-section');
            interfaceSections.forEach(section => {
                section.addEventListener('click', function() {
                    this.style.transform = 'scale(1.02)';
                    setTimeout(() => {
                        this.style.transform = 'translateY(-2px)';
                    }, 150);
                });
            });
        });
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    print("Starting Hemingwix Web Interface...")
    print("Open your browser and go to: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, port=8000, host='0.0.0.0')