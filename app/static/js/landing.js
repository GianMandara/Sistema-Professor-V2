// Abre/fecha o login embutido na landing page sem navegar para uma URL
// separada. Sem JavaScript, os links "Acessar sistema" (?login=1) já
// fazem o servidor renderizar o formulário visível — isto só evita o
// recarregamento da página quando JS está disponível.
(function () {
  const modal = document.getElementById("login");
  if (!modal) return;

  function abrirLogin(evento) {
    evento?.preventDefault();
    modal.removeAttribute("hidden");
    document.getElementById("usuario")?.focus();
    history.replaceState(null, "", "#login");
  }

  function fecharLogin() {
    modal.setAttribute("hidden", "");
    history.replaceState(null, "", window.location.pathname);
  }

  document.querySelectorAll(".abrir-login").forEach((link) => {
    link.addEventListener("click", abrirLogin);
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
