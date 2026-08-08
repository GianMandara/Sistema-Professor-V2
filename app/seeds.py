"""Dados iniciais (seed) para o banco começar utilizável.

Sem isso, o select de "Conteúdo" na Agenda ficaria vazio até o professor
cadastrar algo manualmente em /conteudos.
"""
from .extensions import db
from .models import Conteudo

CONTEUDOS_PADRAO = [
    "Português",
    "Matemática",
    "Inglês",
    "Redação",
    "História",
    "Geografia",
    "Ciências",
    "Física",
    "Química",
    "Biologia",
    "Programação",
    "Conversação",
]


def seed_conteudos_padrao():
    """Insere as matérias comuns apenas se a tabela ainda estiver vazia."""
    if Conteudo.query.count() > 0:
        return

    db.session.add_all([Conteudo(titulo=titulo) for titulo in CONTEUDOS_PADRAO])
    db.session.commit()
