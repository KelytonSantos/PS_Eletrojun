import math
import threading
from unittest.mock import MagicMock, patch

import pytest

import log_service as service

# ============================================================
# TESTES DE VALIDAÇÃO — CA-004
# ============================================================

@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (
            "24.0,58.0,2026-10-05T17:00:29",
            (24.0, 58.0, "2026-10-05T17:00:29"),
        ),
        (
            "25.5,60.2,2026-10-05T17:00:29",
            (25.5, 60.2, "2026-10-05T17:00:29"),
        ),
    ],
)
def test_payload_valido(payload, expected):
    assert service.validate_and_parse(payload) == expected


@pytest.mark.parametrize(
    "payload",
    [
        "",
        "   ",
        "24.0,58.0",
        "24.0,58.0,2026-10-05T17:00:29,extra",
        "abc,58.0,2026-10-05T17:00:29",
        "24.0,abc,2026-10-05T17:00:29",
        "NaN,58.0,2026-10-05T17:00:29",
        "24.0,inf,2026-10-05T17:00:29",
        "24.0,-inf,2026-10-05T17:00:29",
        "24.0,58.0,data-invalida",
        "24.0,58.0,",
    ],
)
def test_payload_invalido(payload):
    with pytest.raises(ValueError):
        service.validate_and_parse(payload)


# ============================================================
# TESTES DE ARQUIVO — CA-002, CA-003 E CA-007
# ============================================================

def test_cria_arquivo_e_acrescenta_leitura(tmp_path, monkeypatch):
    log_file = tmp_path / "logs" / "LogEsp.txt"
    monkeypatch.setattr(service, "LOG_FILE", log_file)

    service.write_log("2026-10-05T17:00:29 | temperatura=24.0 | umidade=58.0")

    assert log_file.exists()
    assert log_file.read_text(encoding="utf-8") == (
        "2026-10-05T17:00:29 | temperatura=24.0 | umidade=58.0\n"
    )


def test_preserva_historico(tmp_path, monkeypatch):
    log_file = tmp_path / "LogEsp.txt"
    log_file.write_text("registro anterior\n", encoding="utf-8")
    monkeypatch.setattr(service, "LOG_FILE", log_file)

    service.write_log("novo registro")

    assert log_file.read_text(encoding="utf-8") == (
        "registro anterior\nnovo registro\n"
    )


def test_falha_de_escrita_e_explicita(tmp_path, monkeypatch):
    # Um diretório não pode ser aberto como arquivo de texto.
    log_file = tmp_path / "sou_um_diretorio"
    log_file.mkdir()
    monkeypatch.setattr(service, "LOG_FILE", log_file)

    with pytest.raises(OSError):
        service.write_log("teste")


# ============================================================
# TESTES DE MENSAGENS — CONTINUIDADE DO CONSUMIDOR
# ============================================================

def test_mensagem_invalida_nao_grava_e_valida_posterior_grava(
    tmp_path, monkeypatch
):
    log_file = tmp_path / "LogEsp.txt"
    monkeypatch.setattr(service, "LOG_FILE", log_file)

    invalid_message = MagicMock()
    invalid_message.payload = b"mensagem invalida"

    valid_message = MagicMock()
    valid_message.payload = b"24.0,58.0,2026-10-05T17:00:29"

    with patch.object(service.logger, "warning") as warning:
        service.on_message(None, None, invalid_message)
        warning.assert_called_once()

    service.on_message(None, None, valid_message)

    assert log_file.read_text(encoding="utf-8") == (
        "2026-10-05T17:00:29 | temperatura=24.0 | umidade=58.0\n"
    )


def test_falha_de_escrita_nao_anuncia_sucesso(monkeypatch):
    message = MagicMock()
    message.payload = b"24.0,58.0,2026-10-05T17:00:29"

    with (
        patch.object(
            service,
            "write_log",
            side_effect=PermissionError("acesso negado"),
        ),
        patch.object(service.logger, "exception") as log_error,
        patch.object(service.logger, "info") as log_info,
    ):
        service.on_message(None, None, message)

    log_error.assert_called_once()
    log_info.assert_not_called()


# ============================================================
# TESTE DE CONCORRÊNCIA — CA-006
# ============================================================

def test_escritas_concorrentes_sem_misturar_linhas(
    tmp_path, monkeypatch
):
    log_file = tmp_path / "LogEsp.txt"
    monkeypatch.setattr(service, "LOG_FILE", log_file)

    quantidade = 100

    threads = [
        threading.Thread(
            target=service.write_log,
            args=(f"registro-{i:03d}",),
        )
        for i in range(quantidade)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    linhas = log_file.read_text(encoding="utf-8").splitlines()

    assert len(linhas) == quantidade
    assert set(linhas) == {
        f"registro-{i:03d}" for i in range(quantidade)
    }

def test_assina_topico_ao_conectar():
    client = MagicMock()
    client.subscribe.return_value = (service.mqtt.MQTT_ERR_SUCCESS, 1)

    # Simula a primeira conexão bem-sucedida.
    service.on_connect(
        client,
        None,
        {},
        service.mqtt.ReasonCode(
            service.mqtt.PacketTypes.CONNACK, "Success"
        ),
        None,
    )

    client.subscribe.assert_called_once_with(service.TOPIC)


def test_reassina_topico_apos_reconexao():
    client = MagicMock()
    client.subscribe.return_value = (service.mqtt.MQTT_ERR_SUCCESS, 1)

    # Duas conexões bem-sucedidas simulam a conexão inicial
    # e uma reconexão posterior.
    success = service.mqtt.ReasonCode(
        service.mqtt.PacketTypes.CONNACK, "Success"
    )

    service.on_connect(client, None, {}, success, None)
    service.on_connect(client, None, {}, success, None)

    assert client.subscribe.call_count == 2