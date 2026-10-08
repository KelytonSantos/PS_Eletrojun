package com.eletrojun.eletrojun_project.controller;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import com.eletrojun.eletrojun_project.model.Message;
import com.eletrojun.eletrojun_project.service.MqttApplicationService;
import com.eletrojun.eletrojun_project.service.event.SensorDataReceivedEvent;

@CrossOrigin(origins = "*")
@RestController
@RequestMapping("/api/realtime")
public class RealtimeController {

    @Autowired
    private MqttApplicationService mqttApplicationService;

    private final List<SseEmitter> emitters = new CopyOnWriteArrayList<>();
    private final List<Message> recentReadings = new CopyOnWriteArrayList<>();
    private static final int MAX_HISTORY_SIZE = 100;

    @GetMapping(value = "/automatico/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
        emitters.add(emitter);

        emitter.onCompletion(() -> emitters.remove(emitter));
        emitter.onTimeout(() -> emitters.remove(emitter));
        emitter.onError((e) -> emitters.remove(emitter));

        if (!recentReadings.isEmpty()) {
            try {
                emitter.send(SseEmitter.event()
                        .name("sensor-readings")
                        .data(recentReadings.get(0)));
            } catch (IOException e) {
                emitters.remove(emitter);
            }
        }

        return emitter;
    }

    @EventListener
    public void onSensorData(SensorDataReceivedEvent event) {
        if (event == null || event.msg() == null) {
            return;
        }

        Message msg = event.msg();

        // Adiciona ao topo do histórico (mais recente primeiro)
        recentReadings.add(0, msg);
        if (recentReadings.size() > MAX_HISTORY_SIZE) {
            recentReadings.remove(recentReadings.size() - 1);
        }

        // Notifica clientes conectados via SSE
        for (SseEmitter emitter : emitters) {
            try {
                emitter.send(SseEmitter.event()
                        .name("sensor-readings")
                        .data(msg));
            } catch (IOException e) {
                emitters.remove(emitter);
            }
        }
    }

    @GetMapping("/history")
    public ResponseEntity<List<Message>> getHistory() {
        return ResponseEntity.ok(Collections.unmodifiableList(new ArrayList<>(recentReadings)));
    }

    @GetMapping("/mode")
    public ResponseEntity<Map<String, Object>> getMode() {
        String currentMode = mqttApplicationService.getActualMode();
        boolean connected = mqttApplicationService.isConnected();

        return ResponseEntity.ok(Map.of(
                "mode", currentMode,
                "mqttConnected", connected));
    }

    @PostMapping("/mode/{mode}")
    public ResponseEntity<Map<String, Object>> setMode(@PathVariable String mode) {
        if (mode == null || mode.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of(
                    "status", "ERROR",
                    "message", "O modo especificado não pode ser vazio."));
        }

        String normalized = mode.trim().toUpperCase();

        // Leitura sob demanda (CA-004 e CA-005)
        if ("LEITURA".equals(normalized)) {
            String currentMode = mqttApplicationService.getActualMode();
            if (!"LIGADO".equalsIgnoreCase(currentMode)) {
                return ResponseEntity.badRequest().body(Map.of(
                        "status", "ERROR",
                        "message",
                        "Leitura manual só é permitida quando o dispositivo estiver no modo LIGADO (modo atual: "
                                + currentMode + ")."));
            }

            if (!mqttApplicationService.isConnected()) {
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of(
                        "status", "ERROR",
                        "message", "Broker MQTT indisponível no momento."));
            }

            try {
                mqttApplicationService.requestManualReading();
                return ResponseEntity.ok(Map.of(
                        "status", "SUCCESS",
                        "mode", currentMode,
                        "message", "Solicitação de leitura manual enviada ao dispositivo."));
            } catch (Exception e) {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                        "status", "ERROR",
                        "message", "Falha ao publicar leitura manual: " + e.getMessage()));
            }
        }

        if (!normalized.equals("LIGADO") && !normalized.equals("DESLIGADO") && !normalized.equals("AUTOMATICO")) {
            return ResponseEntity.badRequest().body(Map.of(
                    "status", "ERROR",
                    "message",
                    "Modo desconhecido: '" + mode + "'. Valores permitidos: LIGADO, DESLIGADO, AUTOMATICO."));
        }

        if (!mqttApplicationService.isConnected()) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of(
                    "status", "ERROR",
                    "message", "Broker MQTT indisponível para aplicar a alteração de modo."));
        }

        try {
            mqttApplicationService.applyMode(normalized);
            return ResponseEntity.ok(Map.of(
                    "status", "SUCCESS",
                    "mode", normalized,
                    "message", "Modo atualizado com sucesso."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of(
                    "status", "ERROR",
                    "message", "Erro ao aplicar modo: " + e.getMessage()));
        }
    }
}
