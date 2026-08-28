"""Rotas que renderizam páginas HTML (server-side rendering com Jinja2).

Continuam funcionando sem JavaScript (progressive enhancement) — o JS no
front-end apenas melhora a experiência (validação, feedback, gráficos).
"""
from datetime import date, datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from ..extensions import db
from ..models import Aluno, Aula, Conteudo, Usuario
from ..relatorios import montar_boletim, nome_do_mes
from ..services.email import enviar_email_boletim, enviar_lembrete_aula

views_bp = Blueprint("views", __name__)

# Só a landing e o boletim (aberto pelo aluno via link, sem conta) não
# exigem login. O resto (dashboard, alunos, agenda, conteúdos,
# acompanhamento, gerar boletim) fica atrás de autenticação.
_ROTAS_PUBLICAS = {"views.landing", "views.boletim"}

SALT_BOLETIM = "boletim-mensal"
VALIDADE_BOLETIM_SEGUNDOS = 60 * 60 * 24 * 90  # 90 dias — bem mais longo
# que o token de redefinir senha (1h), já que o boletim precisa continuar
# acessível por um bom tempo depois de enviado.


def _serializer_boletim() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


@views_bp.before_request
def exigir_login():
    if request.endpoint in _ROTAS_PUBLICAS:
        return None
    if not session.get("usuario_id"):
        # O login fica embutido na própria landing page (não em uma URL
        # separada) — login=1 faz a seção de login já aparecer visível.
        return redirect(url_for("views.landing", login="1", proximo=request.path))
    return None


@views_bp.context_processor
def injetar_usuario_atual():
    usuario_id = session.get("usuario_id")
    return {"usuario_atual": db.session.get(Usuario, usuario_id) if usuario_id else None}

DIAS_SEMANA = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]
MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def _data_por_extenso(d: date) -> str:
    dia_semana = DIAS_SEMANA[d.weekday()].capitalize()
    return f"{dia_semana}, {d.day} de {MESES[d.month - 1]} de {d.year}"


def _saudacao(hora: int) -> str:
    if hora < 12:
        return "Bom dia"
    if hora < 18:
        return "Boa tarde"
    return "Boa noite"


@views_bp.get("/")
def landing():
    """Landing page pública — apresenta o produto e também é onde o
    professor entra, cria conta ou pede redefinição de senha (tudo
    embutido em um modal, sem navegar para uma URL separada)."""
    total_alunos = Aluno.query.count()
    total_aulas = Aula.query.count()

    if request.args.get("cadastro") == "1":
        painel_ativo = "cadastro"
    elif request.args.get("esqueci") == "1":
        painel_ativo = "esqueci"
    elif request.args.get("login") == "1":
        painel_ativo = "entrar"
    else:
        painel_ativo = None

    return render_template(
        "landing.html",
        total_alunos=total_alunos,
        total_aulas=total_aulas,
        painel_ativo=painel_ativo,
        proximo=request.args.get("proximo", ""),
    )


@views_bp.get("/dashboard")
def dashboard():
    agora = datetime.now()
    hoje = agora.date()

    total_alunos = Aluno.query.count()
    total_aulas = Aula.query.count()
    total_conteudos = Conteudo.query.count()
    proximas_aulas = (
        Aula.query.order_by(Aula.data.asc(), Aula.horario.asc()).limit(5).all()
    )
    return render_template(
        "dashboard.html",
        total_alunos=total_alunos,
        total_aulas=total_aulas,
        total_conteudos=total_conteudos,
        proximas_aulas=proximas_aulas,
        saudacao=_saudacao(agora.hour),
        data_extenso=_data_por_extenso(hoje),
        hoje_iso=hoje.isoformat(),
    )


@views_bp.route("/alunos", methods=["GET", "POST"])
def alunos():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        if not nome:
            flash("O nome do aluno é obrigatório.", "erro")
        else:
            aluno = Aluno(
                nome=nome,
                email=request.form.get("email", "").strip(),
                telefone=request.form.get("telefone", "").strip(),
            )
            db.session.add(aluno)
            db.session.commit()
            flash(f"Aluno {nome} cadastrado com sucesso.", "sucesso")
        return redirect(url_for("views.alunos"))

    lista = Aluno.query.order_by(Aluno.nome.asc()).all()
    return render_template("alunos.html", alunos=lista)


@views_bp.route("/alunos/<int:aluno_id>/editar", methods=["GET", "POST"])
def editar_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    if request.method == "POST":
        aluno.nome = request.form.get("nome", "").strip()
        aluno.email = request.form.get("email", "").strip()
        aluno.telefone = request.form.get("telefone", "").strip()
        db.session.commit()
        flash("Dados do aluno atualizados.", "sucesso")
        return redirect(url_for("views.alunos"))
    return render_template("editar_aluno.html", aluno=aluno)


@views_bp.post("/alunos/<int:aluno_id>/excluir")
def excluir_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    db.session.delete(aluno)
    db.session.commit()
    flash("Aluno removido.", "sucesso")
    return redirect(url_for("views.alunos"))


@views_bp.route("/conteudos", methods=["GET", "POST"])
def conteudos():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        if not titulo:
            flash("O título do conteúdo é obrigatório.", "erro")
        else:
            conteudo = Conteudo(titulo=titulo, descricao=request.form.get("descricao", "").strip())
            db.session.add(conteudo)
            db.session.commit()
            flash(f"Conteúdo {titulo} cadastrado com sucesso.", "sucesso")
        return redirect(url_for("views.conteudos"))

    lista = Conteudo.query.order_by(Conteudo.titulo.asc()).all()
    return render_template("conteudos.html", conteudos=lista)


@views_bp.post("/conteudos/<int:conteudo_id>/excluir")
def excluir_conteudo(conteudo_id):
    conteudo = Conteudo.query.get_or_404(conteudo_id)
    db.session.delete(conteudo)
    db.session.commit()
    flash("Conteúdo removido.", "sucesso")
    return redirect(url_for("views.conteudos"))


@views_bp.route("/agenda", methods=["GET", "POST"])
def agenda():
    if request.method == "POST":
        aluno_id = request.form.get("aluno_id")
        data = request.form.get("data", "").strip()
        horario = request.form.get("horario", "").strip()
        if not aluno_id or not data or not horario:
            flash("Aluno, data e horário são obrigatórios.", "erro")
        else:
            aula = Aula(
                aluno_id=aluno_id,
                conteudo_id=request.form.get("conteudo_id") or None,
                data=data,
                horario=horario,
                observacoes=request.form.get("observacoes", "").strip(),
            )
            db.session.add(aula)
            db.session.commit()

            if not aula.aluno.email:
                flash(
                    "Aula agendada com sucesso. Cadastre o e-mail do aluno para enviar lembretes automáticos.",
                    "sucesso",
                )
            elif enviar_lembrete_aula(aula):
                flash("Aula agendada com sucesso. Lembrete enviado por e-mail ao aluno.", "sucesso")
            else:
                flash(
                    "Aula agendada com sucesso, mas não foi possível enviar o lembrete por e-mail.",
                    "sucesso",
                )
        return redirect(url_for("views.agenda"))

    aulas = Aula.query.order_by(Aula.data.asc(), Aula.horario.asc()).all()
    alunos = Aluno.query.order_by(Aluno.nome.asc()).all()
    conteudos = Conteudo.query.order_by(Conteudo.titulo.asc()).all()
    return render_template("agenda.html", aulas=aulas, alunos=alunos, conteudos=conteudos)


@views_bp.route("/agenda/<int:aula_id>/editar", methods=["GET", "POST"])
def editar_aula(aula_id):
    aula = Aula.query.get_or_404(aula_id)
    if request.method == "POST":
        aula.aluno_id = request.form.get("aluno_id")
        aula.conteudo_id = request.form.get("conteudo_id") or None
        aula.data = request.form.get("data", "").strip()
        aula.horario = request.form.get("horario", "").strip()
        aula.observacoes = request.form.get("observacoes", "").strip()

        compareceu_raw = request.form.get("compareceu", "")
        aula.compareceu = {"sim": True, "nao": False}.get(compareceu_raw)

        nota_raw = request.form.get("nota", "").strip()
        if not nota_raw:
            aula.nota = None
        else:
            try:
                nota = float(nota_raw.replace(",", "."))
                if not 0 <= nota <= 10:
                    raise ValueError
                aula.nota = nota
            except ValueError:
                flash("A nota deve ser um número entre 0 e 10.", "erro")
                alunos = Aluno.query.order_by(Aluno.nome.asc()).all()
                conteudos = Conteudo.query.order_by(Conteudo.titulo.asc()).all()
                return render_template("editar_aula.html", aula=aula, alunos=alunos, conteudos=conteudos)

        db.session.commit()
        flash("Aula atualizada.", "sucesso")
        return redirect(url_for("views.agenda"))

    alunos = Aluno.query.order_by(Aluno.nome.asc()).all()
    conteudos = Conteudo.query.order_by(Conteudo.titulo.asc()).all()
    return render_template("editar_aula.html", aula=aula, alunos=alunos, conteudos=conteudos)


@views_bp.post("/agenda/<int:aula_id>/excluir")
def excluir_aula(aula_id):
    aula = Aula.query.get_or_404(aula_id)
    db.session.delete(aula)
    db.session.commit()
    flash("Aula removida.", "sucesso")
    return redirect(url_for("views.agenda"))


@views_bp.get("/acompanhamento")
def acompanhamento():
    """Página de análise de dados: números vêm via fetch em /api/estatisticas
    e /api/alunos/<id>/aulas."""
    alunos = Aluno.query.order_by(Aluno.nome.asc()).all()

    # Sugere por padrão o último mês já fechado (o mês anterior ao atual)
    # para o formulário de boletim — o professor pode trocar livremente.
    hoje = date.today()
    mes_fechado = hoje.month - 1 or 12
    ano_fechado = hoje.year if hoje.month > 1 else hoje.year - 1

    return render_template(
        "acompanhamento.html",
        alunos=alunos,
        mes_padrao=mes_fechado,
        ano_padrao=ano_fechado,
    )


@views_bp.post("/acompanhamento/gerar-boletim")
def gerar_boletim():
    """Gera o link do boletim mensal, envia por e-mail ao aluno e leva o
    professor direto para a mesma página que o aluno vai ver."""
    aluno = Aluno.query.get_or_404(request.form.get("aluno_id"))
    mes_ano = request.form.get("mes_ano", "")  # formato do <input type="month">: AAAA-MM

    try:
        ano_str, mes_str = mes_ano.split("-")
        ano, mes = int(ano_str), int(mes_str)
        if not 1 <= mes <= 12:
            raise ValueError
    except ValueError:
        flash("Selecione um mês válido para gerar o boletim.", "erro")
        return redirect(url_for("views.acompanhamento"))

    if not aluno.email:
        flash(
            f"{aluno.nome} não tem e-mail cadastrado — cadastre um e-mail para enviar o boletim.",
            "erro",
        )
        return redirect(url_for("views.acompanhamento"))

    token = _serializer_boletim().dumps(
        {"aluno_id": aluno.id, "mes": mes, "ano": ano}, salt=SALT_BOLETIM
    )
    link = url_for("views.boletim", token=token, _external=True)

    if enviar_email_boletim(aluno, nome_do_mes(mes), ano, link):
        flash(f"Boletim de {nome_do_mes(mes)}/{ano} enviado para {aluno.nome}.", "sucesso")
    else:
        flash(
            "Boletim gerado, mas não foi possível enviar por e-mail "
            "(verifique a configuração de e-mail). Veja abaixo como ficou.",
            "erro",
        )

    # O professor vê exatamente a mesma página que o aluno recebeu por e-mail.
    return redirect(url_for("views.boletim", token=token))


@views_bp.get("/boletim/<token>")
def boletim(token):
    """Página pública do boletim mensal — aberta pelo aluno através do
    link assinado enviado por e-mail, sem precisar de conta/login."""
    try:
        dados_token = _serializer_boletim().loads(
            token, salt=SALT_BOLETIM, max_age=VALIDADE_BOLETIM_SEGUNDOS
        )
    except (BadSignature, SignatureExpired):
        abort(404)

    aluno = db.session.get(Aluno, dados_token.get("aluno_id"))
    if not aluno:
        abort(404)

    dados = montar_boletim(aluno, dados_token["mes"], dados_token["ano"])
    return render_template("boletim.html", **dados)
