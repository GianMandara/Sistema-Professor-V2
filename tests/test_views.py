def test_landing_carrega(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "Acessar sistema" in resposta.get_data(as_text=True)


def test_dashboard_carrega(client):
    resposta = client.get("/dashboard")
    assert resposta.status_code == 200
    assert "Dashboard" in resposta.get_data(as_text=True)


def test_paginas_possuem_skip_link_e_lang_pt_br(client):
    """Checagem básica de acessibilidade: idioma declarado e link de pular
    navegação presentes em todas as páginas (landing + app shell)."""
    for rota in ("/", "/dashboard", "/alunos", "/conteudos", "/agenda", "/acompanhamento"):
        html = client.get(rota).get_data(as_text=True)
        assert 'lang="pt-br"' in html
        assert "skip-link" in html


def test_conteudos_pagina_lista_materias_padrao(client):
    """A tabela alunos/conteúdos parte vazia, mas conteúdos deve vir com as
    matérias comuns pré-cadastradas (seed), senão o select da Agenda fica
    sem opções para escolher."""
    html = client.get("/conteudos").get_data(as_text=True)
    assert "Português" in html
    assert "Matemática" in html


def test_agenda_select_de_conteudo_vem_populado(client):
    html = client.get("/agenda").get_data(as_text=True)
    assert "Português" in html
    assert "Matemática" in html


def test_cadastrar_conteudo_via_formulario_html(client):
    resposta = client.post("/conteudos", data={"titulo": "Filosofia", "descricao": ""})
    assert resposta.status_code == 302

    html = client.get("/conteudos").get_data(as_text=True)
    assert "Filosofia" in html


def test_registrar_presenca_e_nota_ao_editar_aula(client):
    aluno = client.post("/api/alunos", json={"nome": "Camila"}).get_json()
    aula = client.post(
        "/agenda",
        data={"aluno_id": aluno["id"], "data": "2026-08-14", "horario": "11:00"},
    )
    assert aula.status_code == 302

    aula_id = [a["id"] for a in client.get("/api/aulas").get_json() if a["aluno_id"] == aluno["id"]][0]

    resposta = client.post(
        f"/agenda/{aula_id}/editar",
        data={
            "aluno_id": aluno["id"],
            "data": "2026-08-14",
            "horario": "11:00",
            "compareceu": "sim",
            "nota": "9.5",
        },
    )
    assert resposta.status_code == 302

    aula_atualizada = client.get("/api/aulas").get_json()[0]
    assert aula_atualizada["compareceu"] is True
    assert aula_atualizada["nota"] == 9.5


def test_editar_aula_com_nota_invalida_mostra_erro(client):
    aluno = client.post("/api/alunos", json={"nome": "Diego"}).get_json()
    client.post("/agenda", data={"aluno_id": aluno["id"], "data": "2026-08-15", "horario": "09:00"})
    aula_id = [a["id"] for a in client.get("/api/aulas").get_json() if a["aluno_id"] == aluno["id"]][0]

    resposta = client.post(
        f"/agenda/{aula_id}/editar",
        data={"aluno_id": aluno["id"], "data": "2026-08-15", "horario": "09:00", "nota": "15"},
    )
    assert resposta.status_code == 200
    assert "A nota deve ser um número entre 0 e 10." in resposta.get_data(as_text=True)


def test_agendar_aula_avisa_quando_aluno_nao_tem_email(client):
    aluno = client.post("/api/alunos", json={"nome": "Marcos"}).get_json()

    resposta = client.post(
        "/agenda",
        data={"aluno_id": aluno["id"], "data": "2026-08-16", "horario": "13:00"},
        follow_redirects=True,
    )
    assert "Cadastre o e-mail do aluno para enviar lembretes automáticos." in resposta.get_data(as_text=True)


def test_agendar_aula_com_email_configurado_confirma_envio(client, monkeypatch):
    import app.routes.views as views_module

    monkeypatch.setattr(views_module, "enviar_lembrete_aula", lambda aula: True)

    aluno = client.post("/api/alunos", json={"nome": "Nina", "email": "nina@exemplo.com"}).get_json()
    resposta = client.post(
        "/agenda",
        data={"aluno_id": aluno["id"], "data": "2026-08-17", "horario": "14:00"},
        follow_redirects=True,
    )
    assert "Lembrete enviado por e-mail ao aluno." in resposta.get_data(as_text=True)


def test_agendar_aula_com_falha_no_envio_avisa_sem_quebrar(client, monkeypatch):
    import app.routes.views as views_module

    monkeypatch.setattr(views_module, "enviar_lembrete_aula", lambda aula: False)

    aluno = client.post("/api/alunos", json={"nome": "Otavio", "email": "otavio@exemplo.com"}).get_json()
    resposta = client.post(
        "/agenda",
        data={"aluno_id": aluno["id"], "data": "2026-08-18", "horario": "08:00"},
        follow_redirects=True,
    )
    assert "não foi possível enviar o lembrete por e-mail" in resposta.get_data(as_text=True)


def test_acompanhamento_lista_alunos_no_seletor_de_historico(client):
    client.post("/api/alunos", json={"nome": "Fernanda"})
    html = client.get("/acompanhamento").get_data(as_text=True)
    assert "Fernanda" in html
    assert 'id="seletor-aluno"' in html


def test_cadastrar_aluno_via_formulario_html(client):
    resposta = client.post(
        "/alunos", data={"nome": "Pedro Alves", "email": "pedro@exemplo.com", "telefone": ""}
    )
    assert resposta.status_code == 302  # redireciona após salvar (padrão PRG)

    html = client.get("/alunos").get_data(as_text=True)
    assert "Pedro Alves" in html


def test_health_check(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok"}
