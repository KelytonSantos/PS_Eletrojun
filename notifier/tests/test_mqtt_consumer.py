from types import SimpleNamespace

from notifier.mqtt_consumer import MQTTConsumer


class InlineExecutor:
    def submit(self, fn):
        fn()


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.subscriptions = []
        self.connected = None
        self.loop_started = False
        self.auth = None
        self.reconnect_called = False
        self.connect_async_args = None
        self.fail_connect = False
        self.reconnect_delay_args = None

    def username_pw_set(self, username, password):
        self.auth = (username, password)

    def subscribe(self, topic, qos):
        self.subscriptions.append((topic, qos))

    def connect(self, host, port):
        if self.fail_connect:
            raise OSError("broker unavailable")
        self.connected = (host, port)

    def connect_async(self, host, port):
        self.connect_async_args = (host, port)

    def loop_start(self):
        self.loop_started = True

    def loop_stop(self):
        self.loop_started = False

    def disconnect(self):
        self.connected = None

    def reconnect(self):
        self.reconnect_called = True

    def reconnect_delay_set(self, min_delay, max_delay):
        self.reconnect_delay_args = (min_delay, max_delay)


class FakeAlertEngine:
    def __init__(self):
        self.calls = []

    def process_reading(self, reading, source_topic):
        self.calls.append((reading, source_topic))


def test_mqtt_subscribe_connect_and_valid_payload_processing():
    engine = FakeAlertEngine()
    consumer = MQTTConsumer(
        "localhost",
        1883,
        "esp32_Eletrojun_Dht11/sensor",
        1,
        "notifier",
        "user",
        "pass",
        InlineExecutor(),
        engine,
        mqtt_client_factory=FakeClient,
    )

    consumer.start()
    assert consumer.client.connected == ("localhost", 1883)
    assert consumer.client.loop_started is True

    consumer._on_connect(consumer.client, None, None, 0, None)
    assert consumer.client.subscriptions == [("esp32_Eletrojun_Dht11/sensor", 1)]

    msg = SimpleNamespace(
        payload=b"36.5,18.0,2026-10-05T20:34:38", topic="esp32_Eletrojun_Dht11/sensor"
    )
    consumer._on_message(consumer.client, None, msg)
    assert len(engine.calls) == 1


def test_mqtt_ignores_invalid_payloads():
    engine = FakeAlertEngine()
    consumer = MQTTConsumer(
        "localhost",
        1883,
        "esp32_Eletrojun_Dht11/sensor",
        1,
        "notifier",
        None,
        None,
        InlineExecutor(),
        engine,
        mqtt_client_factory=FakeClient,
    )

    msg = SimpleNamespace(payload=b"invalid", topic="esp32_Eletrojun_Dht11/sensor")
    consumer._on_message(consumer.client, None, msg)
    assert engine.calls == []


def test_mqtt_reconnect_and_resubscribe_after_disconnect():
    engine = FakeAlertEngine()
    consumer = MQTTConsumer(
        "localhost",
        1883,
        "esp32_Eletrojun_Dht11/sensor",
        1,
        "notifier",
        None,
        None,
        InlineExecutor(),
        engine,
        mqtt_client_factory=FakeClient,
    )

    consumer._on_disconnect(consumer.client, None, None, 1, None)
    assert consumer.client.reconnect_called is True

    consumer._on_connect(consumer.client, None, None, 0, None)
    assert ("esp32_Eletrojun_Dht11/sensor", 1) in consumer.client.subscriptions


def test_mqtt_start_handles_unavailable_broker_and_enables_async_retry():
    engine = FakeAlertEngine()
    consumer = MQTTConsumer(
        "localhost",
        1883,
        "esp32_Eletrojun_Dht11/sensor",
        1,
        "notifier",
        None,
        None,
        InlineExecutor(),
        engine,
        mqtt_client_factory=FakeClient,
    )
    consumer.client.fail_connect = True

    consumer.start()

    assert consumer.client.reconnect_delay_args == (1, 30)
    assert consumer.client.connect_async_args == ("localhost", 1883)
    assert consumer.client.loop_started is True
