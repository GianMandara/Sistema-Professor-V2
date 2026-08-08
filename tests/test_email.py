import app.services.email as email_service
from app.models import Aluno, Aula


class SMTPFalso:
    """Substitui smtplib.SMTP nos testes — nunca abre conexão de rede real."""

    mensagens_enviadas = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        pass

    def login(self, usuario, senha):
        pass

    def send_message(self, mensagem):
        SMTPFalso.mensagens_enviadas.append(mensagem)


class SMTPQueFalha(SMTPFalso):
    def send_message(self, mensagem):
        raise email_service.smtplib.SMTPException("recusado pelo servidor")


def _configurar_smtp(app):
    app.config.update(
        MAIL_HABILITADO=True,
        MAIL_SERVER="smtp.exemplo.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME="professor@exemplo.com",
        MAIL_PASSWORD="senha",
        MAIL_REMETENTE="professor@exemplo.com",
    )


def test_sem_smtp_configurado_nao_envia(app, sessao_bd):
    aluno = Aluno(nome="Igor", email="igor@exemplo.com")
    sessao_bd.add(aluno)
    sessao_bd.commit()
    aula = Aula(aluno_id=aluno.id, data="2026-08-20", horario="10:00")
    sessao_bd.add(aula)
    sessao_bd.commit()

    with app.app_context():
        assert email_service.enviar_lembrete_aula(aula) is False


def test_aluno_sem_email_nao_envia(app, sessao_bd):
    _configurar_smtp(app)
    aluno = Aluno(nome="Julia")
    sessao_bd.add(aluno)
    sessao_bd.commit()
    aula = Aula(aluno_id=aluno.id, data="2026-08-21", horario="11:00")
    sessao_bd.add(aula)
    sessao_bd.commit()

    with app.app_context():
        assert email_service.enviar_lembrete_aula(aula) is False


def test_envia_lembrete_com_smtp_configurado(app, sessao_bd, monkeypatch):
    _configurar_smtp(app)
    SMTPFalso.mensagens_enviadas = []
    monkeypatch.setattr(email_service.smtplib, "SMTP", SMTPFalso)

    aluno = Aluno(nome="Karina", email="karina@exemplo.com")
    sessao_bd.add(aluno)
    sessao_bd.commit()
    aula = Aula(aluno_id=aluno.id, data="2026-08-22", horario="16:00")
    sessao_bd.add(aula)
    sessao_bd.commit()

    with app.app_context():
        assert email_service.enviar_lembrete_aula(aula) is True

    assert len(SMTPFalso.mensagens_enviadas) == 1
    enviada = SMTPFalso.mensagens_enviadas[0]
    assert enviada["To"] == "karina@exemplo.com"
    assert "2026-08-22" in enviada["Subject"]


def test_falha_no_envio_retorna_false_sem_lancar_excecao(app, sessao_bd, monkeypatch):
    _configurar_smtp(app)
    monkeypatch.setattr(email_service.smtplib, "SMTP", SMTPQueFalha)

    aluno = Aluno(nome="Leandro", email="leandro@exemplo.com")
    sessao_bd.add(aluno)
    sessao_bd.commit()
    aula = Aula(aluno_id=aluno.id, data="2026-08-23", horario="09:00")
    sessao_bd.add(aula)
    sessao_bd.commit()

    with app.app_context():
        assert email_service.enviar_lembrete_aula(aula) is False
