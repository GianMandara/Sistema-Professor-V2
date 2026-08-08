import pytest

from app import create_app
from app.extensions import db
from app.models import Usuario

EMAIL_TESTE = "professor@teste.com"
SENHA_TESTE = "senha-teste-123"


@pytest.fixture
def app():
    application = create_app(testing=True)
    yield application


@pytest.fixture
def client_anonimo(app):
    """Cliente sem sessão — usado para testar cadastro, login, logout e os
    redirecionamentos de quem tenta acessar sem estar autenticado."""
    return app.test_client()


@pytest.fixture
def client(client_anonimo, app):
    """A maioria dos testes precisa de uma sessão logada, já que quase
    todas as rotas exigem autenticação. Cria uma conta de teste e loga."""
    with app.app_context():
        usuario = Usuario(nome="Professor Teste", email=EMAIL_TESTE)
        usuario.definir_senha(SENHA_TESTE)
        db.session.add(usuario)
        db.session.commit()

    client_anonimo.post("/login", data={"email": EMAIL_TESTE, "senha": SENHA_TESTE})
    return client_anonimo


@pytest.fixture
def sessao_bd(app):
    with app.app_context():
        yield db.session
        db.session.remove()
