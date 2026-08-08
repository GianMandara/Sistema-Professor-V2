import app.services.feriados as feriados_service


def test_criar_e_listar_aluno_via_api(client):
    resposta = client.post("/api/alunos", json={"nome": "Carla Nunes", "email": "carla@exemplo.com"})
    assert resposta.status_code == 201
    assert resposta.get_json()["nome"] == "Carla Nunes"

    resposta = client.get("/api/alunos")
    nomes = [a["nome"] for a in resposta.get_json()]
    assert "Carla Nunes" in nomes


def test_criar_aluno_sem_nome_retorna_400(client):
    resposta = client.post("/api/alunos", json={"email": "sem-nome@exemplo.com"})
    assert resposta.status_code == 400


def test_deletar_aluno_via_api(client):
    criado = client.post("/api/alunos", json={"nome": "Temporário"}).get_json()
    resposta = client.delete(f"/api/alunos/{criado['id']}")
    assert resposta.status_code == 200

    restantes = [a["id"] for a in client.get("/api/alunos").get_json()]
    assert criado["id"] not in restantes


def test_conteudos_vem_pre_cadastrados_via_seed(client):
    titulos = [c["titulo"] for c in client.get("/api/conteudos").get_json()]
    assert "Português" in titulos
    assert "Matemática" in titulos
    assert len(titulos) >= 10


def test_deletar_conteudo_via_api(client):
    criado = client.post("/api/conteudos", json={"titulo": "Temporário"}).get_json()
    resposta = client.delete(f"/api/conteudos/{criado['id']}")
    assert resposta.status_code == 200

    restantes = [c["id"] for c in client.get("/api/conteudos").get_json()]
    assert criado["id"] not in restantes


def test_historico_de_aulas_do_aluno(client):
    aluno = client.post("/api/alunos", json={"nome": "Beatriz"}).get_json()

    resposta = client.get(f"/api/alunos/{aluno['id']}/aulas")
    assert resposta.status_code == 200
    assert resposta.get_json() == []


def test_historico_de_aluno_inexistente_retorna_404(client):
    resposta = client.get("/api/alunos/9999/aulas")
    assert resposta.status_code == 404


def test_estatisticas_sem_aulas_retorna_zerado(client):
    resposta = client.get("/api/estatisticas")
    dados = resposta.get_json()
    assert dados["total_aulas"] == 0
    assert dados["aulas_por_mes"] == []


def test_verificar_feriado_usa_api_externa(client, monkeypatch):
    """Substitui a chamada HTTP real por uma resposta simulada, garantindo
    que o teste não dependa de rede nem da BrasilAPI estar no ar."""
    feriados_service._feriados_do_ano.cache_clear()

    class RespostaFalsa:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"date": "2026-01-01", "name": "Confraternização Universal"}]

    monkeypatch.setattr(feriados_service.requests, "get", lambda *a, **k: RespostaFalsa())

    resposta = client.get("/api/feriados/2026-01-01")
    dados = resposta.get_json()
    assert dados["feriado"] is True
    assert dados["nome"] == "Confraternização Universal"

    resposta = client.get("/api/feriados/2026-01-02")
    assert resposta.get_json()["feriado"] is False
