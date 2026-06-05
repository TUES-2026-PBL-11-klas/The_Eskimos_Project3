# EventHub

An event-aggregator for Bulgarian events. Monorepo of three services:

- **[ingestion/](ingestion/)** — one-shot worker (CronJob) that scrapes, normalizes, dedups,
  categorizes and persists events. Sole owner/writer of the Postgres `events` schema.
- **[api/](api/)** — read-only FastAPI REST the frontend consumes; also owns the `users` database.
- **[frontend/](frontend/)** — Next.js app.

Text handling is bilingual (Bulgarian + English) throughout.

## Local development

Each service runs in Docker — no local venv or Postgres needed. From a service directory use
`./tasks.ps1` (Windows) or `make` (mirrors 1:1). See [ingestion/](ingestion/) for the full target
list (`build`, `up`, `migrate`, `seed`, `run`, `lint`, `fmt`, `test`, …).

```powershell
cd ingestion; ./tasks.ps1 build; ./tasks.ps1 run
```

Pre-commit hooks (gitleaks, ruff, mypy, hadolint, eslint) are in
[.pre-commit-config.yaml](.pre-commit-config.yaml):

```powershell
pre-commit install
pre-commit run --all-files
```

## Deployment (CI/CD on DigitalOcean Kubernetes)

CI (lint → test → build → Trivy scan → push to GHCR) and CD (`helm upgrade` to DOKS after CI
passes on `main`) live in [.github/workflows/](.github/workflows/). Infrastructure is
Terraform + Helm under [infra/](infra/).

- **Runbook & secrets:** [infra/README.md](infra/README.md)
- **Architecture diagram:** [docs/infrastructure-diagram.md](docs/infrastructure-diagram.md)
- **Roll back a deploy:** `helm rollback eventhub -n eventhub`

Observability is Prometheus + Alertmanager (no Grafana); alerts route to Discord. The API is
scraped on `/metrics`; the ingestion CronJob pushes run metrics to a Prometheus Pushgateway.
