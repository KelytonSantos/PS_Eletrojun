// www/javascript/ui.js - Renderização e Atualizações Visuais

const ui = {
  limiteTempMax: 30.0,
  limiteHumiMin: 20.0,

  // 1. Atualiza os cards de telemetria em tempo real
  atualizarLeituras(temperatura, umidade, dataHora) {
    const cardTemp = document.getElementById("valor-temperatura");
    const cardHumi = document.getElementById("valor-umidade");
    const tempoTemp = document.getElementById("tempo-temperatura");
    const tempoHumi = document.getElementById("tempo-umidade");
    const tempProgress = document.getElementById("temp-progress");
    const humidProgress = document.getElementById("humid-progress");
    const histCurTemp = document.getElementById("hist-cur-temp");
    const histCurHumi = document.getElementById("hist-cur-humi");
    const statusClimaBadge = document.getElementById("status-clima-badge");

    if (cardTemp) cardTemp.textContent = temperatura.toFixed(1);
    if (cardHumi) cardHumi.textContent = umidade.toFixed(1);
    if (histCurTemp) histCurTemp.textContent = temperatura.toFixed(1);
    if (histCurHumi) histCurHumi.textContent = umidade.toFixed(1);

    // Ajusta barras de progresso (0 - 50°C para temp, 0 - 100% para umidade)
    if (tempProgress) {
      const pctTemp = Math.min(100, Math.max(0, (temperatura / 50) * 100));
      tempProgress.style.width = `${pctTemp}%`;
    }
    if (humidProgress) {
      const pctHumi = Math.min(100, Math.max(0, umidade));
      humidProgress.style.width = `${pctHumi}%`;
    }

    // Status do clima (Ideal vs Alerta)
    if (statusClimaBadge) {
      const emAlerta = temperatura >= this.limiteTempMax || umidade <= this.limiteHumiMin;
      if (emAlerta) {
        statusClimaBadge.textContent = "ALERTA";
        statusClimaBadge.style.color = "var(--color-error)";
        statusClimaBadge.style.backgroundColor = "var(--color-error-container)";
      } else {
        statusClimaBadge.textContent = "IDEAL";
        statusClimaBadge.style.color = "var(--color-secondary)";
        statusClimaBadge.style.backgroundColor = "var(--color-surface-lowest)";
      }
    }

    let horaFormatada = "";
    if (dataHora) {
      const parsed = new Date(dataHora);
      horaFormatada = !isNaN(parsed.getTime())
        ? parsed.toLocaleTimeString("pt-BR")
        : new Date().toLocaleTimeString("pt-BR");
    } else {
      horaFormatada = new Date().toLocaleTimeString("pt-BR");
    }

    if (tempoTemp) tempoTemp.textContent = horaFormatada;
    if (tempoHumi) tempoHumi.textContent = horaFormatada;
  },

  // Atualiza os valores limites exibidos dentro dos cards
  atualizarLimitesCards(tempMax, humiMin) {
    const cardLimTemp = document.getElementById("card-limite-temp");
    const cardLimHumi = document.getElementById("card-limite-humi");

    if (!isNaN(tempMax)) {
      this.limiteTempMax = Number(tempMax);
      if (cardLimTemp) cardLimTemp.textContent = `${Number(tempMax).toFixed(1)}°C`;
    }
    if (!isNaN(humiMin)) {
      this.limiteHumiMin = Number(humiMin);
      if (cardLimHumi) cardLimHumi.textContent = `${Number(humiMin).toFixed(1)}%`;
    }
  },

  // Atualiza os inputs do formulário de configurações
  atualizarLimitesInputs(tempMax, humiMin) {
    const inputTempMax = document.getElementById("input-temp-max");
    const inputUmidMax = document.getElementById("input-umid-max");

    if (inputTempMax && !isNaN(tempMax)) inputTempMax.value = Number(tempMax);
    if (inputUmidMax && !isNaN(humiMin)) inputUmidMax.value = Number(humiMin);
  },

  // Formata timestamp ISO para pt-BR (DD/MM HH:MM:SS)
  formatarDataHora(dataHora) {
    let dataObj = new Date();
    if (dataHora) {
      const parsed = new Date(dataHora);
      if (!isNaN(parsed.getTime())) {
        dataObj = parsed;
      }
    }
    const dia = String(dataObj.getDate()).padStart(2, "0");
    const mes = String(dataObj.getMonth() + 1).padStart(2, "0");
    const hora = String(dataObj.getHours()).padStart(2, "0");
    const min = String(dataObj.getMinutes()).padStart(2, "0");
    const seg = String(dataObj.getSeconds()).padStart(2, "0");
    return `${dia}/${mes} ${hora}:${min}:${seg}`;
  },

  // Renderiza o histórico inicial vindo da API
  renderizarHistoricoInicial(listaHistorico) {
    const container = document.getElementById("tabela-historico-body");
    const countBadge = document.getElementById("hist-registros-count");
    if (!container) return;

    container.innerHTML = "";
    if (!Array.isArray(listaHistorico) || listaHistorico.length === 0) {
      container.innerHTML = `
        <div style="padding:20px; text-align:center; font-size:12px; color:var(--color-outline);">
          Nenhuma leitura registrada no histórico.
        </div>
      `;
      if (countBadge) countBadge.textContent = "0 registros";
      return;
    }

    const amostra = listaHistorico.slice(0, 15);
    amostra.forEach((item) => {
      const temp = Number(item.temperature);
      const humi = Number(item.humidity);
      const dataFormatada = this.formatarDataHora(item.dateAndTime);

      const row = document.createElement("div");
      row.className = "history-row";
      row.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="dot-pulse" style="width:6px; height:6px;"></span>
          <span style="color:var(--color-on-surface); font-weight:600;">${dataFormatada}</span>
        </div>
        <div style="text-align:center; color:var(--color-primary); font-weight:700;">
          ${!isNaN(temp) ? temp.toFixed(1) : "--"}<span style="font-size:10px; color:var(--color-on-surface-variant); font-weight:500;">°C</span>
        </div>
        <div style="text-align:right; color:var(--color-primary); font-weight:700;">
          ${!isNaN(humi) ? humi.toFixed(1) : "--"}<span style="font-size:10px; color:var(--color-on-surface-variant); font-weight:500;">%</span>
        </div>
      `;
      container.appendChild(row);
    });

    if (countBadge) {
      countBadge.textContent = `${amostra.length} registros`;
    }
  },

  // Adiciona nova leitura no topo do histórico com animação
  adicionarHistorico(temperatura, umidade, dataHora) {
    const container = document.getElementById("tabela-historico-body");
    const countBadge = document.getElementById("hist-registros-count");
    if (!container) return;

    const dataFormatada = this.formatarDataHora(dataHora);

    const row = document.createElement("div");
    row.className = "history-row history-row-new";
    row.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px;">
        <span class="dot-pulse" style="width:6px; height:6px;"></span>
        <span style="color:var(--color-on-surface); font-weight:700;">${dataFormatada}</span>
      </div>
      <div style="text-align:center; color:var(--color-primary); font-weight:700;">
        ${temperatura.toFixed(1)}<span style="font-size:10px; color:var(--color-on-surface-variant); font-weight:500;">°C</span>
      </div>
      <div style="text-align:right; color:var(--color-primary); font-weight:700;">
        ${umidade.toFixed(1)}<span style="font-size:10px; color:var(--color-on-surface-variant); font-weight:500;">%</span>
      </div>
    `;

    if (container.firstElementChild) {
      container.insertBefore(row, container.firstElementChild);
    } else {
      container.appendChild(row);
    }

    // Mantém no máximo 15 registros visíveis
    while (container.children.length > 15) {
      container.removeChild(container.lastChild);
    }

    if (countBadge) {
      countBadge.textContent = `${container.children.length} registros`;
    }
  },

  // Controla o estado visual dos modos de operação
  alterarModoVisual(modo) {
    const badgeTexto = document.getElementById("badge-texto");
    const activeModeLabel = document.getElementById("active-mode-label");

    const mapaNomes = {
      DESLIGADO: "DESLIG.",
      LIGADO: "LIGADO",
      AUTOMATICO: "AUTO",
      "AUTOMÁTICO": "AUTO"
    };

    const mapaLabels = {
      DESLIGADO: "DESLIGADO",
      LIGADO: "MANUAL ATIVO",
      AUTOMATICO: "AUTO ATIVO",
      "AUTOMÁTICO": "AUTO ATIVO"
    };

    if (badgeTexto) {
      badgeTexto.textContent = mapaNomes[modo] || modo;
    }

    if (activeModeLabel) {
      activeModeLabel.textContent = mapaLabels[modo] || modo;
    }

    const mapaBotoes = {
      DESLIGADO: "btn-desligado",
      LIGADO: "btn-ligado",
      AUTOMATICO: "btn-automatico",
      "AUTOMÁTICO": "btn-automatico"
    };

    const botaoAtivoId = mapaBotoes[modo];

    ["btn-desligado", "btn-ligado", "btn-automatico"].forEach((id) => {
      const btn = document.getElementById(id);
      if (btn) {
        btn.classList.toggle("active", id === botaoAtivoId);
      }
    });

    // Exibe ou oculta o painel de leitura manual (apenas no modo LIGADO)
    const acaoLeitura = document.getElementById("acao-leitura");
    if (acaoLeitura) {
      acaoLeitura.style.display = modo === "LIGADO" ? "block" : "none";
    }
  },

  // Renderiza a lista de e-mails para notificação
  renderizarEmails(listaEmails, onDeleteCallback) {
    const container = document.getElementById("lista-emails-ul");
    const counterBadge = document.getElementById("email-counter");
    const emptyState = document.getElementById("email-empty");
    if (!container) return;

    container.innerHTML = "";

    const count = Array.isArray(listaEmails) ? listaEmails.length : 0;
    if (counterBadge) {
      counterBadge.textContent = count === 1 ? "1 REGISTRADO" : `${count} REGISTRADOS`;
    }

    if (count === 0) {
      if (emptyState) emptyState.style.display = "flex";
      return;
    }

    if (emptyState) emptyState.style.display = "none";

    listaEmails.forEach((email) => {
      const item = document.createElement("div");
      item.className = "email-item";
      item.innerHTML = `
        <div style="display:flex; align-items:center; gap:10px; min-width:0;">
          <span class="dot-pulse" style="width:6px; height:6px;"></span>
          <div style="display:flex; flex-direction:column; min-width:0;">
            <span style="font-size:13px; font-weight:600; color:var(--color-primary); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${email}</span>
            <span style="font-size:10px; color:var(--color-on-surface-variant);">Prioridade ALTA • Notificação Ativa</span>
          </div>
        </div>
        <button class="btn-remove-email" title="Remover e-mail" type="button">
          <span class="material-symbols-outlined" style="font-size:18px;">close</span>
        </button>
      `;

      const btnDelete = item.querySelector(".btn-remove-email");
      if (btnDelete) {
        btnDelete.addEventListener("click", () => onDeleteCallback(email));
      }

      container.appendChild(item);
    });
  }
};
