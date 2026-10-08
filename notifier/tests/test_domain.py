from datetime import datetime

import pytest

from notifier.domain import parse_sensor_payload, validate_limits


@pytest.mark.parametrize(
    "payload",
    [
        "",
        "36.5,18.0",
        "abc,18.0,2026-10-05T20:34:38",
        "nan,18.0,2026-10-05T20:34:38",
        "36.5,inf,2026-10-05T20:34:38",
        "36.5,18.0,not-a-date",
    ],
)
def test_parse_sensor_payload_invalid(payload):
    with pytest.raises(ValueError):
        parse_sensor_payload(payload)


def test_parse_sensor_payload_accepts_spaces():
    reading = parse_sensor_payload(" 36.5 , 18.0 , 2026-10-05T20:34:38 ")
    assert reading.temperature == 36.5
    assert reading.humidity == 18.0
    assert reading.measured_at == datetime(2026, 10, 5, 20, 34, 38)


def test_validate_limits_range_and_required_values():
    limits = validate_limits(35.0, 20.0)
    assert limits.temp_max == 35.0
    assert limits.humi_min == 20.0

    with pytest.raises(ValueError):
        validate_limits(121, 20)
    with pytest.raises(ValueError):
        validate_limits(35, -1)
