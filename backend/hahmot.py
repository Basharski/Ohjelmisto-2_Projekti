import random

ROLE_BASE_STATS = {
    "kokki": {"ruoka": 80, "fuel": 100, "ammo": 5},
    "pilotti": {"ruoka": 3, "fuel": 130, "ammo": 5},
    "taistelija": {"ruoka": 3, "fuel": 100, "ammo": 60},
}


STARTING_ROCKET_PARTS = 0

def create_player(rooli: str) -> dict:

    rooli = rooli.lower()
    if rooli not in ROLE_BASE_STATS:
        raise ValueError("Tuntematon rooli: käytä 'kokki', 'pilotti' tai 'taistelija'")
    stats = ROLE_BASE_STATS[rooli].copy()

    stats["hp"] = 100
    stats["rakettiosat"] = STARTING_ROCKET_PARTS
    stats["rooli"] = rooli
    return stats

def add_loot(p: dict, loot: dict) -> dict:

    for k, v in loot.items():
        if k not in p or not isinstance(p[k], int):
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

    if "rakettiosat" not in p or not isinstance(p["rakettiosat"], int):
        p["rakettiosat"] = 0
    p["rakettiosat"] += int(n)
    return p