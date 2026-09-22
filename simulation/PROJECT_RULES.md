# Project Rules

## Project Directory and Sample Separation

Confirmed on 2026-09-21. The project is named `simulation`.

- Store all finite-element calculation files under `simulation/FEA/`.
- Give every sample its own folder: `FEA/sample 1/`, `FEA/sample 2/`, etc. Keep the sample's code, raw data, configuration, processed data, model inputs, solver results, logs and figures together within that sample folder, with separate subfolders by purpose.
- The current FEA chat belongs to `simulation/FEA/sample 1/`. New sample-specific files from this chat must be placed there.
- Do not mix samples' code/data/results or place sample-specific files at the project root or directly in `FEA/`. Create the appropriate sample folder before starting work on a new sample.
- Keep FEA work separate from `simulation/MD/`. Project-wide rules, README and the existing knowledge base stay at the `simulation/` root; identify each sample clearly in shared documentation.
- Use the actual directory names, including spaces, and quote paths in shell commands. Preserve sample-relative references inside frozen records.
- These rules govern placement of future work; they do not authorize deleting, moving, renaming or modifying existing files to reorganize them.

## File Safety

- Do not delete, move, rename, overwrite, truncate, or replace any existing file on the user's computer unless the user explicitly requests the exact action and target file.
- Do not modify source data files, experimental records, documents, images, simulation files, or software configuration files without explicit user approval.
- Treat all existing files as user-owned, including files created during earlier work.
- Do not run destructive commands such as recursive deletion, reset, clean, checkout, or force overwrite commands.
- Do not write temporary files outside the project workspace unless explicitly required and authorized.

## Analysis and Simulation Work

- Before creating code, simulation input decks, processed datasets, plots, or any other artifact, state what will be created and obtain the user's explicit approval.
- Keep raw experimental data unchanged. Any approved processed data must be saved as a new, clearly named file and must identify its source file and every processing operation.
- Do not assume missing material properties, boundary conditions, geometry, loading conditions, units, or solver settings. Record assumptions and request confirmation when they materially affect results.
- Do not run a solver, install software, download dependencies, or change the computing environment without explicit approval.

## Reporting

- Distinguish clearly between raw data, derived data, analytical estimates, dry-run checks, and validated simulation results.
- Report uncertainty, assumptions, and limitations directly.
- Do not describe a model, plot, or calculation as validated unless it has been checked against the relevant experiment.

## Current Project Scope

- Current topic: finite-element planning for impact loading of sample1.
- Existing experimental files must remain unchanged.
- The user will decide when code, processed files, simulation models, or solver runs are authorized.

## Documentation, Knowledge Base, and Code Comments

- Keep `KNOWLEDGE_BASE.md` current whenever a project fact, assumption, modelling decision, data-processing rule, solver choice, or output convention is confirmed or changed.
- Before creating approved code, add concise English comments where they explain a non-obvious decision, particularly units and conversions, data treatment, modelling assumptions, boundary/loading conditions, and output interpretation. Do not add comments that merely repeat self-evident code.
- Each newly created code file, or the project README that governs it, must state the following nine items before the code is treated as ready to run:
  1. Purpose and intended result.
  2. Inputs and outputs, including file formats and units.
  3. Prerequisites and modelling assumptions.
  4. Software requirements, versions, and run instructions.
  5. Key parameters, their physical meanings, units, and valid ranges.
  6. Data-processing rules.
  7. Result interpretation and sign/coordinate conventions where applicable.
  8. Author, creation date, and last-modified date.
  9. Related data files, documentation, rules, and literature sources.
- Update the relevant documentation when approved code or its inputs, outputs, or assumptions change.

## Project Structure and Traceability

- Read `AGENTS.md` and `README.md` together with this file before working in `FEA/`. `AGENTS.md` defines agent workflow and evidence boundaries; `README.md` states current capabilities and entry points.
- Separate raw source data, derived data, modelling decisions, solver decks, execution evidence, post-processing, and reports. A derived artifact must never replace or be stored as though it were a raw experimental record.
- Keep code split by responsibility. Data extraction, authorized preprocessing, material fitting, deck generation, solver launch, result parsing, plotting, and report writing must be independently reviewable files or modules with explicit handoffs.
- Do not create a catch-all script or document that both changes scientific input and interprets results. A script that writes data or launches a solver must state this behavior at its entry point and record its outputs.
- Store executable model parameters in their future solver/model inputs, modelling rationale in `KNOWLEDGE_BASE.md`, and actual run evidence in dedicated run directories. Do not create competing undocumented copies of solver settings.
- Preserve disagreements between existing documents as unresolved issues. Do not silently rewrite a historical note or select one assumption merely to make a model internally consistent.

## Execution Evidence and Verification

- Each approved solver run must use a new, explicit output directory and preserve the input deck, source-data references, solver version, command, logs, status, and result inventory.
- A Starter pass, Engine exit code, generated contour, or plot is not by itself a validated simulation result. Report input validity, numerical completion, contact/energy/mesh checks, and experimental agreement as separate findings.
- A failed or completed Run must remain intact. Any retry, changed input, longer duration, or modified solver setting creates a new Run rather than overwriting prior evidence.
