# Simulation Project Agent Guide

## Directory routing and sample isolation

Confirmed by the user on 2026-09-21:

- The project root is `simulation/`. Project-wide instructions remain in `simulation/AGENTS.md` and `simulation/PROJECT_RULES.md`.
- All finite-element work belongs under `simulation/FEA/`. Molecular-dynamics work belongs under `simulation/MD/`; do not mix these workflows. The FEA-specific instructions below apply to finite-element work.
- Create a separate directory for each FEA sample, following the existing names `FEA/sample 1/`, `FEA/sample 2/`, and so on. Preserve the spaces in these directory names.
- This chat is assigned to `simulation/FEA/sample 1/`. Place its sample-specific code, input data, configuration, derived data, candidate decks, runs, logs, figures and notes inside that directory.
- Keep each sample's `scripts/`, `config/`, `derived/`, `models/`, `runs/` and analysis outputs inside its own directory as needed. Do not put sample-specific files directly in `simulation/` or `FEA/`, or reuse another sample's output directory. Never write into another sample directory merely because a script defaults to it.
- Project-wide rules and the existing project knowledge base are the exception to sample-local storage. Label sample-specific knowledge-base entries with their sample identity. Do not introduce shared code/data folders without an explicit project decision.
- Resolve sample paths from the actual script location or an explicit sample-root parameter; quote shell paths containing spaces. In sample scripts, a historical `PROJECT_ROOT` or `ROOT` variable may refer to the sample root, not `simulation/`.
- Existing relative paths in frozen manifests remain relative to their original sample root. Do not rewrite frozen decks, provenance or historical reports just to update the project name. This organization rule does not authorize moving, deleting or rewriting existing user files.

## Purpose and current boundary

The FEA workspace supports traceable finite-element planning and post-processing for impact tests on soft gel samples. The current chat's active case is `sample1`, stored in `FEA/sample 1/`. It contains experimental records, derived analysis, preparation scripts and candidate OpenRadioss inputs with local static checks. No solver run or validated impact result exists yet.

Scientific traceability, preservation of source data, and a clear distinction between evidence types take priority over implementation speed or brevity.

## Read before acting

- Read the project-root `README.md`, `PROJECT_RULES.md`, `KNOWLEDGE_BASE.md`, and the documents closest to the target files before editing or executing a task. Apply any more specific `AGENTS.md` in the target subtree as well.
- Treat raw experiment files, solver input decks, result files, and historical reports as user-owned sources. Do not infer their meaning from filenames alone.
- Identify whether a statement is a raw experimental fact, derived analysis, modelling assumption, dry-run or solver result, or an untested hypothesis.
- If documents disagree, preserve the conflict and cite its locations. Do not silently select one version or rewrite earlier evidence to make it consistent.

## Project layout and ownership

| Location | Responsibility |
| --- | --- |
| `README.md` | Actual project entry points, supported workflow, current limits, and how to use the workspace. |
| `AGENTS.md` | Rules for agent work, authorization, source protection, evidence, and verification. |
| `PROJECT_RULES.md` | Stable user-facing safety and documentation requirements. |
| `KNOWLEDGE_BASE.md` | Confirmed facts, modelling decisions, unresolved questions, and evidence boundaries. |
| `FEA/sample N/` | One sample's raw data, code and artifacts; never mix samples. |
| `FEA/sample N/sample*_analysis/` | Derived artifacts for that sample; never a replacement for raw experiment records. |
| `FEA/sample N/analyze_*.py` | Existing source-data extraction and numerical summary scripts. |
| `FEA/sample N/prepare_*.py` | Existing authorized preprocessing or preflight scripts. |
| `FEA/sample N/plot_*.py` | Existing rendering utilities; identify experimental, derived or solver data. |
| `FEA/sample N/scripts/` | New sample-specific utilities, split by responsibility. |
| `FEA/sample N/models/` | Solver decks and frozen material/geometry/contact definitions. |
| `FEA/sample N/runs/` | Solver outputs, logs, checkpoints and manifests in separate run directories. |

Do not create one all-purpose script or one all-purpose document for ingestion, data processing, constitutive fitting, deck generation, solver execution, result extraction, plotting, and reporting. Split work by stable responsibility and make the handoff between files explicit.

## Code and document boundaries

- One module or script should have one primary responsibility. Reuse shared routines only when the input and output contract is truly common; do not create speculative framework layers.
- Keep data extraction, baseline correction, curve fitting, model/deck generation, solver launch, result parsing, plotting, and report generation independently inspectable.
- A script must state its purpose, input files and units, output files and units, assumptions, processing steps, and whether it can change state or call a solver.
- Use explicit paths relative to the project root through `pathlib.Path`; do not depend on an arbitrary shell working directory.
- Keep units in field names, table columns, plot axes, and exported values. Record sign, coordinate, strain, stress, and contact-force conventions where they apply.
- Do not add a new dependency, install software, or change the solver environment without explicit user authorization.

## Scientific input and evidence

- Keep raw data unchanged. Derived data must retain source paths, source hashes where practical, units, and every transformation applied.
- Do not silently smooth, offset-correct, clip, interpolate, extrapolate, change units, or remove data points. Each operation requires an explicit record and a new output artifact.
- Keep material identity, specimen geometry, boundary/support conditions, impactor definition, contact settings, constitutive model, numerical protocol, and output requests separate. A valid deck does not prove that the model is physically appropriate.
- Maintain one canonical location for each type of information: modelling explanations in `KNOWLEDGE_BASE.md`; executable values in a future model/deck; actual execution evidence in its Run directory. Do not maintain competing copies of solver parameters in narrative documents.
- Do not label a result as validated because a solver completed. Report engineering completion, numerical checks, mesh/contact checks, sampling or convergence evidence, and experimental agreement separately.

## Runs, results, and recovery

- New solver runs require an explicit, new output directory that contains the frozen input deck, material data reference, software/version record, command, timestamps, and result inventory.
- Never overwrite a completed or failed run to retry it. Create a new run ID and record the parent input or prior run.
- A log file, output file, or zero exit code alone is insufficient evidence of a successful simulation. Check the requested termination state, numerical warnings, contact behavior, energy balance where applicable, and the actual output time or increment.
- Keep preprocessing, solver outputs, and post-processing outputs separate. A post-processing failure does not authorize rerunning or modifying the solver model.
- Archive or move run evidence only with explicit authorization and a verified inventory. Git history, if introduced later, is not a replacement for simulation-data backup.

## Authorization and safety

- Requests to explain, review, design, inspect, or diagnose authorize read-only work only.
- Before modifying a file, state the exact target and intended change. A request to update documentation authorizes only the requested documentation changes.
- Creating a model, processing raw data, generating a solver deck, running a solver, installing dependencies, downloading data, changing a global environment, or overwriting formal outputs each require explicit authorization.
- Preserve unrelated user changes. Never delete, rename, move, truncate, reset, clean, force-overwrite, or replace user files without exact authorization.

## Verification and handoff

- Use the smallest verification sufficient for the change. For documentation, check referenced paths, commands, units, and claims against current files.
- For changes to a processing script, run a relevant non-destructive check using isolated output only when authorized. For deck or solver changes, verify the deck and use a bounded solver smoke test only when authorized.
- At handoff, state what changed, what evidence was consulted, which checks ran, what did not run, and the remaining scientific limitations.
