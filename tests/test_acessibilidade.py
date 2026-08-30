"""A lógica de cada ferramenta (fonte, contraste, guia de leitura etc.)
vive em JavaScript puro no navegador — não dá pra testar com pytest.
Aqui só garantimos que o widget está presente (HTML/CSS/JS incluídos)
em toda página-raiz do sistema, pública ou não."""


def test_widget_presente_na_landing(client_anonimo):
    html = client_anonimo.get("/").get_data(as_text=True)
    assert 'id="a11y-abrir"' in html
    assert 'id="a11y-painel"' in html
    assert "css/acessibilidade.css" in html
    assert "js/acessibilidade.js" in html


def test_widget_presente_no_dashboard(client):
    html = client.get("/dashboard").get_data(as_text=True)
    assert 'id="a11y-abrir"' in html


def test_widget_tem_todas_as_ferramentas_esperadas(client_anonimo):
    html = client_anonimo.get("/").get_data(as_text=True)
    for acao in [
        "fonte-aumentar",
        "fonte-diminuir",
        "alto-contraste",
        "fonte-legivel",
        "espacamento",
        "links",
        "escala-cinza",
        "sem-animacao",
        "cursor-grande",
        "guia-leitura",
        "resetar",
    ]:
        assert f'data-acao="{acao}"' in html, f"ferramenta {acao} não encontrada no HTML"
    assert 'id="a11y-libras"' in html


def test_widget_presente_no_boletim_publico(client, monkeypatch, app):
    import app.routes.views as views_module

    resposta = client.post(
        "/alunos", data={"nome": "Aluno A11y Widget", "email": "a11ywidget@exemplo.com", "telefone": ""}
    )
    assert resposta.status_code == 302
    aluno = next(a for a in client.get("/api/alunos").get_json() if a["nome"] == "Aluno A11y Widget")

    monkeypatch.setattr(views_module, "enviar_email_boletim", lambda *a, **k: True)

    html = client.get("/acompanhamento").get_data(as_text=True)
    import re

    token = re.search(r'name="csrf_token" value="([^"]*)"', html).group(1)
    resposta_boletim = client.post(
        "/acompanhamento/gerar-boletim",
        data={"csrf_token": token, "aluno_id": aluno["id"], "mes_ano": "2026-08"},
        follow_redirects=True,
    )
    assert 'id="a11y-abrir"' in resposta_boletim.get_data(as_text=True)
