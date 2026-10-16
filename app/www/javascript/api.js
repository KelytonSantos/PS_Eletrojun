// www/javascript/api.js

const DEFAULT_NGROK = "https://undecadently-incalescent-sabra.ngrok-free.dev";
const DEFAULT_LOCAL = "http://localhost:8080";

const api = {
  // Retorna a URL base da API (prioriza o salvo no localStorage, depois o ngrok como padrão mobile)
  getBaseUrl() {
    const salvo = localStorage.getItem("API_SERVER_URL");
    if (salvo && salvo.trim()) {
      return salvo.trim().replace(/\/+$/, "");
    }
    // Detecta se está em dispositivo móvel (Android, iOS) ou Capacitor
    const isMobile =
      /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) ||
      window.Capacitor !== undefined ||
      window.location.protocol === "capacitor:" ||
      window.location.protocol === "file:";

    // No celular, o padrão NUNCA pode ser localhost (pois o backend roda no notebook)
    if (isMobile) {
      return DEFAULT_NGROK;
    }

    const isDesktopLocal =
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1";

    return isDesktopLocal ? DEFAULT_LOCAL : DEFAULT_NGROK;
  },

  // Salva nova URL base
  setBaseUrl(url) {
    if (url && url.trim()) {
      localStorage.setItem("API_SERVER_URL", url.trim().replace(/\/+$/, ""));
    } else {
      localStorage.removeItem("API_SERVER_URL");
    }
  },

  getRealtimeUrl() {
    return `${this.getBaseUrl()}/api/realtime`;
  },

  getAlertsUrl() {
    return `${this.getBaseUrl()}/api/alerts`;
  },

  // Helper para requisições fetch com header anti-bloqueio do ngrok
  async _fetch(url, options = {}) {
    const headers = {
      "ngrok-skip-browser-warning": "true",
      ...(options.headers || {}),
    };
    return fetch(url, { ...options, headers });
  },

  // ==========================================
  // API Java — /api/realtime (Porta interna 8081)
  // ==========================================

  _activeEventSource: null,
  _streamCallback: null,

  // Conecta ao Stream SSE da API Java (GET /api/realtime/automatico/stream)
  conectarStream(callbackDados) {
    if (callbackDados) {
      this._streamCallback = callbackDados;
    }
    if (this._activeEventSource) {
      try {
        this._activeEventSource.close();
      } catch (e) {}
      this._activeEventSource = null;
    }

    // Parâmetro query para garantir que o ngrok nunca bloqueie o SSE
    const streamUrl = `${this.getRealtimeUrl()}/automatico/stream?ngrok-skip-browser-warning=true`;
    console.log("[SSE] Conectando ao stream:", streamUrl);
    const eventSource = new EventSource(streamUrl);
    this._activeEventSource = eventSource;

    eventSource.addEventListener("sensor-readings", (event) => {
      try {
        const dados = JSON.parse(event.data);
        if (this._streamCallback) {
          this._streamCallback(dados);
        }
      } catch (e) {
        console.error("Erro ao parsear dados do SSE:", e);
      }
    });

    eventSource.onopen = () => {
      console.log("[SSE] Conectado ao stream em tempo real:", streamUrl);
    };

    eventSource.onerror = (err) => {
      console.warn("[SSE] Conexão SSE oscilou ou reconectando...", err);
    };

    return eventSource;
  },

  // Reinicia a conexão SSE com a URL ativa
  reiniciarStream() {
    if (this._streamCallback) {
      return this.conectarStream(this._streamCallback);
    }
  },

  // Consulta modo atual e conexão MQTT (GET /api/realtime/mode)
  async obterModo() {
    try {
      const response = await this._fetch(`${this.getRealtimeUrl()}/mode`);
      if (response.ok) {
        return await response.json(); // { mode: "AUTOMATICO", mqttConnected: true }
      }
      console.error("Erro ao obter modo:", response.status);
      return null;
    } catch (error) {
      console.error("Erro na requisição GET /api/realtime/mode:", error);
      return null;
    }
  },

  // Altera o modo no ESP32: AUTOMATICO, LIGADO ou DESLIGADO (POST /api/realtime/mode/{mode})
  async alterarModo(modo) {
    try {
      const response = await this._fetch(
        `${this.getRealtimeUrl()}/mode/${encodeURIComponent(modo)}`,
        { method: "POST" }
      );
      const data = await response.json().catch(() => null);
      return {
        ok: response.ok,
        status: response.status,
        data: data,
        message:
          data?.message ||
          (response.ok
            ? "Modo atualizado com sucesso."
            : "Erro ao alterar modo."),
      };
    } catch (error) {
      console.error("Erro ao alterar modo:", error);
      return { ok: false, message: "Erro de conexão ao alterar modo." };
    }
  },

  // Dispara leitura avulsa quando em modo LIGADO (POST /api/realtime/mode/LEITURA)
  async solicitarLeitura() {
    try {
      const response = await this._fetch(`${this.getRealtimeUrl()}/mode/LEITURA`, {
        method: "POST",
      });
      const data = await response.json().catch(() => null);
      return {
        ok: response.ok,
        status: response.status,
        data: data,
        message:
          data?.message ||
          (response.ok
            ? "Solicitação de leitura enviada."
            : "Erro ao solicitar leitura."),
      };
    } catch (error) {
      console.error("Erro ao solicitar leitura avulsa:", error);
      return { ok: false, message: "Erro de conexão ao solicitar leitura." };
    }
  },

  // Retorna histórico recente de leituras (GET /api/realtime/history)
  async obterHistorico() {
    try {
      const response = await this._fetch(`${this.getRealtimeUrl()}/history`);
      if (response.ok) {
        return await response.json(); // Lista da mais recente para a mais antiga
      }
      console.error("Erro ao obter histórico:", response.status);
      return [];
    } catch (error) {
      console.error("Erro na requisição GET /api/realtime/history:", error);
      return [];
    }
  },

  // ==========================================
  // Notifier Python — /api/alerts (Porta interna 8082)
  // ==========================================

  // Consulta os limites para alerta (GET /api/alerts/limits)
  async obterLimites() {
    try {
      const response = await this._fetch(`${this.getAlertsUrl()}/limits`);
      if (response.ok) {
        return await response.json(); // { tempMax: 30.0, humiMin: 20.0 }
      }
      console.error("Erro ao obter limites:", response.status);
      return null;
    } catch (error) {
      console.error("Erro na requisição GET /api/alerts/limits:", error);
      return null;
    }
  },

  // Atualiza limites de alerta (POST /api/alerts/limits)
  async salvarLimites(temperatura, umidade) {
    try {
      const response = await this._fetch(`${this.getAlertsUrl()}/limits`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          temp: Number(temperatura),
          humi: Number(umidade),
        }),
      });

      const data = await response.json().catch(() => null);
      return {
        ok: response.ok,
        status: response.status,
        tempMax: data?.tempMax,
        humiMin: data?.humiMin,
        error: data?.error,
      };
    } catch (error) {
      console.error("Erro ao salvar limites:", error);
      return { ok: false, error: "Erro de conexão ao salvar limites." };
    }
  },

  // Lista os e-mails cadastrados (GET /api/alerts/emails)
  async listarEmails() {
    try {
      const response = await this._fetch(`${this.getAlertsUrl()}/emails`);
      if (response.ok) {
        const data = await response.json();
        return Array.isArray(data.emails) ? data.emails : [];
      }
      console.error("Erro ao buscar e-mails:", response.status);
      return [];
    } catch (error) {
      console.error("Erro na requisição GET /api/alerts/emails:", error);
      return [];
    }
  },

  // Adiciona e-mail destinatário de alerta (POST /api/alerts/email/{email})
  async adicionarEmail(email) {
    try {
      const response = await this._fetch(
        `${this.getAlertsUrl()}/email/${encodeURIComponent(email)}`,
        { method: "POST" }
      );
      const data = await response.json().catch(() => null);
      return {
        ok: response.ok,
        status: response.status,
        emails: data?.emails || [],
        error: data?.error,
      };
    } catch (error) {
      console.error("Erro ao adicionar e-mail:", error);
      return { ok: false, error: "Erro de conexão ao adicionar e-mail." };
    }
  },

  // Remove um e-mail cadastrado (DELETE /api/alerts/email/{email})
  async removerEmail(email) {
    try {
      const response = await this._fetch(
        `${this.getAlertsUrl()}/email/${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const data = await response.json().catch(() => null);
      return {
        ok: response.ok,
        status: response.status,
        emails: data?.emails || [],
        error: data?.error,
      };
    } catch (error) {
      console.error("Erro ao remover e-mail:", error);
      return { ok: false, error: "Erro de conexão ao remover e-mail." };
    }
  },
};
