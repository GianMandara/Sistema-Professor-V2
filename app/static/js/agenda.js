// 1) Consulta a API externa de feriados (via nosso backend, em /api/feriados)
//    assim que o professor escolhe uma data, avisando sem bloquear o envio.
// 2) Reaproveita o mesmo padrão de exclusão progressiva usado em alunos.js.
(function () {
  const campoData = document.getElementById("data");
  const aviso = document.getElementById("aviso-feriado");

  if (campoData && aviso) {
    campoData.addEventListener("change", async () => {
      const data = campoData.value;
      if (!data) {
        aviso.hidden = true;
        return;
      }

      try {
        const resposta = await fetch(`/api/feriados/${data}`);
        const info = await resposta.json();

        if (info.feriado) {
          aviso.hidden = false;
          aviso.textContent = `Atenção: ${data} é feriado nacional (${info.nome}).`;
        } else {
          aviso.hidden = true;
        }
      } catch (erro) {
        // Falha de rede não deve impedir o professor de agendar a aula.
        aviso.hidden = true;
      }
    });
  }

  const regiaoAnuncio = document.createElement("div");
  regiaoAnuncio.setAttribute("aria-live", "polite");
  regiaoAnuncio.className = "visualmente-oculto";
  document.body.appendChild(regiaoAnuncio);

  document.querySelectorAll(".form-excluir").forEach((form) => {
    form.addEventListener("submit", async (evento) => {
      evento.preventDefault();
      const linha = form.closest("tr");
      const aulaId = form.action.match(/\/agenda\/(\d+)\/excluir/)?.[1];

      const confirmou = window.confirm("Excluir esta aula? Essa ação não pode ser desfeita.");
      if (!confirmou) return;

      try {
        const resposta = await fetch(`/api/aulas/${aulaId}`, {
          method: "DELETE",
          headers: { "X-CSRFToken": window.CSRF_TOKEN },
        });
        if (!resposta.ok) throw new Error("Falha ao excluir");

        linha.remove();
        regiaoAnuncio.textContent = "Aula excluída com sucesso.";
      } catch (erro) {
        regiaoAnuncio.textContent = "Não foi possível excluir a aula. Tente novamente.";
      }
    });
  });
})();
