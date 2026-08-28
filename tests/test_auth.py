import app.routes.auth as auth_module
from app.extensions import db
from app.models import Usuario


def test_dashboard_redireciona_para_landing_com_login_sem_sessao(client_anonimo):
    """O login não é uma página própria — quem tenta acessar uma rota
    protegida sem sessão volta para a landing (/) com ?login=1, que faz o
    formulário aparecer já visível embutido ali."""
    resposta = client_anonimo.get("/dashboard")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/?login=1&proximo=/dashboard"


def test_alunos_redireciona_para_landing_com_login_sem_sessao(client_anonimo):
    resposta = client_anonimo.get("/alunos")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/?login=1&proximo=/alunos"


def test_landing_com_login_1_mostra_painel_entrar_visivel(client_anonimo):
    html = client_anonimo.get("/?login=1").get_data(as_text=True)
    assert 'id="painel-entrar"' in html
    assert "hidden" not in html.split('id="painel-entrar"')[1].split(">")[0]


def test_landing_sem_parametros_mantem_modal_oculto(client_anonimo):
    html = client_anonimo.get("/").get_data(as_text=True)
    assert "hidden" in html.split('id="login"')[1].split(">")[0]


def test_landing_e_health_nao_exigem_login(client_anonimo):
    assert client_anonimo.get("/").status_code == 200
    assert client_anonimo.get("/health").status_code == 200


def test_api_sem_sessao_retorna_401(client_anonimo):
    resposta = client_anonimo.get("/api/alunos")
    assert resposta.status_code == 401


# ---------------------------------------------------------------- cadastro --
def test_cadastro_cria_conta_e_ja_loga(client_anonimo, app):
    resposta = client_anonimo.post(
        "/cadastro",
        data={
            "nome": "Beatriz Souza",
            "email": "beatriz@exemplo.com",
            "senha": "senha-forte-123",
            "confirmar_senha": "senha-forte-123",
        },
    )
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/dashboard"

    with app.app_context():
        # o e-mail fica criptografado em repouso — não dá mais para
        # filtrar direto por ele; a busca de verdade usa email_hash
        # (ver _buscar_usuario_por_email em auth.py e test_crypto.py)
        criado = next((u for u in Usuario.query.all() if u.email == "beatriz@exemplo.com"), None)
        assert criado is not None
        assert criado.email_hash  # já vem preenchido, sem precisar de migração

    # a conta recém-criada já deixa a sessão autenticada
    assert client_anonimo.get("/dashboard").status_code == 200


def test_cadastro_envia_email_de_boas_vindas(client_anonimo, app, monkeypatch):
    chamadas = []
    monkeypatch.setattr(auth_module, "enviar_email_boas_vindas", lambda usuario: chamadas.append(usuario.email))

    client_anonimo.post(
        "/cadastro",
        data={
            "nome": "Carlos Lima",
            "email": "carlos@exemplo.com",
            "senha": "senha-forte-123",
            "confirmar_senha": "senha-forte-123",
        },
    )
    assert chamadas == ["carlos@exemplo.com"]


def test_cadastro_com_email_ja_existente_falha(client_anonimo, app):
    with app.app_context():
        usuario = Usuario(nome="Existente", email="ja-existe@exemplo.com")
        usuario.definir_senha("qualquer-senha")

        db.session.add(usuario)
        db.session.commit()

    resposta = client_anonimo.post(
        "/cadastro",
        data={
            "nome": "Outro",
            "email": "ja-existe@exemplo.com",
            "senha": "senha-forte-123",
            "confirmar_senha": "senha-forte-123",
        },
        follow_redirects=True,
    )
    assert "Já existe uma conta com esse e-mail." in resposta.get_data(as_text=True)


def test_cadastro_com_senha_curta_falha(client_anonimo):
    resposta = client_anonimo.post(
        "/cadastro",
        data={"nome": "Ana", "email": "ana@exemplo.com", "senha": "123", "confirmar_senha": "123"},
        follow_redirects=True,
    )
    assert "A senha deve ter pelo menos 8 caracteres." in resposta.get_data(as_text=True)


def test_cadastro_com_senhas_diferentes_falha(client_anonimo):
    resposta = client_anonimo.post(
        "/cadastro",
        data={
            "nome": "Ana",
            "email": "ana2@exemplo.com",
            "senha": "senha-forte-123",
            "confirmar_senha": "outra-coisa",
        },
        follow_redirects=True,
    )
    assert "As senhas não coincidem." in resposta.get_data(as_text=True)


# ------------------------------------------------------------------- login --
def test_login_com_credenciais_corretas_redireciona_ao_dashboard(client_anonimo, app):
    with app.app_context():
        usuario = Usuario(nome="Diana", email="diana@exemplo.com")
        usuario.definir_senha("senha-teste-123")

        db.session.add(usuario)
        db.session.commit()

    resposta = client_anonimo.post("/login", data={"email": "diana@exemplo.com", "senha": "senha-teste-123"})
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/dashboard"
    assert client_anonimo.get("/dashboard").status_code == 200


def test_login_com_senha_errada_mostra_erro(client_anonimo, app):
    with app.app_context():
        usuario = Usuario(nome="Diana", email="diana2@exemplo.com")
        usuario.definir_senha("senha-teste-123")

        db.session.add(usuario)
        db.session.commit()

    resposta = client_anonimo.post(
        "/login", data={"email": "diana2@exemplo.com", "senha": "senha-errada"}, follow_redirects=True
    )
    assert "E-mail ou senha inválidos." in resposta.get_data(as_text=True)
    assert client_anonimo.get("/dashboard").status_code == 302


def test_login_com_email_inexistente_mostra_erro(client_anonimo):
    resposta = client_anonimo.post(
        "/login", data={"email": "nao-existe@exemplo.com", "senha": "qualquer"}, follow_redirects=True
    )
    assert "E-mail ou senha inválidos." in resposta.get_data(as_text=True)


# ------------------------------------------------------- notificação de acesso --
def test_login_com_sucesso_notifica_novo_acesso_por_email(client_anonimo, app, monkeypatch):
    with app.app_context():
        usuario = Usuario(nome="Igor", email="igor-acesso@exemplo.com")
        usuario.definir_senha("senha-teste-123")
        db.session.add(usuario)
        db.session.commit()

    chamadas = []
    monkeypatch.setattr(
        auth_module, "enviar_email_novo_acesso", lambda usuario, ip, quando: chamadas.append(usuario.email)
    )

    client_anonimo.post("/login", data={"email": "igor-acesso@exemplo.com", "senha": "senha-teste-123"})
    assert chamadas == ["igor-acesso@exemplo.com"]


def test_login_com_senha_errada_notifica_tentativa_por_email(client_anonimo, app, monkeypatch):
    with app.app_context():
        usuario = Usuario(nome="Julia", email="julia-tentativa@exemplo.com")
        usuario.definir_senha("senha-teste-123")
        db.session.add(usuario)
        db.session.commit()

    chamadas = []
    monkeypatch.setattr(
        auth_module, "enviar_email_tentativa_falha", lambda usuario, ip, quando: chamadas.append(usuario.email)
    )

    client_anonimo.post("/login", data={"email": "julia-tentativa@exemplo.com", "senha": "senha-errada"})
    assert chamadas == ["julia-tentativa@exemplo.com"]


def test_login_com_email_inexistente_nao_notifica_ninguem(client_anonimo, monkeypatch):
    """Sem conta correspondente, não há quem notificar — e notificar
    mesmo assim revelaria quais e-mails têm conta."""
    chamadas = []
    monkeypatch.setattr(
        auth_module, "enviar_email_tentativa_falha", lambda usuario, ip, quando: chamadas.append(usuario.email)
    )

    client_anonimo.post("/login", data={"email": "ninguem-aqui@exemplo.com", "senha": "qualquer"})
    assert chamadas == []


def test_login_respeita_proximo_como_destino_pos_login(client):
    # `client` já está logado; deslogar e logar de novo informando proximo.
    client.post("/logout")
    resposta = client.post(
        "/login",
        data={"email": "professor@teste.com", "senha": "senha-teste-123", "proximo": "/agenda"},
    )
    assert resposta.headers["Location"] == "/agenda"


def test_login_ignora_proximo_que_nao_e_caminho_interno(client):
    """Evita open redirect: ?proximo=https://site-malicioso.com não deve
    ser seguido depois do login."""
    client.post("/logout")
    resposta = client.post(
        "/login",
        data={
            "email": "professor@teste.com",
            "senha": "senha-teste-123",
            "proximo": "https://site-malicioso.com",
        },
    )
    assert resposta.headers["Location"] == "/dashboard"


def test_logout_encerra_sessao(client):
    assert client.get("/dashboard").status_code == 200

    resposta = client.post("/logout")
    assert resposta.status_code == 302

    assert client.get("/dashboard").status_code == 302


# --------------------------------------------------------- esqueci a senha --
def test_esqueci_senha_com_email_existente_envia_link(client_anonimo, app, monkeypatch):
    with app.app_context():
        usuario = Usuario(nome="Elisa", email="elisa@exemplo.com")
        usuario.definir_senha("senha-antiga-123")

        db.session.add(usuario)
        db.session.commit()

    chamadas = []
    monkeypatch.setattr(
        auth_module, "enviar_email_redefinicao_senha", lambda usuario, link: chamadas.append((usuario.email, link))
    )

    resposta = client_anonimo.post("/esqueci-senha", data={"email": "elisa@exemplo.com"}, follow_redirects=True)
    assert "enviamos um link para redefinir a senha" in resposta.get_data(as_text=True)
    assert len(chamadas) == 1
    assert chamadas[0][0] == "elisa@exemplo.com"
    assert "/redefinir-senha/" in chamadas[0][1]


def test_esqueci_senha_com_email_inexistente_mostra_mesma_mensagem(client_anonimo, monkeypatch):
    """Não revela quais e-mails têm conta: mesma mensagem em ambos os casos."""
    chamadas = []
    monkeypatch.setattr(
        auth_module, "enviar_email_redefinicao_senha", lambda usuario, link: chamadas.append(usuario.email)
    )

    resposta = client_anonimo.post(
        "/esqueci-senha", data={"email": "nunca-existiu@exemplo.com"}, follow_redirects=True
    )
    assert "enviamos um link para redefinir a senha" in resposta.get_data(as_text=True)
    assert chamadas == []


def test_redefinir_senha_com_token_valido_troca_a_senha(client_anonimo, app):
    with app.app_context():
        usuario = Usuario(nome="Fabio", email="fabio@exemplo.com")
        usuario.definir_senha("senha-antiga-123")

        db.session.add(usuario)
        db.session.commit()

        token = auth_module._serializer().dumps("fabio@exemplo.com", salt=auth_module.SALT_REDEFINICAO_SENHA)

    resposta = client_anonimo.post(
        f"/redefinir-senha/{token}",
        data={"senha": "senha-nova-456", "confirmar_senha": "senha-nova-456"},
    )
    assert resposta.status_code == 302

    # a senha antiga não funciona mais, a nova funciona
    falha = client_anonimo.post("/login", data={"email": "fabio@exemplo.com", "senha": "senha-antiga-123"})
    assert falha.headers["Location"] != "/dashboard"

    sucesso = client_anonimo.post("/login", data={"email": "fabio@exemplo.com", "senha": "senha-nova-456"})
    assert sucesso.headers["Location"] == "/dashboard"


def test_redefinir_senha_com_token_invalido_redireciona(client_anonimo):
    resposta = client_anonimo.get("/redefinir-senha/token-invalido-qualquer", follow_redirects=True)
    assert "inválido ou expirou" in resposta.get_data(as_text=True)


def test_redefinir_senha_com_token_expirado_redireciona(client_anonimo, app):
    with app.app_context():
        usuario = Usuario(nome="Gustavo", email="gustavo@exemplo.com")
        usuario.definir_senha("senha-antiga-123")

        db.session.add(usuario)
        db.session.commit()

        token = auth_module._serializer().dumps("gustavo@exemplo.com", salt=auth_module.SALT_REDEFINICAO_SENHA)

    # simula token expirado exigindo validade negativa
    original = auth_module.VALIDADE_TOKEN_SEGUNDOS
    auth_module.VALIDADE_TOKEN_SEGUNDOS = -1
    try:
        resposta = client_anonimo.get(f"/redefinir-senha/{token}", follow_redirects=True)
    finally:
        auth_module.VALIDADE_TOKEN_SEGUNDOS = original

    assert "inválido ou expirou" in resposta.get_data(as_text=True)


def test_redefinir_senha_com_senhas_diferentes_mostra_erro(client_anonimo, app):
    with app.app_context():
        usuario = Usuario(nome="Helena", email="helena@exemplo.com")
        usuario.definir_senha("senha-antiga-123")

        db.session.add(usuario)
        db.session.commit()

        token = auth_module._serializer().dumps("helena@exemplo.com", salt=auth_module.SALT_REDEFINICAO_SENHA)

    resposta = client_anonimo.post(
        f"/redefinir-senha/{token}",
        data={"senha": "senha-nova-456", "confirmar_senha": "outra-coisa"},
    )
    assert "As senhas não coincidem." in resposta.get_data(as_text=True)
