"""Migração leve, sem Alembic.

O projeto usa `db.create_all()`, que só cria tabelas que ainda não existem
— não altera tabelas já existentes. Quando um campo novo é adicionado a um
modelo (como `compareceu`/`nota` em Aula), bancos criados antes dessa
mudança ficam desatualizados. Esta função corrige isso adicionando as
colunas que faltarem, de forma idempotente (roda a cada início da app sem
causar erro se a coluna já existir).
"""
from flask import current_app
from sqlalchemy import inspect, text
from sqlalchemy.orm.attributes import flag_modified

from .extensions import db

# Cada entrada: (tabela, coluna, definição SQL usada apenas se a coluna faltar)
COLUNAS_ESPERADAS = [
    ("aulas", "compareceu", "BOOLEAN"),
    ("aulas", "nota", "FLOAT"),
    ("usuarios", "email_hash", "VARCHAR(64)"),
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


def garantir_indice_unico_email_hash():
    """Cria o índice único de usuarios.email_hash se ainda não existir.

    Em instalações novas, `db.create_all()` já cria isso a partir do
    `unique=True` do modelo — esta função só cobre quem tinha a tabela
    `usuarios` de antes dessa coluna existir."""
    inspetor = inspect(db.engine)
    if "usuarios" not in inspetor.get_table_names():
        return

    ja_existe = any(
        "email_hash" in idx.get("column_names", []) for idx in inspetor.get_indexes("usuarios")
    ) or any(
        "email_hash" in uq.get("column_names", [])
        for uq in inspetor.get_unique_constraints("usuarios")
    )
    if ja_existe:
        return

    with db.engine.begin() as conexao:
        conexao.execute(
            text("CREATE UNIQUE INDEX ix_usuarios_email_hash_unico ON usuarios (email_hash)")
        )


def criptografar_dados_legados():
    """Recriptografa registros gravados antes de ENCRYPTION_KEY existir
    (ou antes de um campo específico virar CampoCriptografado).

    Idempotente e "single-shot": só existe trabalho a fazer enquanto
    houver alguma conta sem email_hash; depois da primeira migração
    completa, todas as contas novas já nascem com ele preenchido (ver
    Usuario._atualizar_indice_de_busca em app/models.py), então esta
    função vira um no-op nas próximas inicializações — sem ficar
    reescrevendo o banco toda hora à toa.
    """
    chave = current_app.config.get("ENCRYPTION_KEY")
    if not chave:
        return

    from .models import Aluno, Aula, Usuario  # import tardio: evita ciclo de import

    pendente = Usuario.query.filter(
        (Usuario.email_hash.is_(None)) | (Usuario.email_hash == "")
    ).first()
    if pendente is None:
        return  # já migrado

    for usuario in Usuario.query.all():
        flag_modified(usuario, "nome")
        flag_modified(usuario, "email")
        usuario.email = usuario.email  # dispara @validates -> recalcula email_hash

    for aluno in Aluno.query.all():
        flag_modified(aluno, "email")
        flag_modified(aluno, "telefone")

    for aula in Aula.query.all():
        flag_modified(aula, "observacoes")

    db.session.commit()
