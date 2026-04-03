#!/usr/bin/env python3
"""
usage_example.py — Shows every tool in action, end to end.

This isn't a test — it's a readable walkthrough you can run directly
to see the server working before hooking it up to an MCP client.

Run it from the pokedex_mcp folder:
    python usage_example.py
"""

from pokedex_mcp import lookup_pokemon, register_trainer, get_trainer, add_pokemon, remove_pokemon


def main():
    print("Pokédex MCP Server — Usage Examples")
    print("=" * 45)

    # ── 1. Look up a Pokémon ──────────────────────
    print("\n1. Looking up Pikachu:")
    info = lookup_pokemon("pikachu")
    print(f"   Name    : {info['name']} (#{info['id']})")
    print(f"   Types   : {', '.join(info['types'])}")
    print(f"   Height  : {info['height_m']}m  |  Weight: {info['weight_kg']}kg")
    print(f"   Dex     : {info['description'][:80]}...")

    print("\n2. Looking up a non-existent Pokémon:")
    bad = lookup_pokemon("missingno")
    print(f"   Result  : {bad}")

    # ── 2. Register trainers ──────────────────────
    print("\n3. Registering trainers:")
    print(f"   {register_trainer('Ash')}")
    print(f"   {register_trainer('Misty')}")
    print(f"   {register_trainer('Ash')}")   # already registered — friendly response

    # ── 3. Build a collection ─────────────────────
    print("\n4. Ash catches some Pokémon:")
    for pokemon in ["pikachu", "charizard", "snorlax"]:
        print(f"   {add_pokemon('Ash', pokemon)}")

    print("\n5. Trying to add a duplicate:")
    print(f"   {add_pokemon('Ash', 'pikachu')}")

    print("\n6. Misty catches her favourites:")
    for pokemon in ["starmie", "psyduck"]:
        print(f"   {add_pokemon('Misty', pokemon)}")

    # ── 4. View collections ───────────────────────
    print("\n7. Ash's Pokédex:")
    ash = get_trainer("Ash")
    print(f"   Trainer : {ash['name']}")
    print(f"   Count   : {ash['pokemon_count']}")
    print(f"   Pokémon : {', '.join(ash['pokemon'])}")

    print("\n8. Misty's Pokédex:")
    misty = get_trainer("Misty")
    print(f"   Trainer : {misty['name']}")
    print(f"   Pokémon : {', '.join(misty['pokemon'])}")

    # ── 5. Remove a Pokémon ───────────────────────
    print("\n9. Ash releases Snorlax:")
    print(f"   {remove_pokemon('Ash', 'snorlax')}")

    print("\n10. Ash's updated Pokédex:")
    ash = get_trainer("Ash")
    print(f"    Pokémon : {', '.join(ash['pokemon'])}")

    print("\n11. Trying to remove a Pokémon Ash doesn't have:")
    print(f"    {remove_pokemon('Ash', 'mewtwo')}")

    print("\n12. Looking up a trainer who doesn't exist:")
    print(f"    {get_trainer('Gary')}")


if __name__ == "__main__":
    main()