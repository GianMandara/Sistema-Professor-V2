// Login/cadastro/esqueci-senha embutidos na landing page, sem navegar
// para uma URL separada. Sem JavaScript, os links (?login=1 / ?cadastro=1
// / ?esqueci=1) já fazem o servidor renderizar o painel certo visível —
// isto só evita o recarregamento da página quando JS está disponível.
(function () {
  const modal = document.getElementById("login");
  if (!modal) return;

  // Elemento que tinha o foco antes de o modal abrir — recebe o foco de
  // volta ao fechar (X, Escape ou clique fora), como pede o padrão ARIA de
  // dialog (o modal usa role="dialog" aria-modal="true").
  let elementoQueAbriu = null;

  const SELETOR_FOCAVEL =
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function elementosFocaveisVisiveis() {
    // Os painéis não ativos ficam com o atributo "hidden" (display: none),
    // então offsetParent é null para os campos deles — filtra automaticamente.
    return Array.from(modal.querySelectorAll(SELETOR_FOCAVEL)).filter(
      (el) => el.offsetParent !== null
    );
  }

  function mostrarPainel(nome, evento) {
    evento?.preventDefault();
    if (modal.hasAttribute("hidden")) {
      elementoQueAbriu = document.activeElement;
    }
    modal.removeAttribute("hidden");
    document.querySelectorAll(".painel-auth").forEach((painel) => {
      painel.hidden = painel.id !== `painel-${nome}`;
    });
    // :not([type="hidden"]) é essencial aqui — cada painel tem um campo
    // csrf_token oculto ANTES do primeiro campo visível; sem esse filtro,
    // o querySelector pegava o campo oculto e o .focus() virava um no-op
    // silencioso (o foco ficava preso no <body>).
    modal.querySelector(`#painel-${nome} input:not([type="hidden"])`)?.focus();
    history.replaceState(null, "", "#login");
  }

  function fecharLogin() {
    modal.setAttribute("hidden", "");
    history.replaceState(null, "", window.location.pathname);
    elementoQueAbriu?.focus();
    elementoQueAbriu = null;
  }

  document.querySelectorAll(".link-painel").forEach((link) => {
    link.addEventListener("click", (evento) => mostrarPainel(link.dataset.painel, evento));
  });

  document.getElementById("fechar-login")?.addEventListener("click", fecharLogin);

  // Fecha ao clicar fora do cartão (no fundo escurecido).
  modal.addEventListener("click", (evento) => {
    if (evento.target === modal) fecharLogin();
  });

  document.addEventListener("keydown", (evento) => {
    if (modal.hasAttribute("hidden")) return;

    if (evento.key === "Escape") {
      fecharLogin();
      return;
    }

    // Focus trap: com o modal aberto, o Tab não pode escapar para o
    // conteúdo por trás dele — essencial para quem navega só por teclado.
    if (evento.key === "Tab") {
      const focaveis = elementosFocaveisVisiveis();
      if (focaveis.length === 0) return;

      const primeiro = focaveis[0];
      const ultimo = focaveis[focaveis.length - 1];

      if (evento.shiftKey && document.activeElement === primeiro) {
        evento.preventDefault();
        ultimo.focus();
      } else if (!evento.shiftKey && document.activeElement === ultimo) {
        evento.preventDefault();
        primeiro.focus();
      }
    }
  });
})();
