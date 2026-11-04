from flask import Flask, jsonify, request


app = Flask(__name__)

# Events gemmes i hukommelsen og nulstilles, når API-processen genstartes.
events = [
    {
        "id": 1,
        "title": "Quizaften",
        "date": "2026-11-13",
        "capacity": 3,
        "participants": ["Anna", "Bo"],
    },
    {
        "id": 2,
        "title": "Brætspilsaften",
        "date": "2026-11-20",
        "capacity": 10,
        "participants": [],
    },
]


# Tælleren sikrer, at slettede event-ID'er ikke genbruges i samme proces.
next_event_id = 3


@app.get("/events")
def get_events():
    """Returnerer alle events som JSON."""
    return jsonify(events), 200




@app.get("/events/<int:event_id>")
def get_event(event_id):
    """Returnerer det ønskede event eller en JSON-fejl, hvis det ikke findes."""
    for event in events:
        if event["id"] == event_id:
            return jsonify(event), 200

    return jsonify({"error": "Eventet findes ikke"}), 404




@app.post("/events")
def create_event():
    """Validerer forespørgslen og opretter et event med et unikt ID."""
    global next_event_id

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Body skal være et JSON-objekt"}), 400

    title = data.get("title")
    date = data.get("date")
    capacity = data.get("capacity")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "title skal være en ikke-tom tekst"}), 400

    if not isinstance(date, str) or not date.strip():
        return jsonify({"error": "date skal være en ikke-tom tekst"}), 400

    if type(capacity) is not int or capacity <= 0:
        return jsonify({"error": "capacity skal være et positivt heltal"}), 400

    event = {
        "id": next_event_id,
        "title": title.strip(),
        "date": date.strip(),
        "capacity": capacity,
        "participants": [],
    }

    events.append(event)
    next_event_id += 1

    return jsonify(event), 201





@app.post("/events/<int:event_id>/signups")
def create_signup(event_id):
    """Tilmelder en deltager, hvis eventet har plads, og navnet ikke er tilmeldt."""
    for event in events:
        if event["id"] == event_id:
            data = request.get_json(silent=True)

            if not isinstance(data, dict):
                return jsonify({"error": "Body skal være et JSON-objekt"}), 400

            name = data.get("name")

            if not isinstance(name, str) or not name.strip():
                return jsonify({"error": "name skal være en ikke-tom tekst"}), 400

            name = name.strip()

            if name in event["participants"]:
                return jsonify({"error": "Personen er allerede tilmeldt"}), 409

            if len(event["participants"]) >= event["capacity"]:
                return jsonify({"error": "Eventet er fuldt"}), 409

            event["participants"].append(name)

            return jsonify(event), 201

    return jsonify({"error": "Eventet findes ikke"}), 404





@app.delete("/events/<int:event_id>/signups/<string:name>")
def delete_signup(event_id, name):
    """Fjerner en eksisterende tilmelding fra det ønskede event."""
    for event in events:
        if event["id"] == event_id:
            if name not in event["participants"]:
                return jsonify({"error": "Tilmeldingen findes ikke"}), 404

            event["participants"].remove(name)

            return "", 204

    return jsonify({"error": "Eventet findes ikke"}), 404




@app.delete("/events/<int:event_id>")
def delete_event(event_id):
    """Sletter det ønskede event inklusive dets tilmeldinger."""
    for event in events:
        if event["id"] == event_id:
            events.remove(event)

            return "", 204

    return jsonify({"error": "Eventet findes ikke"}), 404



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)