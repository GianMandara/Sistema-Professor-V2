from app.crypto import calcular_hash_busca
from app.extensions import db
from app.models import Aluno, Usuario


def test_email_e_nome_sao_criptografados_no_banco_mas_legiveis_via_orm(app, sessao_bd):
    """O texto puro nunca deve aparecer na coluna de verdade do banco —
    só quando lido através do ORM (que decripta na hora)."""
    usuario = Usuario(nome="Fernanda Lima", email="fernanda@exemplo.com")
    usuario.definir_senha("senha-teste-123")
    sessao_bd.add(usuario)
    sessao_bd.commit()

    # via ORM: sempre o texto puro, de forma transparente
    assert usuario.nome == "Fernanda Lima"
    assert usuario.email == "fernanda@exemplo.com"

    # via SQL cru: o valor gravado de verdade é o texto cifrado
    linha = db.session.execute(
        db.text("SELECT nome, email FROM usuarios WHERE id = :id"), {"id": usuario.id}
    ).first()
    assert linha.nome != "Fernanda Lima"
    assert linha.email != "fernanda@exemplo.com"
    assert linha.nome.startswith("gAAAAA")  # prefixo padrão de um token Fernet


def test_aluno_email_e_telefone_criptografados(app, sessao_bd):
    aluno = Aluno(nome="Pedro Alves", email="pedro@exemplo.com", telefone="11999998888")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    assert aluno.email == "pedro@exemplo.com"
    assert aluno.telefone == "11999998888"

    linha = db.session.execute(
        db.text("SELECT email, telefone FROM alunos WHERE id = :id"), {"id": aluno.id}
    ).first()
    assert linha.email != "pedro@exemplo.com"
    assert linha.telefone != "11999998888"


def test_aluno_nome_fica_em_texto_puro_de_proposito(app, sessao_bd):
    """nome não é criptografado — é usado em ORDER BY (listagem
    alfabética); criptografar quebraria a ordenação."""
    aluno = Aluno(nome="Zeca Ordenacao")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    linha = db.session.execute(
        db.text("SELECT nome FROM alunos WHERE id = :id"), {"id": aluno.id}
    ).first()
    assert linha.nome == "Zeca Ordenacao"


def test_sem_chave_configurada_campo_criptografado_funciona_em_texto_puro(app, sessao_bd):
    """Sem ENCRYPTION_KEY, os campos continuam funcionando normalmente —
    só sem a camada extra de criptografia (mesma filosofia fail-safe do
    resto do projeto)."""
    app.config["ENCRYPTION_KEY"] = ""

    aluno = Aluno(nome="Sem Chave", email="semchave@exemplo.com")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    assert aluno.email == "semchave@exemplo.com"
    linha = db.session.execute(
        db.text("SELECT email FROM alunos WHERE id = :id"), {"id": aluno.id}
    ).first()
    assert linha.email == "semchave@exemplo.com"  # gravado em texto puro mesmo


def test_dado_legado_em_texto_puro_nao_quebra_a_leitura(app, sessao_bd):
    """Um registro gravado antes de existir ENCRYPTION_KEY (ou escrito via
    SQL direto) não pode derrubar a página ao ser lido — o decrypt falha
    silenciosamente e devolve o valor como está."""
    aluno = Aluno(nome="Legado")
    sessao_bd.add(aluno)
    sessao_bd.commit()

    db.session.execute(
        db.text("UPDATE alunos SET email = :email WHERE id = :id"),
        {"email": "legado-em-texto-puro@exemplo.com", "id": aluno.id},
    )
    db.session.commit()
    db.session.expire_all()

    aluno_relido = db.session.get(Aluno, aluno.id)
    assert aluno_relido.email == "legado-em-texto-puro@exemplo.com"


def test_hash_de_busca_e_deterministico_e_sensivel_ao_valor(app):
    chave = app.config["ENCRYPTION_KEY"]
    h1 = calcular_hash_busca("Professor@Exemplo.com", chave)
    h2 = calcular_hash_busca("professor@exemplo.com  ", chave)  # normalização
    h3 = calcular_hash_busca("outro@exemplo.com", chave)

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # hex de sha256


def test_usuario_email_hash_preenchido_automaticamente_ao_atribuir_email(app, sessao_bd):
    usuario = Usuario(nome="Gabriel", email="gabriel@exemplo.com")
    usuario.definir_senha("senha-teste-123")
    sessao_bd.add(usuario)
    sessao_bd.commit()

    esperado = calcular_hash_busca("gabriel@exemplo.com", app.config["ENCRYPTION_KEY"])
    assert usuario.email_hash == esperado


def test_migracao_recriptografa_dados_legados_e_preenche_email_hash(app, sessao_bd):
    from app.migrations import criptografar_dados_legados

    # Simula uma conta criada ANTES de ENCRYPTION_KEY existir: grava tudo
    # em texto puro via SQL direto e sem email_hash.
    db.session.execute(
        db.text(
            "INSERT INTO usuarios (nome, email, senha_hash, email_hash) "
            "VALUES (:nome, :email, 'hash-qualquer', NULL)"
        ),
        {"nome": "Conta Legada", "email": "legado@exemplo.com"},
    )
    db.session.commit()

    with app.app_context():
        criptografar_dados_legados()

    db.session.expire_all()
    usuario = next(u for u in Usuario.query.all() if u.email == "legado@exemplo.com")
    assert usuario.email_hash == calcular_hash_busca("legado@exemplo.com", app.config["ENCRYPTION_KEY"])

    linha = db.session.execute(
        db.text("SELECT email FROM usuarios WHERE id = :id"), {"id": usuario.id}
    ).first()
    assert linha.email.startswith("gAAAAA")  # agora está de fato criptografado
