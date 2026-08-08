"""Login único do professor.

Sem tabela de usuários no banco — as credenciais vêm de variáveis de
ambiente (LOGIN_USUARIO/LOGIN_SENHA), comparadas em tempo constante para
evitar timing attacks. Um único professor usa este sistema, então uma
tabela `users` completa seria complexidade sem benefício real aqui.
"""
import hmac

from flask import Blueprint, current_app, flash, redirect, request, session, url_for

auth_bp = Blueprint("auth", __name__)


def _credenciais_validas(usuario: str, senha: str) -> bool:
    esperado_usuario = current_app.config["LOGIN_USUARIO"]
    esperado_senha = current_app.config["LOGIN_SENHA"]

    # Fail-closed: sem credenciais configuradas, login nunca é aceito —
    # mesmo que alguém envie usuário/senha em branco.
    if not esperado_usuario or not esperado_senha:
        return False

    usuario_ok = hmac.compare_digest(usuario, esperado_usuario)
    senha_ok = hmac.compare_digest(senha, esperado_senha)
    return usuario_ok and senha_ok


def _destino_seguro(proximo: str | None) -> str:
    """Só permite redirecionar para caminhos internos (evita open redirect
    via ?proximo=https://site-malicioso.com)."""
    if proximo and proximo.startswith("/") and not proximo.startswith("//"):
        return proximo
    return url_for("views.dashboard")


@auth_bp.post("/login")
def login():
    """O formulário de login vive embutido na landing page (não em uma
    página própria) — ver `views.landing`. Esta rota só processa o envio."""
    usuario = request.form.get("usuario", "")
    senha = request.form.get("senha", "")
    proximo = request.form.get("proximo", "")

    if not current_app.config["LOGIN_USUARIO"] or not current_app.config["LOGIN_SENHA"]:
        flash("Login não configurado. Defina LOGIN_USUARIO e LOGIN_SENHA no .env.", "erro")
    elif _credenciais_validas(usuario, senha):
        session.clear()
        session["autenticado"] = True
        return redirect(_destino_seguro(proximo))
    else:
        flash("Usuário ou senha inválidos.", "erro")

    return redirect(url_for("views.landing", login="1", proximo=proximo))


@auth_bp.post("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("views.landing"))
