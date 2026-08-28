"""Contas de professor: cadastro, login, logout, "esqueci a senha" e
redefinição de senha — como em sites profissionais.

As senhas nunca são guardadas em texto puro (só o hash, via
werkzeug.security). O link de redefinição de senha é um token assinado
com SECRET_KEY (itsdangerous), válido por 1 hora, sem precisar de uma
tabela extra no banco para guardá-lo. Dados pessoais (nome/e-mail) ficam
criptografados em repouso — ver app/crypto.py e app/models.py.
"""
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from ..crypto import calcular_hash_busca
from ..extensions import db
from ..models import Usuario
from ..services.email import (
    enviar_email_boas_vindas,
    enviar_email_novo_acesso,
    enviar_email_redefinicao_senha,
    enviar_email_tentativa_falha,
)

auth_bp = Blueprint("auth", __name__)

SALT_REDEFINICAO_SENHA = "redefinir-senha"
VALIDADE_TOKEN_SEGUNDOS = 3600  # 1 hora


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _buscar_usuario_por_email(email: str) -> Usuario | None:
    """Localiza a conta pelo e-mail. Com ENCRYPTION_KEY configurada, o
    e-mail fica criptografado no banco (não dá para fazer
    "WHERE email = ..." nele) — a busca usa email_hash, um índice
    determinístico (HMAC) calculado a partir do mesmo e-mail. Sem chave
    configurada, o e-mail continua em texto puro e a busca direta funciona
    normalmente."""
    chave = current_app.config.get("ENCRYPTION_KEY")
    if chave:
        return Usuario.query.filter_by(email_hash=calcular_hash_busca(email, chave)).first()
    return Usuario.query.filter_by(email=email).first()


def _destino_seguro(proximo: str | None) -> str:
    """Só permite redirecionar para caminhos internos (evita open redirect
    via ?proximo=https://site-malicioso.com)."""
    if proximo and proximo.startswith("/") and not proximo.startswith("//"):
        return proximo
    return url_for("views.dashboard")


def _agora_formatado() -> str:
    return datetime.now().strftime("%d/%m/%Y às %H:%M")


@auth_bp.post("/login")
def login():
    """O formulário vive embutido na landing page (não em uma página
    própria) — ver `views.landing`. Esta rota só processa o envio."""
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")
    proximo = request.form.get("proximo", "")

    usuario = _buscar_usuario_por_email(email)
    ip = request.remote_addr or "desconhecido"
    quando = _agora_formatado()

    if usuario and usuario.verificar_senha(senha):
        session.clear()
        session["usuario_id"] = usuario.id
        enviar_email_novo_acesso(usuario, ip, quando)
        return redirect(_destino_seguro(proximo))

    # Só avisamos por e-mail quando a conta existe de verdade — para um
    # e-mail que nunca foi cadastrado não há ninguém para notificar (e
    # notificar mesmo assim revelaria quais contas existem).
    if usuario:
        enviar_email_tentativa_falha(usuario, ip, quando)

    flash("E-mail ou senha inválidos.", "erro")
    return redirect(url_for("views.landing", login="1", proximo=proximo))


@auth_bp.post("/cadastro")
def cadastro():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")
    confirmar_senha = request.form.get("confirmar_senha", "")

    erro = None
    if not nome or not email or not senha:
        erro = "Preencha nome, e-mail e senha."
    elif len(senha) < 8:
        erro = "A senha deve ter pelo menos 8 caracteres."
    elif senha != confirmar_senha:
        erro = "As senhas não coincidem."
    elif _buscar_usuario_por_email(email):
        erro = "Já existe uma conta com esse e-mail."

    if erro:
        flash(erro, "erro")
        return redirect(url_for("views.landing", cadastro="1"))

    usuario = Usuario(nome=nome, email=email)
    usuario.definir_senha(senha)
    db.session.add(usuario)
    db.session.commit()

    enviar_email_boas_vindas(usuario)

    session.clear()
    session["usuario_id"] = usuario.id
    flash(f"Conta criada com sucesso. Bem-vindo(a), {nome}!", "sucesso")
    return redirect(url_for("views.dashboard"))


@auth_bp.post("/esqueci-senha")
def esqueci_senha():
    email = request.form.get("email", "").strip().lower()
    usuario = _buscar_usuario_por_email(email)

    if usuario:
        token = _serializer().dumps(usuario.email, salt=SALT_REDEFINICAO_SENHA)
        link = url_for("auth.redefinir_senha", token=token, _external=True)
        enviar_email_redefinicao_senha(usuario, link)

    # Mesma mensagem exista ou não a conta — não revela quais e-mails
    # estão cadastrados.
    flash("Se esse e-mail estiver cadastrado, enviamos um link para redefinir a senha.", "sucesso")
    return redirect(url_for("views.landing", esqueci="1"))


@auth_bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    try:
        email = _serializer().loads(token, salt=SALT_REDEFINICAO_SENHA, max_age=VALIDADE_TOKEN_SEGUNDOS)
    except (BadSignature, SignatureExpired):
        flash("Este link de redefinição é inválido ou expirou. Solicite um novo.", "erro")
        return redirect(url_for("views.landing", esqueci="1"))

    usuario = _buscar_usuario_por_email(email)
    if not usuario:
        flash("Conta não encontrada.", "erro")
        return redirect(url_for("views.landing"))

    if request.method == "POST":
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if len(senha) < 8:
            flash("A senha deve ter pelo menos 8 caracteres.", "erro")
        elif senha != confirmar_senha:
            flash("As senhas não coincidem.", "erro")
        else:
            usuario.definir_senha(senha)
            db.session.commit()
            flash("Senha redefinida com sucesso. Faça login com a nova senha.", "sucesso")
            return redirect(url_for("views.landing", login="1"))

    return render_template("redefinir_senha.html", token=token)


@auth_bp.post("/logout")
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("views.landing"))
