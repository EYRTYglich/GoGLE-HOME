from flask import Flask, request, jsonify, send_from_directory, redirect
import os
import threading

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# AKTUALNA WARTOŚĆ
# =========================

value = "00000000"

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

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "success": False,
            "error": "Nieprawidlowy JSON"
        }), 400

    if "value" not in data:
        return jsonify({
            "success": False,
            "error": "Brak value"
        }), 400

    new_value = str(data["value"])

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
# FAKE AUTH
# =========================

@app.route("/fakeauth", methods=["GET"])
def fakeauth():

    redirect_uri = request.args.get("redirect_uri")
    state = request.args.get("state")

    if not redirect_uri:
        return jsonify({
            "success": False,
            "error": "Brak redirect_uri"
        }), 400

    code = "test_auth_code"

    return redirect(
        redirect_uri
        + "?code="
        + code
        + "&state="
        + (state or "")
    )


# =========================
# FAKE TOKEN
# =========================

@app.route("/faketoken", methods=["POST"])
def faketoken():

    grant_type = request.form.get("grant_type")

    if grant_type == "authorization_code":

        return jsonify({
            "token_type": "Bearer",
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        })

    if grant_type == "refresh_token":

        return jsonify({
            "token_type": "Bearer",
            "access_token": "test_access_token",
            "expires_in": 3600
        })

    return jsonify({
        "error": "unsupported_grant_type"
    }), 400


# =========================
# GOOGLE SMART HOME
# =========================

@app.route("/google/smarthome", methods=["POST"])
def google_smarthome():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Brak JSON"
        }), 400

    request_id = data.get("requestId", "unknown")

    inputs = data.get("inputs", [])

    if not inputs:
        return jsonify({
            "error": "Brak inputs"
        }), 400

    intent = inputs[0].get("intent")

    print("")
    print("================================")
    print("GOOGLE HOME")
    print("INTENT:", intent)
    print("================================")

    # =========================
    # SYNC
    # =========================

    if intent == "action.devices.SYNC":

        devices = []

        for number in range(1, 9):

            devices.append({
                "id": "switch_" + str(number),

                "type": "action.devices.types.SWITCH",

                "traits": [
                    "action.devices.traits.OnOff"
                ],

                "name": {
                    "defaultNames": [
                        "Switch " + str(number)
                    ],

                    "name": "Switch " + str(number),

                    "nicknames": [
                        str(number),
                        "switch " + str(number)
                    ]
                },

                "willReportState": False
            })

        return jsonify({
            "requestId": request_id,

            "payload": {
                "agentUserId": "render_user",

                "devices": devices
            }
        })


    # =========================
    # QUERY
    # =========================

    if intent == "action.devices.QUERY":

        device_ids = inputs[0].get(
            "payload",
            {}
        ).get(
            "devices",
            []
        )

        with value_lock:
            current_value = value

        devices = {}

        for device in device_ids:

            device_id = device.get("id")

            if not device_id:
                continue

            try:
                number = int(
                    device_id.replace(
                        "switch_",
                        ""
                    )
                )

            except:
                continue

            if number < 1 or number > 8:
                continue

            bit = "0" * (number - 1) + "1" + "0" * (8 - number)

            devices[device_id] = {
                "online": True,
                "on": current_value == bit
            }

        return jsonify({
            "requestId": request_id,

            "payload": {
                "devices": devices
            }
        })


    # =========================
    # EXECUTE
    # =========================

    if intent == "action.devices.EXECUTE":

        commands = inputs[0].get(
            "payload",
            {}
        ).get(
            "commands",
            []
        )

        results = []

        for command in commands:

            devices = command.get(
                "devices",
                []
            )

            executions = command.get(
                "execution",
                []
            )

            for execution in executions:

                command_name = execution.get(
                    "command"
                )

                params = execution.get(
                    "params",
                    {}
                )

                if command_name != "action.devices.commands.OnOff":
                    continue

                requested_state = params.get(
                    "on"
                )

                for device in devices:

                    device_id = device.get("id")

                    if not device_id:
                        continue

                    try:
                        number = int(
                            device_id.replace(
                                "switch_",
                                ""
                            )
                        )

                    except:
                        continue

                    if number < 1 or number > 8:
                        continue

                    # 1 = 00000001
                    # 2 = 00000010
                    # ...
                    # 8 = 10000000

                    if requested_state:

                        new_value = (
                            "0" * (number - 1)
                            + "1"
                            + "0" * (8 - number)
                        )

                    else:

                        new_value = "00000000"

                    global value

                    with value_lock:
                        value = new_value

                    print(
                        "GOOGLE:",
                        device_id,
                        "ON" if requested_state else "OFF",
                        "->",
                        new_value
                    )

                    results.append({
                        "ids": [
                            device_id
                        ],

                        "status": "SUCCESS",

                        "states": {
                            "online": True,
                            "on": requested_state
                        }
                    })

        return jsonify({
            "requestId": request_id,

            "payload": {
                "commands": results
            }
        })


    # =========================
    # DISCONNECT
    # =========================

    if intent == "action.devices.DISCONNECT":

        print("GOOGLE HOME DISCONNECT")

        return jsonify({})


    # =========================
    # NIEZNANY INTENT
    # =========================

    return jsonify({
        "error": "Unknown intent"
    }), 400


# =========================
# START SERWERA
# =========================

if __name__ == "__main__":

    print("================================")
    print("SERVER STARTED")
    print("================================")

    print("PORT: 10000")

    print("HOME:")
    print("http://127.0.0.1:10000/")

    print("CONTROL:")
    print("http://127.0.0.1:10000/control.html")

    print("API VALUE:")
    print("http://127.0.0.1:10000/api/value")

    print("API SEND:")
    print("http://127.0.0.1:10000/api/send")

    print("FAKE AUTH:")
    print("http://127.0.0.1:10000/fakeauth")

    print("FAKE TOKEN:")
    print("http://127.0.0.1:10000/faketoken")

    print("GOOGLE HOME:")
    print("http://127.0.0.1:10000/google/smarthome")

    print("================================")

    app.run(
        host="0.0.0.0",
        port=10000,
        debug=False
    )
