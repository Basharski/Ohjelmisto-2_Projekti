import random
from geopy.distance import geodesic
import mysql.connector


def get_connection():

    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        database="flight_game",
        user="ali",
        password="saalasana1",
        autocommit=True,
        use_pure=True,
    )

def get_airport_by_icao(conn, icao):

    sql = """SELECT ident, name, latitude_deg, longitude_deg, iso_country, municipality
             FROM airport WHERE ident = %s"""
    cur = conn.cursor()
    cur.execute(sql, (icao,))
    row = cur.fetchone()
    cur.close()
    if row is None:
        return None
    return {
        "ident": row[0],
        "name": row[1],
        "lat": float(row[2]),
        "lon": float(row[3]),
        "iso_country": row[4],
        "municipality": row[5],
    }

def get_country_name(conn, iso_country):

    cur = conn.cursor()
    cur.execute("SELECT name FROM country WHERE iso_country = %s", (iso_country,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else iso_country

def nearest_country_options(conn, current, max_km):

    sql = """
        SELECT ident, latitude_deg, longitude_deg, iso_country
        FROM airport
        WHERE iso_country <> %s
          AND latitude_deg IS NOT NULL AND longitude_deg IS NOT NULL
    """
    cur = conn.cursor()
    cur.execute(sql, (current["iso_country"],))
    rows = cur.fetchall()
    cur.close()
    origin = (current["lat"], current["lon"])
    best_by_country = {}
    for ident, lat, lon, iso_country in rows:
        dist = geodesic(origin, (float(lat), float(lon))).km
        if dist <= max_km:
            prev = best_by_country.get(iso_country)
            if prev is None or dist < prev["distance"]:
                best_by_country[iso_country] = {"icao": ident, "distance": dist}
    results = []
    for iso, info in best_by_country.items():
        cname = get_country_name(conn, iso)
        results.append({
            "country": cname,
            "icao": info["icao"],
            "iso": iso,
            "distance": info["distance"],
        })
    results.sort(key=lambda x: x["distance"])
    return results

def init_game_state(conn):

    state = {}
    # Start in Helsinki (EFHK).
    state["location"] = get_airport_by_icao(conn, "EFHK")
    state["range_km"] = 400
    state["time_left"] = 168
    # Choose 4 random countries excluding Finland to hide rocket parts.
    state["parts"] = spawn_rocket_parts(conn, 4, state["location"]["iso_country"])
    return state

def fly_to(conn, state, player, dest_icao):

    dest = get_airport_by_icao(conn, dest_icao)
    if dest is None:
        return False, state, player, {}
    origin = (state["location"]["lat"], state["location"]["lon"])
    distance = geodesic(origin, (dest["lat"], dest["lon"])).km
    # Maximum flight range check.
    if distance > state.get("range_km", 0):
        return False, state, player, {}
    # Use a constant fuel cost per flight.
    fuel_cost = 30
    # Not enough fuel for the flight.
    if player.get("fuel", 0) < fuel_cost:
        return False, state, player, {}
    # Deduct constant fuel cost.
    player["fuel"] -= fuel_cost
    # Update time and range.
    state["time_left"] -= 12
    state["range_km"] += 50
    # Reduce HP by 10 if present.
    if "hp" in player:
        player["hp"] = max(0, player["hp"] - 10)
    # Move to the new location.
    state["location"] = dest
    context = {"distance": distance, "fuel_cost": fuel_cost}
    return True, state, player, context

def spawn_rocket_parts(conn, n, exclude_iso):

    cur = conn.cursor()
    # Fetch only the country codes to improve performance.
    cur.execute("SELECT iso_country FROM country WHERE iso_country <> %s", (exclude_iso,))
    rows = cur.fetchall()
    cur.close()
    # Flatten list of tuples to list of strings.
    codes = [row[0] for row in rows]
    # If there are fewer than n countries available, just use them all.
    n = min(n, len(codes))
    chosen = random.sample(codes, n) if n > 0 else []
    return chosen