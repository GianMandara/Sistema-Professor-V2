// Busca as estatísticas (agregadas com pandas no backend) via API e
// desenha os gráficos com Chart.js. As tabelas HTML equivalentes também
// são preenchidas, servindo de alternativa acessível ao <canvas>.
(function () {
  async function carregar() {
    const resposta = await fetch("/api/estatisticas");
    const dados = await resposta.json();

    preencherTabela("tabela-aulas-mes", dados.aulas_por_mes, "mes", "quantidade");
    preencherTabela("tabela-aulas-conteudo", dados.aulas_por_conteudo, "conteudo", "quantidade");

    desenharGrafico(
      "grafico-aulas-mes",
      "bar",
      dados.aulas_por_mes.map((linha) => linha.mes),
      dados.aulas_por_mes.map((linha) => linha.quantidade),
      "Aulas por mês"
    );

    desenharGrafico(
      "grafico-aulas-conteudo",
      "bar",
      dados.aulas_por_conteudo.map((linha) => linha.conteudo),
      dados.aulas_por_conteudo.map((linha) => linha.quantidade),
      "Aulas por conteúdo"
    );
  }

  function preencherTabela(idTabela, linhas, chaveRotulo, chaveValor) {
    const corpo = document.querySelector(`#${idTabela} tbody`);
    if (!corpo) return;
    corpo.innerHTML = "";
    linhas.forEach((linha) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${linha[chaveRotulo]}</td><td>${linha[chaveValor]}</td>`;
      corpo.appendChild(tr);
    });
  }

  function desenharGrafico(idCanvas, tipo, rotulos, valores, titulo) {
    const canvas = document.getElementById(idCanvas);
    if (!canvas || typeof Chart === "undefined") return;

    new Chart(canvas, {
      type: tipo,
      data: {
        labels: rotulos,
        datasets: [{ label: titulo, data: valores, backgroundColor: "#3454d1" }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, title: { display: true, text: titulo } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      },
    });
  }

  carregar();
})();
