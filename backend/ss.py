from flask import Flask, request, jsonify
from flask_cors import CORS

import kartta
import hahmot
import taistelu


app = Flask(__name__)
# Enable Cross-Origin Resource Sharing so that the frontend can make requests
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
        ok, new_state, new_player = kartta.fly_to(conn, current_state, current_player, dest_icao)
    finally:
        conn.close()
    if not ok:
        return jsonify({"Error": "Flying failed"})
    # Assign the updated state/player immediately to retain mutations.
    current_state = new_state
    current_player = new_player
    # Check for rocket part at the destination.
    dest_iso = current_state["location"]["iso_country"]
    if isinstance(current_state.get("parts"), list) and dest_iso in current_state["parts"]:
        hahmot.add_rocket_part(current_player, 1)
        current_state["parts"].remove(dest_iso)
    # Award random loot for completing a flight.
    loot = hahmot.generate_loot()
    hahmot.add_loot(current_player, loot)
    # Possibly encounter an enemy.
    if taistelu.encounter_chance():
        # Resolve the fight but ignore the return value – the player object is mutated.
        taistelu.taistelu(current_player)
    return jsonify({"state": current_state, "player": current_player})

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

if __name__ == "__main__":
    # When run directly, start the Flask development server.
    # Bind to localhost to match the API_BASE used in the frontend.
    app.run(host="localhost", port=5000)