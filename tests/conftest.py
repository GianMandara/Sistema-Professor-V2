import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    application = create_app(testing=True)
    yield application


@pytest.fixture
def client_anonimo(app):
    """Cliente sem sessão — usado para testar login, logout e os
    redirecionamentos de quem tenta acessar sem estar autenticado."""
    return app.test_client()


@pytest.fixture
def client(client_anonimo):
    """A maioria dos testes precisa de uma sessão logada, já que quase
    todas as rotas exigem autenticação. Credenciais vêm de TestingConfig."""
    client_anonimo.post("/login", data={"usuario": "teste", "senha": "teste123"})
    return client_anonimo


@pytest.fixture
def sessao_bd(app):
    with app.app_context():
        yield db.session
        db.session.remove()
