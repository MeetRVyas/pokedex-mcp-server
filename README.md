# 🔴 Pokédex MCP Server + Chatbot

A live Pokédex as an MCP server — look up Pokémon, register trainers, and manage collections. Comes with a multi-provider AI chatbot frontend.

---

## What's Inside

| File | Purpose |
|---|---|
| `server.py` | The MCP server (FastMCP, 5 tools) |
| `backend.py` | MCP client + LLM routing (OpenAI, Groq, Gemini, Anthropic) |
| `app.py` | Streamlit chatbot frontend |
| `test_server.py` | Unit tests for server logic |
| `test_stdio.py` | Protocol-level MCP stdio tests |
| `usage_example.py` | End-to-end usage demo (no LLM needed) |

---

## MCP Tools

| Tool | What it does |
|---|---|
| `lookup_pokemon` | Look up any Pokémon — types, stats, description (live from PokeAPI) |
| `register_trainer` | Register a new trainer by name |
| `get_trainer` | View a trainer's profile and Pokémon collection |
| `add_pokemon` | Add a Pokémon to a trainer's collection |
| `remove_pokemon` | Remove a Pokémon from a trainer's collection |

---

## Chatbot Setup

### 1. Install dependencies

```bash
pip install streamlit fastmcp requests langchain langchain-core langgraph

# Install the SDK for your chosen provider:
pip install langchain-openai          # OpenAI
pip install langchain-groq            # Groq
pip install langchain-anthropic       # Anthropic
pip install langchain-google-genai    # Google Gemini
```

### 2. Run the chatbot

```bash
cd app
streamlit run frontend.py
```

### 3. In the sidebar

- Select your **LLM provider** (OpenAI / Groq / Google Gemini / Anthropic)
- Select a **model**
- Enter your **API key** (used only for the session, never stored)
- Click **START MCP SERVER**
- Start chatting!

---

## Why `uvx` for MCP Clients?

`uvx` is part of the [`uv`](https://github.com/astral-sh/uv) Python toolchain. It lets MCP clients (Claude Desktop, Cursor, etc.) run your server **directly from GitHub without any manual install step**:

```
uvx --from git+https://github.com/MeetRVyas/pokedex-mcp-server.git pokedex-mcp-server
```

This:
- Pulls the code from GitHub automatically
- Creates an isolated virtual environment
- Runs the `pokedex-mcp-server` entry point defined in `pyproject.toml`
- Works identically on any machine — no path configuration needed

### Install `uv` first

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Claude Desktop Config

Add to your `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pokedex": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/MeetRVyas/pokedex-mcp-server.git",
        "pokedex-mcp-server"
      ]
    }
  }
}
```

Restart Claude Desktop — the tools will appear automatically.

---

## Local Development

```bash
# Run server directly
python server.py

# Run tests
python test_server.py
python test_stdio.py

# Run usage demo (hits PokeAPI live)
python usage_example.py
```

---

## Example Prompts

> "Register me as a trainer named Ash"  
> "Look up Gengar"  
> "Add Pikachu to Ash's collection"  
> "Show me Ash's Pokédex"  
> "Remove Pikachu from Ash's collection"  
> "What are Charizard's base stats?"