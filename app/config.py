import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# `flask run` carrega .env sozinho, mas `python run.py` e o gunicorn em
# produção não — por isso carregamos aqui, no import do módulo de config,
# antes de qualquer os.environ.get() ser avaliado abaixo. Se as variáveis
# já vierem do ambiente real (Render, Docker, etc.), load_dotenv() não as
# sobrescreve.
load_dotenv(BASE_DIR / ".env")


class Config:
    """Configuração base. Lê tudo de variáveis de ambiente (12-factor app)."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-troque-em-producao")

    # Em nuvem (Render/Railway/etc.) a variável DATABASE_URL normalmente vem
    # no formato postgres://..., mas o SQLAlchemy 2.x exige postgresql://.
    _database_url = os.environ.get("DATABASE_URL")
    if _database_url and _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _database_url or f"sqlite:///{BASE_DIR / 'instance' / 'escola.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # URL base da API pública de feriados (BrasilAPI). Configurável para
    # permitir apontar para um mock/stub durante os testes.
    FERIADOS_API_URL = os.environ.get(
        "FERIADOS_API_URL", "https://brasilapi.com.br/api/feriados/v1"
    )

    # E-mail de lembrete ao agendar uma aula (via SMTP, sem dependências
    # extras). Sem MAIL_SERVER/MAIL_USERNAME configurados, o envio é
    # simplesmente pulado — agendar uma aula nunca falha por causa disso.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    # Senhas de app do Google são exibidas em blocos ("abcd efgh ijkl mnop")
    # mas o valor real não tem espaços — removê-los aqui evita falha de
    # autenticação por um copiar-e-colar comum.
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "").replace(" ", "")
    MAIL_REMETENTE = os.environ.get("MAIL_REMETENTE", "") or MAIL_USERNAME
    MAIL_HABILITADO = bool(MAIL_SERVER and MAIL_USERNAME)

    # Cookies de sessão mais seguros. SESSION_COOKIE_SECURE só pode ser True
    # atrás de HTTPS (Render fornece isso em produção); em dev local por
    # http://, deixe False, senão o navegador nunca envia o cookie de volta.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

    # Testes nunca devem depender (nem ser afetados) por segredos reais que
    # existam no .env local do desenvolvedor — e-mail é sempre desativado
    # aqui, os testes que precisam dele configuram explicitamente via
    # app.config.update(...) (ver tests/test_email.py).
    MAIL_HABILITADO = False
