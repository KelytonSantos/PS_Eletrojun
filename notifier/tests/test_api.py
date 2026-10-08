from pathlib import Path

from notifier.http_api import create_http_app
from notifier.storage import AlertStorage


def test_email_crud_and_validation(tmp_path: Path):
    storage = AlertStorage(str(tmp_path / "alerts.sqlite3"))
    app = create_http_app(storage)
    client = app.test_client()

    res = client.post("/api/realtime/email/test@example.com")
    assert res.status_code == 200
    assert res.json["emails"] == ["test@example.com"]

    res = client.post("/api/realtime/email/TEST@example.com")
    assert res.status_code == 400

    res = client.post("/api/realtime/email/invalid")
    assert res.status_code == 400

    res = client.get("/api/realtime/emails")
    assert res.status_code == 200
    assert res.json["emails"] == ["test@example.com"]

    res = client.delete("/api/realtime/email/missing@example.com")
    assert res.status_code == 200

    res = client.delete("/api/realtime/email/test@example.com")
    assert res.status_code == 200
    assert res.json["emails"] == []


def test_limits_get_and_update_json_and_query(tmp_path: Path):
    storage = AlertStorage(str(tmp_path / "alerts.sqlite3"))
    app = create_http_app(storage)
    client = app.test_client()

    res = client.get("/api/realtime/limits")
    assert res.status_code == 200
    assert res.json == {"tempMax": 35.0, "humiMin": 20.0}

    res = client.post("/api/realtime/limits", json={"temp": 34.0, "humi": 19.0})
    assert res.status_code == 200
    assert res.json["tempMax"] == 34.0
    assert res.json["humiMin"] == 19.0

    res = client.post("/api/realtime/limits?temp=33.0&humi=18.0")
    assert res.status_code == 200
    assert res.json["tempMax"] == 33.0
    assert res.json["humiMin"] == 18.0

    res = client.post("/api/realtime/limits", json={"temp": 200})
    assert res.status_code == 400

    res = client.get("/api/realtime/limits")
    assert res.json == {"tempMax": 33.0, "humiMin": 18.0}
