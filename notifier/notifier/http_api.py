from __future__ import annotations

from flask import Flask, jsonify, request

from .storage import AlertStorage


def create_http_app(storage: AlertStorage) -> Flask:
    app = Flask(__name__)

    @app.get("/api/realtime/emails")
    def list_emails():
        return jsonify({"success": True, "emails": storage.list_emails()})

    @app.post("/api/realtime/email/<path:email>")
    def add_email(email: str):
        try:
            emails = storage.add_email(email)
        except ValueError:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Email vazio, inválido ou já cadastrado",
                    }
                ),
                400,
            )
        return jsonify({"success": True, "emails": emails})

    @app.delete("/api/realtime/email/<path:email>")
    def delete_email(email: str):
        try:
            emails = storage.remove_email(email)
        except ValueError:
            return jsonify({"success": False, "error": "Email vazio ou inválido"}), 400
        return jsonify({"success": True, "emails": emails})

    @app.get("/api/realtime/limits")
    def get_limits():
        limits = storage.get_limits()
        return jsonify({"tempMax": limits.temp_max, "humiMin": limits.humi_min})

    @app.post("/api/realtime/limits")
    def update_limits():
        body = request.get_json(silent=True)
        temp = None
        humi = None

        if isinstance(body, dict):
            temp = body.get("temp")
            humi = body.get("humi")

        if temp is None or humi is None:
            temp = request.args.get("temp", temp)
            humi = request.args.get("humi", humi)

        if temp is None or humi is None:
            return jsonify({"success": False, "error": "temp and humi are required"}), 400

        try:
            limits = storage.update_limits(temp=temp, humi=humi)
        except ValueError:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "temp e humi são obrigatórios, finitos e dentro das faixas permitidas",
                    }
                ),
                400,
            )

        return jsonify({"success": True, "tempMax": limits.temp_max, "humiMin": limits.humi_min})

    return app
