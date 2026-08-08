"""Migração leve, sem Alembic.

O projeto usa `db.create_all()`, que só cria tabelas que ainda não existem
— não altera tabelas já existentes. Quando um campo novo é adicionado a um
modelo (como `compareceu`/`nota` em Aula), bancos criados antes dessa
mudança ficam desatualizados. Esta função corrige isso adicionando as
colunas que faltarem, de forma idempotente (roda a cada início da app sem
causar erro se a coluna já existir).
"""
from sqlalchemy import inspect, text

from .extensions import db

# Cada entrada: (tabela, coluna, definição SQL usada apenas se a coluna faltar)
COLUNAS_ESPERADAS = [
    ("aulas", "compareceu", "BOOLEAN"),
    ("aulas", "nota", "FLOAT"),
]


def aplicar_migracoes_leves():
    inspetor = inspect(db.engine)
    tabelas_existentes = set(inspetor.get_table_names())

    with db.engine.begin() as conexao:
        for tabela, coluna, tipo_sql in COLUNAS_ESPERADAS:
            if tabela not in tabelas_existentes:
                continue
            colunas_atuais = {c["name"] for c in inspetor.get_columns(tabela)}
            if coluna not in colunas_atuais:
                conexao.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo_sql}"))
