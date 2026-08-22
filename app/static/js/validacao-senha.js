// Checagem de "senha" vs. "confirmar_senha" em tempo real, usando a API
// nativa de validação do HTML (setCustomValidity). O navegador já anuncia
// esse erro de forma acessível (foco no campo + balão de erro lido por
// leitores de tela) quando o formulário é submetido — sem precisar de
// nenhum aria-live extra aqui. O servidor continua validando de novo
// (esta checagem é só uma camada extra de usabilidade, não substitui a
// validação de verdade).
(function () {
  document.querySelectorAll("form").forEach((form) => {
    const senha = form.querySelector('input[name="senha"]');
    const confirmar = form.querySelector('input[name="confirmar_senha"]');
    if (!senha || !confirmar) return;

    function verificar() {
      if (confirmar.value && confirmar.value !== senha.value) {
        confirmar.setCustomValidity("As senhas precisam ser iguais.");
      } else {
        confirmar.setCustomValidity("");
      }
    }

    senha.addEventListener("input", verificar);
    confirmar.addEventListener("input", verificar);
  });
})();
