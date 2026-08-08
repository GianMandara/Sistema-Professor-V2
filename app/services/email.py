"""Envio de e-mail de lembrete ao agendar uma aula.

Usa `smtplib` da biblioteca padrão (sem dependência extra). Sem as
variáveis de ambiente MAIL_SERVER/MAIL_USERNAME configuradas, o envio é
apenas pulado — agendar uma aula nunca deve falhar por causa do e-mail.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app


def enviar_lembrete_aula(aula) -> bool:
    """Envia o lembrete ao aluno da aula recém-agendada.

    Retorna True se o e-mail foi enviado, False se foi pulado (sem SMTP
    configurado ou sem e-mail cadastrado) ou se o envio falhou.
    """
    config = current_app.config
    if not config.get("MAIL_HABILITADO"):
        return False

    aluno = aula.aluno
    if not aluno or not aluno.email:
        return False

    conteudo = aula.conteudo.titulo if aula.conteudo else "a definir"

    mensagem = EmailMessage()
    mensagem["Subject"] = f"Lembrete: aula agendada para {aula.data} às {aula.horario}"
    mensagem["From"] = config["MAIL_REMETENTE"]
    mensagem["To"] = aluno.email

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
    mensagem.set_content(corpo)

    try:
        with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=10) as servidor:
            if config.get("MAIL_USE_TLS"):
                servidor.starttls()
            servidor.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
            servidor.send_message(mensagem)
        return True
    except (smtplib.SMTPException, OSError) as erro:
        current_app.logger.warning("Falha ao enviar e-mail de lembrete: %s", erro)
        return False
