"""Envio de e-mails do sistema: lembrete de aula, boas-vindas ao criar
conta e link de redefinição de senha.

Usa `smtplib` da biblioteca padrão (sem dependência extra). Sem as
variáveis de ambiente MAIL_SERVER/MAIL_USERNAME configuradas, o envio é
apenas pulado — nenhuma ação do usuário deve falhar por causa do e-mail.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app


def _enviar(destinatario: str | None, assunto: str, corpo: str) -> bool:
    """Envia um e-mail simples de texto. Retorna True se enviado, False se
    pulado (sem SMTP configurado / sem destinatário) ou se falhou."""
    config = current_app.config
    if not config.get("MAIL_HABILITADO") or not destinatario:
        return False

    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = config["MAIL_REMETENTE"]
    mensagem["To"] = destinatario
    mensagem.set_content(corpo)

    try:
        with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=10) as servidor:
            if config.get("MAIL_USE_TLS"):
                servidor.starttls()
            servidor.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
            servidor.send_message(mensagem)
        return True
    except (smtplib.SMTPException, OSError) as erro:
        current_app.logger.warning("Falha ao enviar e-mail (%s): %s", assunto, erro)
        return False


def enviar_lembrete_aula(aula) -> bool:
    """Envia o lembrete ao aluno da aula recém-agendada."""
    aluno = aula.aluno
    if not aluno or not aluno.email:
        return False

    conteudo = aula.conteudo.titulo if aula.conteudo else "a definir"
    corpo = (
        f"Olá, {aluno.nome}!\n\n"
        "Sua aula foi agendada com os seguintes detalhes:\n\n"
        f"Data: {aula.data}\n"
        f"Horário: {aula.horario}\n"
        f"Conteúdo: {conteudo}\n"
    )
    if aula.observacoes:
        corpo += f"Observações: {aula.observacoes}\n"
    corpo += "\nNos vemos lá!"

    return _enviar(aluno.email, f"Lembrete: aula agendada para {aula.data} às {aula.horario}", corpo)


def enviar_email_boas_vindas(usuario) -> bool:
    """Confirma a criação da conta para quem se cadastrou."""
    corpo = (
        f"Olá, {usuario.nome}!\n\n"
        f"Sua conta no Sistema de Gestão de Aulas foi criada com sucesso, "
        f"usando o e-mail {usuario.email}.\n\n"
        "Agora você já pode acessar o sistema e organizar seus alunos e aulas.\n\n"
        "Se não foi você quem criou essa conta, ignore este e-mail."
    )
    return _enviar(usuario.email, "Bem-vindo(a) ao Sistema de Gestão de Aulas", corpo)


def enviar_email_redefinicao_senha(usuario, link: str) -> bool:
    """Envia o link (assinado, válido por 1 hora) para redefinir a senha."""
    corpo = (
        f"Olá, {usuario.nome}!\n\n"
        "Recebemos um pedido para redefinir a senha da sua conta.\n"
        f"Clique no link abaixo para escolher uma nova senha (válido por 1 hora):\n\n"
        f"{link}\n\n"
        "Se não foi você quem pediu isso, ignore este e-mail — sua senha continua a mesma."
    )
    return _enviar(usuario.email, "Redefinição de senha — Sistema de Gestão de Aulas", corpo)
