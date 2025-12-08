from flask import Flask, request, jsonify
from flask_cors import CORS


import kartta
import hahmot
import taistelu

app = Flask(__name__)
CORS(app)


current_state = None
current_player = None

@app.post("/start")
def start_game():

    global current_state, current_player



    conn = kartta.get_connection()
    current_state = kartta.init_game_state(conn)
    conn.close()

    return jsonify({"state": current_state, "player": current_player})

@app.post("/choose_role")
def choose_role():
    global current_player

    data = request.json
    role = data.get("role")

    try:
        current_player = hahmot.create_player(role)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"state": current_state, "player": current_player})

@app.get("/countries")
def countries():
    global current_state

    if current_state is None:
        return jsonify({"Error": "No game running"}), 400

    conn = kartta.get_connection()
    maat = kartta.nearest_country_options(
        conn,
        current_state  ["location"],
        current_state  ["range_km"]

    )

    conn.close()
    return jsonify(maat)

@app.post("/fly")
def fly():
    global current_state, current_player

    if current_state is None:
        return jsonify({"Error":"No game running"}), 400

    data = request.json
    dest_icao = data.get("icao")
    if not dest_icao:
        return jsonify({"Error":"No icao found"}), 400

    conn = kartta.get_connection()
    ok, state, player = kartta.fly_to(conn, current_player, current_state,dest_icao)
    conn.close()

    if not ok:
        return jsonify({"Error":"Flying failed"})

    current_state = state
    current_player = player

    return jsonify({"state": current_state, "player": current_player})

@app.post("/fight")
def fight():
    global current_player

    if current_state is None:
        return jsonify({"Error":"No game running"}), 400

    result, updated_player = taistelu.fight(current_player)
    current_player = updated_player

    return jsonify({"state": current_state, "player": current_player, "result": result})


if __name__ == "__main__":
    app.run(host="localhost", port=5000)