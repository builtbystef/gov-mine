export interface paths {
    "/health/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Health
         * @description Liveness: the process is up.
         */
        get: operations["health-read_health"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/db": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Health Db
         * @description Readiness: the database answers.
         */
        get: operations["health-read_health_db"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health/storage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Health Storage
         * @description Readiness: the object store answers and the bucket exists.
         */
        get: operations["health-read_health_storage"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Runs
         * @description Every run, newest first.
         */
        get: operations["runs-list_runs"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/runs/{run_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Run */
        get: operations["runs-read_run"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/runs/{run_id}/fetches": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Fetches
         * @description The run's fetch log, one row per attempt, in the order the requests were made.
         */
        get: operations["runs-list_fetches"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/snapshots/{snapshot_id}/text/{page}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Text
         * @description The markdown of one page of the snapshot, from 1. 409 while it is being parsed; 404 when
         *     it has no text.
         */
        get: operations["snapshots-read_text"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/snapshots/{snapshot_id}/bytes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Bytes
         * @description The snapshot's raw bytes, with the media type they were fetched with.
         */
        get: operations["snapshots-read_bytes"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/runs/{run_id}/sources": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Run Sources
         * @description The sources found by the run's classifications, next crawl first.
         */
        get: operations["runs-list_run_sources"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/runs/{run_id}/document-counts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Count Run Documents
         * @description How many documents the run's classifications found, by type.
         */
        get: operations["runs-count_run_documents"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/ai-calls": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Ai Calls
         * @description The run's paid calls, by purpose, oldest first within each.
         */
        get: operations["ai-calls-list_ai_calls"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Root */
        get: operations["read_root"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /**
         * AICallOutput
         * @description One paid call. `cost` is from the price list; `reported_cost` is what OpenRouter said.
         */
        AICallOutput: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Crawl Run Id */
            crawl_run_id: string | null;
            /** Classification Id */
            classification_id: string | null;
            /** Extraction Id */
            extraction_id: string | null;
            purpose: components["schemas"]["AIPurpose"];
            /** Provider */
            provider: string;
            /** Model */
            model: string;
            /** Input Tokens */
            input_tokens: number;
            /** Output Tokens */
            output_tokens: number;
            /** Cost */
            cost: string;
            /** Reported Cost */
            reported_cost: string | null;
            /** Price List Version */
            price_list_version: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * AIPurpose
         * @enum {string}
         */
        AIPurpose: "classify" | "extract" | "ocr" | "transcribe";
        /**
         * DocumentType
         * @description What a source lists and what a document is. A `project_material` is assigned by a
         *     project's extraction, never by the classifier.
         * @enum {string}
         */
        DocumentType: "purchase_order" | "meeting_minutes" | "budget" | "procurement_guidelines" | "youtube" | "rfp" | "grants" | "press_releases" | "projects" | "project_material" | "annual_report" | "strategic_plan" | "staff_directory";
        /** DocumentTypeCount */
        DocumentTypeCount: {
            document_type: components["schemas"]["DocumentType"];
            /** Count */
            count: number;
        };
        /**
         * FetchOutcome
         * @enum {string}
         */
        FetchOutcome: "fetched" | "not_modified" | "unchanged" | "blocked_robots" | "skipped_scope" | "skipped_type" | "skipped_size" | "skipped_depth" | "failed_http" | "failed_timeout";
        /**
         * FetchOutput
         * @description One attempt at a URL. `snapshot` is the copy it wrote, if it wrote one.
         */
        FetchOutput: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Webpage Id
             * Format: uuid
             */
            webpage_id: string;
            /** Url */
            url: string;
            /**
             * Requested At
             * Format: date-time
             */
            requested_at: string;
            /** Duration Ms */
            duration_ms: number | null;
            outcome: components["schemas"]["FetchOutcome"];
            /** Http Status */
            http_status: number | null;
            /** Reason */
            reason: string | null;
            snapshot: components["schemas"]["SnapshotSummary"] | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** Health */
        Health: {
            /** Status */
            status: string;
        };
        /** Page[AICallOutput] */
        Page_AICallOutput_: {
            /** Items */
            items: components["schemas"]["AICallOutput"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** Page[FetchOutput] */
        Page_FetchOutput_: {
            /** Items */
            items: components["schemas"]["FetchOutput"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** Page[RunOutput] */
        Page_RunOutput_: {
            /** Items */
            items: components["schemas"]["RunOutput"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** Page[SourceOutput] */
        Page_SourceOutput_: {
            /** Items */
            items: components["schemas"]["SourceOutput"][];
            /** Total */
            total: number;
            /** Limit */
            limit: number;
            /** Offset */
            offset: number;
        };
        /** RunOutput */
        RunOutput: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Institution Id
             * Format: uuid
             */
            institution_id: string;
            /** Institution Name */
            institution_name: string;
            status: components["schemas"]["RunStatus"];
            settings: components["schemas"]["RunSettings"];
            /** Started At */
            started_at: string | null;
            /** Finished At */
            finished_at: string | null;
            /** Error */
            error: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * RunSettings
         * @description What a run was asked to do, kept on the run so two runs can be compared.
         */
        RunSettings: {
            /**
             * Trigger
             * @enum {string}
             */
            trigger: "cli" | "dashboard" | "scheduled";
            /**
             * Mode
             * @enum {string}
             */
            mode: "full" | "incremental";
            /** Limit */
            limit?: number | null;
            /** Max File Bytes */
            max_file_bytes?: number | null;
        };
        /**
         * RunStatus
         * @enum {string}
         */
        RunStatus: "queued" | "running" | "finished" | "failed" | "cancelled";
        /** SnapshotSummary */
        SnapshotSummary: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Content Hash */
            content_hash: string;
            /** Media Type */
            media_type: string;
            /** Size Bytes */
            size_bytes: number;
        };
        /**
         * SourceOutput
         * @description A listing page the run found, revisited every `crawl_interval`.
         */
        SourceOutput: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Webpage Id
             * Format: uuid
             */
            webpage_id: string;
            /** Url */
            url: string;
            document_type: components["schemas"]["DocumentType"];
            /**
             * Crawl Interval
             * Format: duration
             */
            crawl_interval: string;
            /**
             * Next Crawl At
             * Format: date-time
             */
            next_crawl_at: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type AiCallOutput = components['schemas']['AICallOutput'];
export type AiPurpose = components['schemas']['AIPurpose'];
export type DocumentType = components['schemas']['DocumentType'];
export type DocumentTypeCount = components['schemas']['DocumentTypeCount'];
export type FetchOutcome = components['schemas']['FetchOutcome'];
export type FetchOutput = components['schemas']['FetchOutput'];
export type HttpValidationError = components['schemas']['HTTPValidationError'];
export type Health = components['schemas']['Health'];
export type PageAiCallOutput = components['schemas']['Page_AICallOutput_'];
export type PageFetchOutput = components['schemas']['Page_FetchOutput_'];
export type PageRunOutput = components['schemas']['Page_RunOutput_'];
export type PageSourceOutput = components['schemas']['Page_SourceOutput_'];
export type RunOutput = components['schemas']['RunOutput'];
export type RunSettings = components['schemas']['RunSettings'];
export type RunStatus = components['schemas']['RunStatus'];
export type SnapshotSummary = components['schemas']['SnapshotSummary'];
export type SourceOutput = components['schemas']['SourceOutput'];
export type ValidationError = components['schemas']['ValidationError'];
export type $defs = Record<string, never>;
export interface operations {
    "health-read_health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    "health-read_health_db": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    "health-read_health_storage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    "runs-list_runs": {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_RunOutput_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    "runs-read_run": {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RunOutput"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    "runs-list_fetches": {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_FetchOutput_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    "snapshots-read_text": {
        parameters: {
            query?: never;
            header?: never;
            path: {
                snapshot_id: string;
                page: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "text/markdown": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    "snapshots-read_bytes": {
        parameters: {
            query?: never;
            header?: never;
            path: {
                snapshot_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/octet-stream": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    "runs-list_run_sources": {
        parameters: {
            query?: {
                limit?: number;
                offset?: number;
            };
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_SourceOutput_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    "runs-count_run_documents": {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DocumentTypeCount"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    "ai-calls-list_ai_calls": {
        parameters: {
            query: {
                run: string;
                limit?: number;
                offset?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page_AICallOutput_"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_root: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
}
