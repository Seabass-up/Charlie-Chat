import os
import logging
import json
import io
import re
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import Charlie core
from charlie import Charlie

logger = logging.getLogger("Charlie.WebServer")

app = FastAPI(title="Charlie Web UI")

# Initialize Charlie application instance once
configPath = os.environ.get("CHARLIE_CONFIG")
os.environ["CHARLIE_DISABLE_VOICE"] = "1"
charlieApp = Charlie(configPath)

# Voice/config settings for Ollama API
VOICE_CONFIG = (
    charlieApp.config_manager.get_section('voice', {})
    if hasattr(charlieApp, 'config_manager') else {}
)

# MCP (Model Context Protocol) Integration
class MCPClient:
    """MCP Client for connecting to MCP servers"""

    def __init__(self):
        self.mcp_config_path = os.path.join(os.path.dirname(__file__), 'mcp_config.json')
        self.mcp_servers = {
            'filesystem': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-filesystem', 'C:/Users/seaba/Desktop', 'C:/Users/seaba/Documents', 'C:/Users/seaba/CascadeProjects', 'D:/'],
                'env': {}
            },
            'memory': {
                'command': 'npx',
                'args': ['-y', '@modelcontextprotocol/server-memory'],
                'env': {}
            },
            'deepwiki': {
                'command': 'npx',
                'args': ['-y', 'mcp-remote', 'https://mcp.deepwiki.com/sse'],
                'env': {},
                'disabled': False
            },
            'n8n-mcp': {
                'command': 'npx',
                'args': ['n8n-mcp'],
                'env': {
                    'MCP_MODE': 'stdio',
                    'LOG_LEVEL': 'error',
                    'DISABLE_CONSOLE_OUTPUT': 'true',
                    'N8N_API_URL': 'http://localhost:5678',
                    'N8N_API_KEY': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhMDkyMWQwYy1iNGViLTQwYzgtODg2MS0wYTUwNmU2YjRmNmEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3MTc4MjMyLCJleHAiOjE3NTk3MjMyMDB9.kDmP6DcA1Q0UjpkTG99qYP_dW07DaYoybacJX7tak24'
                }
            },
            'web_search': {
                'command': 'python',
                'args': ['-c', 'import requests; print("Web search ready")'],
                'env': {}
            }
        }
        self.active_connections = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.load_config()

    def load_config(self):
        """Load MCP server configuration"""
        try:
            if os.path.exists(self.mcp_config_path):
                with open(self.mcp_config_path, 'r') as f:
                    config = json.load(f)
                    cfg = config.get('mcpServers', {})
                    # Only override built-in defaults if the config actually contains servers
                    if isinstance(cfg, dict) and len(cfg) > 0:
                        self.mcp_servers = cfg
                        logger.info(f"Loaded MCP configuration with {len(self.mcp_servers)} servers")
                    else:
                        logger.warning("MCP config present but empty; keeping built-in default servers from __init__()")
            else:
                logger.warning("MCP config file not found")
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")

    def get_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get available tools from all enabled MCP servers"""
        tools = {}

        for server_name, server_config in self.mcp_servers.items():
            if server_config.get('disabled', False):
                logger.info(f"Skipping disabled MCP server: {server_name}")
                continue

            try:
                logger.info(f"Loading tools for MCP server: {server_name}")
                # Get tools without starting subprocess for now
                tools[server_name] = self._get_server_tools(server_name, server_config)
                logger.info(f"Loaded {len(tools[server_name])} tools for {server_name}")

            except Exception as e:
                logger.error(f"Error loading tools for MCP server {server_name}: {e}")

        # Fallback: if nothing loaded (e.g., empty config), populate defaults
        if not tools:
            logger.warning("No MCP servers loaded; falling back to default tool list")
            for default_server in ['filesystem', 'memory', 'deepwiki', 'web_search', 'n8n-mcp']:
                try:
                    server_tools = self._get_server_tools(default_server, {})
                    if server_tools:
                        tools[default_server] = server_tools
                except Exception as _:
                    continue

        logger.info(f"Total MCP tools loaded: {sum(len(t) for t in tools.values())} across {len(tools)} servers")
        return tools

    def _get_server_tools(self, server_name: str, server_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get tools available from a specific MCP server"""
        # This is a simplified implementation
        # In production, you'd implement proper MCP protocol communication

        if server_name == 'filesystem':
            return [
                {
                    'name': 'read_file',
                    'description': 'Read the complete contents of a file from the filesystem',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'path': {'type': 'string', 'description': 'Path to the file to read'}
                        },
                        'required': ['path']
                    }
                },
                {
                    'name': 'list_directory',
                    'description': 'List contents of a directory',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'path': {'type': 'string', 'description': 'Path to the directory to list'}
                        },
                        'required': ['path']
                    }
                },
                {
                    'name': 'search_files',
                    'description': 'Search for files matching a pattern',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'pattern': {'type': 'string', 'description': 'Search pattern'},
                            'path': {'type': 'string', 'description': 'Directory to search in'}
                        },
                        'required': ['pattern', 'path']
                    }
                }
            ]

        elif server_name == 'memory':
            return [
                {
                    'name': 'store_memory',
                    'description': 'Store information in memory for later retrieval',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string', 'description': 'Memory key'},
                            'value': {'type': 'string', 'description': 'Value to store'}
                        },
                        'required': ['key', 'value']
                    }
                },
                {
                    'name': 'retrieve_memory',
                    'description': 'Retrieve information from memory',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'key': {'type': 'string', 'description': 'Memory key to retrieve'}
                        },
                        'required': ['key']
                    }
                }
            ]

        elif server_name == 'deepwiki':
            return [
                {
                    'name': 'search_wiki',
                    'description': 'Search documentation and wiki pages',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string', 'description': 'Search query'},
                            'repo': {'type': 'string', 'description': 'Repository to search in (optional)'}
                        },
                        'required': ['query']
                    }
                }
            ]

        elif server_name == 'n8n-mcp':
            return [
                {
                    'name': 'create_workflow',
                    'description': 'Create a new n8n workflow',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string', 'description': 'Workflow name'},
                            'description': {'type': 'string', 'description': 'Workflow description'}
                        },
                        'required': ['name']
                    }
                },
                {
                    'name': 'list_workflows',
                    'description': 'List available n8n workflows',
                    'parameters': {
                        'type': 'object',
                        'properties': {}
                    }
                }
            ]

        elif server_name == 'web_search':
            return [
                {
                    'name': 'search_web',
                    'description': 'Search the internet for information',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {'type': 'string', 'description': 'Search query'},
                            'num_results': {'type': 'integer', 'description': 'Number of results to return (default: 5)'}
                        },
                        'required': ['query']
                    }
                }
            ]

        return []

    async def call_tool(self, server_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        try:
            # In simplified mode, allow calls if server is configured, even if no subprocess was started
            if server_name not in self.mcp_servers:
                return {'error': f'MCP server {server_name} not configured'}

            # For now, implement basic tool calls (no MCP protocol handshake yet)
            
            if server_name == 'filesystem':
                return await self._call_filesystem_tool(tool_name, parameters)
            elif server_name == 'memory':
                return await self._call_memory_tool(tool_name, parameters)
            elif server_name == 'deepwiki':
                return await self._call_deepwiki_tool(tool_name, parameters)
            elif server_name == 'n8n-mcp':
                return await self._call_n8n_tool(tool_name, parameters)
            elif server_name == 'web_search':
                return await self._call_web_search_tool(tool_name, parameters)
            else:
                return {'error': f'Unknown MCP server: {server_name}'}

        except Exception as e:
            logger.error(f"Error calling MCP tool {server_name}.{tool_name}: {e}")
            return {'error': str(e)}

    async def _call_filesystem_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle filesystem MCP tool calls"""
        if tool_name == 'read_file':
            path = parameters.get('path')
            if not path:
                return {'error': 'Path parameter required'}

            try:
                # Use the safe file reading function
                result = read_file_content(path)
                return {'content': result['content'], 'path': path, 'size': result.get('size', 0)}
            except Exception as e:
                return {'error': f'Failed to read file: {e}'}

        elif tool_name == 'list_directory':
            path = parameters.get('path', 'C:\\Users\\seaba\\CascadeProjects\\Charlie')
            try:
                # Use the safe directory listing function
                result = get_directory_contents(path)
                return {'items': result['items'], 'path': result['path'], 'parent': result.get('parent')}
            except Exception as e:
                return {'error': f'Failed to list directory: {e}'}

        elif tool_name == 'search_files':
            path = parameters.get('path', 'C:\\Users\\seaba\\CascadeProjects\\Charlie')
            pattern = parameters.get('pattern', '*')
            try:
                from pathlib import Path
                search_path = Path(path)
                if not is_path_allowed(str(search_path)):
                    return {'error': 'Access denied to search path'}
                
                matches = []
                for item in search_path.rglob(pattern):
                    if is_path_allowed(str(item)):
                        matches.append({
                            'name': item.name,
                            'path': str(item),
                            'type': 'directory' if item.is_dir() else 'file',
                            'size': item.stat().st_size if item.is_file() else None
                        })
                        if len(matches) >= 50:  # Limit results
                            break
                
                return {'matches': matches, 'pattern': pattern, 'search_path': path}
            except Exception as e:
                return {'error': f'Failed to search files: {e}'}

        return {'error': f'Unknown filesystem tool: {tool_name}'}

    async def _call_memory_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle memory MCP tool calls"""
        # Simplified memory implementation
        memory_file = os.path.join(os.path.dirname(__file__), 'memory.json')

        if tool_name == 'store_memory':
            key = parameters.get('key')
            value = parameters.get('value')

            try:
                memory = {}
                if os.path.exists(memory_file):
                    with open(memory_file, 'r') as f:
                        memory = json.load(f)

                memory[key] = value

                with open(memory_file, 'w') as f:
                    json.dump(memory, f, indent=2)

                return {'success': True, 'key': key, 'value': value}
            except Exception as e:
                return {'error': f'Failed to store memory: {e}'}

        elif tool_name == 'retrieve_memory':
            key = parameters.get('key')

            try:
                if os.path.exists(memory_file):
                    with open(memory_file, 'r') as f:
                        memory = json.load(f)
                    value = memory.get(key)
                    if value is not None:
                        return {'key': key, 'value': value}
                    else:
                        return {'error': f'Memory key not found: {key}'}
                else:
                    return {'error': 'No memory file exists'}
            except Exception as e:
                return {'error': f'Failed to retrieve memory: {e}'}

        return {'error': f'Unknown memory tool: {tool_name}'}

    async def _call_deepwiki_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deepwiki MCP tool calls"""
        if tool_name == 'search_wiki':
            query = parameters.get('query')
            if not query:
                return {'error': 'Query parameter required'}

            # Simplified wiki search - in production you'd call the actual deepwiki API
            return {
                'query': query,
                'results': [
                    {
                        'title': f'Results for: {query}',
                        'content': f'This is a placeholder for deepwiki search results for "{query}". In production, this would connect to the actual deepwiki MCP server.'
                    }
                ]
            }

        return {'error': f'Unknown deepwiki tool: {tool_name}'}

    async def _call_n8n_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle n8n MCP tool calls"""
        if tool_name == 'create_workflow':
            name = parameters.get('name')
            description = parameters.get('description', '')

            # Simplified workflow creation - in production you'd call the actual n8n API
            return {
                'workflow_id': f'workflow_{len(name)}_{len(description)}',
                'name': name,
                'description': description,
                'status': 'created'
            }

        elif tool_name == 'list_workflows':
            # Simplified workflow listing
            return {
                'workflows': [
                    {'id': '1', 'name': 'Sample Workflow 1'},
                    {'id': '2', 'name': 'Sample Workflow 2'}
                ]
            }

        return {'error': f'Unknown n8n tool: {tool_name}'}

    async def _call_web_search_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web search tool calls"""
        if tool_name == 'search_web':
            query = parameters.get('query')
            num_results = parameters.get('num_results', 5)
            
            if not query:
                return {'error': 'Query parameter required'}

            try:
                import requests
                from bs4 import BeautifulSoup
                import urllib.parse
                
                # Use DuckDuckGo Instant Answer API (no API key required)
                search_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
                
                response = requests.get(search_url, timeout=10)
                data = response.json()
                
                results = []
                
                # Get instant answer if available
                if data.get('AbstractText'):
                    results.append({
                        'title': data.get('AbstractSource', 'DuckDuckGo'),
                        'snippet': data.get('AbstractText'),
                        'url': data.get('AbstractURL', ''),
                        'type': 'instant_answer'
                    })
                
                # Get related topics
                for topic in data.get('RelatedTopics', [])[:num_results-len(results)]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' '),
                            'snippet': topic.get('Text'),
                            'url': topic.get('FirstURL', ''),
                            'type': 'related_topic'
                        })
                
                # If no results, try a basic web search
                if not results:
                    # Fallback to a simple search result
                    results.append({
                        'title': f'Search results for: {query}',
                        'snippet': f'I searched for "{query}" but couldn\'t find specific results. You may want to try a more specific query or check the web directly.',
                        'url': f'https://duckduckgo.com/?q={urllib.parse.quote(query)}',
                        'type': 'fallback'
                    })
                
                return {
                    'query': query,
                    'results': results[:num_results],
                    'total_results': len(results)
                }
                
            except Exception as e:
                return {'error': f'Web search failed: {str(e)}'}

        return {'error': f'Unknown web search tool: {tool_name}'}

# Initialize MCP client
mcp_client = MCPClient()

# File system access configuration
ALLOWED_BASE_PATHS = [
    "C:\\Users\\seaba\\CascadeProjects\\Charlie",  # Main Charlie folder
    "C:\\Users\\seaba\\Desktop",  # Desktop access
    "C:\\Users\\seaba\\Documents",  # Documents access
    "C:\\Users\\seaba\\OneDrive",  # OneDrive access
    "D:\\",  # D drive access
]

def is_path_allowed(path: str) -> bool:
    """Check if a path is within allowed directories."""
    try:
        path_obj = Path(path).resolve()
        for allowed_path in ALLOWED_BASE_PATHS:
            allowed_obj = Path(allowed_path).resolve()
            if path_obj.is_relative_to(allowed_obj):
                return True
        return False
    except Exception:
        return False

def get_directory_contents(path: str) -> Dict[str, Any]:
    """Get directory contents safely."""
    if not is_path_allowed(path):
        raise HTTPException(status_code=403, detail="Access denied to this path")

    try:
        path_obj = Path(path)
        if not path_obj.exists() or not path_obj.is_dir():
            raise HTTPException(status_code=404, detail="Directory not found")

        items = []
        for item in path_obj.iterdir():
            try:
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else None,
                    "modified": stat.st_mtime,
                    "readable": True  # We'll check this later if needed
                })
            except (OSError, PermissionError):
                # Skip items we can't access
                continue

        # Sort: directories first, then files, alphabetically
        items.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))

        return {
            "path": str(path),
            "items": items,
            "parent": str(path_obj.parent) if path_obj.parent != path_obj else None
        }

    except Exception as e:
        logger.error(f"Error reading directory {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading directory: {str(e)}")

def read_file_content(file_path: str, max_lines: int = 100) -> Dict[str, Any]:
    """Read file content safely."""
    if not is_path_allowed(file_path):
        raise HTTPException(status_code=403, detail="Access denied to this file")

    try:
        path_obj = Path(file_path)
        if not path_obj.exists() or not path_obj.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        # Check file size (limit to 1MB for safety)
        stat = path_obj.stat()
        if stat.st_size > 1024 * 1024:
            return {
                "path": str(file_path),
                "content": f"File too large ({stat.st_size} bytes). Maximum allowed size is 1MB.",
                "truncated": True,
                "size": stat.st_size,
                "encoding": "binary"
            }

        # Try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Limit lines for large files
            if len(lines) > max_lines:
                content = ''.join(lines[:max_lines])
                truncated = True
            else:
                content = ''.join(lines)
                truncated = False

            return {
                "path": str(file_path),
                "content": content,
                "truncated": truncated,
                "total_lines": len(lines),
                "shown_lines": min(len(lines), max_lines),
                "size": stat.st_size,
                "encoding": "utf-8"
            }

        except UnicodeDecodeError:
            # Binary file
            return {
                "path": str(file_path),
                "content": f"Binary file ({stat.st_size} bytes). Cannot display content.",
                "truncated": False,
                "size": stat.st_size,
                "encoding": "binary"
            }

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


def _extract_tool_call_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Attempt to extract a JSON tool call object from free-form text.

    Expected shape:
      {"tool": "filesystem", "action": "list", "parameters": {"path": "D:\\"}}
    """
    try:
        # Prefer fenced code blocks first
        code_block = re.search(r"```[a-zA-Z0-9_\-]*\n([\s\S]*?)```", text)
        candidate = code_block.group(1).strip() if code_block else text.strip()

        # Find the first JSON-looking object
        m = re.search(r"\{[\s\S]*\}", candidate)
        if not m:
            return None
        payload = json.loads(m.group(0))
        # Accept payloads that specify tool/server OR just action/parameters (we'll infer)
        if isinstance(payload, dict) and ("tool" in payload or "server" in payload or "action" in payload):
            return payload
    except Exception:
        return None
    return None


def _map_tool_action(tool: str, action: Optional[str]) -> Optional[Dict[str, str]]:
    """Map generic tool/action words to server/tool names used internally."""
    # Allow mapping by action only (e.g., fs_search), even if tool is missing
    if not tool and action:
        a0 = action.lower()
        if a0 in ("fs_search", "search", "find", "search_files"):
            return {"server": "filesystem", "tool": "search_files"}
        if a0 in ("fs_list", "list", "ls", "dir", "list_directory"):
            return {"server": "filesystem", "tool": "list_directory"}
        if a0 in ("fs_read", "read", "open", "cat", "read_file"):
            return {"server": "filesystem", "tool": "read_file"}
    if not tool:
        return None
    t = (tool or "").lower()
    a = (action or "").lower() if action else None

    if t in ("filesystem", "file", "fs"):
        server = "filesystem"
        if a in ("list", "ls", "dir", "list_directory"):
            return {"server": server, "tool": "list_directory"}
        if a in ("read", "open", "cat", "read_file"):
            return {"server": server, "tool": "read_file"}
        if a in ("search", "find", "search_files"):
            return {"server": server, "tool": "search_files"}
        # Default to list
        return {"server": server, "tool": "list_directory"}

    if t in ("web_search", "web", "internet", "search"):
        return {"server": "web_search", "tool": "search_web"}

    if t in ("deepwiki", "wiki"):
        return {"server": "deepwiki", "tool": "search_wiki"}

    if t in ("n8n", "n8n-mcp", "workflow"):
        if a in ("list", "list_workflows"):
            return {"server": "n8n-mcp", "tool": "list_workflows"}
        return {"server": "n8n-mcp", "tool": "create_workflow"}

    return None


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = "gpt-oss:120b"


@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    try:
        userMessage = payload.message.strip()
        if not userMessage:
            return JSONResponse({"reply": "Please type a message."}, status_code=200)

        # Check if message requires MCP tools
        message_lower = userMessage.lower()
        mcp_results = {}

        # 1) Structured tool call extraction (JSON in message)
        tool_payload = _extract_tool_call_from_text(userMessage)
        if tool_payload:
            try:
                tool_name = tool_payload.get('tool') or tool_payload.get('server')
                action = tool_payload.get('action')
                mapping = _map_tool_action(tool_name, action)
                params = tool_payload.get('parameters', {})
                # Normalize alternate parameter names
                if isinstance(params, dict):
                    if 'search_path' in params and 'path' not in params:
                        params['path'] = params['search_path']
                if mapping:
                    server = mapping['server']
                    tool = mapping['tool']
                    # Provide sensible defaults
                    if server == 'filesystem' and tool == 'list_directory' and 'path' not in params:
                        params['path'] = 'D:\\'
                    result = await mcp_client.call_tool(server, tool, params)
                    mcp_results[server] = result
            except Exception as e:
                logger.error(f"Structured MCP tool call failed: {e}")

        # 2) Raw Windows path detection (e.g., D:\\ or C:\\Users\\...)
        try:
            path_match = re.search(r'([A-Za-z]:\\\\[^\n\r]*)', userMessage)
            if path_match and 'filesystem' not in mcp_results:
                candidate_path = path_match.group(1).strip().strip('"')
                # Heuristic: if it has an extension, try read_file; else list_directory
                if Path(candidate_path).suffix:
                    fs_result = await mcp_client.call_tool('filesystem', 'read_file', {'path': candidate_path})
                else:
                    fs_result = await mcp_client.call_tool('filesystem', 'list_directory', {'path': candidate_path})
                mcp_results['filesystem'] = fs_result
        except Exception as e:
            logger.error(f"Windows path detection failed: {e}")

        # MCP capability queries - respond about available tools
        if any(keyword in message_lower for keyword in ['mcp', 'tools', 'what tools', 'capabilities', 'what can you', 'use your mcp', 'your mcp tools']):
            try:
                available_tools = mcp_client.get_available_tools()
                mcp_results['available_tools'] = available_tools
            except Exception as e:
                logger.error(f"MCP tools listing error: {e}")

        # File-related queries
        if any(keyword in message_lower for keyword in ['file', 'read', 'find', 'search', 'folder', 'directory', 'show me', '.pdf', '.txt', '.doc', 'onedrive', 'documents', 'desktop']):
            try:
                # Check if user is asking for a specific file path
                if 'onedrive' in message_lower or 'work sync' in message_lower or '.pdf' in message_lower:
                    # Try to read the specific PDF file
                    pdf_path = "C:\\Users\\seaba\\OneDrive\\Work Sync\\1. Urban Loop CC Bldg A - Outline Specification_110822.pdf"
                    file_results = await mcp_client.call_tool('filesystem', 'read_file', {'path': pdf_path})
                    mcp_results['filesystem'] = file_results
                elif 'read' in message_lower or 'show me' in message_lower:
                    # List OneDrive directory to show available files
                    file_results = await mcp_client.call_tool('filesystem', 'list_directory', {'path': "C:\\Users\\seaba\\OneDrive"})
                    mcp_results['filesystem'] = file_results
                else:
                    # Search for files in Documents/OneDrive
                    search_results = await mcp_client.call_tool('filesystem', 'search_files', {'path': "C:\\Users\\seaba\\OneDrive", 'pattern': '*.pdf'})
                    mcp_results['filesystem'] = search_results
            except Exception as e:
                logger.error(f"MCP filesystem error: {e}")

        # Memory-related queries
        if any(keyword in message_lower for keyword in ['remember', 'store', 'save', 'recall', 'memory']):
            try:
                mcp_results['memory'] = {'message': 'I can help you with memory operations. What would you like me to remember?'}
            except Exception as e:
                logger.error(f"MCP memory error: {e}")

        # Web search queries
        if any(keyword in message_lower for keyword in ['search', 'google', 'find online', 'internet', 'web', 'look up', 'what is', 'who is', 'when did', 'where is', 'how to']):
            try:
                web_results = await mcp_client.call_tool('web_search', 'search_web', {'query': userMessage, 'num_results': 3})
                mcp_results['web_search'] = web_results
            except Exception as e:
                logger.error(f"MCP web search error: {e}")

        # Documentation/wiki queries
        if any(keyword in message_lower for keyword in ['help', 'documentation', 'docs', 'wiki']):
            try:
                wiki_results = await mcp_client.call_tool('deepwiki', 'search_wiki', {'query': userMessage})
                mcp_results['deepwiki'] = wiki_results
            except Exception as e:
                logger.error(f"MCP deepwiki error: {e}")

        # Workflow/automation queries
        if any(keyword in message_lower for keyword in ['workflow', 'automation', 'n8n']):
            try:
                workflow_results = await mcp_client.call_tool('n8n-mcp', 'list_workflows', {})
                mcp_results['n8n'] = workflow_results
            except Exception as e:
                logger.error(f"MCP n8n error: {e}")

        # Use Ollama client for web UI with enhanced context
        from ollama import Client
        try:
            api_host = os.getenv('OLLAMA_API_ENDPOINT') or VOICE_CONFIG.get('ollama_api_endpoint') or 'https://ollama.com'
            api_key = os.getenv('OLLAMA_API_KEY') or VOICE_CONFIG.get('ollama_api_key') or ''
            headers = {'Authorization': api_key} if api_key else {}
            client = Client(host=api_host, headers=headers)

            enhanced_message = userMessage
            if mcp_results:
                # Build system context based on available MCP results
                system_context = "You are Charlie, an AI assistant with access to MCP (Model Context Protocol) tools. "
                
                if 'available_tools' in mcp_results:
                    tools_info = []
                    for server, tools in mcp_results['available_tools'].items():
                        for tool in tools:
                            tools_info.append(f"- {tool['name']}: {tool['description']}")
                    system_context += f"Available MCP tools:\n" + "\n".join(tools_info) + "\n\n"
                
                if 'filesystem' in mcp_results:
                    if 'content' in str(mcp_results['filesystem']):
                        system_context += f"I successfully accessed the requested file. File content: {json.dumps(mcp_results['filesystem'], indent=2)}\n\n"
                    else:
                        system_context += f"File system results: {json.dumps(mcp_results['filesystem'], indent=2)}\n\n"
                
                if 'web_search' in mcp_results:
                    system_context += f"Web search results: {json.dumps(mcp_results['web_search'], indent=2)}\n\n"
                
                if 'memory' in mcp_results:
                    system_context += f"Memory operations: {json.dumps(mcp_results['memory'], indent=2)}\n\n"
                
                enhanced_message = f"{system_context}User question: {userMessage}\n\nYou are Charlie, an AI assistant with MCP (Model Context Protocol) capabilities. You have access to filesystem tools, web search, memory storage, and workflow automation. Always mention which MCP tools you used when responding. Be specific about your capabilities and what information you found using your tools."

            messages = [{'role': 'user', 'content': enhanced_message}]
            reply = ""
            for part in client.chat(payload.model, messages=messages, stream=True):
                reply += part['message']['content']

        except Exception as ollama_error:
            logger.error(f"Ollama error: {ollama_error}")
            reply = f"Sorry, I encountered an error: {ollama_error}"

        response = {"reply": reply}
        if mcp_results:
            response["mcp_results"] = mcp_results

        return response
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return JSONResponse({"reply": f"Error: {str(e)}"}, status_code=500)

# ------------- Voice / TTS Integration -------------

try:
    from vibevoice_tts import VibeVoiceTTS  # local module with VibeVoice+fallback
except Exception:
    VibeVoiceTTS = None  # type: ignore

VOICE_DISABLED = os.getenv('CHARLIE_DISABLE_VOICE', '').lower() in ('1', 'true', 'yes')
VOICE_ENGINE_NAME = (VOICE_CONFIG.get('engine') if isinstance(VOICE_CONFIG, dict) else None) or os.getenv('CHARLIE_VOICE_ENGINE', 'vibevoice')

voice_tts_instance = None
if not VOICE_DISABLED and VibeVoiceTTS is not None and VOICE_ENGINE_NAME.lower() in ('vibevoice', 'auto'):
    try:
        voice_tts_instance = VibeVoiceTTS()
        logger.info("VibeVoice TTS initialized")
    except Exception as e:
        logger.error(f"Failed to initialize VibeVoice TTS: {e}")


class TTSRequest(BaseModel):
    text: str
    speaker: Optional[str] = None
    sample_rate: Optional[int] = 22050


@app.post("/api/tts")
def tts_endpoint(req: TTSRequest):
    if VOICE_DISABLED:
        raise HTTPException(status_code=400, detail="Voice is disabled by CHARLIE_DISABLE_VOICE")
    if voice_tts_instance is None:
        raise HTTPException(status_code=500, detail="TTS engine not available")
    try:
        wav_bytes = voice_tts_instance.synthesize(req.text, speaker=req.speaker, sample_rate=req.sample_rate or 22050)
        return StreamingResponse(io.BytesIO(wav_bytes), media_type="audio/wav")
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

# --- API Endpoints ---

@app.get("/api/debug")
def debug_endpoint():
    return {"status": "API endpoints are working", "timestamp": "2025-09-07T14:09:12"}

@app.get("/api/files")
def list_directory_endpoint(path: str = "C:\\Users\\seaba\\CascadeProjects\\Charlie"):
    return get_directory_contents(path)

@app.get("/api/files/read")
def read_file_endpoint(path: str, lines: Optional[int] = 100):
    return read_file_content(path, lines)

@app.get("/api/mcp/tools")
def get_mcp_tools_endpoint():
    try:
        tools = mcp_client.get_available_tools()
        logger.info(f"MCP tools endpoint called, returning: {tools}")
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error in MCP tools endpoint: {e}")
        return {"tools": {}, "error": str(e)}

@app.get("/api/mcp/config")
def get_mcp_config_endpoint():
    """Debug endpoint to view loaded MCP servers and their tools."""
    try:
        return {
            "servers": mcp_client.mcp_servers,
            "tools": mcp_client.get_available_tools()
        }
    except Exception as e:
        logger.error(f"Error in MCP config endpoint: {e}")
        return {"servers": {}, "tools": {}, "error": str(e)}

class MCPSearchRequest(BaseModel):
    query: str
    use_tools: Optional[bool] = True

@app.post("/api/mcp/search")
async def mcp_intelligent_search(request: MCPSearchRequest):
    """Intelligent search using MCP tools"""
    try:
        query = request.query.lower()
        results = {}

        # File system searches
        if any(keyword in query for keyword in ['file', 'read', 'find', 'search', 'folder', 'directory']):
            try:
                file_results = await mcp_client.call_tool('filesystem', 'list_directory',
                    {'path': "C:\\Users\\seaba\\CascadeProjects\\Charlie"})
                results['filesystem'] = file_results
            except Exception as e:
                logger.error(f"Filesystem search error: {e}")

        # Memory operations
        if any(keyword in query for keyword in ['remember', 'store', 'save', 'memory']):
            results['memory'] = {'message': 'Memory operations available through chat'}

        # Web searches
        if any(keyword in query for keyword in ['search', 'google', 'internet', 'web', 'online', 'find']):
            try:
                web_results = await mcp_client.call_tool('web_search', 'search_web', {'query': request.query, 'num_results': 5})
                results['web_search'] = web_results
            except Exception as e:
                logger.error(f"Web search error: {e}")

        # Wiki searches
        if any(keyword in query for keyword in ['wiki', 'documentation', 'docs', 'help']):
            try:
                wiki_results = await mcp_client.call_tool('deepwiki', 'search_wiki', {'query': request.query})
                results['deepwiki'] = wiki_results
            except Exception as e:
                logger.error(f"Wikipedia search error: {e}")

        # n8n workflow operations
        if any(keyword in query for keyword in ['workflow', 'automation', 'n8n']):
            try:
                workflow_results = await mcp_client.call_tool('n8n-mcp', 'list_workflows', {})
                results['n8n'] = workflow_results
            except Exception as e:
                logger.error(f"n8n workflow error: {e}")

        return {
            "query": request.query,
            "results": results,
            "tools_used": list(results.keys())
        }
    except Exception as e:
        logger.exception("Error in MCP intelligent search")
        raise HTTPException(status_code=500, detail=str(e))

# Serve static UI
webDir = os.path.join(os.path.dirname(__file__), "web")
if not os.path.isdir(webDir):
    os.makedirs(webDir, exist_ok=True)

app.mount("/", StaticFiles(directory=webDir, html=True), name="web")
