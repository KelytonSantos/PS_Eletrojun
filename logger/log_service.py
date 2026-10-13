import logging
import math
import os
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import paho.mqtt.client as mqtt
#=======================================================================================
#CONFIGURAÇÕES
#=======================================================================================

#Diretório do próprio microsservico, independente de onde o comando Python for executado
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(dotenv_path=BASE_DIR/ ".env")


BROKER_URL = os.getenv("MQTT_BROKER_URL", "localhost")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "eletronjun-log-service")
TOPIC = os.getenv(
    "MQTT_TOPIC",
    "esp32_Eletronjun_Dht11/sensor",   
)

#O padrão fica ao lado do código, não no diretório de execução acidental do terminal
LOG_FILE_CONFIG = os.getenv("LOG_FILE_PATH", "LogEsp.txt")
LOG_FILE = Path(LOG_FILE_CONFIG).expanduser()

if not LOG_FILE.is_absolute():
    LOG_FILE = BASE_DIR / LOG_FILE

LOG_FILE = LOG_FILE.resolve()

#Impede que duas callbacks da mesma instância escrevam simultaneamente no arquivo.
file_lock = threading.Lock()

#Formato da saída operacional no terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("eletronjun.log.service")

#=======================================================================================
#VALIDAÇÃO DO PAYLOAD - CA-004
#=======================================================================================

def validate_and_parse(payload: str):
    """ 
    Valida o formato: temperatuda, umidade, data-hora
    Retorna: (temperatura, umidade, timestamp_original)
    A data/hora original é preservada na saída
    """
    if not payload or not payload.strip(","):
        raise ValueError("Payload vazio.")

    parts = payload.split(",")

    if len(parts) != 3:
        raise ValueError(
            f"Esperado 3 campos; foram recebidos {len(parts)}."
        )

    try:
        temperatura = float(parts[0].strip())
        umidade = float(parts[1].strip())
    except ValueError as exc:
        raise ValueError("Temperatura ou umidade não é numérica.") from exc

    #Rejeita NaN, +inf e -inf
    if not math.isfinite(temperatura):
        raise ValueError("Temperatura não é um valor finito.")

    if not math.isfinite(umidade):
        raise ValueError("Umidade não é um valor finito.")

    timestamp = parts[2].strip()

    if not timestamp:
        raise ValueError("Sem data/hora.")

    try:
        datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ValueError(f"Data/hora inválida: {timestamp!r}.") from exc

    return temperatura, umidade, timestamp

#=======================================================================================
#PERSISTÊNCIA - CA-002, CA-003, CA-006 E CA-007
#=======================================================================================

def write_log(log_line: str):
    """
    Acrescenta uma linha ao arquivo sem apagar o histórico.
    Cria os diretórios necessários e propago os erros de I/O
    para que o callback não anuncie sucesso indevidamente
    """

    with file_lock:
        #cria a pasta pai, se necessário
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        #'a' preserva os registros anteriores, o bloco garante o fechamento do arquivo
        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(log_line + "\n")

#=======================================================================================
#CALLBACKS MQTT - CA-001 E CA-005
#=======================================================================================

def on_connect(client, userdata, flags, reason_code, properties):
    """
    Executada após cada conexão bem-sucedida
    A assinatura é feita novamente sempre que há reconexão ao broker
    """

    if reason_code == 0:
        logger.info("Conexão MQTT estabelecida.")

        result, _ = client.subscribe(TOPIC)

        if result == mqtt.MQTT_ERR_SUCCESS:
            logger.info("Solicitada assinatura do tópico: %s", TOPIC)
        else:
            logger.error("Falha ao solicitar assinatura do tópico: %s código: %s", TOPIC, result)

    else:
        logger.error("Falha na conexão MQTT: %s", reason_code)

      
def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """
    Registra a desconexão para fins de observabilidade.
    """

    if reason_code == 0:
        logger.info("MQTT desconectado normalmente.")
    else:
        logger.warning(
            "Conexão MQTT perdida; o cliente tentará reconectar. "
            "Motivo: %s", reason_code
            )


def on_message(client, userdata, msg):
    """Processa mensagens sem interrupção"""

    try:
        payload = msg.payload.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("Mensagem inválida: payload não é UTF-8.")
        return

    try:
        temperatura, umidade, timestamp = validate_and_parse(payload)

    except ValueError as exc:
        #Não registra payload completo
        logger.warning("Mensagem inválida rejeitada: %s", exc)
        return

    #Mantém o formato estável
    log_line = (f"{timestamp} | temperatura={temperatura:.1f} | umidade={umidade:.1f}")

    try:
        write_log(log_line)
    except OSError:
        #Registra o erro com traceback
        logger.exception("Falha ao gravar leitura no arquivo %s", LOG_FILE)
        return

    logger.info("Leitura registrada: %s", log_line)

#=======================================================================================
#INICIALIAZAÇÃO DO MICROSSERVIÇO
#=======================================================================================

def main():
    logger.info("Iniciando microsserviço de log MQTT.")
    logger.info("Broker: %s:%s", BROKER_URL, BROKER_PORT)
    logger.info("Client ID: %s", CLIENT_ID)
    logger.info("Tópico: %s", TOPIC)
    logger.info("Arquivo de log: %s", LOG_FILE)

    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.reconnect_delay_set(min_delay=1, max_delay=120)

    try:
        client.connect(BROKER_URL, BROKER_PORT, keepalive=60)
        client.loop_forever()

    except KeyboardInterrupt:
        logger.info("Encerramento solicitado pelo operador.")

    except (OSError, ValueError):
        logger.exception("Falha na execução do cliente MQTT.")

    finally:
        client.disconnect()
        logger.info("Microsserviço encerrado.")

if __name__ == "__main__":
    main()