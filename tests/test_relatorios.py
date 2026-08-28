from app.models import Aluno, Aula
from app.relatorios import montar_boletim, nome_do_mes


def test_nome_do_mes():
    assert nome_do_mes(1) == "janeiro"
    assert nome_do_mes(12) == "dezembro"


def test_montar_boletim_filtra_so_o_mes_pedido(app, sessao_bd):
    aluno = Aluno(nome="Rafaela")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    sessao_bd.add_all([
        Aula(aluno_id=aluno.id, data="2026-08-05", horario="10:00", compareceu=True, nota=8.0),
        Aula(aluno_id=aluno.id, data="2026-08-19", horario="10:00", compareceu=False, nota=None),
        Aula(aluno_id=aluno.id, data="2026-09-02", horario="10:00", compareceu=True, nota=9.5),  # outro mês
    ])
    sessao_bd.commit()
    sessao_bd.refresh(aluno)

    boletim = montar_boletim(aluno, mes=8, ano=2026)

    assert boletim["total_aulas"] == 2
    assert boletim["presencas"] == 1
    assert boletim["faltas"] == 1
    assert boletim["media"] == 8.0
    assert boletim["notas_evolucao"] == [8.0]
    assert boletim["nome_mes"] == "agosto"
    # aula de setembro não deve aparecer
    assert all(a.data.startswith("2026-08") for a in boletim["aulas"])


def test_montar_boletim_sem_aulas_no_mes(app, sessao_bd):
    aluno = Aluno(nome="Sem Aulas")
    sessao_bd.add(aluno)
    sessao_bd.commit()
    sessao_bd.refresh(aluno)

    boletim = montar_boletim(aluno, mes=1, ano=2027)

    assert boletim["total_aulas"] == 0
    assert boletim["media"] is None
    assert boletim["notas_evolucao"] == []


def test_montar_boletim_ordena_aulas_cronologicamente(app, sessao_bd):
    aluno = Aluno(nome="Ordem")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    sessao_bd.add_all([
        Aula(aluno_id=aluno.id, data="2026-08-20", horario="09:00", nota=6.0),
        Aula(aluno_id=aluno.id, data="2026-08-05", horario="14:00", nota=7.0),
        Aula(aluno_id=aluno.id, data="2026-08-05", horario="09:00", nota=5.0),
    ])
    sessao_bd.commit()
    sessao_bd.refresh(aluno)

    boletim = montar_boletim(aluno, mes=8, ano=2026)
    datas_horarios = [(a.data, a.horario) for a in boletim["aulas"]]
    assert datas_horarios == [("2026-08-05", "09:00"), ("2026-08-05", "14:00"), ("2026-08-20", "09:00")]
