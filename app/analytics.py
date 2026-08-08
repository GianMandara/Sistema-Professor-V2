"""Análise de dados (opcional) com pandas.

Agrega os registros de aulas para alimentar os gráficos da página
"Acompanhamento": aulas por mês e aulas por conteúdo trabalhado.
"""
import pandas as pd

from .models import Aula


def estatisticas_gerais() -> dict:
    aulas = Aula.query.all()

    if not aulas:
        return {"aulas_por_mes": [], "aulas_por_conteudo": [], "total_aulas": 0}

    df = pd.DataFrame(
        [
            {
                "data": a.data,
                "conteudo": a.conteudo.titulo if a.conteudo else "Sem conteúdo definido",
            }
            for a in aulas
        ]
    )
    df["mes"] = pd.to_datetime(df["data"], errors="coerce").dt.strftime("%Y-%m")

    por_mes = (
        df.dropna(subset=["mes"])
        .groupby("mes")
        .size()
        .reset_index(name="quantidade")
        .sort_values("mes")
    )
    por_conteudo = (
        df.groupby("conteudo").size().reset_index(name="quantidade").sort_values(
            "quantidade", ascending=False
        )
    )

    return {
        "total_aulas": int(len(df)),
        "aulas_por_mes": por_mes.to_dict(orient="records"),
        "aulas_por_conteudo": por_conteudo.to_dict(orient="records"),
    }
