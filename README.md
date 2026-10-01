# Gym Management SaaS (Vue 3 + Django/DRF)

A multi-tenant, India-focused gym management SaaS — a Vue 3 + Django rebuild of
the concepts in `vibhudawar/gym-management-saas` (originally Next.js + Supabase).

**Stack:** Django 5 + DRF + SimpleJWT + Postgres (backend) · Vue 3 + Vite +
Pinia + Vue Router + Tailwind + TanStack Query (frontend). Money is stored as
integer **paise**; timestamps are UTC-stored / IST-displayed; there is **no
public signup** — tenants are provisioned with a management command.

## Phase 0 (Foundation) — what's here

- Multi-tenant base: `common.TenantScoped` model + soft-delete managers, a
  `TenantScopedViewSet` that filters every queryset by the authenticated user's
  gym (and branch for non-owners), and a standard `{ok,data}|{ok,error,code}`
  response envelope.
- `tenants` app: `Gym`, `Branch`, and a custom email-login `User` (roles:
  super_admin / owner / branch_manager / receptionist).
- Auth: SimpleJWT login + refresh, `auth/me`, forgot-password scaffold.
- `create_tenant` management command (gym / staff / branch modes).
- Vue app shell with role-aware nav, login flow, JWT refresh interceptor.
- Docker Compose (db + backend + frontend) and a 2-tenant isolation test.

## Run it (Docker)

```bash
cp .env.example .env          # optional for compose; compose sets its own vars
docker compose up --build
```

Then seed a tenant and sign in:

```bash
docker compose exec backend python manage.py create_tenant \
  --gym "Iron Paradise" \
  --owner-email owner@example.com --owner-password 'changeme123' \
  --owner-name "Asha Rao"
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/health/
- Log in at the frontend with the owner credentials above.

## Run it (local, without Docker)

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# point DATABASE_URL at a running Postgres (see .env.example)
python manage.py migrate
python manage.py create_tenant --gym "Iron Paradise" \
  --owner-email owner@example.com --owner-password 'changeme123'
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
cd backend
pytest                 # includes the 2-tenant isolation test
ruff check .
```

## Roadmap

Phases 1–6 (catalogue + members → revenue loop → freeze + today → reports +
audit → notifications + PDF → settings + hardening) are tracked in the plan doc.
