"""API REST em JSON.

Consumida pelo JavaScript do front-end (fetch) — protegida pela mesma
sessão de login do resto do sistema, já que expõe dados de alunos.
"""
from flask import Blueprint, jsonify, request, session

from ..analytics import estatisticas_gerais
from ..extensions import db
from ..models import Aluno, Aula, Conteudo
from ..services.feriados import eh_feriado

api_bp = Blueprint("api", __name__)


@api_bp.before_request
def exigir_login_api():
    if not session.get("usuario_id"):
        return jsonify({"erro": "Não autenticado."}), 401
    return None


# ---------------------------------------------------------------- alunos --
@api_bp.get("/alunos")
def listar_alunos():
    alunos = Aluno.query.order_by(Aluno.nome.asc()).all()
    return jsonify([a.to_dict() for a in alunos])


@api_bp.post("/alunos")
def criar_aluno():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório."}), 400

    aluno = Aluno(nome=nome, email=dados.get("email"), telefone=dados.get("telefone"))
    db.session.add(aluno)
    db.session.commit()
    return jsonify(aluno.to_dict()), 201


@api_bp.delete("/alunos/<int:aluno_id>")
def deletar_aluno(aluno_id):
    aluno = Aluno.query.get_or_404(aluno_id)
    db.session.delete(aluno)
    db.session.commit()
    return jsonify({"removido": aluno_id})


@api_bp.get("/alunos/<int:aluno_id>/aulas")
def historico_do_aluno(aluno_id):
    """Histórico de aulas de um aluno: usado pela página de Acompanhamento
    para mostrar presença e notas ao longo do tempo."""
    Aluno.query.get_or_404(aluno_id)
    aulas = (
        Aula.query.filter_by(aluno_id=aluno_id)
        .order_by(Aula.data.desc(), Aula.horario.desc())
        .all()
    )
    return jsonify([a.to_dict() for a in aulas])


# -------------------------------------------------------------- conteudos--
@api_bp.get("/conteudos")
def listar_conteudos():
    conteudos = Conteudo.query.order_by(Conteudo.titulo.asc()).all()
    return jsonify([c.to_dict() for c in conteudos])


@api_bp.post("/conteudos")
def criar_conteudo():
    dados = request.get_json(silent=True) or {}
    titulo = (dados.get("titulo") or "").strip()
    if not titulo:
        return jsonify({"erro": "O campo 'titulo' é obrigatório."}), 400

    conteudo = Conteudo(titulo=titulo, descricao=dados.get("descricao"))
    db.session.add(conteudo)
    db.session.commit()
    return jsonify(conteudo.to_dict()), 201


@api_bp.delete("/conteudos/<int:conteudo_id>")
def deletar_conteudo(conteudo_id):
    conteudo = Conteudo.query.get_or_404(conteudo_id)
    db.session.delete(conteudo)
    db.session.commit()
    return jsonify({"removido": conteudo_id})


# ------------------------------------------------------------------ aulas--
@api_bp.get("/aulas")
def listar_aulas():
    aulas = Aula.query.order_by(Aula.data.asc(), Aula.horario.asc()).all()
    return jsonify([a.to_dict() for a in aulas])


@api_bp.delete("/aulas/<int:aula_id>")
def deletar_aula(aula_id):
    aula = Aula.query.get_or_404(aula_id)
    db.session.delete(aula)
    db.session.commit()
    return jsonify({"removido": aula_id})


# ------------------------------------------------------- feriados (API externa) --
@api_bp.get("/feriados/<data>")
def verificar_feriado(data):
    """Consulta a BrasilAPI para avisar o professor se a data escolhida é feriado.

    `data` no formato YYYY-MM-DD. Usado pelo agenda.js antes de confirmar o
    agendamento de uma aula.
    """
    info = eh_feriado(data)
    if info is None:
        return jsonify({"data": data, "disponivel": False, "erro": "não foi possível consultar a API de feriados"}), 502
    return jsonify({"data": data, **info})


# --------------------------------------------------------- estatísticas ---
@api_bp.get("/estatisticas")
def estatisticas():
    """Dados agregados (pandas) para os gráficos da página de acompanhamento."""
    return jsonify(estatisticas_gerais())
