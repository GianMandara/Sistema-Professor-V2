"""Rotas que renderizam páginas HTML (server-side rendering com Jinja2).

Continuam funcionando sem JavaScript (progressive enhancement) — o JS no
front-end apenas melhora a experiência (validação, feedback, gráficos).
"""
from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import Aluno, Aula, Conteudo
from ..services.email import enviar_lembrete_aula

views_bp = Blueprint("views", __name__)

# Única página deste blueprint que não exige login — o resto (dashboard,
# alunos, agenda, conteúdos, acompanhamento) fica atrás de autenticação.
_ROTAS_PUBLICAS = {"views.landing"}


@views_bp.before_request
def exigir_login():
    if request.endpoint in _ROTAS_PUBLICAS:
        return None
    if not session.get("autenticado"):
        # O login fica embutido na própria landing page (não em uma URL
        # separada) — login=1 faz a seção de login já aparecer visível.
        return redirect(url_for("views.landing", login="1", proximo=request.path))
    return None

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
    """Landing page pública — apresenta o produto e também é onde o login
    acontece (seção embutida, sem navegar para uma URL separada)."""
    total_alunos = Aluno.query.count()
    total_aulas = Aula.query.count()
    return render_template(
        "landing.html",
        total_alunos=total_alunos,
        total_aulas=total_aulas,
        mostrar_login=request.args.get("login") == "1",
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
    return render_template("acompanhamento.html", alunos=alunos)
