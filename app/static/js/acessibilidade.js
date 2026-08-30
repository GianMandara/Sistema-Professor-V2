// Barra de acessibilidade própria: liga/desliga classes utilitárias em
// <html> (definidas em acessibilidade.css) e guarda a preferência do
// visitante em localStorage, por navegador — não depende de conta nem
// de servidor, então funciona igual na landing pública e no boletim do
// aluno, sem sessão nenhuma.
(function () {
  const painel = document.getElementById("a11y-painel");
  const botaoAbrir = document.getElementById("a11y-abrir");
  if (!painel || !botaoAbrir) return;

  const CHAVE_LS = "sistema-professor-a11y";
  const html = document.documentElement;
  const botaoFechar = document.getElementById("a11y-fechar");
  const guiaBarra = document.getElementById("a11y-guia-leitura-barra");
  const botaoLibras = document.getElementById("a11y-libras");

  const NIVEIS_FONTE = 4; // além do nível 0 (padrão)
  const ACOES_BOOLEANAS = [
    "alto-contraste",
    "fonte-legivel",
    "espacamento",
    "links",
    "escala-cinza",
    "sem-animacao",
    "cursor-grande",
    "guia-leitura",
  ];

  function carregarEstado() {
    try {
      return JSON.parse(localStorage.getItem(CHAVE_LS)) || {};
    } catch (erro) {
      return {};
    }
  }

  function salvarEstado(estado) {
    try {
      localStorage.setItem(CHAVE_LS, JSON.stringify(estado));
    } catch (erro) {
      // localStorage indisponível (aba anônima com bloqueio, por exemplo)
      // — as ferramentas continuam funcionando, só não persistem entre
      // páginas.
    }
  }

  let estado = carregarEstado();

  function aplicarNivelFonte(nivel) {
    for (let i = 1; i <= NIVEIS_FONTE; i++) html.classList.remove(`a11y-fonte-${i}`);
    if (nivel > 0) html.classList.add(`a11y-fonte-${nivel}`);
    estado.fonte = nivel;
    salvarEstado(estado);
  }

  function atualizarBotaoPressionado(acao, ativo) {
    const botao = painel.querySelector(`[data-acao="${acao}"]`);
    botao?.setAttribute("aria-pressed", String(ativo));
  }

  function alternar(acao) {
    const classe = `a11y-${acao}`;
    const ativo = html.classList.toggle(classe);
    estado[acao] = ativo;
    salvarEstado(estado);
    atualizarBotaoPressionado(acao, ativo);
    if (acao === "guia-leitura") guiaBarra.hidden = !ativo;
  }

  function resetarTudo() {
    ACOES_BOOLEANAS.forEach((acao) => {
      html.classList.remove(`a11y-${acao}`);
      atualizarBotaoPressionado(acao, false);
    });
    aplicarNivelFonte(0);
    guiaBarra.hidden = true;
    estado = {};
    salvarEstado(estado);
  }

  // Restaura o que já estava salvo, ao carregar a página.
  aplicarNivelFonte(estado.fonte || 0);
  ACOES_BOOLEANAS.forEach((acao) => {
    if (estado[acao]) {
      html.classList.add(`a11y-${acao}`);
      atualizarBotaoPressionado(acao, true);
    }
  });
  guiaBarra.hidden = !html.classList.contains("a11y-guia-leitura");

  painel.querySelectorAll("[data-acao]").forEach((botao) => {
    botao.addEventListener("click", () => {
      const acao = botao.dataset.acao;
      if (acao === "fonte-aumentar") {
        aplicarNivelFonte(Math.min((estado.fonte || 0) + 1, NIVEIS_FONTE));
      } else if (acao === "fonte-diminuir") {
        aplicarNivelFonte(Math.max((estado.fonte || 0) - 1, 0));
      } else if (acao === "resetar") {
        resetarTudo();
      } else {
        alternar(acao);
      }
    });
  });

  // O Libras em si é o VLibras (ver _vlibras.html) — este botão só aciona
  // o widget dele, para ficar tudo num único menu de acessibilidade.
  botaoLibras?.addEventListener("click", () => {
    document.querySelector("[vw-access-button]")?.click();
  });

  function abrirPainel() {
    painel.hidden = false;
    botaoAbrir.setAttribute("aria-expanded", "true");
    painel.querySelector(".a11y-botao")?.focus();
  }

  function fecharPainel() {
    painel.hidden = true;
    botaoAbrir.setAttribute("aria-expanded", "false");
    botaoAbrir.focus();
  }

  botaoAbrir.addEventListener("click", () => {
    painel.hidden ? abrirPainel() : fecharPainel();
  });
  botaoFechar?.addEventListener("click", fecharPainel);

  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !painel.hidden) fecharPainel();
  });

  // Fecha ao clicar fora do painel/botão (mas não trava o resto da
  // página — diferente do modal de login, este menu não é bloqueante).
  document.addEventListener("click", (evento) => {
    if (painel.hidden) return;
    const dentroDoPainel = painel.contains(evento.target);
    const noBotaoAbrir = botaoAbrir.contains(evento.target);
    if (!dentroDoPainel && !noBotaoAbrir) fecharPainel();
  });

  document.addEventListener("mousemove", (evento) => {
    if (html.classList.contains("a11y-guia-leitura")) {
      guiaBarra.style.top = `${evento.clientY - 22}px`;
    }
  });
})();
