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
    "/institutions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Institutions
         * @description Every institution, by name, with its last run and when the next is due.
         */
        get: operations["institutions-list_institutions"];
        put?: never;
        /**
         * Create Institution
         * @description Adds the institution and makes its website's host a `crawl` domain.
         */
        post: operations["institutions-create_institution"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/institutions/{institution_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Institution */
        get: operations["institutions-read_institution"];
        /**
         * Update Institution
         * @description Replaces the institution's fields; its website's host becomes a `crawl` domain.
         */
        put: operations["institutions-update_institution"];
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
        /**
         * Create Run
         * @description Queues a full run of the institution from the dashboard. 409 while it has a queued or
         *     running run.
         */
        post: operations["runs-create_run"];
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
    "/runs/{run_id}/report": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Report
         * @description The run's numbers, each a query over its logs. Costs come from `ai_calls`: estimated from
         *     the price list, and as reported by OpenRouter.
         */
        get: operations["runs-read_report"];
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
         * @description The run's fetch log, one row per attempt, in the order the requests were made: only those
         *     with `outcome`, and only URLs containing `q` (any case), when given.
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
    "/runs/{run_id}/snapshots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Snapshots
         * @description The snapshots the run wrote, in the order it wrote them.
         */
        get: operations["runs-list_snapshots"];
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
    "/runs/{run_id}/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Run Documents
         * @description The documents the run created or gave a new version, by type then title.
         */
        get: operations["runs-list_run_documents"];
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
    "/snapshots/{snapshot_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Snapshot */
        get: operations["snapshots-read_snapshot"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/webpages/{webpage_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Webpage
         * @description The webpage, its domain, `missing_since`, every fetch of it newest first, and its
         *     snapshots newest first.
         */
        get: operations["webpages-read_webpage"];
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
         * DocumentOutput
         * @description A document a run's classifications found.
         */
        DocumentOutput: {
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
            /** Title */
            title: string | null;
            /** Document Date */
            document_date: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
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
             * Crawl Run Id
             * Format: uuid
             */
            crawl_run_id: string;
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
        /**
         * InstitutionInput
         * @description What the Add and Edit forms send. The website must be http or https.
         */
        InstitutionInput: {
            /** Name */
            name: string;
            institution_type: components["schemas"]["InstitutionType"];
            /**
             * Website Url
             * Format: uri
             */
            website_url: string;
            /** Country Code */
            country_code?: string | null;
            /** State */
            state?: string | null;
            /** City */
            city?: string | null;
        };
        /** InstitutionOutput */
        InstitutionOutput: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            institution_type: components["schemas"]["InstitutionType"];
            /** Website Url */
            website_url: string;
            /** Country Code */
            country_code: string | null;
            /** State */
            state: string | null;
            /** City */
            city: string | null;
            /** Paused */
            paused: boolean;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            last_run: components["schemas"]["LastRun"] | null;
            /** Next Run At */
            next_run_at: string | null;
        };
        /**
         * InstitutionType
         * @enum {string}
         */
        InstitutionType: "state" | "state_agency" | "county" | "city" | "police_agency" | "fire_department" | "special_district" | "k12_district" | "higher_education" | "municipal_agency";
        /** LastRun */
        LastRun: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            status: components["schemas"]["RunStatus"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /**
         * OutcomeCount
         * @description The run's `fetches` rows with one outcome; `requests` are those that sent a request.
         */
        OutcomeCount: {
            outcome: components["schemas"]["FetchOutcome"];
            /** Fetches */
            fetches: number;
            /** Requests */
            requests: number;
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
        /** Page[DocumentOutput] */
        Page_DocumentOutput_: {
            /** Items */
            items: components["schemas"]["DocumentOutput"][];
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
        /** Page[InstitutionOutput] */
        Page_InstitutionOutput_: {
            /** Items */
            items: components["schemas"]["InstitutionOutput"][];
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
        /** Page[SnapshotOutput] */
        Page_SnapshotOutput_: {
            /** Items */
            items: components["schemas"]["SnapshotOutput"][];
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
        /**
         * ProviderCost
         * @description Like `PurposeCalls`, per provider. `calls_without_reported_cost` are left out of
         *     `reported_cost`.
         */
        ProviderCost: {
            /** Provider */
            provider: string;
            /** Calls */
            calls: number;
            /** Estimated Cost */
            estimated_cost: string;
            /** Reported Cost */
            reported_cost: string | null;
            /** Calls Without Reported Cost */
            calls_without_reported_cost: number;
        };
        /**
         * PurposeCalls
         * @description Paid calls for one purpose. `estimated_cost` is USD from the price list; `reported_cost`
         *     is what OpenRouter said it charged, summed over the calls it reported a cost for.
         */
        PurposeCalls: {
            purpose: components["schemas"]["AIPurpose"];
            /** Calls */
            calls: number;
            /** Input Tokens */
            input_tokens: number;
            /** Output Tokens */
            output_tokens: number;
            /** Estimated Cost */
            estimated_cost: string;
            /** Reported Cost */
            reported_cost: string | null;
        };
        /** RecordCounts */
        RecordCounts: {
            /** Created */
            created: number;
            /** Amended */
            amended: number;
        };
        /**
         * RemovedDocument
         * @description A document whose webpage first returned 404 in the run.
         */
        RemovedDocument: {
            /**
             * Document Id
             * Format: uuid
             */
            document_id: string;
            /** Url */
            url: string;
            /** Title */
            title: string | null;
            /**
             * Missing Since
             * Format: date-time
             */
            missing_since: string;
        };
        /**
         * RunCounts
         * @description What the run's fetch log and ledger say so far. `skipped` is every `skipped_*` outcome,
         *     `failed` every `failed_*`, `not_modified` includes `unchanged`.
         */
        RunCounts: {
            /** Fetched */
            fetched: number;
            /** Not Modified */
            not_modified: number;
            /** Skipped */
            skipped: number;
            /** Blocked */
            blocked: number;
            /** Failed */
            failed: number;
            /** Snapshots */
            snapshots: number;
            /** Cost */
            cost: string;
        };
        /**
         * RunCreate
         * @description A run started from the dashboard; only full runs exist until sources do.
         */
        RunCreate: {
            /**
             * Institution Id
             * Format: uuid
             */
            institution_id: string;
            /**
             * Mode
             * @default full
             * @constant
             */
            mode: "full";
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
            /** Elapsed Seconds */
            elapsed_seconds: number | null;
            counts: components["schemas"]["RunCounts"];
        };
        /**
         * RunReport
         * @description A run's numbers, each a query over the logs. `elapsed_seconds` is null until the run has
         *     finished. `records`, `unextracted_document_ids` and `fallback_reasons_by_source` have been
         *     given since extraction (023); they stay nullable so the client's types are unchanged.
         */
        RunReport: {
            run: components["schemas"]["RunOutput"];
            /** Elapsed Seconds */
            elapsed_seconds: number | null;
            /** Requests Sent */
            requests_sent: number;
            /** Fetches By Outcome */
            fetches_by_outcome: components["schemas"]["OutcomeCount"][];
            /** Snapshots Written */
            snapshots_written: number;
            /** Files Processed */
            files_processed: number;
            /** Files Failed */
            files_failed: number;
            /** Files Parsing */
            files_parsing: number;
            /** Documents New */
            documents_new: number;
            /** Documents Changed */
            documents_changed: number;
            records: components["schemas"]["RecordCounts"] | null;
            /** Paid Calls */
            paid_calls: number;
            /** Estimated Cost */
            estimated_cost: string;
            /** Reported Cost */
            reported_cost: string | null;
            /** Calls By Purpose */
            calls_by_purpose: components["schemas"]["PurposeCalls"][];
            /** Cost By Provider */
            cost_by_provider: components["schemas"]["ProviderCost"][];
            /** Removed Documents */
            removed_documents: components["schemas"]["RemovedDocument"][];
            /** Unextracted Document Ids */
            unextracted_document_ids: string[] | null;
            /** Fallback Reasons By Source */
            fallback_reasons_by_source: {
                [key: string]: {
                    [key: string]: number;
                };
            } | null;
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
            /** Extractors */
            extractors?: {
                [key: string]: string;
            } | null;
            /** Replay */
            replay?: string | null;
            /** Cutoff */
            cutoff?: string | null;
        };
        /**
         * RunStatus
         * @enum {string}
         */
        RunStatus: "queued" | "running" | "finished" | "failed" | "cancelled";
        /**
         * SnapshotOutput
         * @description A stored copy of a webpage. Its text is at `GET /snapshots/{id}/text/{page}` once
         *     `text_status` is `ready`, and its bytes at `GET /snapshots/{id}/bytes`.
         */
        SnapshotOutput: {
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
            /** Content Hash */
            content_hash: string;
            /** Media Type */
            media_type: string;
            /** Size Bytes */
            size_bytes: number;
            text_status: components["schemas"]["TextStatus"];
            /** Text Error */
            text_error: string | null;
            /** Parser */
            parser: string | null;
            /** Stated Date */
            stated_date: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
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
        /**
         * TextStatus
         * @enum {string}
         */
        TextStatus: "parsing" | "ready" | "partial" | "failed" | "none";
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
        /**
         * WebpageOutput
         * @description A URL the crawler has seen, with every fetch of it (newest first) and its snapshots.
         */
        WebpageOutput: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Url */
            url: string;
            /** Domain */
            domain: string;
            /** Missing Since */
            missing_since: string | null;
            /** Fetches */
            fetches: components["schemas"]["FetchOutput"][];
            /** Snapshots */
            snapshots: components["schemas"]["SnapshotOutput"][];
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
export type DocumentOutput = components['schemas']['DocumentOutput'];
export type DocumentType = components['schemas']['DocumentType'];
export type DocumentTypeCount = components['schemas']['DocumentTypeCount'];
export type FetchOutcome = components['schemas']['FetchOutcome'];
export type FetchOutput = components['schemas']['FetchOutput'];
export type HttpValidationError = components['schemas']['HTTPValidationError'];
export type Health = components['schemas']['Health'];
export type InstitutionInput = components['schemas']['InstitutionInput'];
export type InstitutionOutput = components['schemas']['InstitutionOutput'];
export type InstitutionType = components['schemas']['InstitutionType'];
export type LastRun = components['schemas']['LastRun'];
export type OutcomeCount = components['schemas']['OutcomeCount'];
export type PageAiCallOutput = components['schemas']['Page_AICallOutput_'];
export type PageDocumentOutput = components['schemas']['Page_DocumentOutput_'];
export type PageFetchOutput = components['schemas']['Page_FetchOutput_'];
export type PageInstitutionOutput = components['schemas']['Page_InstitutionOutput_'];
export type PageRunOutput = components['schemas']['Page_RunOutput_'];
export type PageSnapshotOutput = components['schemas']['Page_SnapshotOutput_'];
export type PageSourceOutput = components['schemas']['Page_SourceOutput_'];
export type ProviderCost = components['schemas']['ProviderCost'];
export type PurposeCalls = components['schemas']['PurposeCalls'];
export type RecordCounts = components['schemas']['RecordCounts'];
export type RemovedDocument = components['schemas']['RemovedDocument'];
export type RunCounts = components['schemas']['RunCounts'];
export type RunCreate = components['schemas']['RunCreate'];
export type RunOutput = components['schemas']['RunOutput'];
export type RunReport = components['schemas']['RunReport'];
export type RunSettings = components['schemas']['RunSettings'];
export type RunStatus = components['schemas']['RunStatus'];
export type SnapshotOutput = components['schemas']['SnapshotOutput'];
export type SnapshotSummary = components['schemas']['SnapshotSummary'];
export type SourceOutput = components['schemas']['SourceOutput'];
export type TextStatus = components['schemas']['TextStatus'];
export type ValidationError = components['schemas']['ValidationError'];
export type WebpageOutput = components['schemas']['WebpageOutput'];
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
    "institutions-list_institutions": {
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
                    "application/json": components["schemas"]["Page_InstitutionOutput_"];
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
    "institutions-create_institution": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InstitutionInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InstitutionOutput"];
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
    "institutions-read_institution": {
        parameters: {
            query?: never;
            header?: never;
            path: {
                institution_id: string;
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
                    "application/json": components["schemas"]["InstitutionOutput"];
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
    "institutions-update_institution": {
        parameters: {
            query?: never;
            header?: never;
            path: {
                institution_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InstitutionInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InstitutionOutput"];
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
    "runs-create_run": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RunCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
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
    "runs-read_report": {
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
                    "application/json": components["schemas"]["RunReport"];
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
                outcome?: components["schemas"]["FetchOutcome"] | null;
                q?: string | null;
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
    "runs-list_snapshots": {
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
                    "application/json": components["schemas"]["Page_SnapshotOutput_"];
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
    "runs-list_run_documents": {
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
                    "application/json": components["schemas"]["Page_DocumentOutput_"];
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
    "snapshots-read_snapshot": {
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
                    "application/json": components["schemas"]["SnapshotOutput"];
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
    "webpages-read_webpage": {
        parameters: {
            query?: never;
            header?: never;
            path: {
                webpage_id: string;
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
                    "application/json": components["schemas"]["WebpageOutput"];
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
