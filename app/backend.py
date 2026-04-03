"""
backend.py — Pokédex MCP Chatbot Backend (LangGraph Version)
"""

import json
import subprocess
import sys
import time
import threading
from pathlib import Path
from typing import Any, Optional

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

# ── LangGraph Imports ──
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode

# ─────────────────────────────────────────────────────────────────────────────
# MCP Server process manager (stdio transport)
# ─────────────────────────────────────────────────────────────────────────────

SERVER_PATH = Path(__file__).parent.parent / "pokedex_mcp" / "server.py"

class MCPClient:
    """
    Talks to the Pokédex MCP server over stdin/stdout (JSON-RPC 2.0).
    Spawns the server as a subprocess and keeps it alive for the session.
    """

    def __init__(self):
        self.proc: Optional[subprocess.Popen] = None
        self._id = 0
        self._lock = threading.Lock()
        self._initialized = False

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def start(self):
        """Spawn the MCP server subprocess."""
        self.proc = subprocess.Popen(
            [sys.executable, str(SERVER_PATH)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        time.sleep(0.5)
        self._do_initialize()

    def _send(self, method: str, params: dict) -> Any:
        if self.proc is None or self.proc.poll() is not None:
            raise RuntimeError("MCP server is not running.")

        msg = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params,
        }
        with self._lock:
            self.proc.stdin.write(json.dumps(msg) + "\n")
            self.proc.stdin.flush()
            raw = self.proc.stdout.readline()
            if not raw.strip():
                raise RuntimeError("Empty response from MCP server.")
            response = json.loads(raw.strip())

        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        return response.get("result")

    def _do_initialize(self):
        self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pokedex-chatbot", "version": "1.0.0"},
        })
        self._initialized = True

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool and return the result as a string."""
        result = self._send("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        if isinstance(result, dict) and "content" in result:
            parts = result["content"]
            return "\n".join(
                block.get("text", str(block))
                for block in parts
                if isinstance(block, dict)
            )
        return str(result)

    def list_tools(self) -> list:
        result = self._send("tools/list", {})
        return result.get("tools", []) if isinstance(result, dict) else []

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=5)


# ─────────────────────────────────────────────────────────────────────────────
# LangChain Tool Definitions
# ─────────────────────────────────────────────────────────────────────────────

def get_mcp_tools(mcp: MCPClient):
    """Returns a list of LangChain @tool definitions bound to the MCPClient."""

    @tool
    def lookup_pokemon(name: str) -> str:
        """Look up a Pokémon by name. Returns types, stats, height, weight, and Pokédex description."""
        return mcp.call_tool("lookup_pokemon", {"name": name})

    @tool
    def register_trainer(trainer_name: str) -> str:
        """Register a new Pokémon trainer by name."""
        return mcp.call_tool("register_trainer", {"trainer_name": trainer_name})

    @tool
    def get_trainer(trainer_name: str) -> str:
        """Get a trainer's profile and their Pokémon collection."""
        return mcp.call_tool("get_trainer", {"trainer_name": trainer_name})

    @tool
    def add_pokemon(trainer_name: str, pokemon_name: str) -> str:
        """Add a Pokémon to a trainer's collection."""
        return mcp.call_tool("add_pokemon", {"trainer_name": trainer_name, "pokemon_name": pokemon_name})

    @tool
    def remove_pokemon(trainer_name: str, pokemon_name: str) -> str:
        """Remove a Pokémon from a trainer's collection."""
        return mcp.call_tool("remove_pokemon", {"trainer_name": trainer_name, "pokemon_name": pokemon_name})

    return [lookup_pokemon, register_trainer, get_trainer, add_pokemon, remove_pokemon]


SYSTEM_PROMPT = """You are PokéBot, an enthusiastic AI assistant powered by a live Pokédex MCP server.
You can look up Pokémon, register trainers, and manage their collections.
Always be helpful, friendly, and a little bit excited — you love Pokémon!
When a user asks about a Pokémon or trainer action, use the appropriate tool.
Format Pokémon data in a clear, readable way with emojis where it fits naturally."""


# ─────────────────────────────────────────────────────────────────────────────
# LLM Initialization Factory
# ─────────────────────────────────────────────────────────────────────────────

PROVIDER_MODELS = {
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "Groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
    "Google Gemini": ["gemini-3.1-pro-preview", "gemini-3-flash-preview", "gemini-3.1-flash-lite-preview", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"],
    "Anthropic": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
}

def _get_llm(provider: str, model: str, api_key: str):
    """Dynamically returns the initialized LangChain BaseChatModel based on provider."""
    if provider == "OpenAI":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=api_key)
    elif provider == "Groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, api_key=api_key)
    elif provider == "Anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key)
    elif provider == "Google Gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# ─────────────────────────────────────────────────────────────────────────────
# Main dispatch (LangGraph Workflow)
# ─────────────────────────────────────────────────────────────────────────────

def get_response(
    provider: str,
    model: str,
    api_key: str,
    messages: list,
    mcp: MCPClient,
) -> str:
    """
    Route a conversation to the selected LLM provider using LangGraph.
    Returns the assistant's reply as a clean string.
    """
    
    # 1. Instantiate the LLM & bind MCP tools
    llm = _get_llm(provider, model, api_key)
    lc_tools = get_mcp_tools(mcp)
    llm_with_tools = llm.bind_tools(lc_tools)

    # 2. Build the LangGraph Workflow (StateGraph)
    workflow = StateGraph(MessagesState)

    # Node: Chat Node invokes the LLM
    def chatnode(state: MessagesState):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    # Node: Tool Node automatically triggers the functions requested by LLM
    toolnode = ToolNode(lc_tools)

    workflow.add_node("chatnode", chatnode)
    workflow.add_node("toolnode", toolnode)

    # Routing Edge: Check if the LLM called a tool or is done
    def should_continue(state: MessagesState) -> str:
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "toolnode"
        return END

    workflow.add_edge(START, "chatnode")
    workflow.add_conditional_edges(
        "chatnode", 
        should_continue, 
        {"toolnode": "toolnode", END: END}
    )
    workflow.add_edge("toolnode", "chatnode")

    app = workflow.compile()

    # 3. Convert basic dict messages to LangChain message abstractions
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "system":
            lc_messages[0] = SystemMessage(content=content)
        elif role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))

    # 4. Invoke the Graph
    final_state = app.invoke({"messages": lc_messages})

    # 5. Extract and format the final string
    final_content = final_state["messages"][-1].content
    
    # If the provider returned a plain string, return it directly
    if isinstance(final_content, str):
        return final_content
        
    # If the provider returned a list of blocks (common with Anthropic/Gemini)
    elif isinstance(final_content, list):
        extracted_text = []
        for block in final_content:
            if isinstance(block, dict) and "text" in block:
                extracted_text.append(block["text"])
            elif isinstance(block, str):
                extracted_text.append(block)
        return "".join(extracted_text)
        
    # Fallback
    return str(final_content)