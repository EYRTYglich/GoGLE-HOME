from flask import Flask, request, jsonify, send_from_directory
import os
import threading

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Aktualna wartość
value = "00000000"

# Zabezpieczenie przed jednoczesnym dostępem
value_lock = threading.Lock()


# =========================
# STRONA GŁÓWNA
# =========================

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


# =========================
# CONTROL
# =========================

@app.route("/control.html")
def control():
    return send_from_directory(BASE_DIR, "control.html")


# =========================
# API SEND
# =========================

@app.route("/api/send", methods=["POST"])
def send_api():

    global value

    # Pobierz JSON
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "success": False,
            "error": "Nieprawidlowy JSON"
        }), 400

    # Sprawdź value
    if "value" not in data:
        return jsonify({
            "success": False,
            "error": "Brak value"
        }), 400

    new_value = str(data["value"])


    # =========================
    # SPRAWDZ BINARNĄ WARTOŚĆ
    # =========================

    if len(new_value) != 8:

        return jsonify({
            "success": False,
            "error": "value musi miec 8 bitow"
        }), 400


    if any(bit not in "01" for bit in new_value):

        return jsonify({
            "success": False,
            "error": "value musi zawierac tylko 0 i 1"
        }), 400


    # =========================
    # ZAPISZ WARTOŚĆ
    # =========================

    with value_lock:

        value = new_value


    print("VALUE =", value)


    return jsonify({
        "success": True,
        "value": value
    })


# =========================
# API VALUE
# =========================

@app.route("/api/value", methods=["GET"])
def value_api():

    with value_lock:

        current_value = value


    return jsonify({
        "success": True,
        "value": current_value
    })


# =========================
# START
# =========================

if __name__ == "__main__":

    print("================================")
    print("SERVER STARTED")
    print("================================")

    print("SEND:")
    print("http://127.0.0.1:5000/")

    print("CONTROL:")
    print("http://127.0.0.1:5000/control.html")

    print("API VALUE:")
    print("http://127.0.0.1:5000/api/value")

    print("================================")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )