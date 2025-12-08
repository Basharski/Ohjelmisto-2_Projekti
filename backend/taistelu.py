

import random
import hahmot


def encounter_chance():
    return random.randint(0, 1) == 1


def taistelu(pelaaja):

    if pelaaja["ammo"] > 0:
        pelaaja["ammo"] -= 1
        loot = hahmot.generate_loot()
        hahmot.add_loot(pelaaja, loot)
        return True
    else:
        return False


def bossfight(pelaaja):
    if pelaaja["ammo"] > 0:
        pelaaja["ammo"] -= 1
        return True
    else:
        return False