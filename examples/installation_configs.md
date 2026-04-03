# MCP Server Installation and Registration Configurations

This document covers how to register the Pokédex MCP server with different clients.

---

## Why `uvx`?

`uvx` (from the [`uv`](https://github.com/astral-sh/uv) toolchain) lets you run a Python package **directly from GitHub without installing anything manually**. It:

- Auto-creates an isolated virtual environment
- Pulls the latest code straight from your GitHub repo
- Uses the `[project.scripts]` entry point defined in `pyproject.toml`
- Means anyone can run your server with just a URL — no local setup needed

---

## Installation Methods

### ✅ Method 1: uvx from GitHub (Recommended)

No install needed. Pulls and runs directly from your repo:

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

### Method 2: uvx from a specific branch or tag

```json
{
  "mcpServers": {
    "pokedex": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/MeetRVyas/pokedex-mcp-server.git@main",
        "pokedex-mcp-server"
      ]
    }
  }
}
```

### Method 3: uvx from PyPI (once published)

```json
{
  "mcpServers": {
    "pokedex": {
      "command": "uvx",
      "args": ["pokedex-mcp-server"]
    }
  }
}
```

### Method 4: Direct Python script (local dev)

```json
{
  "mcpServers": {
    "pokedex": {
      "command": "python",
      "args": ["/absolute/path/to/pokedex_mcp/server.py"]
    }
  }
}
```

---

## Client-Specific Configurations

### Claude Desktop

**Config file location:**
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

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

### Cursor IDE

```json
{
  "mcpServers": {
    "pokedex": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/MeetRVyas/pokedex-mcp-server.git",
        "pokedex-mcp-server"
      ],
      "transport": {
        "type": "stdio"
      }
    }
  }
}
```

### Continue.dev

```json
{
  "mcpServers": {
    "pokedex": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/MeetRVyas/pokedex-mcp-server.git",
        "pokedex-mcp-server"
      ],
      "transport": {
        "type": "stdio"
      }
    }
  }
}
```

---

## With Environment Variables

```json
{
  "mcpServers": {
    "pokedex": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/MeetRVyas/pokedex-mcp-server.git",
        "pokedex-mcp-server"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

---

## Verification

After updating your config, restart the MCP client. The following tools should appear:

| Tool | Description |
|---|---|
| `lookup_pokemon` | Look up any Pokémon by name |
| `register_trainer` | Register as a new trainer |
| `get_trainer` | View a trainer's profile and collection |
| `add_pokemon` | Add a Pokémon to a trainer's collection |
| `remove_pokemon` | Remove a Pokémon from a trainer's collection |

## Troubleshooting

- **`uvx` not found**: Install `uv` first — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Tools not appearing**: Check config JSON syntax and restart the client
- **Network errors**: The server calls PokeAPI live — ensure internet access
- **Path issues**: For local dev, always use absolute paths