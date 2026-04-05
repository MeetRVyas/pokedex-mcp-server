"""Pokédex MCP Server — a simple tool for Pokémon trainers."""

import json
import requests
from pathlib import Path
from typing import Any, Dict
from fastmcp import FastMCP

mcp = FastMCP("Pokédex MCP Server")

# Simple JSON file for persistent trainer data
DATA_FILE = Path("/data/trainers.json")


def load_data() -> Dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {}


def save_data(data: Dict):
    DATA_FILE.write_text(json.dumps(data, indent=2))


# ─────────────────────────────────────────
# Pokémon lookup (PokeAPI)
# ─────────────────────────────────────────

@mcp.tool()
def lookup_pokemon(name: str) -> Dict[str, Any]:
    """
    Look up a Pokémon by name.
    Returns basic info: ID, name, types, height, weight, and a short description.

    Args:
        name: The Pokémon's name (e.g. "pikachu", "bulbasaur")
    """
    name = name.lower().strip()
    resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}", timeout=10)

    if resp.status_code == 404:
        return {"error": f"No Pokémon named '{name}' found. Double-check the spelling!"}
    resp.raise_for_status()
    data = resp.json()

    # Grab the English flavor text from species endpoint
    species_resp = requests.get(data["species"]["url"], timeout=10)
    description = ""
    if species_resp.ok:
        for entry in species_resp.json().get("flavor_text_entries", []):
            if entry["language"]["name"] == "en":
                description = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
                break

    return {
        "id": data["id"],
        "name": data["name"].capitalize(),
        "types": [t["type"]["name"].capitalize() for t in data["types"]],
        "height_m": data["height"] / 10,
        "weight_kg": data["weight"] / 10,
        "base_stats": {s["stat"]["name"]: s["base_stat"] for s in data["stats"]},
        "description": description,
    }


# ─────────────────────────────────────────
# Trainer registration
# ─────────────────────────────────────────

@mcp.tool()
def register_trainer(trainer_name: str) -> str:
    """
    Register a new Pokémon trainer.
    No password needed — just pick a name and you're in!

    Args:
        trainer_name: The trainer's name
    """
    data = load_data()
    key = trainer_name.lower().strip()

    if key in data:
        return f"Welcome back, {data[key]['name']}! You're already registered."

    data[key] = {"name": trainer_name.strip(), "pokemon": []}
    save_data(data)
    return f"Welcome, Trainer {trainer_name.strip()}! Your Pokédex is ready. Go catch 'em all!"


# ─────────────────────────────────────────
# Trainer's Pokémon collection
# ─────────────────────────────────────────

@mcp.tool()
def get_trainer(trainer_name: str) -> Dict[str, Any]:
    """
    Get a trainer's profile and their Pokémon collection.

    Args:
        trainer_name: The trainer's name
    """
    data = load_data()
    key = trainer_name.lower().strip()

    if key not in data:
        return {"error": f"No trainer named '{trainer_name}' found. Register first!"}

    trainer = data[key]
    return {
        "name": trainer["name"],
        "pokemon_count": len(trainer["pokemon"]),
        "pokemon": trainer["pokemon"],
    }


@mcp.tool()
def add_pokemon(trainer_name: str, pokemon_name: str) -> str:
    """
    Add a Pokémon to a trainer's collection.
    Looks up the Pokémon first to make sure it's real.

    Args:
        trainer_name: The trainer's name
        pokemon_name: The Pokémon to add (e.g. "charmander")
    """
    data = load_data()
    key = trainer_name.lower().strip()

    if key not in data:
        return f"Trainer '{trainer_name}' not found. Register first!"

    # Validate the Pokémon exists
    result = lookup_pokemon(pokemon_name)
    if "error" in result:
        return result["error"]

    canonical_name = result["name"]  # Properly capitalized

    if canonical_name in data[key]["pokemon"]:
        return f"{canonical_name} is already in {data[key]['name']}'s Pokédex!"

    data[key]["pokemon"].append(canonical_name)
    save_data(data)

    count = len(data[key]["pokemon"])
    return f"{data[key]['name']} caught {canonical_name}! ({count} Pokémon registered)"


@mcp.tool()
def remove_pokemon(trainer_name: str, pokemon_name: str) -> str:
    """
    Remove a Pokémon from a trainer's collection.

    Args:
        trainer_name: The trainer's name
        pokemon_name: The Pokémon to remove
    """
    data = load_data()
    key = trainer_name.lower().strip()

    if key not in data:
        return f"Trainer '{trainer_name}' not found."

    # Normalize name for comparison
    normalized = pokemon_name.strip().capitalize()
    collection = data[key]["pokemon"]

    if normalized not in collection:
        return f"{normalized} isn't in {data[key]['name']}'s Pokédex."

    collection.remove(normalized)
    save_data(data)
    return f"{normalized} was removed from {data[key]['name']}'s Pokédex."


# ─────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", default="streamable-http", choices=["stdio", "sse", "streamable-http"])
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()