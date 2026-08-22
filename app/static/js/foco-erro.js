// Depois de um envio de formulário com erro, a página recarrega e a
// mensagem de erro aparece no topo — mas nada move o foco/a leitura até
// lá. Quem usa teclado ou leitor de tela pode não perceber que algo deu
// errado. Aqui, movemos o foco para o bloco de mensagens assim que a
// página carrega, se houver algum erro nele.
(function () {
  const bloco = document.getElementById("mensagens-flash");
  if (!bloco) return;

  const temErro = bloco.querySelector(".mensagem-erro");
  if (temErro) bloco.focus();
})();
