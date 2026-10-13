from __future__ import annotations

from flask import Flask, jsonify, request

from .storage import AlertStorage


API_PREFIX = "/api/alerts"


def create_http_app(storage: AlertStorage) -> Flask:
    app = Flask(__name__)

    @app.after_request
    def after_request(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        return response

    @app.get(f"{API_PREFIX}/emails")
    def list_emails():
        return jsonify({"success": True, "emails": storage.list_emails()})

    @app.post(f"{API_PREFIX}/email/<path:email>")
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

    @app.delete(f"{API_PREFIX}/email/<path:email>")
    def delete_email(email: str):
        try:
            emails = storage.remove_email(email)
        except ValueError:
            return jsonify({"success": False, "error": "Email vazio ou inválido"}), 400
        return jsonify({"success": True, "emails": emails})

    @app.get(f"{API_PREFIX}/limits")
    def get_limits():
        limits = storage.get_limits()
        return jsonify({"tempMax": limits.temp_max, "humiMin": limits.humi_min})

    @app.post(f"{API_PREFIX}/limits")
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
