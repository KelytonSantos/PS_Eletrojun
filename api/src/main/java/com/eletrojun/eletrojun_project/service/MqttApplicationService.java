package com.eletrojun.eletrojun_project.service;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;

import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;

import com.eletrojun.eletrojun_project.model.Message;
import com.eletrojun.eletrojun_project.service.event.SensorDataReceivedEvent;

@Service
public class MqttApplicationService {

    private static final Logger log = LoggerFactory.getLogger(MqttApplicationService.class);

    @Value("${app.mqtt.broker:tcp://broker.hivemq.com:1883}")
    private String broker;

    @Value("${app.mqtt.sensor-topic:esp32_Eletrojun_Dht11/sensor}")
    private String subTopic;

    @Value("${app.mqtt.mode-topic:esp32_Eletrojun_Dht11/modo}")
    private String pubTopic;

    // CA-001: Modo inicial deve ser AUTOMATICO
    private final AtomicReference<String> actualMode = new AtomicReference<>("AUTOMATICO");

    private final String clientId = "eletrojun-api-" + UUID.randomUUID().toString().substring(0, 8);
    private MqttClient client;

    private final ApplicationEventPublisher eventPublisher;

    public MqttApplicationService(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }

    @PostConstruct
    public void start() {
        try {
            log.info("Iniciando MqttApplicationService em {} com Client ID {}", broker, clientId);
            client = new MqttClient(broker, clientId, new MemoryPersistence());

            MqttConnectOptions options = new MqttConnectOptions();
            options.setCleanSession(true);
            options.setAutomaticReconnect(true);
            options.setConnectionTimeout(10);
            options.setKeepAliveInterval(30);

            client.connect(options);
            log.info("Conectado com sucesso ao broker MQTT.");

            client.subscribe(subTopic, (topic, mqttMessage) -> {
                try {
                    String payload = new String(mqttMessage.getPayload(), StandardCharsets.UTF_8);
                    Message msg = parsePayload(payload);

                    if (msg != null) {
                        eventPublisher.publishEvent(new SensorDataReceivedEvent(msg));
                    }
                } catch (Exception e) {
                    log.error("Erro ao processar mensagem recebida no tópico {}: {}", topic, e.getMessage());
                }
            });
            log.info("Inscrito no tópico de sensores: {}", subTopic);

        } catch (MqttException e) {
            log.warn("Não foi possível conectar imediatamente ao broker MQTT: {}. Reconexão automática ativa.",
                    e.getMessage());
        }
    }

    public String getActualMode() {
        return actualMode.get();
    }

    public boolean isConnected() {
        return client != null && client.isConnected();
    }

    public void applyMode(String mode) throws MqttException {
        if (mode == null || mode.isBlank()) {
            throw new IllegalArgumentException("Modo não pode ser vazio");
        }

        String normalized = mode.trim().toUpperCase();
        if (!normalized.equals("LIGADO") && !normalized.equals("DESLIGADO") && !normalized.equals("AUTOMATICO")) {
            throw new IllegalArgumentException(
                    "Modo inválido: '" + mode + "'. Valores aceitos: LIGADO, DESLIGADO, AUTOMATICO");
        }

        if (client == null || !client.isConnected()) {
            throw new IllegalStateException("Broker MQTT indisponível");
        }

        MqttMessage msg = new MqttMessage(normalized.getBytes(StandardCharsets.UTF_8));
        msg.setQos(1);
        client.publish(pubTopic, msg);

        actualMode.set(normalized);
        log.info("Modo operacional alterado com sucesso para: {}", normalized);
    }

    public void requestManualReading() throws MqttException {
        String current = actualMode.get();
        if (!"LIGADO".equalsIgnoreCase(current)) {
            throw new IllegalStateException(
                    "Leitura manual só é permitida quando o modo for LIGADO (modo atual: " + current + ")");
        }

        if (client == null || !client.isConnected()) {
            throw new IllegalStateException("Broker MQTT indisponível");
        }

        MqttMessage msg = new MqttMessage("LEITURA".getBytes(StandardCharsets.UTF_8));
        msg.setQos(1);
        client.publish(pubTopic, msg);
        log.info("Comando LEITURA publicado com sucesso no tópico {}", pubTopic);
    }

    public void pub(String mode) {
        try {
            if ("LEITURA".equalsIgnoreCase(mode)) {
                requestManualReading();
            } else {
                applyMode(mode);
            }
        } catch (Exception e) {
            log.error("Erro na publicação MQTT: {}", e.getMessage());
        }
    }

    private Message parsePayload(String payload) {
        if (payload == null || payload.isBlank()) {
            return null;
        }

        String[] partes = payload.split(",");
        if (partes.length < 3) {
            return null;
        }

        try {
            Message msg = new Message();
            msg.setTemperature(Float.parseFloat(partes[0].trim()));
            msg.setHumidity(Float.parseFloat(partes[1].trim()));
            msg.setDateAndTime(LocalDateTime.parse(partes[2].trim()));
            return msg;
        } catch (Exception e) {
            log.warn("Ignorando payload com formato inválido: '{}'", payload);
            return null;
        }
    }

    @PreDestroy
    public void stop() {
        try {
            if (client != null && client.isConnected()) {
                client.disconnect();
                client.close();
                log.info("Cliente MQTT encerrado.");
            }
        } catch (MqttException e) {
            log.error("Erro ao encerrar cliente MQTT: {}", e.getMessage());
        }
    }
}
