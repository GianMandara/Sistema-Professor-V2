"""Criptografia de dados pessoais em repouso.

Usa Fernet (AES-128-CBC + HMAC autenticado) da biblioteca `cryptography`
— um dos padrões mais usados para criptografia simétrica em aplicações
Python. A chave (ENCRYPTION_KEY) vem só de variável de ambiente, nunca do
código-fonte nem do banco.

Sem ENCRYPTION_KEY configurada, os campos continuam funcionando
normalmente, só sem a camada extra de criptografia — mesma filosofia
"fail-safe" do resto do projeto (como MAIL_HABILITADO): a ausência de uma
configuração opcional nunca derruba a aplicação.

⚠️ Se a chave for perdida, os dados já criptografados ficam
irrecuperáveis — não existe "esqueci a chave" para criptografia de
verdade. Guarde uma cópia segura fora do .env (gerenciador de senhas,
por exemplo).
"""
from __future__ import annotations

import hashlib
import hmac

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
from sqlalchemy import types


def _fernet() -> Fernet | None:
    chave = current_app.config.get("ENCRYPTION_KEY")
    if not chave:
        return None
    return Fernet(chave.encode() if isinstance(chave, str) else chave)


class CampoCriptografado(types.TypeDecorator):
    """Coluna de texto criptografada em repouso, transparente para o
    resto da aplicação: o código Python sempre lê/escreve o valor em
    texto puro — a criptografia acontece só na fronteira com o banco."""

    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if not value:
            return value
        f = _fernet()
        if f is None:
            return value  # sem chave configurada: grava em texto puro
        return f.encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        if not value:
            return value
        f = _fernet()
        if f is None:
            return value
        try:
            return f.decrypt(value.encode()).decode()
        except (InvalidToken, ValueError):
            # Dado gravado antes de ENCRYPTION_KEY existir (ou com uma
            # chave diferente) — devolve como está em vez de quebrar a
            # página. app/migrations.py cuida de recriptografar esses
            # registros legados na próxima inicialização.
            return value


def _chave_derivada_para_indice(chave_mestra: str) -> bytes:
    """Deriva uma chave separada da chave de criptografia principal, só
    para o índice de busca por e-mail (HMAC) — nunca reaproveita a mesma
    chave para dois usos criptográficos diferentes."""
    chave_bytes = chave_mestra.encode() if isinstance(chave_mestra, str) else chave_mestra
    return hashlib.sha256(chave_bytes + b":indice-busca-email").digest()


def calcular_hash_busca(valor: str, chave_mestra: str) -> str:
    """HMAC-SHA256 determinístico do valor normalizado — permite localizar
    um registro pelo e-mail (ex.: login) sem guardar o e-mail em texto
    puro numa coluna indexada. Determinístico só aqui, de propósito: é o
    único jeito de buscar por igualdade num valor criptografado sem
    decriptar a tabela inteira a cada consulta."""
    valor_normalizado = (valor or "").strip().lower()
    chave_indice = _chave_derivada_para_indice(chave_mestra)
    return hmac.new(chave_indice, valor_normalizado.encode(), hashlib.sha256).hexdigest()
