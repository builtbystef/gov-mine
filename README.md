# gov-mine

Crawls a public institution's website from its homepage, keeps a copy of every
page and file, extracts typed records with a verified citation for every
field, and re-runs on a schedule. The first institution is CreateTO. The
design is in [docs/specification/](docs/specification/README.md).

| Concern    | TypeScript                                    | Python                          |
| ---------- | --------------------------------------------- | ------------------------------- |
| Packages   | pnpm via [Vite+](https://viteplus.dev) (`vp`) | [uv](https://docs.astral.sh/uv) |
| Format     | oxfmt (`vp check`)                            | Ruff                            |
| Lint       | oxlint (`vp check`)                           | Ruff                            |
| Type check | tsc (`vp check`)                              | [ty](https://docs.astral.sh/ty) |
| Tests      | Vitest (`vp test`)                            | pytest                          |

## Requirements

- Node ≥ 24, Python ≥ 3.14 (uv downloads it), uv ≥ 0.12
- Docker with Compose, for the local PostgreSQL and RustFS

## Commands

```sh
vp run check         # format + lint + typecheck, both languages (check:fix to apply fixes)
vp run test          # Vitest + pytest; one file: vp test <file> or uv run pytest <path>
vp run generate      # regenerate the API client after an API change
vp run ci            # everything CI runs
vp run db:up         # PostgreSQL and RustFS in Docker, needed by integration tests
vp run db:migrate    # alembic upgrade head
vp run dev           # API, worker, and web together
vp run dev:api       # http://127.0.0.1:8000/docs
vp run dev:web       # http://localhost:3000
```

Run `vp config` once after cloning to activate the pre-commit hook.

## Layout

Each project has a README with its code map and the rules its code relies on.
Read it before changing the project.

| Project               | What it is                                                   | README                                                         |
| --------------------- | ------------------------------------------------------------ | -------------------------------------------------------------- |
| `apps/server`         | FastAPI app and Procrastinate worker                         | [apps/server/README.md](apps/server/README.md)                 |
| `apps/web`            | Next.js 16 dashboard; the only process with a public address | [apps/web/README.md](apps/web/README.md)                       |
| `packages/api-client` | Typed fetch client generated from the API's OpenAPI schema   | [packages/api-client/README.md](packages/api-client/README.md) |

The browser talks only to `apps/web`, which forwards `/api/*` to `apps/server`.
The two share types only through the generated client.

New projects go in `apps/*`, `packages/*`, or `tools/*`. TypeScript projects
extend a preset from `tsconfig/` and take versions from the catalog in
`pnpm-workspace.yaml`. Python projects are listed under
`[tool.uv.workspace] members` in the root `pyproject.toml`.

## Deploying

One image per app, one command per process, settings from environment variables:

| Process  | Image         | Command                                   | Port |
| -------- | ------------- | ----------------------------------------- | ---- |
| `api`    | `apps/server` | `fastapi run --port 8000 --proxy-headers` | 8000 |
| `worker` | `apps/server` | `gov-mine-worker`                         | none |
| `web`    | `apps/web`    | `node apps/web/server.js`                 | 3000 |

Plus managed PostgreSQL and an S3-compatible bucket. Only `web` needs a
public address; it forwards `/api/*` to the API. Run `alembic upgrade head`
from `/app/apps/server` before new code starts. Health checks: `/health/`
(liveness), `/health/{db,storage}` (readiness).

```sh
GOV_MINE_DATABASE_URL=postgresql+psycopg://...
GOV_MINE_STORAGE_ENDPOINT_URL=... GOV_MINE_STORAGE_BUCKET=... GOV_MINE_STORAGE_ACCESS_KEY=... GOV_MINE_STORAGE_SECRET_KEY=...
GOV_MINE_STORAGE_PATH_STYLE=false   # true for MinIO and RustFS
GOV_MINE_OPENAI_API_KEY=...         # optional; unset, nothing calls the model
API_URL=http://api.internal:8000    # web only
```

`.github/workflows/images.yml` builds `ghcr.io/<owner>/<repo>/{server,web}`
after CI passes on `main`.

## Supply-chain policy

New package versions are held back for 4 days before install (pnpm
`minimumReleaseAge`, uv `exclude-newer`), and Dependabot runs weekly with the
same cooldown. pnpm runs no dependency build scripts (`strictDepBuilds` with
an empty `allowBuilds`), blocks exotic sub-dependencies, and refuses trust
downgrades. CI uses least-privilege permissions, SHA-pinned actions, and
frozen lockfiles.

## License

[MIT](LICENSE) © builtbystef
