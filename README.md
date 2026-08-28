# Sistema de Gestão de Aulas — v2

Evolução do projeto original [`sistema-professor`](https://github.com/GianMandara/sistema-professor),
mantendo o mesmo domínio (alunos, conteúdos, aulas) e adicionando os
requisitos abaixo. **Este código vive em uma pasta separada
(`sistema-professor-v2`) e não altera o projeto original.**

## Requisitos atendidos e onde encontrá-los

| Requisito | Como foi implementado |
|---|---|
| Framework web + banco de dados | [Flask](https://flask.palletsprojects.com/) com [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) (ORM). Modelos em [`app/models.py`](app/models.py): `Aluno`, `Conteudo`, `Aula`. SQLite localmente, Postgres em produção (mesma URI, trocando só a env var `DATABASE_URL`) |
| Script web (JavaScript) | [`app/static/js/`](app/static/js): `main.js` (tema escuro/claro), `alunos.js` e `agenda.js` (exclusão via `fetch` sem recarregar a página, validação), `acompanhamento.js` (gráficos com Chart.js consumindo a API) |
| Nuvem | [`render.yaml`](render.yaml) + [`Procfile`](Procfile) para deploy no [Render](https://render.com) (grátis), com banco Postgres gerenciado e endpoint `/health` para health-check |
| Uso de API | API REST interna em [`app/routes/api.py`](app/routes/api.py) (JSON, consumida pelo JS) **e** integração com API externa pública — [BrasilAPI de feriados](https://brasilapi.com.br/) em [`app/services/feriados.py`](app/services/feriados.py), usada para avisar o professor se a data da aula é feriado |
| Acessibilidade | HTML semântico, `lang="pt-br"`, skip-link, labels associados, foco visível, contraste AA (claro e escuro), gráficos com tabela de dados equivalente, tradução em Libras (VLibras), navegação completa por teclado com *focus trap* no modal, mensagens de erro anunciadas (`role="alert"`) e movidas para o foco. Ver seção [Sobre acessibilidade](#sobre-acessibilidade) |
| Controle de versão | Repositório Git próprio, [`.gitignore`](.gitignore), [GitHub Actions CI](.github/workflows/ci.yml) rodando os testes a cada push/PR |
| Testes | [`pytest`](tests/) cobrindo modelos, rotas HTML e API (incluindo a integração externa, mockada com `monkeypatch`) |
| Análise de dados (opcional) | [`app/analytics.py`](app/analytics.py) usa **pandas** para agregar aulas por mês e por conteúdo; exposto em `/api/estatisticas` e visualizado no Dashboard |
| Lembrete por e-mail | [`app/services/email.py`](app/services/email.py) envia um e-mail ao aluno (via SMTP, `smtplib` da biblioteca padrão) sempre que uma aula é agendada em `/agenda`, se o aluno tiver e-mail cadastrado e o SMTP estiver configurado |
| Controle de segurança | Contas de professor com cadastro, login, "esqueci a senha" e redefinição por e-mail ([`app/routes/auth.py`](app/routes/auth.py)), senhas com hash (`werkzeug.security`); protege todas as páginas e a API; proteção CSRF ([Flask-WTF](https://flask-wtf.readthedocs.io/)); cookies de sessão `HttpOnly`/`SameSite=Lax`; **criptografia de dados pessoais em repouso** (Fernet, [`app/crypto.py`](app/crypto.py)); **e-mail de notificação em toda tentativa de acesso** (sucesso ou senha errada) |
| Boletim mensal | [`app/relatorios.py`](app/relatorios.py) monta notas/presença/evolução do aluno num mês; o professor gera pela página de Acompanhamento e o sistema envia um link seguro por e-mail ao aluno — ver [Sobre o boletim mensal](#sobre-o-boletim-mensal) |

## Estrutura do projeto

```
sistema-professor-v2/
├── app/
│   ├── __init__.py          # application factory
│   ├── config.py            # configuração via variáveis de ambiente
│   ├── extensions.py        # instância do SQLAlchemy
│   ├── models.py            # Aluno, Conteudo, Aula
│   ├── analytics.py         # agregações com pandas
│   ├── routes/
│   │   ├── views.py         # páginas HTML (dashboard, alunos, agenda...)
│   │   └── api.py           # API REST em JSON
│   ├── services/
│   │   ├── feriados.py      # integração com a BrasilAPI
│   │   └── email.py         # lembrete por e-mail ao agendar aula
│   ├── templates/           # Jinja2 (HTML acessível)
│   └── static/
│       ├── css/style.css
│       └── js/              # main.js, alunos.js, agenda.js, acompanhamento.js
├── tests/                   # pytest
├── .github/workflows/ci.yml # integração contínua
├── render.yaml / Procfile   # deploy em nuvem
├── requirements.txt
└── run.py                   # ponto de entrada local
```

## Como rodar localmente

```bash
cd sistema-professor-v2
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # ajuste se necessário
python run.py
```

Acesse `http://127.0.0.1:5000`. O banco SQLite é criado automaticamente em
`instance/escola.db` na primeira execução.

Clique em "Acessar sistema" e depois em "Criar conta" para cadastrar seu
primeiro usuário — não há usuário/senha pré-configurado (ver
[Sobre o controle de segurança](#sobre-o-controle-de-segurança)).

## Como rodar os testes

```bash
pytest -v
```

## Como publicar na nuvem (Render)

1. Crie um repositório no GitHub para este projeto (`git init`, `git add`,
   `git commit`, `git push`).
2. Em [render.com](https://render.com), clique em **New > Blueprint** e
   aponte para o repositório — o Render lê o `render.yaml` automaticamente
   e provisiona o serviço web **e** o banco Postgres.
3. O Render injeta `DATABASE_URL` e `SECRET_KEY` como variáveis de
   ambiente; o app detecta e usa Postgres em vez de SQLite (veja
   `app/config.py`).
4. O endpoint `/health` é usado pelo Render para verificar se o serviço
   está no ar.

## Sobre a integração com API externa (feriados)

Ao escolher a data de uma aula em **Agenda**, o front-end chama
`GET /api/feriados/<data>`, que por sua vez consulta a BrasilAPI. Se a
data cair em feriado nacional, um aviso acessível (`role="alert"`) aparece
sem impedir o agendamento — apenas informa o professor.

## Sobre o lembrete por e-mail

Ao agendar uma aula em **Agenda**, o sistema tenta enviar um e-mail de
lembrete ao aluno com data, horário, conteúdo e observações. Isso só
acontece se:

1. O aluno tiver um e-mail cadastrado, **e**
2. As variáveis `MAIL_SERVER` e `MAIL_USERNAME` estiverem configuradas no `.env`.

Sem isso, o agendamento continua funcionando normalmente — só não envia o
e-mail (e a mensagem de sucesso avisa por que). Exemplo de configuração
com Gmail (use uma [senha de app](https://myaccount.google.com/apppasswords),
não a senha normal da conta):

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=senha-de-app-de-16-caracteres
MAIL_REMETENTE=seu-email@gmail.com
```

Para testar sem enviar e-mails de verdade, use um serviço como o
[Mailtrap](https://mailtrap.io) (sandbox de SMTP) apontando `MAIL_SERVER`
para as credenciais de teste dele.

## Sobre o controle de segurança

Contas são criadas pelos próprios usuários, direto no sistema — como em
qualquer site profissional:

- **Criar conta**: nome, e-mail e senha (mínimo 8 caracteres). A senha
  nunca é guardada em texto puro, só o hash (`werkzeug.security`). Ao
  cadastrar, um e-mail de boas-vindas é enviado (se o SMTP estiver
  configurado — ver [Sobre o lembrete por e-mail](#sobre-o-lembrete-por-e-mail)).
- **Esqueci minha senha**: gera um link assinado (`itsdangerous`), válido
  por 1 hora, enviado por e-mail. A mensagem de confirmação é sempre a
  mesma, exista ou não uma conta com aquele e-mail — isso evita que
  alguém descubra quais e-mails estão cadastrados testando um por um.
- **Entrar/Criar conta/Esqueci a senha não são páginas separadas** — são
  painéis dentro de um modal embutido na própria landing page (`/`),
  abertos ao clicar em "Acessar sistema" (ou automaticamente, se você
  tentar abrir uma página protegida sem estar logado). O link de
  redefinição de senha do e-mail é a única exceção: abre uma página
  própria (`/redefinir-senha/<token>`), já que vem de fora do site.
- Toda página do sistema (dashboard, alunos, agenda, conteúdos,
  acompanhamento) e toda a API exigem login; só a landing pública (`/`) e
  o health-check (`/health`) ficam abertos.
- A sessão é assinada com `SECRET_KEY` e guardada em cookie `HttpOnly` +
  `SameSite=Lax` (não acessível via JavaScript, não enviado em navegação
  cross-site).
- Todo formulário e toda ação de exclusão via JavaScript carregam um
  token CSRF (Flask-WTF) — sem ele, a requisição é rejeitada.
- Em produção, defina `SESSION_COOKIE_SECURE=true` (o Render já faz isso
  via `render.yaml`) para o cookie de sessão só trafegar por HTTPS.

### Criptografia de dados pessoais em repouso

Como o sistema lida com dados pessoais de professores e alunos, os
campos mais sensíveis ficam **criptografados dentro do próprio banco de
dados** (não só protegidos por senha de acesso):

| Campo | Criptografado? | Por quê |
|---|---|---|
| `Usuario.nome`, `Usuario.email` | ✅ | Dados pessoais do professor |
| `Aluno.email`, `Aluno.telefone` | ✅ | Dados pessoais do aluno |
| `Aula.observacoes` | ✅ | Pode conter informação sensível sobre o aluno |
| `Aluno.nome` | ❌ (proposital) | Usado para ordenar a listagem alfabética — criptografar quebraria a ordenação |

Implementado em [`app/crypto.py`](app/crypto.py) com **Fernet**
(AES-128 + HMAC autenticado, da biblioteca `cryptography`), por meio de
um tipo de coluna do SQLAlchemy (`CampoCriptografado`) que criptografa/
decripta de forma transparente — o resto do código sempre lê e escreve
texto puro, a criptografia acontece só na fronteira com o banco.

Como o e-mail do professor precisa ser localizável no login (não dá pra
fazer `WHERE email = ...` num valor criptografado, que muda a cada
criptografia), existe uma segunda coluna, `email_hash` — um HMAC-SHA256
determinístico do e-mail, calculado com uma chave *derivada* da
`ENCRYPTION_KEY` (nunca a mesma chave usada para criptografar). O login
busca por esse hash, nunca pelo e-mail em texto puro.

**Configuração — `ENCRYPTION_KEY` no `.env`:**
```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Cole o resultado em `ENCRYPTION_KEY=`. Sem essa variável, tudo continua
funcionando — só sem a criptografia extra.

⚠️ **Se você perder essa chave, os dados já criptografados ficam
irrecuperáveis para sempre** — não existe "esqueci a chave" para
criptografia de verdade, diferente de uma senha. Guarde uma cópia em um
gerenciador de senhas ou outro lugar seguro, fora do `.env`. Use uma
chave **diferente** em produção (Render) e em desenvolvimento local.

Bancos criados antes dessa mudança são migrados automaticamente na
próxima inicialização ([`app/migrations.py`](app/migrations.py),
`criptografar_dados_legados`) — roda uma vez só, de forma seletiva
(só quando houver conta sem `email_hash`), sem reescrever o banco a
cada início da aplicação.

### Notificação de acesso por e-mail

Toda tentativa de entrar numa conta gera um e-mail para o dono dela
([`app/services/email.py`](app/services/email.py)):

- **Login com sucesso** → "Novo acesso à sua conta", com data/hora e IP.
  Se não foi o professor, ele sabe na hora que a senha pode estar
  comprometida.
- **Senha errada numa conta que existe** → "Tentativa de acesso à sua
  conta", com os mesmos detalhes — ajuda a perceber tentativas de invasão
  mesmo quando elas falham.
- **E-mail que não corresponde a nenhuma conta** → nenhuma notificação
  (não há dono para avisar, e notificar mesmo assim revelaria quais
  e-mails têm conta cadastrada).

Assim como os outros e-mails do sistema, isso depende de `MAIL_SERVER`/
`MAIL_USERNAME` estarem configurados — sem SMTP, o login continua
funcionando normalmente, só não envia a notificação.

**Importante:** como o cadastro é aberto (qualquer pessoa com o link pode
criar uma conta), qualquer conta criada enxerga os mesmos dados de
alunos/aulas — não há isolamento por usuário. Se isso for um problema
(por exemplo, se o link do sistema circular além de quem deveria ter
acesso), me avise para adicionarmos um convite/aprovação antes do
cadastro.

## Sobre o boletim mensal

Como em uma escola, o professor pode gerar um boletim mensal por aluno —
com notas, presença/faltas e um gráfico de evolução das notas ao longo
do mês:

1. Na página **Acompanhamento**, seção "Boletim mensal": escolha o aluno
   e o mês (por padrão já vem selecionado o **último mês fechado** — o
   anterior ao atual) e clique em "Gerar e enviar boletim".
2. O sistema monta o boletim daquele mês, calculado na hora a partir das
   aulas registradas (não é uma foto congelada — se você corrigir uma
   nota depois, o boletim reflete a correção da próxima vez que for
   aberto) e **envia por e-mail ao aluno** um link exclusivo.
3. Você (professor) é levado direto para essa mesma página — a mesma
   que o aluno vai ver — pra conferir como ficou.

**Como o aluno acessa sem ter conta no sistema:** o link enviado por
e-mail carrega um token assinado (`itsdangerous`, o mesmo mecanismo do
"esqueci a senha"), válido por 90 dias — dá pra abrir sem login/senha,
mas só quem tem o link (ninguém adivinha um token assinado) vê os dados
daquele aluno naquele mês específico. Passado esse prazo, o link expira
e é preciso gerar um novo.

Alunos sem e-mail cadastrado ficam desabilitados no seletor da tela —
cadastre um e-mail em **Alunos** antes de gerar o boletim dele.

## Sobre acessibilidade

O sistema segue as diretrizes WCAG 2.1 nível AA. Abaixo, o que foi
verificado/implementado ponto a ponto:

- **Tradução para Libras (VLibras)**: widget oficial do governo federal
  embutido em todas as páginas ([`app/templates/_vlibras.html`](app/templates/_vlibras.html)),
  com avatar 3D que traduz o conteúdo da página. Escolhido em vez do Hand
  Talk por ser gratuito e não exigir cadastro/token de API. Requer acesso
  a `vlibras.gov.br` (mesmo padrão de CDN externo já usado para o
  Chart.js e as fontes do Google).
- **Texto alternativo em imagens**: o projeto não usa nenhuma tag
  `<img>` — todo elemento gráfico é SVG inline com `aria-hidden="true"`
  (puramente decorativo) ou ícones que acompanham texto visível. Se uma
  `<img>` for adicionada no futuro, ela precisa de um `alt` descritivo.
- **Navegação por teclado**: todo o site é operável só com Tab/Shift+Tab,
  Enter e Esc. O modal de login/cadastro/esqueci-senha (`role="dialog"
  aria-modal="true"`) tem *focus trap* — o Tab não escapa para o conteúdo
  atrás dele enquanto está aberto — e devolve o foco para quem abriu o
  modal ao fechar ([`app/static/js/landing.js`](app/static/js/landing.js)).
- **Contraste de cores**: todos os pares texto/fundo do tema claro e
  escuro foram medidos (fórmula de luminância relativa do WCAG) e passam
  de 4,5:1. Foi encontrada e corrigida uma falha real: no modo escuro,
  texto branco sobre `--primaria` (usado em botões) dava só 2,89:1 —
  criamos uma variável `--botao-fundo` separada, reaproveitando o azul
  mais saturado do tema claro (6,3:1 com texto branco), sem alterar a cor
  usada em links/ícones (que já estava correta).
- **Fontes escaláveis**: todo `font-size` do CSS usa `rem`/`clamp()`, sem
  nenhum valor fixo em `px` e sem `html { font-size: ... }` travando a
  base — o layout acompanha o zoom e a preferência de fonte do navegador
  sem cortar texto.
- **Legendas e transcrições**: o sistema não tem nenhum `<video>`/`<audio>`
  atualmente, então não há conteúdo a legendar. Se algum vídeo/áudio for
  adicionado no futuro, ele precisa de legenda (vídeo) ou transcrição
  (áudio).
- **Estrutura semântica**: `<header>`, `<nav>`, `<main>`, `<footer>` em
  todas as páginas, um único `<h1>` por página, `<button>` para ações que
  não navegam e `<a>` para as que navegam.
- **Formulários claros**: todo campo tem `<label>` associado via `for`/`id`.
  A validação nativa do HTML5 (`required`, `type="email"`, `minlength`,
  `pattern`) foi reativada (antes ficava desligada por `novalidate`), o
  que faz o navegador focar e anunciar automaticamente o campo com erro
  antes mesmo de enviar o formulário. A confirmação de senha (cadastro e
  redefinição) é checada em tempo real via `setCustomValidity`
  ([`app/static/js/validacao-senha.js`](app/static/js/validacao-senha.js)).
  Erros vindos do servidor usam `role="alert"` (mensagens de sucesso usam
  `role="status"`) e o foco é movido automaticamente para a mensagem ao
  recarregar a página ([`app/static/js/foco-erro.js`](app/static/js/foco-erro.js)).

## Diferenças em relação ao projeto original

- Banco de dados acessado via ORM (SQLAlchemy) em vez de SQL puro,
  facilitando trocar SQLite por Postgres sem mudar o código.
- Front-end ganhou interatividade via JavaScript (exclusão sem reload,
  aviso de feriado, gráficos), mantendo funcionamento básico sem JS.
- Adicionada camada de API JSON reaproveitável por outros clientes.
- Adicionada suíte de testes automatizados e pipeline de CI.
- Adicionada configuração pronta para deploy em nuvem.
- Página de acompanhamento passou a usar pandas para agregações e
  Chart.js para visualização.
