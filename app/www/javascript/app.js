// www/javascript/app.js - Lógica e Orquestração do Front-end

document.addEventListener("DOMContentLoaded", () => {
  let modoAtual = "AUTOMATICO";

  // Configuração da barra de status no celular (ícones escuros no topo)
  if (window.Capacitor && window.Capacitor.Plugins && window.Capacitor.Plugins.StatusBar) {
    window.Capacitor.Plugins.StatusBar.setStyle({ style: 'LIGHT' }).catch(() => {});
  }

  // 1. Conexão SSE para receber dados dos sensores em tempo real
  api.conectarStream((dados) => {
    if (dados) {
      const temp = Number(dados.temperature);
      const humi = Number(dados.humidity);
      const dataHora = dados.dateAndTime;

      if (!isNaN(temp) && !isNaN(humi)) {
        ui.atualizarLeituras(temp, humi, dataHora);
        ui.adicionarHistorico(temp, humi, dataHora);
      }
    }
  });

  // 2. Ações de alternância de Modo (POST /api/realtime/mode/{mode})
  window.setModo = async function (modo) {
    const modoAnterior = modoAtual;
    const modoFormatado = modo.toUpperCase();
    ui.alterarModoVisual(modoFormatado);
    modoAtual = modoFormatado;

    const res = await api.alterarModo(modoFormatado);
    if (!res.ok) {
      console.warn("Falha ao sincronizar modo com a API:", res.message);
      alert(res.message || "Erro ao atualizar modo no dispositivo.");
      // Reverte visualmente para o modo anterior em caso de erro
      modoAtual = modoAnterior;
      ui.alterarModoVisual(modoAnterior);
    }
  };

  // Botões do seletor segmentado de modo
  const btnDesligado = document.getElementById("btn-desligado");
  const btnLigado = document.getElementById("btn-ligado");
  const btnAutomatico = document.getElementById("btn-automatico");

  if (btnDesligado) {
    btnDesligado.onclick = () => setModo("DESLIGADO");
  }
  if (btnLigado) {
    btnLigado.onclick = () => setModo("LIGADO");
  }
  if (btnAutomatico) {
    btnAutomatico.onclick = () => setModo("AUTOMATICO");
  }

  // 3. Botão de Leitura Manual (exclusivo do modo LIGADO: POST /api/realtime/mode/LEITURA)
  const btnLeitura = document.getElementById("btn-realizar-leitura");
  const btnLeituraLabel = document.getElementById("btn-leitura-label");

  if (btnLeitura) {
    btnLeitura.onclick = async () => {
      btnLeitura.disabled = true;
      if (btnLeituraLabel) btnLeituraLabel.textContent = "SOLICITANDO LEITURA...";

      const res = await api.solicitarLeitura();
      if (!res.ok) {
        alert(res.message || "Erro ao solicitar leitura manual.");
      }

      setTimeout(() => {
        btnLeitura.disabled = false;
        if (btnLeituraLabel) btnLeituraLabel.textContent = "REALIZAR LEITURA";
      }, 1200);
    };
  }

  // 4. Salvar Limites para Alerta (POST /api/alerts/limits)
  const btnSalvarLimites = document.getElementById("btn-salvar-limites");
  const btnSalvarLabel = document.getElementById("btn-salvar-label");
  const inputTempMax = document.getElementById("input-temp-max");
  const inputUmidMax = document.getElementById("input-umid-max");
  const saveFeedback = document.getElementById("save-feedback");

  if (btnSalvarLimites && inputTempMax && inputUmidMax) {
    btnSalvarLimites.onclick = async () => {
      const temp = parseFloat(inputTempMax.value);
      const humi = parseFloat(inputUmidMax.value);

      if (isNaN(temp) || isNaN(humi)) {
        alert("Por favor, preencha valores numéricos válidos.");
        return;
      }

      if (temp < -50 || temp > 120) {
        alert("Temperatura deve estar entre -50 e 120°C.");
        return;
      }

      if (humi < 0 || humi > 100) {
        alert("Umidade deve estar entre 0 e 100%.");
        return;
      }

      btnSalvarLimites.disabled = true;
      if (btnSalvarLabel) btnSalvarLabel.textContent = "SALVANDO...";

      const res = await api.salvarLimites(temp, humi);
      if (res.ok) {
        const tVal = res.tempMax ?? temp;
        const hVal = res.humiMin ?? humi;
        ui.atualizarLimitesCards(tVal, hVal);
        ui.atualizarLimitesInputs(tVal, hVal);

        if (saveFeedback) {
          saveFeedback.style.display = "block";
          setTimeout(() => {
            saveFeedback.style.display = "none";
          }, 3500);
        }

        if (btnSalvarLabel) btnSalvarLabel.textContent = "LIMITES SALVOS!";
        setTimeout(() => {
          if (btnSalvarLabel) btnSalvarLabel.textContent = "SALVAR LIMITES";
          btnSalvarLimites.disabled = false;
        }, 1200);
      } else {
        alert(res.error || "Erro ao salvar limites no servidor.");
        if (btnSalvarLabel) btnSalvarLabel.textContent = "SALVAR LIMITES";
        btnSalvarLimites.disabled = false;
      }
    };
  }

  // 5. Gerenciamento de E-mails (/api/alerts/emails e /api/alerts/email/{email})
  const inputEmail = document.getElementById("input-email");
  const btnAddEmail = document.getElementById("btn-add-email");

  async function carregarEmails() {
    const emails = await api.listarEmails();
    ui.renderizarEmails(emails, deletarEmail);
  }

  async function deletarEmail(email) {
    const res = await api.removerEmail(email);
    if (res.ok) {
      if (Array.isArray(res.emails)) {
        ui.renderizarEmails(res.emails, deletarEmail);
      } else {
        await carregarEmails();
      }
    } else {
      alert(res.error || "Não foi possível remover o e-mail.");
    }
  }

  async function adicionarEmailHandler() {
    if (!inputEmail) return;
    const email = inputEmail.value.trim();
    if (!email || !email.includes("@")) {
      alert("Digite um e-mail válido.");
      return;
    }

    if (btnAddEmail) btnAddEmail.disabled = true;
    const res = await api.adicionarEmail(email);
    if (res.ok) {
      inputEmail.value = "";
      if (Array.isArray(res.emails) && res.emails.length > 0) {
        ui.renderizarEmails(res.emails, deletarEmail);
      } else {
        await carregarEmails();
      }
    } else {
      alert(res.error || "Erro ao adicionar e-mail.");
    }
    if (btnAddEmail) btnAddEmail.disabled = false;
  }

  if (btnAddEmail) {
    btnAddEmail.onclick = adicionarEmailHandler;
  }
  if (inputEmail) {
    inputEmail.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        adicionarEmailHandler();
      }
    });
  }

  // 6. Abas da Tab Bar (Navegação entre Views)
  const tabItems = document.querySelectorAll(".tab-item");
  const tabViews = [
    document.getElementById("view-painel"),
    document.getElementById("view-historico"),
    document.getElementById("view-config"),
  ];
  const headerSubtitulo = document.getElementById("header-subtitulo");

  function alternarAba(indexAtivo) {
    tabItems.forEach((tab, index) => {
      tab.classList.toggle("active", index === indexAtivo);
    });

    tabViews.forEach((view, index) => {
      if (!view) return;
      if (index === indexAtivo) {
        view.classList.add("active");
      } else {
        view.classList.remove("active");
      }
    });

    const scrollArea = document.getElementById("app-content");
    if (scrollArea) {
      scrollArea.scrollTop = 0;
    }

    if (headerSubtitulo) {
      const titulos = ["Painel de controle", "Histórico de leituras", "Configurações"];
      headerSubtitulo.textContent = titulos[indexAtivo] || "Painel de controle";
    }

    // Ao abrir a aba de Histórico, sincroniza com os dados do servidor
    if (indexAtivo === 1) {
      carregarHistoricoInicial();
    }
  }

  tabItems.forEach((tab, index) => {
    tab.addEventListener("click", () => {
      alternarAba(index);
    });
  });

  // Botão para atualizar o histórico sob demanda
  const btnAtualizarHistorico = document.getElementById("btn-atualizar-historico");
  const refreshIcon = document.getElementById("refresh-icon");
  const refreshLabel = document.getElementById("refresh-label");

  if (btnAtualizarHistorico) {
    btnAtualizarHistorico.addEventListener("click", async () => {
      if (refreshIcon) {
        refreshIcon.style.transition = "transform 0.5s ease";
        refreshIcon.style.transform = "rotate(360deg)";
      }
      if (refreshLabel) refreshLabel.textContent = "Carregando...";

      try {
        await carregarHistoricoInicial();
      } finally {
        setTimeout(() => {
          if (refreshIcon) refreshIcon.style.transform = "rotate(0deg)";
          if (refreshLabel) refreshLabel.textContent = "Atualizar";
        }, 500);
      }
    });
  }

  // 7. Gerenciamento dinâmico da URL do Servidor (API)
  const inputApiUrl = document.getElementById("input-api-url");
  const btnSalvarApiUrl = document.getElementById("btn-salvar-api-url");
  const btnResetApiUrl = document.getElementById("btn-reset-api-url");
  const apiUrlFeedback = document.getElementById("api-url-feedback");
  const serverStatusPill = document.getElementById("server-status-pill");

  if (inputApiUrl) {
    inputApiUrl.value = api.getBaseUrl();
    if (serverStatusPill) {
      serverStatusPill.textContent = api.getBaseUrl().includes("ngrok")
        ? "TÚNEL NGROK"
        : "LOCALHOST";
    }
  }

  if (btnSalvarApiUrl && inputApiUrl) {
    btnSalvarApiUrl.onclick = () => {
      const url = inputApiUrl.value.trim();
      if (!url) {
        alert("Digite uma URL válida.");
        return;
      }
      api.setBaseUrl(url);
      if (serverStatusPill) {
        serverStatusPill.textContent = url.includes("ngrok")
          ? "TÚNEL NGROK"
          : "PERSONALIZADO";
      }
      if (apiUrlFeedback) {
        apiUrlFeedback.textContent = "Servidor atualizado e reconectado com sucesso!";
        apiUrlFeedback.style.display = "block";
        setTimeout(() => {
          apiUrlFeedback.style.display = "none";
        }, 3000);
      }
      api.reiniciarStream();
      carregarModoInicial();
      carregarLimitesIniciais();
      carregarHistoricoInicial();
      carregarEmails();
    };
  }

  if (btnResetApiUrl && inputApiUrl) {
    btnResetApiUrl.onclick = () => {
      const padrao = "https://undecadently-incalescent-sabra.ngrok-free.dev";
      api.setBaseUrl(padrao);
      inputApiUrl.value = padrao;
      if (serverStatusPill) serverStatusPill.textContent = "TÚNEL NGROK";
      if (apiUrlFeedback) {
        apiUrlFeedback.textContent = "Restaurado para o túnel fixo do Ngrok!";
        apiUrlFeedback.style.display = "block";
        setTimeout(() => {
          apiUrlFeedback.style.display = "none";
        }, 3000);
      }
      api.reiniciarStream();
      carregarModoInicial();
      carregarLimitesIniciais();
      carregarHistoricoInicial();
      carregarEmails();
    };
  }

  // 8. Cargas iniciais dos endpoints
  async function carregarModoInicial() {
    const info = await api.obterModo();
    if (info && info.mode) {
      modoAtual = info.mode.toUpperCase();
      ui.alterarModoVisual(modoAtual);
    } else {
      ui.alterarModoVisual(modoAtual);
    }
  }

  async function carregarLimitesIniciais() {
    const limites = await api.obterLimites();
    if (limites) {
      ui.atualizarLimitesInputs(limites.tempMax, limites.humiMin);
      ui.atualizarLimitesCards(limites.tempMax, limites.humiMin);
    }
  }

  async function carregarHistoricoInicial() {
    const historico = await api.obterHistorico();
    if (Array.isArray(historico) && historico.length > 0) {
      ui.renderizarHistoricoInicial(historico);
      // Se não há dados atuais no card, inicializa com o mais recente
      const maisRecente = historico[0];
      if (maisRecente) {
        ui.atualizarLeituras(
          Number(maisRecente.temperature),
          Number(maisRecente.humidity),
          maisRecente.dateAndTime
        );
      }
    }
  }

  // Executa inicializações
  carregarModoInicial();
  carregarLimitesIniciais();
  carregarHistoricoInicial();
  carregarEmails();

  // 9. Sincronização periódica automática a cada 5 segundos (Smart Polling Fallback)
  // Garante que no celular o "Último dado" e os cards atualizem de forma 100% autônoma
  // mesmo se o SSE for suspenso pelo sistema de economia de energia do smartphone.
  setInterval(async () => {
    try {
      const historico = await api.obterHistorico();
      if (Array.isArray(historico) && historico.length > 0) {
        const maisRecente = historico[0];
        if (maisRecente) {
          ui.atualizarLeituras(
            Number(maisRecente.temperature),
            Number(maisRecente.humidity),
            maisRecente.dateAndTime
          );
        }
      }
    } catch (e) {
      // Ignora falhas transitórias de rede silenciosamente
    }
  }, 5000);
});
