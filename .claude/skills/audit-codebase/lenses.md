# Audit lenses

Apply each lens that fits the code. The linters already enforce formatting, function complexity, argument counts, and magic numbers; look for what they can't see.

## Delete, don't move

- Is there a reframing ("code judo") where whole branches, modes, flags, helpers, or layers disappear? Prefer it to any local cleanup.
- Would the code look like this if today's requirements had been known from the start, or were features bolted on one branch at a time?
- A proposed refactor that leaves the reader holding the same number of concepts is not an improvement.

## Depth

- **Shallow module**: an interface nearly as complex as its implementation, where callers must coordinate several calls to do one thing or pass options that expose internal stages.
- **Pass-through**: a function, wrapper, or layer that forwards the same arguments to something of the same shape, or a wrapper with one caller. Inline it.
- **Hypothetical seam**: an interface, protocol, or adapter with one implementation and no second in sight. One adapter is a hypothetical seam; two make it real.
- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If it reappears across many callers, the module earns its keep.

## Ownership and leakage

- **Information leakage**: the same representation, policy, or protocol detail in several modules, so changing it needs coordinated edits. Wire, ORM, or framework types escaping into domain code.
- **Split ownership**: more than one module writes the same state or keeps its own copy. Give state one owner.
- **Hand-synced lists**: the same items listed in several places (enum and map, route table and menu, schema and validator). Derive the others from one, or make the build fail when they disagree.
- **Importable internals**: callers reaching into another module's private parts because nothing stops them.
- **Wrong layer**: feature-specific logic in a shared path; business rules in route handlers or components; a bespoke helper where the codebase has a canonical one.
- **Temporal decomposition**: modules split by execution order (load, validate, transform, save) that each repeat the same knowledge, instead of grouped by the knowledge they own.

## Two ways to do one task

- Two helpers, two clients, two patterns, or an old path and a new path that both stay alive. Agents copy whichever they find first, so both keep growing. Keep one, migrate the callers, delete the other.
- Leftover compatibility shims, deprecated aliases, or feature flags from migrations that finished.

## Branching growth

- Special cases bolted into unrelated flows; boolean parameters or nullable "modes" that fork a function.
- The same condition checked in several places means a missing model: a typed variant, an explicit dispatcher, a state machine, or a policy object.

## Types and boundaries

- Casts, `Any`/`any`, `unknown`, `# type: ignore`, and needless optionality that hide the real contract.
- Loose dicts and ad-hoc object shapes where a named type belongs.
- Validation scattered through the code instead of done once where the data enters.
- Silent fallbacks (`or default`, `?? fallback`, `?.`) papering over an invariant nobody stated.

## Reader load

- **Layers to trace**: how many hops from a question ("where does X come from?") to its answer?
- **State to hold**: mutable module state, long-lived fields, and values synced by hand instead of derived.
- The test: can a new reader answer "where does X come from?" and "what can change X?" in under a minute?
- Files over ~500 lines holding more than one concern; over 1,000 lines almost always need splitting.

## Errors and atomicity

- Swallowed or re-wrapped errors that lose the cause; broad catches.
- Related updates that can leave state half-applied when a transaction or a single write would make them atomic.
- Independent async work run in sequence for no reason, when running it concurrently would also simplify the flow.

## Dead weight

- Unused exports, parameters, config, flags, and branches; code reachable only from tests.
- Comments and docstrings that narrate code, restate a signature, have gone stale, or describe history; `TODO`s that will never be done.
- A comment explaining surprising code of our own: the finding is the reshape (rename, extract, type) that makes the comment unnecessary. Comments about things we can't change (a library quirk, a protocol, a vendor limit) stay.
- `do not remove` or `IMPORTANT` warnings and lint or type suppressions: each is a rule a test, type, or lint could enforce, or a workaround hiding a root cause.

## Tests as a design signal

- Code that is hard to test through its public interface usually has the wrong shape. The interface should be the test surface.
- Tests that mock the project's own modules or reach past the interface point to a missing seam or a tangled module.
- Areas with high churn and no tests are a risk to note on any candidate there, since a refactor needs behavior pinned first.

## Encode the fix

When the same smell shows up three or more times, the finding is the missing rule, not each instance: propose the lint rule, type, or architecture test that makes it impossible, alongside the cleanup.
