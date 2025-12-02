

import random



BASE_INVENTORY = {
    "ruoka": 3,
    "fuel": 100,

    "ammo": 5,
    "rakettiosat": 0
}


def create_player(rooli: str) -> dict:

    p = BASE_INVENTORY.copy()
    rooli = rooli.lower()

    if rooli == "kokki":
        p["ruoka"] += 2
    elif rooli == "pilotti":
        p["fuel"] += 25
    elif rooli == "taistelija":

        p["ammo"] += 2
    else:
        raise ValueError("Tuntematon rooli: käytä 'kokki', 'pilotti' tai 'taistelija'")

    p["rooli"] = rooli
    return p


def add_loot(p: dict, loot: dict) -> dict:

    for k, v in loot.items():
        if k not in p:
            p[k] = 0
        p[k] += int(v)
    return p


def generate_loot() -> dict:


    t = random.randint(1, 5)
    ruoka_gain = 1 if t in (3, 4) else (2 if t == 5 else 0)


    fuel_gain = random.randint(5, 30)


    ammo_gain = 1 if random.randint(1, 5) <= 2 else 0

    return {"ruoka": ruoka_gain, "fuel": fuel_gain, "ammo": ammo_gain}


def add_rocket_part(p: dict, n: int = 1) -> dict:

    p["rakettiosat"] += int(n)
    return p