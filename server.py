from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import random
import time
import threading

app = Flask(__name__)
CORS(app)

rooms = {}

def cleanup_players():
    while True:
        time.sleep(5)
        now = time.time()
        for code in list(rooms.keys()):
            room = rooms[code]
            to_remove = [n for n, p in room["players"].items() if now - p.get("last_seen", 0) > 15]
            for nick in to_remove:
                del room["players"][nick]
            if not room["players"]:
                del rooms[code]

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "online"})

@app.route('/join', methods=['POST'])
def join():
    data = request.json
    code, nick = data['room_code'], data['nick']
    if code not in rooms:
        rooms[code] = {"players": {}, "status": "lobby", "found_order": [], "next_seeker": None}
    rooms[code]["players"][nick] = {
        "lat": 0, "lon": 0, "role": "viewer", "found": False, 
        "ready": False, "pos_locked": False, "last_seen": time.time()
    }
    return jsonify({"status": "joined"})

@app.route('/update', methods=['POST'])
def update():
    data = request.json
    code, nick = data['room_code'], data['nick']
    if code in rooms and nick in rooms[code]["players"]:
        p = rooms[code]["players"][nick]
        p["last_seen"] = time.time()
        # Aktualizuj pozycję tylko jeśli nie jest "zamrożona" (dla chowającego się)
        if p["role"] == "seeker" or not p["pos_locked"]:
            p["lat"] = float(data.get('lat', 0))
            p["lon"] = float(data.get('lon', 0))
        return jsonify(rooms[code])
    return jsonify({"error": "Session lost"}), 404

@app.route('/ready', methods=['POST'])
def ready():
    data = request.json
    code, nick = data['room_code'], data['nick']
    room = rooms.get(code)
    if room and nick in room["players"]:
        room["players"][nick]["ready"] = True
        all_ready = all(p["ready"] for p in room["players"].values())
        if all_ready and len(room["players"]) >= 2:
            p_list = list(room["players"].keys())
            seeker = room["next_seeker"] if room["next_seeker"] in p_list else random.choice(p_list)
            for n in room["players"]:
                room["players"][n].update({"role": "seeker" if n == seeker else "hider", "found": False, "pos_locked": False})
            room["status"] = "playing"
            room["found_order"] = []
        return jsonify({"status": "ok"})
    return jsonify({"error": "Not found"}), 404

@app.route('/lock_position', methods=['POST'])
def lock_position():
    data = request.json
    code, nick = data['room_code'], data['nick']
    if code in rooms and nick in rooms[code]["players"]:
        rooms[code]["players"][nick]["pos_locked"] = True
        return jsonify({"status": "locked"})
    return jsonify({"error": "Not found"}), 404

@app.route('/mark_found', methods=['POST'])
def mark_found():
    data = request.json
    code, nick = data['room_code'], data['nick'] # nick to osoba znaleziona
    room = rooms.get(code)
    if room and nick in room["players"]:
        p = room["players"][nick]
        if not p["found"]:
            p["found"] = True
            room["found_order"].append(nick)
            if len(room["found_order"]) == 1: room["next_seeker"] = nick
            hiders = [n for n, pl in room["players"].items() if pl["role"] == "hider"]
            if all(room["players"][n]["found"] for n in hiders):
                room["status"] = "lobby"
                for n in room["players"]: room["players"][n]["ready"] = False
            return jsonify({"status": "ok"})
    return jsonify({"error": "Not found"}), 404

@app.route('/leave', methods=['POST'])
def leave():
    data = request.json
    code, nick = data['room_code'], data['nick']
    if code in rooms and nick in rooms[code]["players"]:
        del rooms[code]["players"][nick]
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    threading.Thread(target=cleanup_players, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)