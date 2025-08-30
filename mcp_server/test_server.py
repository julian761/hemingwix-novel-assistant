#!/usr/bin/env python3
"""
Test script for Hemingwix Notion MCP Server
Run this to verify your server configuration and Notion connection
"""

import asyncio
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from notion_client import Client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("❌ notion-client not installed. Run: pip install notion-client")

try:
    from server import HemingwixNotionServer
    SERVER_AVAILABLE = True
except ImportError:
    SERVER_AVAILABLE = False
    print("❌ Server module not available")

class NotionMCPTester:
    def __init__(self):
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.databases = {
            "characters": os.getenv("NOTION_CHARACTERS_DB_ID"),
            "chapters": os.getenv("NOTION_CHAPTERS_DB_ID"), 
            "plot_points": os.getenv("NOTION_PLOT_DB_ID"),
            "research": os.getenv("NOTION_RESEARCH_DB_ID")
        }
        
    def test_environment(self) -> Dict[str, bool]:
        """Test environment variable configuration"""
        print("🔧 Testing Environment Configuration...")
        print("=" * 50)
        
        results = {}
        
        # Check Notion token
        if self.notion_token:
            print(f"✅ NOTION_TOKEN: Set (length: {len(self.notion_token)})")
            results["notion_token"] = True
        else:
            print("❌ NOTION_TOKEN: Not set")
            results["notion_token"] = False
            
        # Check database IDs
        for db_name, db_id in self.databases.items():
            if db_id:
                print(f"✅ {db_name.upper()}_DB_ID: Set ({db_id[:8]}...)")
                results[f"{db_name}_db"] = True
            else:
                print(f"❌ {db_name.upper()}_DB_ID: Not set")
                results[f"{db_name}_db"] = False
                
        return results
    
    async def test_notion_connection(self) -> bool:
        """Test connection to Notion API"""
        print("\n🌐 Testing Notion API Connection...")
        print("=" * 50)
        
        if not NOTION_AVAILABLE:
            print("❌ Notion client not available")
            return False
            
        if not self.notion_token:
            print("❌ No Notion token provided")
            return False
            
        try:
            client = Client(auth=self.notion_token)
            
            # Test basic API access
            response = client.users.me()
            print(f"✅ Connected to Notion API")
            print(f"   User: {response.get('name', 'Unknown')}")
            print(f"   ID: {response.get('id', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Notion API: {e}")
            return False
    
    async def test_database_access(self) -> Dict[str, bool]:
        """Test access to configured databases"""
        print("\n📚 Testing Database Access...")
        print("=" * 50)
        
        results = {}
        
        if not NOTION_AVAILABLE or not self.notion_token:
            print("❌ Cannot test databases - Notion not available or no token")
            return results
            
        client = Client(auth=self.notion_token)
        
        for db_name, db_id in self.databases.items():
            if not db_id:
                print(f"⏭️  Skipping {db_name} - No database ID configured")
                results[db_name] = False
                continue
                
            try:
                # Test database query
                response = client.databases.query(
                    database_id=db_id,
                    page_size=1
                )
                
                page_count = len(response.get("results", []))
                has_more = response.get("has_more", False)
                
                print(f"✅ {db_name}: Connected (found {page_count} pages, has_more: {has_more})")
                results[db_name] = True
                
            except Exception as e:
                print(f"❌ {db_name}: Failed - {e}")
                results[db_name] = False
                
        return results
    
    async def test_mcp_server(self) -> bool:
        """Test MCP server functionality"""
        print("\n🖥️  Testing MCP Server...")
        print("=" * 50)
        
        if not SERVER_AVAILABLE:
            print("❌ MCP Server not available")
            return False
            
        try:
            server = HemingwixNotionServer()
            
            # Test server initialization
            print("✅ Server initialized successfully")
            
            # Test database configuration
            configured_dbs = len([db for db in server.databases.values() if db.database_id])
            total_dbs = len(server.databases)
            print(f"✅ Database configuration: {configured_dbs}/{total_dbs} configured")
            
            # Test a simple query (if databases are configured)
            if configured_dbs > 0:
                try:
                    # Try querying the first configured database
                    for db_name, db_config in server.databases.items():
                        if db_config.database_id:
                            results = await server.get_database_entries(db_name, limit=1)
                            print(f"✅ Sample query to {db_name}: Retrieved {len(results)} entries")
                            break
                except Exception as e:
                    print(f"⚠️  Sample query failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ MCP Server test failed: {e}")
            return False
    
    async def run_full_test(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🧪 Hemingwix Notion MCP Server - Test Suite")
        print("=" * 60)
        
        results = {
            "environment": self.test_environment(),
            "notion_connection": await self.test_notion_connection(),
            "database_access": await self.test_database_access(),
            "mcp_server": await self.test_mcp_server()
        }
        
        # Summary
        print("\n📊 Test Results Summary")
        print("=" * 50)
        
        env_passed = sum(results["environment"].values())
        env_total = len(results["environment"])
        print(f"Environment: {env_passed}/{env_total} checks passed")
        
        print(f"Notion Connection: {'✅ PASS' if results['notion_connection'] else '❌ FAIL'}")
        
        db_passed = sum(results["database_access"].values())
        db_total = len(results["database_access"]) 
        print(f"Database Access: {db_passed}/{db_total} databases accessible")
        
        print(f"MCP Server: {'✅ PASS' if results['mcp_server'] else '❌ FAIL'}")
        
        # Overall status
        all_critical_pass = (
            results["notion_connection"] and 
            results["mcp_server"] and
            env_passed >= 1  # At least one database configured
        )
        
        print(f"\n🎯 Overall Status: {'✅ READY FOR USE' if all_critical_pass else '❌ NEEDS CONFIGURATION'}")
        
        if not all_critical_pass:
            print("\n📝 Next Steps:")
            if not results["notion_connection"]:
                print("   1. Check your NOTION_TOKEN in .env file")
                print("   2. Verify token is valid at https://www.notion.so/my-integrations")
            if env_passed == 0:
                print("   3. Configure at least one database ID in .env")
                print("   4. Share databases with your Notion integration")
            if not results["mcp_server"]:
                print("   5. Check Python dependencies: pip install -r requirements.txt")
        
        return results

async def main():
    """Main test execution"""
    tester = NotionMCPTester()
    await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())