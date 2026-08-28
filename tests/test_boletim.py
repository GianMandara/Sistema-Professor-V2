import app.routes.views as views_module
from app.models import Aula


def _criar_aluno(client, nome, email=""):
    resposta = client.post("/alunos", data={"nome": nome, "email": email, "telefone": ""})
    assert resposta.status_code == 302
    aluno = next(a for a in client.get("/api/alunos").get_json() if a["nome"] == nome)
    return aluno["id"]


def test_gerar_boletim_exige_login(client_anonimo):
    resposta = client_anonimo.post(
        "/acompanhamento/gerar-boletim", data={"aluno_id": "1", "mes_ano": "2026-08"}
    )
    assert resposta.status_code == 302
    assert "login=1" in resposta.headers["Location"]


def test_boletim_publico_nao_exige_login(client_anonimo):
    """A própria rota pública deve responder sem sessão — mesmo que com
    404 para um token inválido, e não com redirecionamento para login."""
    resposta = client_anonimo.get("/boletim/token-invalido-qualquer")
    assert resposta.status_code == 404


def test_gerar_boletim_sem_email_do_aluno_mostra_erro(client):
    aluno_id = _criar_aluno(client, "Aluno Sem Email")

    resposta = client.post(
        "/acompanhamento/gerar-boletim",
        data={"aluno_id": aluno_id, "mes_ano": "2026-08"},
        follow_redirects=True,
    )
    assert "não tem e-mail cadastrado" in resposta.get_data(as_text=True)


def test_gerar_boletim_com_mes_invalido_mostra_erro(client):
    aluno_id = _criar_aluno(client, "Aluno Mes Invalido", email="mesinvalido@exemplo.com")

    resposta = client.post(
        "/acompanhamento/gerar-boletim",
        data={"aluno_id": aluno_id, "mes_ano": "nao-e-um-mes"},
        follow_redirects=True,
    )
    assert "Selecione um mês válido" in resposta.get_data(as_text=True)


def test_gerar_boletim_com_sucesso_envia_email_e_mostra_pagina(client, monkeypatch, app):
    aluno_id = _criar_aluno(client, "Aluno Boletim OK", email="boletimok@exemplo.com")

    with app.app_context():
        aula = Aula(aluno_id=aluno_id, data="2026-08-10", horario="10:00", compareceu=True, nota=9.0)
        from app.extensions import db

        db.session.add(aula)
        db.session.commit()

    chamadas = []
    monkeypatch.setattr(
        views_module,
        "enviar_email_boletim",
        lambda aluno, nome_mes, ano, link: chamadas.append((aluno.email, nome_mes, ano)) or True,
    )

    resposta = client.post(
        "/acompanhamento/gerar-boletim",
        data={"aluno_id": aluno_id, "mes_ano": "2026-08"},
        follow_redirects=True,
    )
    assert resposta.status_code == 200
    assert chamadas == [("boletimok@exemplo.com", "agosto", 2026)]

    # o professor foi redirecionado pra mesma página pública que o aluno vê
    texto = resposta.get_data(as_text=True)
    assert "Aluno Boletim OK" in texto
    assert "9.0" in texto or "9,0" in texto


def test_boletim_com_falha_no_envio_ainda_mostra_a_pagina(client, monkeypatch):
    aluno_id = _criar_aluno(client, "Aluno Envio Falho", email="falha@exemplo.com")

    monkeypatch.setattr(views_module, "enviar_email_boletim", lambda *a, **k: False)

    resposta = client.post(
        "/acompanhamento/gerar-boletim",
        data={"aluno_id": aluno_id, "mes_ano": "2026-08"},
        follow_redirects=True,
    )
    assert "Aluno Envio Falho" in resposta.get_data(as_text=True)
    assert "não foi possível enviar" in resposta.get_data(as_text=True)


def test_boletim_publico_mostra_dados_corretos_do_mes(client, app):
    aluno_id = _criar_aluno(client, "Aluno Publico", email="publico@exemplo.com")

    with app.app_context():
        from app.extensions import db

        db.session.add_all([
            Aula(aluno_id=aluno_id, data="2026-08-03", horario="10:00", compareceu=True, nota=7.5),
            Aula(aluno_id=aluno_id, data="2026-09-03", horario="10:00", compareceu=True, nota=10.0),
        ])
        db.session.commit()

    resposta = client.post(
        "/acompanhamento/gerar-boletim",
        data={"aluno_id": aluno_id, "mes_ano": "2026-08"},
        follow_redirects=True,
    )
    texto = resposta.get_data(as_text=True)
    assert "2026-08-03" in texto
    assert "2026-09-03" not in texto  # aula de outro mês não deve aparecer


def test_boletim_publico_com_token_expirado_retorna_404(client_anonimo, app, monkeypatch):
    import app.routes.views as views

    monkeypatch.setattr(views, "VALIDADE_BOLETIM_SEGUNDOS", -1)
    with app.app_context():
        token = views._serializer_boletim().dumps(
            {"aluno_id": 1, "mes": 8, "ano": 2026}, salt=views.SALT_BOLETIM
        )

    resposta = client_anonimo.get(f"/boletim/{token}")
    assert resposta.status_code == 404
