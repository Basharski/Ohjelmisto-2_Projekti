from flask import Flask, request, jsonify
from flask_cors import CORS

import kartta
import hahmot
import taistelu


app = Flask(__name__)
# Enable Cross-Origin Resource Sharing so that the frontend can make requests
# from a different origin (e.g. a static file served from disk).
CORS(app)

# Server-side state.  Only one game can be played at a time with this API.
current_state = None
current_player = None

@app.post("/start")
def start_game():

    global current_state, current_player
    # (Re)initialise game state.
    conn = kartta.get_connection()
    current_state = kartta.init_game_state(conn)
    conn.close()
    # Reset the current player; this will be set in /choose_role.
    current_player = None
    return jsonify({"state": current_state, "player": current_player})

@app.post("/choose_role")
def choose_role():

    global current_player
    data = request.get_json(silent=True) or {}
    role = data.get("role", "")
    try:
        current_player = hahmot.create_player(role)
    except Exception as e:
        # Return a 400 response if the role is invalid.
        return jsonify({"error": str(e)}), 400
    return jsonify({"state": current_state, "player": current_player})

@app.get("/countries")
def countries():

    global current_state
    if current_state is None:
        return jsonify({"Error": "No game running"}), 400
    conn = kartta.get_connection()
    try:
        options = kartta.nearest_country_options(
            conn,
            current_state["location"],
            current_state["range_km"],
        )
    finally:
        conn.close()
    return jsonify(options)

@app.post("/fly")
def fly():

    global current_state, current_player
    if current_state is None:
        return jsonify({"Error": "No game running"}), 400
    data = request.get_json(silent=True) or {}
    dest_icao = data.get("icao", "")
    if not dest_icao:
        return jsonify({"Error": "No ICAO provided"}), 400
    # A player must be chosen before flying.
    if current_player is None:
        return jsonify({"Error": "No player"}), 400
    conn = kartta.get_connection()
    try:
        # Use the correct argument order for fly_to: (conn, state, player, dest_icao).
        ok, new_state, new_player, context = kartta.fly_to(conn, current_state, current_player, dest_icao)
    finally:
        conn.close()
    if not ok:
        return jsonify({"Error": "Flying failed"})
    # Assign the updated state/player immediately to retain mutations.
    current_state = new_state
    current_player = new_player
    messages: list[str] = []
    # Current location ISO and human-readable country name.
    dest_iso = current_state["location"]["iso_country"]
    # Retrieve human-readable country name for messages.
    country_name = None
    try:
        conn2 = kartta.get_connection()
        country_name = kartta.get_country_name(conn2, dest_iso)
    finally:
        try:
            conn2.close()
        except Exception:
            pass
    # Inform about flight cost and distance.
    if country_name:
        messages.append(f"Flew to {country_name}. Time -12h, Fuel -{context.get('fuel_cost', 0)}, Range +50, HP -10.")
    # Check for rocket part at the destination.
    if isinstance(current_state.get("parts"), list) and dest_iso in current_state["parts"]:
        hahmot.add_rocket_part(current_player, 1)
        current_state["parts"].remove(dest_iso)
        if country_name:
            messages.append(f"You found a rocket part in {country_name}!")
    # Award random loot for completing a flight.
    loot = hahmot.generate_loot()
    hahmot.add_loot(current_player, loot)
    gained = [f"{k}+{v}" for k, v in loot.items() if v > 0]
    if gained:
        messages.append("You got loot: " + ", ".join(gained) + ".")
    # Possibly encounter an enemy.
    if taistelu.encounter_chance():
        # Resolve the fight and collect result.
        win = taistelu.taistelu(current_player)
        if win:
            # Winning already consumes ammo inside taistelu.taistelu and adds loot.
            messages.append("Enemy encountered! You used one ammo and won.")
        else:
            messages.append("Enemy encountered but you had no ammo. You lost the fight!")
    return jsonify({"state": current_state, "player": current_player, "messages": messages})

@app.post("/fight")
def fight():

    global current_player
    if current_state is None:
        return jsonify({"Error": "No game running"}), 400
    if current_player is None:
        return jsonify({"Error": "No player"}), 400
    result, updated_player = taistelu.fight(current_player)
    # Assign the updated player reference.
    current_player = updated_player
    return jsonify({"state": current_state, "player": current_player, "result": result})

@app.post("/eat")
def eat_food():

    global current_player
    if current_state is None:
        return jsonify({"Error": "No game running"}), 400
    if current_player is None:
        return jsonify({"Error": "No player"}), 400
    # Ensure the required keys exist.
    if current_player.get("ruoka", 0) <= 0:
        return jsonify({"error": "You have no food to eat."}), 400
    if current_player.get("hp", 100) >= 100:
        return jsonify({"error": "Your HP is already full."}), 400
    # Use one food and restore 10 HP, but not above 100.
    current_player["ruoka"] -= 1
    current_player["hp"] = min(100, current_player["hp"] + 10)
    return jsonify({"state": current_state, "player": current_player})

if __name__ == "__main__":
    # When run directly, start the Flask development server.
    # Bind to localhost to match the API_BASE used in the frontend.
    app.run(host="localhost", port=5000)