import random
import hahmot



def encounter_chance() -> bool:

    # A 50% chance of encountering an enemy.
    return random.randint(0, 1) == 1

def _fight_impl(player: dict) -> bool:

    if player.get("ammo", 0) > 0:
        # Use one ammo to defeat the enemy.
        player["ammo"] -= 1
        # Grant random loot for winning.
        loot = hahmot.generate_loot()
        hahmot.add_loot(player, loot)
        return True
    # No ammo left – defeat.
    return False

def taistelu(pelaaja: dict) -> bool:

    return _fight_impl(pelaaja)

def bossfight(pelaaja: dict) -> bool:

    if pelaaja.get("ammo", 0) > 0:
        pelaaja["ammo"] -= 1
        return True
    return False

def fight(player: dict):

    result = _fight_impl(player)
    return result, player