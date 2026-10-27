# apps/web

The Next.js dashboard for `apps/server` (npm package `@gov-mine/web`).

```sh
vp run dev:web      # from the repo root, http://localhost:3000
vp run dev:api      # the API it talks to, in another terminal
```

```text
apps/web/src/
├── app/              # routes only; each page composes feature components behind <Suspense>
│   ├── api/[...path]/route.ts   # forwards /api/* to the API
│   └── (app)/                   # sidebar layout and the pages inside it
├── features/         # product code by domain, mirroring the API's modules
│   └── <feature>/    # components/, hooks/, queries.ts, mutations.ts, schemas.ts, server.ts
├── components/       # ui/ (shadcn) and shared/ (layout, form, data-table, ...)
├── hooks/            # generic hooks
└── lib/              # api/, formatting/, time-zone/, lists.ts, validation.ts
```

## Rules the code relies on

- **The browser never sees `API_URL`.** Every request goes through the proxy route handler.
- **Routes only in `app/`.** Product code lives in `features/`, one folder per API module.
- **The API does the work.** The dashboard displays what the API returns and computes nothing of its own.
- **One key per query.** Query definitions in `queries.ts` take the client as a parameter, so server and client build identical keys.
- **List state lives in the URL.** Filters, page, and sort are search params.

## Adding things

- **A page**: a route under `app/(app)/` that composes feature components behind `<Suspense>`, a title in `components/shared/layout/page-title.tsx`, and a link in `components/shared/layout/app-sidebar.tsx`.
- **A feature**: a folder in `features/` with the parts it needs from `components/`, `hooks/`, `queries.ts`, `mutations.ts`, `schemas.ts`, and `server.ts`.
- **A shadcn component**: `cd apps/web && pnpm dlx shadcn@latest add card dialog`.
- **A call to a new or changed API route**: run `vp run generate` from the root first, so the client knows its types.

## How it works

- **Calling the API**: the proxy route handler forwards each request to `API_URL`. Server Components use `api` from `@/lib/api/server-client`; Client Components use `browserApi` from `@/lib/api/client`. `unwrap()` turns a non-2xx result into an `ApiError`.
- **Data flow**: pages are Server Components. Read-only pages fetch and render. Pages that mutate or filter prefetch into a per-request `QueryClient` and hand the cache over with `<HydrationBoundary>`, and a Client Component continues with `useSuspenseQuery` on the same key.
- **Forms**: TanStack Form bound to shadcn `Field` via `useAppForm`, validated with the Zod schemas in each feature's `schemas.ts`.
- **Tables**: TanStack Table v9 in manual mode, one page of 50 rows, with sorting and paging done by the API.
- **Styling**: Tailwind CSS v4 and shadcn/ui (`base-nova` style on Base UI, zinc, Geist). Everything lives in `src/app/globals.css`; prefer semantic utilities (`bg-background`, `text-muted-foreground`).
- **React Compiler** is on: write plain React, and use `useMemo`/`useCallback` only where needed.
- **Time zones**: `<TimeZoneSync>` writes the browser's zone to a `tz` cookie, so server and client format dates the same way.
- **Generated files**: `next-env.d.ts` and `.next/types/` are generated and gitignored.
