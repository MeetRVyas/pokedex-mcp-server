"""
backend.py — Pokédex MCP Chatbot Backend (LangGraph Version)
"""

import asyncio
from fastmcp import Client

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

# ── LangGraph Imports ──
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode


MCP_SERVER_URL = "https://pokedex-mcp-server-production.up.railway.app/mcp"

# ─────────────────────────────────────────────────────────────────────────────
# LangChain Tool Definitions
# ─────────────────────────────────────────────────────────────────────────────

def get_mcp_tools(server_url : str) :
    """Returns a list of LangChain @tool definitions."""

    def call(tool_name: str, args: dict) -> str:
        async def _call():
            async with Client(server_url) as client:
                result = await client.call_tool(tool_name, args)
                # result is a list of content blocks
                print(result)
                return "\n".join(
                    block.text if hasattr(block, "text") else str(block)
                    for block in result.content
                )
        return asyncio.run(_call())

    @tool
    def lookup_pokemon(name: str) -> str:
        """Look up a Pokémon by name. Returns types, stats, height, weight, and Pokédex description."""
        return call("lookup_pokemon", {"name": name})

    @tool
    def register_trainer(trainer_name: str) -> str:
        """Register a new Pokémon trainer by name."""
        return call("register_trainer", {"trainer_name": trainer_name})

    @tool
    def get_trainer(trainer_name: str) -> str:
        """Get a trainer's profile and their Pokémon collection."""
        return call("get_trainer", {"trainer_name": trainer_name})

    @tool
    def add_pokemon(trainer_name: str, pokemon_name: str) -> str:
        """Add a Pokémon to a trainer's collection."""
        return call("add_pokemon", {"trainer_name": trainer_name, "pokemon_name": pokemon_name})

    @tool
    def remove_pokemon(trainer_name: str, pokemon_name: str) -> str:
        """Remove a Pokémon from a trainer's collection."""
        return call("remove_pokemon", {"trainer_name": trainer_name, "pokemon_name": pokemon_name})

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
    provider : str,
    model : str,
    api_key : str,
    messages : list,
    server_url : list = MCP_SERVER_URL
) -> str:
    """
    Route a conversation to the selected LLM provider using LangGraph.
    Returns the assistant's reply as a clean string.
    """
    
    # 1. Instantiate the LLM & bind MCP tools
    llm = _get_llm(provider, model, api_key)
    lc_tools = get_mcp_tools(server_url)
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