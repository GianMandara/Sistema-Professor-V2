"""Boletim mensal do aluno: notas, presença e evolução, no mesmo espírito
de um boletim escolar. Gerado sob demanda pelo professor — sem tarefa
agendada rodando sozinha no servidor — e aberto pelo aluno por um link
assinado (token), sem precisar de conta/login."""
from __future__ import annotations

MESES_NOME = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def nome_do_mes(mes: int) -> str:
    return MESES_NOME[mes - 1]


def montar_boletim(aluno, mes: int, ano: int) -> dict:
    """Monta os dados do boletim de um aluno para um mês/ano específicos.

    Sempre calculado na hora a partir dos dados atuais — não é uma foto
    congelada no momento da geração. Se o professor corrigir uma nota
    depois de enviar o link, o aluno vê a versão corrigida ao reabri-lo.
    """
    prefixo = f"{ano:04d}-{mes:02d}"
    aulas_do_mes = sorted(
        (aula for aula in aluno.aulas if aula.data.startswith(prefixo)),
        key=lambda aula: (aula.data, aula.horario),
    )

    notas = [aula.nota for aula in aulas_do_mes if aula.nota is not None]
    presencas = sum(1 for aula in aulas_do_mes if aula.compareceu is True)
    faltas = sum(1 for aula in aulas_do_mes if aula.compareceu is False)
    media = round(sum(notas) / len(notas), 1) if notas else None

    return {
        "aluno": aluno,
        "mes": mes,
        "ano": ano,
        "nome_mes": nome_do_mes(mes),
        "aulas": aulas_do_mes,
        "total_aulas": len(aulas_do_mes),
        "presencas": presencas,
        "faltas": faltas,
        "media": media,
        "notas_evolucao": notas,
    }
