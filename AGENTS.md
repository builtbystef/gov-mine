# Agent notes

Before changing an app or package, read the `README.md` in its folder: it holds the code map and the rules the code relies on.

## Commands

Scripts run through Vite+ (`vp`), not plain pnpm or npx.

- `vp run check`: format, lint, and typecheck for both languages. `vp run check:fix` applies fixes.
- `vp run test`: every test. One file: `vp test <file>` or `uv run pytest <path>`.
- `vp run db:up`: PostgreSQL and object storage, which integration tests need.

## Easy to miss

- A model change needs an Alembic migration (`cd apps/server && uv run alembic revision --autogenerate -m "..."`); CI fails without one.
- A change to API request or response shapes needs `vp run generate`. The client in `packages/api-client/src/generated/` is never edited by hand.
- Dependencies are often newer than your training data. Check APIs against the installed source in `node_modules/` or `.venv/`, not memory.
