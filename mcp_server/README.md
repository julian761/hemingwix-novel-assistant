# Hemingwix Notion MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides AI models with seamless access to your Notion databases for novel writing. This server enables AI assistants to query, search, and interact with your novel's characters, chapters, plot points, and research data stored in Notion.

## 🚀 Features

- **📚 Database Integration**: Connect to multiple Notion databases (Characters, Chapters, Plot Points, Research)
- **🔍 Semantic Search**: Search across all your novel content with natural language queries
- **✍️ Content Creation**: Create new characters, chapters, and plot points directly from AI conversations
- **📊 Structured Data**: Access well-organized novel data with proper relationships
- **🔐 Secure**: Uses official Notion API with secure token authentication
- **⚡ Real-time**: Live connection to your Notion workspace for up-to-date information

## 📋 Prerequisites

1. **Python 3.8+** installed on your system
2. **Notion account** with integration access
3. **Notion databases** set up for your novel (or use our templates)

## 🛠️ Installation

### Option 1: Local Installation

```bash
# Clone the repository (if separate) or navigate to mcp_server directory
cd mcp_server

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your Notion credentials (see Configuration section)
nano .env
```

### Option 2: Docker Installation

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Notion credentials
nano .env

# Build and run with Docker Compose
docker-compose up -d
```

## ⚙️ Configuration

### Step 1: Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **"New integration"**
3. Give it a name (e.g., "Hemingwix MCP Server")
4. Select your workspace
5. Copy the **Integration Token** - you'll need this for `NOTION_TOKEN`

### Step 2: Set Up Notion Databases

Create these databases in your Notion workspace:

#### Characters Database
Properties:
- **Name** (Title)
- **Description** (Text)
- **Archetype** (Select)
- **Motivation** (Text)
- **Backstory** (Text)
- **Voice Notes** (Text)
- **Status** (Select: Draft, In Progress, Complete)

#### Chapters Database  
Properties:
- **Title** (Title)
- **Chapter Number** (Number)
- **Word Count** (Number)
- **Status** (Select: Outlined, Draft, Revision, Complete)
- **POV Character** (Relation to Characters)
- **Content** (Text)
- **Outline** (Text)
- **Notes** (Text)

#### Plot Points Database
Properties:
- **Title** (Title)
- **Description** (Text)
- **Act** (Select: Act I, Act II, Act III)
- **Chapter** (Relation to Chapters)
- **Characters Involved** (Multi-select)
- **Plot Type** (Select: Setup, Inciting Incident, Plot Point 1, Midpoint, Plot Point 2, Climax, Resolution)
- **Status** (Select: Planned, Written, Revised)

#### Research Database
Properties:
- **Title** (Title)
- **Topic** (Select)
- **Summary** (Text)
- **Sources** (Text)
- **Reliability** (Select: High, Medium, Low)
- **Related Chapters** (Relation to Chapters)
- **Tags** (Multi-select)

### Step 3: Get Database IDs

For each database:
1. Open the database in Notion
2. Copy the URL
3. Extract the database ID from the URL

**Example URL**: `https://www.notion.so/workspace/Characters-123abc456def789ghi?v=...`  
**Database ID**: `123abc456def789ghi`

### Step 4: Configure Environment Variables

Edit your `.env` file:

```bash
# Notion Integration Token
NOTION_TOKEN=secret_abc123...

# Database IDs
NOTION_CHARACTERS_DB_ID=123abc456def789ghi
NOTION_CHAPTERS_DB_ID=456def789ghi123abc
NOTION_PLOT_DB_ID=789ghi123abc456def
NOTION_RESEARCH_DB_ID=123abc456def789ghi

# Optional
LOG_LEVEL=INFO
```

### Step 5: Share Databases with Integration

For each database:
1. Click **"Share"** in the top right
2. Click **"Invite"**
3. Find your integration name and click **"Invite"**

## 🏃‍♂️ Running the Server

### Local Execution
```bash
python server.py
```

### Docker Execution
```bash
docker-compose up
```

The server will start and listen for MCP protocol connections via stdio.

## 🔧 MCP Client Configuration

### Claude Desktop Configuration

Add to your Claude Desktop config file (`~/Library/Application Support/Claude/config.json` on macOS):

```json
{
  "mcpServers": {
    "hemingwix-notion": {
      "command": "python",
      "args": ["/path/to/mcp_server/server.py"],
      "env": {
        "NOTION_TOKEN": "your_notion_token_here",
        "NOTION_CHARACTERS_DB_ID": "your_characters_db_id",
        "NOTION_CHAPTERS_DB_ID": "your_chapters_db_id",
        "NOTION_PLOT_DB_ID": "your_plot_db_id",
        "NOTION_RESEARCH_DB_ID": "your_research_db_id"
      }
    }
  }
}
```

### Other MCP Clients

The server implements standard MCP protocol and works with any MCP-compatible client.

## 🎯 Usage Examples

Once connected, you can ask your AI assistant questions like:

### Character Queries
- *"Show me all my characters and their motivations"*
- *"Create a new character named Sarah who is a detective"*
- *"What characters are involved in the climax scene?"*

### Chapter Management
- *"What's the word count for Chapter 5?"*
- *"Show me all chapters that need revision"*
- *"Create an outline for the next chapter"*

### Plot Structure
- *"What are the major plot points in Act II?"*
- *"Show me the story structure with all beats"*
- *"Which characters appear in the midpoint scene?"*

### Research Integration
- *"Find research about detective work for my story"*
- *"What sources do I have for the legal procedures?"*
- *"Show me all research tagged with 'forensics'"*

### Cross-Database Queries
- *"Find all content related to the character Marcus"*
- *"Search for mentions of 'courthouse' across all databases"*
- *"Show me the complete story arc for Chapter 3"*

## 📊 Available Tools

The server provides these MCP tools:

- **`query_characters`** - Query the Characters database with filters
- **`query_chapters`** - Query the Chapters database with filters  
- **`create_character`** - Create a new character entry
- **`search_content`** - Search across all databases
- **`get_plot_structure`** - Get the complete plot structure

## 🌐 Available Resources

The server exposes these MCP resources:

- **`notion://database/characters`** - Characters database content
- **`notion://database/chapters`** - Chapters database content
- **`notion://database/plot_points`** - Plot points database content
- **`notion://database/research`** - Research database content

## 🔍 Troubleshooting

### Common Issues

**"NOTION_TOKEN environment variable not set"**
- Make sure your `.env` file exists and contains your Notion token
- Verify the token is correct and active

**"Database not configured" errors**
- Check that your database IDs are correctly set in `.env`
- Ensure databases are shared with your Notion integration

**"Permission denied" errors**  
- Verify your integration has access to the databases
- Check that the integration has read/write permissions

**"Module not found" errors**
- Install requirements: `pip install -r requirements.txt`
- Ensure you're using Python 3.8+

### Debug Mode

Enable detailed logging:
```bash
LOG_LEVEL=DEBUG python server.py
```

### Testing Connection

Test your Notion connection:
```python
from notion_client import Client
client = Client(auth="your_token")
print(client.databases.list())
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/hemingwix-novel-assistant/issues)
- **Documentation**: [Project Wiki](https://github.com/your-username/hemingwix-novel-assistant/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/hemingwix-novel-assistant/discussions)

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
- [Notion API](https://developers.notion.com) by Notion Labs
- The novel writing community for inspiration and feedback

---

**Happy Writing! ✍️📚**