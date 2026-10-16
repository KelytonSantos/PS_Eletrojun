// www/javascript/notifications.js

const API_BASE = "http://localhost:8080";
const REALTIME_URL = `${API_BASE}/api/realtime`;
const ALERTS_URL = `${API_BASE}/api/alerts`;

const apiAlerts = {
  // Conecta ao Stream SSE da API Java
  conectarStream(callbackDados) {
    const eventSource = new EventSource(`${REALTIME_URL}/automatico/stream`);

    eventSource.addEventListener("sensor-readings", (event) => {
      try {
        const dados = JSON.parse(event.data);
        callbackDados(dados);
      } catch (e) {
        console.error("Erro ao parsear os dados do SSE: ", e);
      }
    });

    eventSource.onerror = (err) => {
      console.warn("Conexão SSE caiu ou reconectando...", err);
    };

    return eventSource;
  },

  // Consulta os limites para alerta
  async obterLimites() {
    try {
      const response = await fetch(`${ALERTS_URL}/limits`);
      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error("Erro ao obter limites:", error);
      return null;
    }
  },

  // Atualiza limites de alerta (POST /api/alerts/limits)
  async setControle(temperatura, umidade) {
    try {
      const response = await fetch(`${ALERTS_URL}/limits`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          temp: Number(temperatura),
          humi: Number(umidade),
        }),
      });
      return response.ok;
    } catch (error) {
      console.error("Erro ao enviar limites:", error);
      return false;
    }
  },

  // Lista os e-mails cadastrados (GET /api/alerts/emails)
  async listarEmails() {
    try {
      const response = await fetch(`${ALERTS_URL}/emails`);
      if (response.ok) {
        const data = await response.json();
        return Array.isArray(data.emails) ? data.emails : [];
      }
      return [];
    } catch (error) {
      console.error("Erro ao buscar e-mails:", error);
      return [];
    }
  },

  // Adiciona e-mail destinatário (POST /api/alerts/email/{email})
  async adicionarEmail(email) {
    try {
      const response = await fetch(
        `${ALERTS_URL}/email/${encodeURIComponent(email)}`,
        { method: "POST" },
      );
      return response.ok;
    } catch (error) {
      console.error("Erro ao adicionar e-mail:", error);
      return false;
    }
  },

  // Remove um e-mail cadastrado (DELETE /api/alerts/email/{email})
  async removerEmail(email) {
    try {
      const response = await fetch(
        `${ALERTS_URL}/email/${encodeURIComponent(email)}`,
        { method: "DELETE" },
      );
      return response.ok;
    } catch (error) {
      console.error("Erro ao remover e-mail:", error);
      return false;
    }
  },
};

