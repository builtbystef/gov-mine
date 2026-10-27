# packages/api-client

A typed fetch client for `apps/server` (npm package `@gov-mine/api-client`), built
on [openapi-fetch](https://openapi-ts.dev/openapi-fetch/) with types generated
by [openapi-typescript](https://openapi-ts.dev).

```sh
vp run generate          # from the repo root, after changing a route or model in apps/server
vp run generate:check    # fail if the committed files are stale (CI)
```

```text
packages/api-client/
├── openapi.json           # the API's schema, exported from apps/server
├── scripts/generate.ts    # exports the schema and regenerates the types
└── src/
    ├── index.ts           # createApiClient and the re-exported types
    └── generated/         # types generated from openapi.json
```

## Rules the code relies on

- **Generated files are never edited by hand.** `openapi.json` and `src/generated/` are both committed and rewritten by `vp run generate`, so consumers never need Python and schema changes show up in review. CI fails when they are stale.

## How it works

```ts
import { createApiClient } from "@gov-mine/api-client";

const api = createApiClient({ baseUrl: "http://127.0.0.1:8000" });
const { data, error } = await api.GET("/health/");
```
