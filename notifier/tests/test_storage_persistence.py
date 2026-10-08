from notifier.storage import AlertStorage


def test_persistence_survives_restart(tmp_path):
    db_path = tmp_path / "alerts.sqlite3"

    storage = AlertStorage(str(db_path))
    storage.add_email("user@example.com")
    storage.update_limits(temp=31.5, humi=25.5)

    restarted = AlertStorage(str(db_path))
    assert restarted.list_emails() == ["user@example.com"]

    limits = restarted.get_limits()
    assert limits.temp_max == 31.5
    assert limits.humi_min == 25.5
