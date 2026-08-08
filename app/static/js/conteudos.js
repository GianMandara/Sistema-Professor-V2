// Mesmo padrão de exclusão progressiva usado em alunos.js: o formulário
// funciona via POST normal sem JS; com JS, usamos a API REST (DELETE) para
// remover a linha sem recarregar a página.
(function () {
  const tabela = document.getElementById("tabela-conteudos");
  if (!tabela) return;

  const regiaoAnuncio = document.createElement("div");
  regiaoAnuncio.setAttribute("aria-live", "polite");
  regiaoAnuncio.className = "visualmente-oculto";
  document.body.appendChild(regiaoAnuncio);

  tabela.querySelectorAll(".form-excluir").forEach((form) => {
    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const linha = form.closest("tr");
      const conteudoId = linha?.dataset.conteudoId;
      const titulo = linha?.children[0]?.textContent ?? "conteúdo";

      const confirmou = window.confirm(`Excluir o conteúdo "${titulo}"? Aulas vinculadas ficarão sem conteúdo definido.`);
      if (!confirmou) return;

      try {
        const resposta = await fetch(`/api/conteudos/${conteudoId}`, {
          method: "DELETE",
          headers: { "X-CSRFToken": window.CSRF_TOKEN },
        });
        if (!resposta.ok) throw new Error("Falha ao excluir");

        linha.remove();
        regiaoAnuncio.textContent = `Conteúdo ${titulo} excluído com sucesso.`;
      } catch (erro) {
        regiaoAnuncio.textContent = `Não foi possível excluir o conteúdo ${titulo}. Tente novamente.`;
      }
    });
  });
})();
