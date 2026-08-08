// Progressive enhancement: os formulários de exclusão funcionam via POST
// normal (sem JS). Quando JS está disponível, interceptamos o envio para
// usar a API REST (fetch + DELETE) e atualizar a tabela sem recarregar a
// página, mantendo o professor informado via região aria-live.
(function () {
  const tabela = document.getElementById("tabela-alunos");
  if (!tabela) return;

  const regiaoAnuncio = document.createElement("div");
  regiaoAnuncio.setAttribute("aria-live", "polite");
  regiaoAnuncio.className = "visualmente-oculto";
  document.body.appendChild(regiaoAnuncio);

  tabela.querySelectorAll(".form-excluir").forEach((form) => {
    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const linha = form.closest("tr");
      const alunoId = linha?.dataset.alunoId;
      const nome = linha?.children[0]?.textContent ?? "aluno";

      const confirmou = window.confirm(`Excluir o aluno "${nome}"? Essa ação não pode ser desfeita.`);
      if (!confirmou) return;

      try {
        const resposta = await fetch(`/api/alunos/${alunoId}`, {
          method: "DELETE",
          headers: { "X-CSRFToken": window.CSRF_TOKEN },
        });
        if (!resposta.ok) throw new Error("Falha ao excluir");

        linha.remove();
        regiaoAnuncio.textContent = `Aluno ${nome} excluído com sucesso.`;
      } catch (erro) {
        regiaoAnuncio.textContent = `Não foi possível excluir o aluno ${nome}. Tente novamente.`;
      }
    });
  });
})();
