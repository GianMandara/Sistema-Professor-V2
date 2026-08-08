"""Integração com a BrasilAPI (https://brasilapi.com.br) para consultar
feriados nacionais.

Uso de API externa: antes de confirmar o agendamento de uma aula, o
front-end pergunta a este serviço se a data cai em um feriado nacional,
evitando que o professor marque aulas em dias sem expediente.
"""
from __future__ import annotations

from datetime import datetime
from functools import lru_cache

import requests
from flask import current_app


@lru_cache(maxsize=8)
def _feriados_do_ano(ano: int) -> list[dict]:
    """Busca (e cacheia em memória) a lista de feriados nacionais de um ano."""
    base_url = current_app.config["FERIADOS_API_URL"]
    resposta = requests.get(f"{base_url}/{ano}", timeout=5)
    resposta.raise_for_status()
    return resposta.json()


def eh_feriado(data_str: str) -> dict | None:
    """Retorna {'feriado': bool, 'nome': str|None} ou None se a API falhar.

    `data_str` deve estar no formato YYYY-MM-DD.
    """
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        feriados = _feriados_do_ano(data.year)
    except (ValueError, requests.RequestException):
        return None

    for feriado in feriados:
        if feriado.get("date") == data_str:
            return {"feriado": True, "nome": feriado.get("name")}
    return {"feriado": False, "nome": None}
