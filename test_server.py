#!/usr/bin/env python3
"""
test_server.py — Tests for the Pokédex MCP server.

Covers trainer registration, Pokémon management, and edge cases.
The PokeAPI calls are mocked so tests run offline and fast.

Run with:
    python test_server.py
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


# ── Mock PokeAPI responses ────────────────────────────────────────────────────

MOCK_POKEMON = {
    "pikachu": {
        "id": 25, "name": "Pikachu",
        "types": ["Electric"],
        "height_m": 0.4, "weight_kg": 6.0,
        "base_stats": {"hp": 35, "speed": 90},
        "description": "When several of these Pokémon gather, their electricity can cause lightning storms.",
    },
    "charizard": {
        "id": 6, "name": "Charizard",
        "types": ["Fire", "Flying"],
        "height_m": 1.7, "weight_kg": 90.5,
        "base_stats": {"hp": 78, "speed": 100},
        "description": "Spits fire that is hot enough to melt boulders.",
    },
}

def mock_lookup(name):
    """Stand-in for lookup_pokemon that doesn't hit the network."""
    result = MOCK_POKEMON.get(name.lower().strip())
    if result:
        return result
    return {"error": f"No Pokémon named '{name}' found. Double-check the spelling!"}


# ── Test cases ────────────────────────────────────────────────────────────────

class TestPokedexServer(unittest.TestCase):

    def setUp(self):
        """Each test gets a fresh temporary trainers.json so they don't interfere."""
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        Path(self.tmp.name).write_text("{}")  # start empty

        import pokedex_mcp
        pokedex_mcp.DATA_FILE = Path(self.tmp.name)

        # Patch out the real PokeAPI call
        self.patcher = patch("server.lookup_pokemon", side_effect=mock_lookup)
        self.patcher.start()

        from pokedex_mcp import register_trainer, get_trainer, add_pokemon, remove_pokemon
        self.register = register_trainer
        self.get = get_trainer
        self.add = add_pokemon
        self.remove = remove_pokemon

    def tearDown(self):
        self.patcher.stop()
        Path(self.tmp.name).unlink(missing_ok=True)

    # ── Registration ──────────────────────────────────────────────────────────

    def test_register_new_trainer(self):
        result = self.register("Ash")
        self.assertIn("Welcome, Trainer Ash", result)

    def test_register_preserves_name_casing(self):
        self.register("Misty")
        trainer = self.get("Misty")
        self.assertEqual(trainer["name"], "Misty")

    def test_register_is_case_insensitive_lookup(self):
        # Registering as "Ash" and looking up as "ash" should work
        self.register("Ash")
        trainer = self.get("ash")
        self.assertEqual(trainer["name"], "Ash")

    def test_register_duplicate_is_friendly(self):
        self.register("Ash")
        result = self.register("Ash")
        self.assertIn("already registered", result)

    def test_get_unknown_trainer(self):
        result = self.get("Gary")
        self.assertIn("error", result)

    # ── Adding Pokémon ────────────────────────────────────────────────────────

    def test_add_pokemon(self):
        self.register("Ash")
        result = self.add("Ash", "pikachu")
        self.assertIn("Pikachu", result)
        self.assertIn("1 Pokémon", result)

    def test_add_multiple_pokemon(self):
        self.register("Ash")
        self.add("Ash", "pikachu")
        self.add("Ash", "charizard")
        trainer = self.get("Ash")
        self.assertEqual(trainer["pokemon_count"], 2)
        self.assertIn("Pikachu", trainer["pokemon"])
        self.assertIn("Charizard", trainer["pokemon"])

    def test_add_duplicate_pokemon(self):
        self.register("Ash")
        self.add("Ash", "pikachu")
        result = self.add("Ash", "pikachu")
        self.assertIn("already in", result)
        # Should still only have one
        self.assertEqual(self.get("Ash")["pokemon_count"], 1)

    def test_add_invalid_pokemon(self):
        self.register("Ash")
        result = self.add("Ash", "fakemon")
        self.assertIn("found", result)

    def test_add_to_unregistered_trainer(self):
        result = self.add("Gary", "pikachu")
        self.assertIn("not found", result)

    # ── Removing Pokémon ──────────────────────────────────────────────────────

    def test_remove_pokemon(self):
        self.register("Ash")
        self.add("Ash", "pikachu")
        result = self.remove("Ash", "pikachu")
        self.assertIn("removed", result)
        self.assertEqual(self.get("Ash")["pokemon_count"], 0)

    def test_remove_pokemon_not_in_collection(self):
        self.register("Ash")
        result = self.remove("Ash", "mewtwo")
        self.assertIn("isn't in", result)

    def test_remove_from_unregistered_trainer(self):
        result = self.remove("Gary", "pikachu")
        self.assertIn("not found", result)

    # ── Data persistence ──────────────────────────────────────────────────────

    def test_data_persists_across_calls(self):
        """Trainer data should survive between function calls (written to disk)."""
        self.register("Ash")
        self.add("Ash", "pikachu")

        # Re-import load_data to simulate a fresh read
        import pokedex_mcp
        data = pokedex_mcp.load_data()
        self.assertIn("ash", data)
        self.assertIn("Pikachu", data["ash"]["pokemon"])


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Pokédex MCP Server — Tests")
    print("=" * 40)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPokedexServer)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)