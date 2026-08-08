// Comportamentos globais do "app shell": modo escuro persistente, foco no
// conteúdo principal ao usar o skip-link, e menu lateral retrátil no mobile.

// Token CSRF exposto globalmente (a tag <meta> existe em toda página que
// estende base.html) para os demais scripts incluírem em requisições
// fetch que alteram dados (DELETE/POST via JS).
window.CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content;

(function () {
  const CHAVE_TEMA = "sistema-professor-tema";
  const botaoTema = document.getElementById("alternar-tema");
  const raiz = document.documentElement;

  function aplicarTema(tema) {
    const rotulo = botaoTema?.querySelector("span");
    if (tema === "escuro") {
      raiz.setAttribute("data-tema", "escuro");
      botaoTema?.setAttribute("aria-pressed", "true");
      if (rotulo) rotulo.textContent = "Modo claro";
    } else {
      raiz.removeAttribute("data-tema");
      botaoTema?.setAttribute("aria-pressed", "false");
      if (rotulo) rotulo.textContent = "Modo escuro";
    }
  }

  const temaSalvo = localStorage.getItem(CHAVE_TEMA);
  if (temaSalvo) aplicarTema(temaSalvo);

  botaoTema?.addEventListener("click", () => {
    const atual = raiz.getAttribute("data-tema") === "escuro" ? "escuro" : "claro";
    const proximo = atual === "escuro" ? "claro" : "escuro";
    aplicarTema(proximo);
    localStorage.setItem(CHAVE_TEMA, proximo);
  });

  // Garante que o skip-link mova o foco de fato (necessário em alguns
  // navegadores para elementos sem tabindex nativo).
  const conteudoPrincipal = document.getElementById("conteudo-principal");
  document.querySelector(".skip-link")?.addEventListener("click", () => {
    conteudoPrincipal?.focus();
  });

  // Menu lateral (sidebar) retrátil em telas estreitas.
  const sidebar = document.getElementById("sidebar");
  const botaoMenu = document.getElementById("abrir-menu");
  const overlay = document.getElementById("overlay-sidebar");

  function fecharMenu() {
    sidebar?.classList.remove("sidebar-aberta");
    overlay?.setAttribute("hidden", "");
    botaoMenu?.setAttribute("aria-expanded", "false");
  }

  function abrirMenu() {
    sidebar?.classList.add("sidebar-aberta");
    overlay?.removeAttribute("hidden");
    botaoMenu?.setAttribute("aria-expanded", "true");
  }

  botaoMenu?.addEventListener("click", () => {
    const aberto = sidebar?.classList.contains("sidebar-aberta");
    aberto ? fecharMenu() : abrirMenu();
  });
  overlay?.addEventListener("click", fecharMenu);
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape") fecharMenu();
  });
})();
