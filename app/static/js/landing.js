// Login/cadastro/esqueci-senha embutidos na landing page, sem navegar
// para uma URL separada. Sem JavaScript, os links (?login=1 / ?cadastro=1
// / ?esqueci=1) já fazem o servidor renderizar o painel certo visível —
// isto só evita o recarregamento da página quando JS está disponível.
(function () {
  const modal = document.getElementById("login");
  if (!modal) return;

  function mostrarPainel(nome, evento) {
    evento?.preventDefault();
    modal.removeAttribute("hidden");
    document.querySelectorAll(".painel-auth").forEach((painel) => {
      painel.hidden = painel.id !== `painel-${nome}`;
    });
    modal.querySelector(`#painel-${nome} input`)?.focus();
    history.replaceState(null, "", "#login");
  }

  function fecharLogin() {
    modal.setAttribute("hidden", "");
    history.replaceState(null, "", window.location.pathname);
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
    if (evento.key === "Escape" && !modal.hasAttribute("hidden")) fecharLogin();
  });
})();
