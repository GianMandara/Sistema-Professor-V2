// Histórico de aulas por aluno: presença e nota registradas em cada aula.
// Os gráficos gerais (aulas por mês/conteúdo) ficam no Dashboard — ver
// static/js/dashboard.js.
(function () {
  const seletorAluno = document.getElementById("seletor-aluno");

  function rotuloPresenca(compareceu) {
    if (compareceu === null) return { texto: "Pendente", classe: "badge-neutro" };
    return compareceu
      ? { texto: "Presente", classe: "badge-sucesso" }
      : { texto: "Faltou", classe: "badge-erro" };
  }

  async function carregarHistoricoAluno(alunoId) {
    const vazio = document.getElementById("historico-vazio");
    const resumo = document.getElementById("resumo-historico");
    const tabela = document.getElementById("tabela-historico-aluno");
    const corpo = tabela.querySelector("tbody");

    if (!alunoId) {
      vazio.hidden = false;
      vazio.textContent = "Nenhum aluno selecionado ainda.";
      resumo.hidden = true;
      tabela.hidden = true;
      corpo.innerHTML = "";
      return;
    }

    const resposta = await fetch(`/api/alunos/${alunoId}/aulas`);
    const aulas = await resposta.json();

    if (aulas.length === 0) {
      vazio.hidden = false;
      vazio.textContent = "Este aluno ainda não tem aulas registradas.";
      resumo.hidden = true;
      tabela.hidden = true;
      corpo.innerHTML = "";
      return;
    }

    vazio.hidden = true;
    resumo.hidden = false;
    tabela.hidden = false;

    const presencas = aulas.filter((a) => a.compareceu === true).length;
    const faltas = aulas.filter((a) => a.compareceu === false).length;
    const notas = aulas.filter((a) => typeof a.nota === "number").map((a) => a.nota);
    const media = notas.length ? (notas.reduce((soma, n) => soma + n, 0) / notas.length).toFixed(1) : "-";

    document.getElementById("resumo-total").textContent = aulas.length;
    document.getElementById("resumo-presencas").textContent = presencas;
    document.getElementById("resumo-faltas").textContent = faltas;
    document.getElementById("resumo-media").textContent = media;

    corpo.innerHTML = "";
    aulas.forEach((aula) => {
      const presenca = rotuloPresenca(aula.compareceu);
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${aula.data}</td>
        <td>${aula.conteudo_titulo ?? "-"}</td>
        <td><span class="badge ${presenca.classe}">${presenca.texto}</span></td>
        <td>${typeof aula.nota === "number" ? aula.nota : "-"}</td>
      `;
      corpo.appendChild(tr);
    });
  }

  seletorAluno?.addEventListener("change", () => carregarHistoricoAluno(seletorAluno.value));
})();
