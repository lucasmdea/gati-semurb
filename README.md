# Atendimentos TI — SEMURB Natal

Sistema web interno para registro de atendimentos da equipe de T.I., com:
- Login (técnico responsável)
- Cadastro e consulta de atendimentos (filtros)
- Inventário de ativos por **serial** (computadores, impressoras, monitores)
- Estoque quantitativo (mouse, teclado, toner etc.) com auditoria de entradas/saídas
- Admin (Django Admin) para cadastros internos

> Este repositório foi comentado para facilitar manutenção por futuros funcionários.

---

## Estrutura rápida do projeto

- `app/` → configuração Django (`settings.py`, `urls.py`)
- `core/` → regras do negócio (models, views, forms, admin)
- `templates/` → telas HTML
- `static/` → CSS/JS/imagens (inclui logo SEMURB)
- `docs/` → manuais e guias (inclui manual dos técnicos)

---

## Rodar pela primeira vez (máquina nova)

Na pasta do projeto:

```bash
docker compose up -d --build
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py seed
docker compose run --rm web python manage.py createsuperuser

# (recomendado) Papéis e permissões (Usuários e Técnicos)
# - adiciona TODOS os usuários (não-superuser) ao grupo de solicitantes
# - você pode incluir técnicos por username (marca como staff automaticamente)
docker compose run --rm web python manage.py setup_roles --include-all-users --tech-users tecnico1 tecnico2

# (legado) Apenas técnicos
docker compose run --rm web python manage.py setup_technicians --include-existing-staff
```

Acessar:
- Sistema: `http://IP_DO_HOST:8000/`
- Admin: `http://IP_DO_HOST:8000/admin/`

---

## Comandos do dia a dia

### Checagem rápida de segurança/config (boa para não regredir)
```bash
docker compose run --rm web python manage.py check --deploy
```

### Após alterar HTML/CSS
Normalmente basta atualizar o navegador (Ctrl+Shift+R).

Se estiver usando `collectstatic` (produção):
```bash
docker compose run --rm web python manage.py collectstatic --noinput
docker compose restart web
```

### Após alterar models (banco)
```bash
docker compose run --rm web python manage.py makemigrations
docker compose run --rm web python manage.py migrate
```

### Após alterar views/forms/admin/urls
```bash
docker compose restart web
```

### Após alterar requirements.txt
```bash
docker compose down
docker compose up -d --build
```

---

## Onde alterar (atalho de manutenção)

### Visual
- Navbar e layout geral: `templates/base.html`
- Tela de login: `templates/auth/login.html`
- Cadastro: `templates/core/ticket_form.html`
- Listagem/filtros: `templates/core/ticket_list.html`
- Cores/estilos: `static/css/app.css`

### Regras do sistema
- Modelos/tabelas: `core/models.py`
- Cadastro/listagem (backend): `core/views.py`
- Validações/formsets: `core/forms.py`
- Admin: `core/admin.py`
- Dados iniciais: `core/management/commands/seed.py`

---

## Banco de dados (PostgreSQL)

Acessar via psql dentro do container:
```bash
docker compose exec db psql -U atend_user -d atendimentos
```

Backup:
```bash
docker compose exec db pg_dump -U atend_user atendimentos > backup_atendimentos.sql
```

Restore:
```bash
cat backup_atendimentos.sql | docker compose exec -T db psql -U atend_user atendimentos
```

---

## Manual operacional

- Manual de técnicos (uso do sistema): `docs/MANUAL_TECNICOS.md`
