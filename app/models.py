from datetime import datetime

from .extensions import db


class Aluno(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(30))
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
    observacoes = db.Column(db.Text)

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
