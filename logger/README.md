# Microsserviço de Registro de Leituras MQTT

## 1. Objetivo

O microsserviço de registro de leituras tem como objetivo receber, validar e armazenar as leituras de temperatura e umidade publicadas por dispositivos, como a ESP32, por meio do protocolo MQTT.

O serviço assina o tópico MQTT configurado, processa as mensagens recebidas e registra as leituras válidas em um arquivo de texto chamado `LogEsp.txt`.

Este microsserviço funciona de maneira **independente da API principal**. Ele possui seu próprio processo de execução, realiza a comunicação diretamente com o broker MQTT e armazena os registros em arquivo, sem depender de endpoints da API para receber ou persistir as leituras.

## 2. Tecnologias utilizadas

- Python 3.
- Paho MQTT para comunicação com o broker.
- Pytest para execução dos testes automatizados.
- Arquivo de texto para armazenamento persistente das leituras.

## 3. Variáveis de ambiente

O serviço utiliza variáveis de ambiente para permitir a configuração sem a necessidade de alterar o código-fonte.

| Variável | Valor padrão | Descrição |
|---|---|---|
| `MQTT_BROKER_URL` | `localhost` | Endereço do broker MQTT. |
| `MQTT_BROKER_PORT` | `1883` | Porta de comunicação com o broker MQTT. |
| `MQTT_CLIENT_ID` | `eletronjun-log-service` | Identificador do cliente MQTT. |
| `MQTT_TOPIC` | `esp32_Eletronjun_Dht11/sensor` | Tópico utilizado para receber as leituras. |
| `LOG_FILE_PATH` | `LogEsp.txt` na pasta do microsserviço | Caminho do arquivo de saída. |

Os valores padrão são utilizados quando as respectivas variáveis de ambiente não são definidas. Se o código utilizar um caminho padrão diferente para o arquivo de log, este valor deverá ser atualizado nesta documentação.

### Exemplo de configuração no PowerShell

```powershell
$env:MQTT_BROKER_URL = "localhost"
$env:MQTT_BROKER_PORT = "1883"
$env:MQTT_CLIENT_ID = "eletronjun-log-service"
$env:MQTT_TOPIC = "esp32_Eletronjun_Dht11/sensor"
$env:LOG_FILE_PATH = "LogEsp.txt"
```

As variáveis definidas dessa forma permanecem disponíveis apenas na sessão atual do terminal.

## 4. Formato das mensagens recebidas

O serviço espera receber mensagens com três campos separados por vírgulas, na seguinte ordem:

```text
temperatura,umidade,data-hora
```

Exemplo de mensagem válida:

```text
24.0,58.0,2026-10-12T11:35:15
```

Os campos representam:

- **Temperatura:** valor numérico da temperatura.
- **Umidade:** valor numérico da umidade.
- **Data-hora:** data e horário associados à leitura, no formato esperado pelo serviço.

Mensagens malformadas, com quantidade incorreta de campos, valores numéricos inválidos ou data-hora inválida devem ser rejeitadas, sem interromper o funcionamento do microsserviço.

## 5. Formato dos registros

Cada leitura válida é armazenada em uma linha do arquivo de log, seguindo o formato:

```text
data-hora | temperatura=X.X | umidade=Y.Y
```

Exemplo:

```text
2026-10-12T11:35:15 | temperatura=24.0 | umidade=58.0
```

O arquivo é aberto em modo de acréscimo, preservando os registros anteriores. Dessa forma, cada nova leitura válida é adicionada ao histórico em uma nova linha.

O acesso ao arquivo deve ser protegido contra escritas simultâneas para evitar conflitos entre operações concorrentes.

## 6. Execução do microsserviço

### Pré-requisitos

- Python instalado.
- Ambiente virtual do projeto configurado.
- Dependências instaladas.
- Broker MQTT em execução e acessível.

### Instalação das dependências

Na raiz do projeto, ative o ambiente virtual e instale as dependências:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Caso o arquivo `requirements.txt` ainda não esteja configurado, instale ao menos a biblioteca MQTT:

```powershell
python -m pip install "paho-mqtt>=2.0,<3.0"
```

### Inicialização

Na raiz do projeto, execute:

```powershell
python log-service/log_service.py
```

Durante a inicialização, o serviço registra informações como endereço do broker, identificador do cliente, tópico utilizado e caminho do arquivo de saída.

## 7. Testes automatizados

Os testes automatizados são executados com Pytest.

Para instalar a ferramenta, caso necessário:

```powershell
python -m pip install pytest
```

Para executar os testes do microsserviço a partir da raiz do projeto:

```powershell
python -m pytest log-service/test_log_service.py -v
```

Os testes devem verificar, conforme a implementação, aspectos como:

- Validação e interpretação das mensagens recebidas.
- Criação do arquivo e acréscimo de novas leituras.
- Preservação do histórico.
- Rejeição de mensagens inválidas.
- Tratamento de erros de escrita.
- Proteção contra escritas concorrentes.
- Assinatura do tópico após a conexão e após uma reconexão.

## 8. Teste manual com MQTT

Com o broker Mosquitto em execução, uma mensagem de teste pode ser publicada com o comando:

```powershell
& "C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -p 1883 -t "esp32_Eletronjun_Dht11/sensor" -m "24.0,58.0,2026-10-12T11:35:15"
```

Após a publicação, verifique se a leitura foi recebida pelo serviço e adicionada ao arquivo `LogEsp.txt`.

## 9. Reconexão e tratamento de falhas

### Reconexão MQTT

O microsserviço utiliza os mecanismos de reconexão da biblioteca Paho MQTT para tentar restabelecer a conexão quando ela é perdida.

Após uma conexão bem-sucedida, o serviço realiza novamente a assinatura do tópico configurado. Isso permite que as mensagens voltem a ser recebidas após uma reconexão.

Os eventos de conexão, desconexão e falha devem ser registrados nos logs da aplicação para facilitar o diagnóstico.

### Falhas de escrita

Se ocorrer um erro ao criar diretórios, abrir o arquivo ou gravar uma leitura, o serviço deve registrar o erro de forma explícita.

O tratamento de falhas evita que problemas de armazenamento passem despercebidos. O comportamento de recuperação depende da implementação: uma leitura cuja gravação falhou não deve ser considerada persistida com sucesso.

### Mensagens inválidas

Mensagens que não respeitem o formato esperado são rejeitadas e registradas para diagnóstico. O processamento deve continuar para permitir o recebimento de leituras válidas posteriores.

### Segurança

O serviço não deve registrar senhas, tokens ou outros dados sensíveis nos logs. As configurações devem ser fornecidas por variáveis de ambiente quando apropriado.