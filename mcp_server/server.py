#!/usr/bin/env python3
"""
Hemingwix Notion MCP Server
Model Context Protocol server for interacting with Notion databases for novel writing
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import os
from dataclasses import dataclass

# MCP imports
try:
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource, 
        Tool, 
        TextContent, 
        ImageContent, 
        EmbeddedResource,
        LoggingLevel
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP not available. Install with: pip install mcp")

# Notion API imports
try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("Notion client not available. Install with: pip install notion-client")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hemingwix-notion-mcp")

@dataclass
class NotionDatabaseConfig:
    """Configuration for a Notion database"""
    name: str
    database_id: str
    description: str
    properties: Dict[str, str]  # property_name -> property_type

class HemingwixNotionServer:
    """MCP Server for Notion database integration"""
    
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        if not self.notion_token:
            logger.warning("NOTION_TOKEN environment variable not set")
            
        self.notion_client = None
        if NOTION_AVAILABLE and self.notion_token:
            self.notion_client = Client(auth=self.notion_token)
            
        # Default database configurations for novel writing
        self.databases = {
            "characters": NotionDatabaseConfig(
                name="Characters",
                database_id=os.getenv("NOTION_CHARACTERS_DB_ID", ""),
                description="Character profiles, backstories, and development",
                properties={
                    "name": "title",
                    "description": "rich_text", 
                    "archetype": "select",
                    "motivation": "rich_text",
                    "backstory": "rich_text",
                    "voice_notes": "rich_text",
                    "status": "select",
                    "created": "created_time",
                    "updated": "last_edited_time"
                }
            ),
            "chapters": NotionDatabaseConfig(
                name="Chapters",
                database_id=os.getenv("NOTION_CHAPTERS_DB_ID", ""),
                description="Chapter content, outlines, and progress tracking",
                properties={
                    "title": "title",
                    "chapter_number": "number",
                    "word_count": "number",
                    "status": "select",
                    "pov_character": "relation",
                    "content": "rich_text",
                    "outline": "rich_text",
                    "notes": "rich_text",
                    "created": "created_time",
                    "updated": "last_edited_time"
                }
            ),
            "plot_points": NotionDatabaseConfig(
                name="Plot Points",
                database_id=os.getenv("NOTION_PLOT_DB_ID", ""),
                description="Story structure, scenes, and narrative beats",
                properties={
                    "title": "title",
                    "description": "rich_text",
                    "act": "select",
                    "chapter": "relation",
                    "characters_involved": "multi_select",
                    "plot_type": "select",
                    "status": "select",
                    "created": "created_time",
                    "updated": "last_edited_time"
                }
            ),
            "research": NotionDatabaseConfig(
                name="Research",
                database_id=os.getenv("NOTION_RESEARCH_DB_ID", ""),
                description="Research notes, sources, and reference material",
                properties={
                    "title": "title",
                    "topic": "select",
                    "summary": "rich_text",
                    "sources": "rich_text",
                    "reliability": "select",
                    "related_chapters": "relation",
                    "tags": "multi_select",
                    "created": "created_time",
                    "updated": "last_edited_time"
                }
            )
        }

    async def get_database_entries(self, database_name: str, filter_params: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
        """Get entries from a Notion database"""
        if not self.notion_client:
            return []
            
        db_config = self.databases.get(database_name)
        if not db_config or not db_config.database_id:
            logger.error(f"Database {database_name} not configured")
            return []
            
        try:
            query_params = {"database_id": db_config.database_id, "page_size": limit}
            if filter_params:
                query_params["filter"] = filter_params
                
            response = self.notion_client.databases.query(**query_params)
            return self._format_database_results(response.get("results", []), db_config)
            
        except Exception as e:
            logger.error(f"Error querying database {database_name}: {e}")
            return []

    def _format_database_results(self, results: List[Dict], db_config: NotionDatabaseConfig) -> List[Dict]:
        """Format Notion API results into clean data"""
        formatted_results = []
        
        for page in results:
            formatted_page = {
                "id": page["id"],
                "url": page["url"],
                "created_time": page["created_time"],
                "last_edited_time": page["last_edited_time"]
            }
            
            properties = page.get("properties", {})
            for prop_name, prop_type in db_config.properties.items():
                if prop_name in properties:
                    formatted_page[prop_name] = self._extract_property_value(
                        properties[prop_name], prop_type
                    )
                    
            formatted_results.append(formatted_page)
            
        return formatted_results

    def _extract_property_value(self, property_data: Dict, prop_type: str) -> Any:
        """Extract value from Notion property based on type"""
        if prop_type == "title" and "title" in property_data:
            return "".join([t.get("plain_text", "") for t in property_data["title"]])
        elif prop_type == "rich_text" and "rich_text" in property_data:
            return "".join([t.get("plain_text", "") for t in property_data["rich_text"]])
        elif prop_type == "select" and "select" in property_data:
            return property_data["select"]["name"] if property_data["select"] else None
        elif prop_type == "multi_select" and "multi_select" in property_data:
            return [item["name"] for item in property_data["multi_select"]]
        elif prop_type == "number" and "number" in property_data:
            return property_data["number"]
        elif prop_type in ["created_time", "last_edited_time"]:
            return property_data.get(prop_type)
        elif prop_type == "relation" and "relation" in property_data:
            return [rel["id"] for rel in property_data["relation"]]
        else:
            return str(property_data) if property_data else None

    async def create_database_entry(self, database_name: str, properties: Dict[str, Any]) -> Optional[str]:
        """Create a new entry in a Notion database"""
        if not self.notion_client:
            return None
            
        db_config = self.databases.get(database_name)
        if not db_config or not db_config.database_id:
            logger.error(f"Database {database_name} not configured")
            return None
            
        try:
            formatted_properties = self._format_properties_for_creation(properties, db_config)
            
            response = self.notion_client.pages.create(
                parent={"database_id": db_config.database_id},
                properties=formatted_properties
            )
            
            return response["id"]
            
        except Exception as e:
            logger.error(f"Error creating entry in {database_name}: {e}")
            return None

    def _format_properties_for_creation(self, properties: Dict[str, Any], db_config: NotionDatabaseConfig) -> Dict:
        """Format properties for Notion API creation"""
        formatted = {}
        
        for prop_name, value in properties.items():
            if prop_name not in db_config.properties:
                continue
                
            prop_type = db_config.properties[prop_name]
            
            if prop_type == "title":
                formatted[prop_name] = {"title": [{"text": {"content": str(value)}}]}
            elif prop_type == "rich_text":
                formatted[prop_name] = {"rich_text": [{"text": {"content": str(value)}}]}
            elif prop_type == "select":
                formatted[prop_name] = {"select": {"name": str(value)}}
            elif prop_type == "multi_select":
                if isinstance(value, list):
                    formatted[prop_name] = {"multi_select": [{"name": str(v)} for v in value]}
            elif prop_type == "number":
                formatted[prop_name] = {"number": float(value) if value else None}
                
        return formatted

    async def search_content(self, query: str, database_filter: Optional[str] = None) -> List[Dict]:
        """Search across databases using Notion's search API"""
        if not self.notion_client:
            return []
            
        try:
            search_params = {"query": query}
            if database_filter and database_filter in self.databases:
                db_id = self.databases[database_filter].database_id
                if db_id:
                    search_params["filter"] = {"property": "object", "value": "page"}
                    
            response = self.notion_client.search(**search_params)
            return response.get("results", [])
            
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []

def create_mcp_server() -> Server:
    """Create and configure the MCP server"""
    if not MCP_AVAILABLE:
        raise ImportError("MCP not available")
        
    server = Server("hemingwix-notion")
    hemingwix = HemingwixNotionServer()
    
    # Resources - expose database schemas and content
    @server.list_resources()
    async def handle_list_resources() -> List[Resource]:
        """List available Notion database resources"""
        resources = []
        
        for db_name, db_config in hemingwix.databases.items():
            resources.append(Resource(
                uri=f"notion://database/{db_name}",
                name=f"{db_config.name} Database",
                description=db_config.description,
                mimeType="application/json"
            ))
            
        return resources

    @server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read content from Notion database resources"""
        if uri.startswith("notion://database/"):
            db_name = uri.split("/")[-1]
            entries = await hemingwix.get_database_entries(db_name)
            return json.dumps(entries, indent=2, default=str)
        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    # Tools - provide interactive capabilities
    @server.list_tools()
    async def handle_list_tools() -> List[Tool]:
        """List available tools for interacting with Notion"""
        return [
            Tool(
                name="query_characters",
                description="Query the Characters database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter": {"type": "object", "description": "Filter parameters"},
                        "limit": {"type": "number", "default": 10}
                    }
                }
            ),
            Tool(
                name="query_chapters",
                description="Query the Chapters database", 
                inputSchema={
                    "type": "object",
                    "properties": {
                        "filter": {"type": "object", "description": "Filter parameters"},
                        "limit": {"type": "number", "default": 10}
                    }
                }
            ),
            Tool(
                name="create_character",
                description="Create a new character entry",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Character name"},
                        "description": {"type": "string", "description": "Character description"},
                        "archetype": {"type": "string", "description": "Character archetype"},
                        "motivation": {"type": "string", "description": "Character motivation"}
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="search_content", 
                description="Search across all databases",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "database": {"type": "string", "description": "Limit to specific database"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_plot_structure",
                description="Get the current plot structure and story beats",
                inputSchema={"type": "object", "properties": {}}
            )
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls"""
        try:
            if name == "query_characters":
                results = await hemingwix.get_database_entries(
                    "characters", 
                    arguments.get("filter"), 
                    arguments.get("limit", 10)
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(results, indent=2, default=str)
                )]
                
            elif name == "query_chapters":
                results = await hemingwix.get_database_entries(
                    "chapters",
                    arguments.get("filter"),
                    arguments.get("limit", 10)
                )
                return [TextContent(
                    type="text", 
                    text=json.dumps(results, indent=2, default=str)
                )]
                
            elif name == "create_character":
                entry_id = await hemingwix.create_database_entry("characters", arguments)
                if entry_id:
                    return [TextContent(
                        type="text",
                        text=f"Created character with ID: {entry_id}"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text="Failed to create character"
                    )]
                    
            elif name == "search_content":
                results = await hemingwix.search_content(
                    arguments["query"],
                    arguments.get("database")
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(results, indent=2, default=str)
                )]
                
            elif name == "get_plot_structure":
                plot_points = await hemingwix.get_database_entries("plot_points")
                return [TextContent(
                    type="text",
                    text=json.dumps(plot_points, indent=2, default=str)
                )]
                
            else:
                raise ValueError(f"Unknown tool: {name}")
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    return server

async def main():
    """Main server entry point"""
    if not MCP_AVAILABLE:
        print("Error: MCP not available. Install with: pip install mcp")
        return
        
    if not NOTION_AVAILABLE:
        print("Error: notion-client not available. Install with: pip install notion-client")
        return
        
    # Check for required environment variables
    if not os.getenv("NOTION_TOKEN"):
        print("Warning: NOTION_TOKEN environment variable not set")
        print("Set your Notion integration token: export NOTION_TOKEN=your_token_here")
        
    server = create_mcp_server()
    
    # Run the server
    options = InitializationOptions(
        server_name="hemingwix-notion",
        server_version="1.0.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={}
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            options
        )

if __name__ == "__main__":
    asyncio.run(main())