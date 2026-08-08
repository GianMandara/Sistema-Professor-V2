def test_dashboard_redireciona_para_landing_com_login_sem_sessao(client_anonimo):
    """O login não é mais uma página própria — quem tenta acessar uma rota
    protegida sem sessão volta para a landing (/) com ?login=1, que faz o
    formulário aparecer já visível embutido ali."""
    resposta = client_anonimo.get("/dashboard")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/?login=1&proximo=/dashboard"


def test_alunos_redireciona_para_landing_com_login_sem_sessao(client_anonimo):
    resposta = client_anonimo.get("/alunos")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/?login=1&proximo=/alunos"


def test_landing_com_login_1_mostra_formulario_visivel(client_anonimo):
    html = client_anonimo.get("/?login=1").get_data(as_text=True)
    assert 'id="login"' in html
    assert "hidden" not in html.split('id="login"')[1].split(">")[0]


def test_landing_sem_login_1_mantem_formulario_oculto(client_anonimo):
    html = client_anonimo.get("/").get_data(as_text=True)
    assert "hidden" in html.split('id="login"')[1].split(">")[0]


def test_landing_e_health_nao_exigem_login(client_anonimo):
    assert client_anonimo.get("/").status_code == 200
    assert client_anonimo.get("/health").status_code == 200


def test_api_sem_sessao_retorna_401(client_anonimo):
    resposta = client_anonimo.get("/api/alunos")
    assert resposta.status_code == 401


def test_login_com_credenciais_corretas_redireciona_ao_dashboard(client_anonimo):
    resposta = client_anonimo.post(
        "/login", data={"usuario": "teste", "senha": "teste123"}
    )
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/dashboard"

    # a sessão criada deve realmente destravar as rotas protegidas
    assert client_anonimo.get("/dashboard").status_code == 200


def test_login_com_credenciais_erradas_mostra_erro(client_anonimo):
    resposta = client_anonimo.post(
        "/login", data={"usuario": "teste", "senha": "senha-errada"}, follow_redirects=True
    )
    assert "Usuário ou senha inválidos." in resposta.get_data(as_text=True)
    assert client_anonimo.get("/dashboard").status_code == 302


def test_login_respeita_proximo_como_destino_pos_login(client_anonimo):
    resposta = client_anonimo.post(
        "/login",
        data={"usuario": "teste", "senha": "teste123", "proximo": "/agenda"},
    )
    assert resposta.headers["Location"] == "/agenda"


def test_login_ignora_proximo_que_nao_e_caminho_interno(client_anonimo):
    """Evita open redirect: ?proximo=https://site-malicioso.com não deve
    ser seguido depois do login."""
    resposta = client_anonimo.post(
        "/login",
        data={"usuario": "teste", "senha": "teste123", "proximo": "https://site-malicioso.com"},
    )
    assert resposta.headers["Location"] == "/dashboard"


def test_logout_encerra_sessao(client):
    assert client.get("/dashboard").status_code == 200

    resposta = client.post("/logout")
    assert resposta.status_code == 302

    assert client.get("/dashboard").status_code == 302


def test_login_sem_credenciais_configuradas_falha_fechado(client_anonimo, app):
    """Sem LOGIN_USUARIO/LOGIN_SENHA definidos, ninguém consegue entrar —
    nem mesmo enviando usuário e senha em branco."""
    app.config["LOGIN_USUARIO"] = ""
    app.config["LOGIN_SENHA"] = ""

    resposta = client_anonimo.post(
        "/login", data={"usuario": "", "senha": ""}, follow_redirects=True
    )
    assert "Login não configurado" in resposta.get_data(as_text=True)
    assert client_anonimo.get("/dashboard").status_code == 302
