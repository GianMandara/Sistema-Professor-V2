from datetime import datetime

from flask import current_app
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from .crypto import CampoCriptografado, calcular_hash_busca
from .extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    # nome e email ficam criptografados em repouso (CampoCriptografado) —
    # são dados pessoais do professor. email_hash é o índice de busca
    # (HMAC determinístico) usado para localizar a conta no login, já que
    # não dá para fazer "WHERE email = ..." direto num valor criptografado.
    nome = db.Column(CampoCriptografado(), nullable=False)
    email = db.Column(CampoCriptografado(), nullable=False)
    email_hash = db.Column(db.String(64), unique=True, index=True, nullable=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    @validates("email")
    def _atualizar_indice_de_busca(self, _nome_do_campo, valor):
        """Mantém email_hash sempre em sincronia com email, para todo
        código que atribuir usuario.email = ... — cadastro, migração de
        dados legados, ou qualquer uso futuro — sem precisar lembrar de
        atualizar os dois campos manualmente em cada lugar."""
        chave = current_app.config.get("ENCRYPTION_KEY") if current_app else None
        if chave and valor:
            self.email_hash = calcular_hash_busca(valor, chave)
        return valor

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "email": self.email}


class Aluno(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.Integer, primary_key=True)
    # nome fica em texto puro de propósito: é usado em ORDER BY (listagem
    # em ordem alfabética) — criptografá-lo quebraria essa ordenação, já
    # que a ordenação passaria a ser pelo texto cifrado, não pelo nome.
    nome = db.Column(db.String(120), nullable=False)
    # email e telefone são dados de contato — nunca usados em filtro/busca
    # neste sistema — então podem ficar criptografados sem custo nenhum.
    email = db.Column(CampoCriptografado())
    telefone = db.Column(CampoCriptografado())
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    aulas = db.relationship("Aula", backref="aluno", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
        }


class Conteudo(db.Model):
    __tablename__ = "conteudos"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)

    aulas = db.relationship("Aula", backref="conteudo")

    def to_dict(self):
        return {"id": self.id, "titulo": self.titulo, "descricao": self.descricao}


class Aula(db.Model):
    __tablename__ = "aulas"

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey("alunos.id"), nullable=False)
    conteudo_id = db.Column(db.Integer, db.ForeignKey("conteudos.id"))
    data = db.Column(db.String(10), nullable=False)  # formato YYYY-MM-DD
    horario = db.Column(db.String(5), nullable=False)  # formato HH:MM
    # observações podem conter informações sensíveis sobre o aluno —
    # criptografadas em repouso pelo mesmo motivo que email/telefone.
    observacoes = db.Column(CampoCriptografado())

    # Preenchidos depois que a aula acontece, na tela de edição.
    # None = ainda não avaliada; True = presente; False = faltou.
    compareceu = db.Column(db.Boolean, nullable=True)
    nota = db.Column(db.Float, nullable=True)  # 0 a 10

    def to_dict(self):
        return {
            "id": self.id,
            "aluno_id": self.aluno_id,
            "aluno_nome": self.aluno.nome if self.aluno else None,
            "conteudo_id": self.conteudo_id,
            "conteudo_titulo": self.conteudo.titulo if self.conteudo else None,
            "data": self.data,
            "horario": self.horario,
            "observacoes": self.observacoes,
            "compareceu": self.compareceu,
            "nota": self.nota,
        }
