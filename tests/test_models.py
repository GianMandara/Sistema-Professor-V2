from app.models import Aluno, Aula, Conteudo


def test_aluno_to_dict(app, sessao_bd):
    aluno = Aluno(nome="Maria Silva", email="maria@exemplo.com", telefone="11999999999")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    dados = aluno.to_dict()
    assert dados["nome"] == "Maria Silva"
    assert dados["email"] == "maria@exemplo.com"
    assert dados["id"] == aluno.id


def test_aula_to_dict_inclui_nome_do_aluno_e_conteudo(app, sessao_bd):
    aluno = Aluno(nome="João Souza")
    conteudo = Conteudo(titulo="Gramática Inglesa")
    sessao_bd.add_all([aluno, conteudo])
    sessao_bd.commit()

    aula = Aula(aluno_id=aluno.id, conteudo_id=conteudo.id, data="2026-08-10", horario="14:00")
    sessao_bd.add(aula)
    sessao_bd.commit()

    dados = aula.to_dict()
    assert dados["aluno_nome"] == "João Souza"
    assert dados["conteudo_titulo"] == "Gramática Inglesa"


def test_aula_presenca_e_nota_ficam_pendentes_por_padrao(app, sessao_bd):
    aluno = Aluno(nome="Rafael")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    aula = Aula(aluno_id=aluno.id, data="2026-08-12", horario="10:00")
    sessao_bd.add(aula)
    sessao_bd.commit()

    dados = aula.to_dict()
    assert dados["compareceu"] is None
    assert dados["nota"] is None


def test_aula_registra_presenca_e_nota(app, sessao_bd):
    aluno = Aluno(nome="Sofia")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    aula = Aula(aluno_id=aluno.id, data="2026-08-13", horario="15:30", compareceu=True, nota=8.5)
    sessao_bd.add(aula)
    sessao_bd.commit()

    dados = aula.to_dict()
    assert dados["compareceu"] is True
    assert dados["nota"] == 8.5


def test_excluir_aluno_remove_aulas_associadas(app, sessao_bd):
    aluno = Aluno(nome="Ana")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    aula = Aula(aluno_id=aluno.id, data="2026-08-11", horario="09:00")
    sessao_bd.add(aula)
    sessao_bd.commit()
    aula_id = aula.id

    sessao_bd.delete(aluno)
    sessao_bd.commit()

    assert Aula.query.get(aula_id) is None
