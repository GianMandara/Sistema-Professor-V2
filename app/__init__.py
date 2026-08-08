from pathlib import Path

from flask import Flask

from .config import Config, TestingConfig
from .extensions import csrf, db


def create_app(testing: bool = False) -> Flask:
    """Application factory. Facilita testes e configuração para nuvem."""
    app = Flask(__name__)
    app.config.from_object(TestingConfig if testing else Config)

    # garante que a pasta instance/ exista para o SQLite local
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"):
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from .routes.auth import auth_bp
    from .routes.views import views_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/health")
    def health():
        """Endpoint de health-check usado por provedores de nuvem (Render/Railway)."""
        return {"status": "ok"}, 200

    with app.app_context():
        from . import models  # noqa: F401  (garante que os modelos sejam registrados)
        from .migrations import aplicar_migracoes_leves
        from .seeds import seed_conteudos_padrao

        db.create_all()
        aplicar_migracoes_leves()
        seed_conteudos_padrao()

    return app
