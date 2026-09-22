# Simulation Workspace

The project root is `simulation/` (user-confirmed reorganization, 2026-09-21). Finite-element work belongs in `FEA/`, with a separate folder for every sample; molecular-dynamics work belongs in `MD/`. Each polymer has an independent project folder in `MD/`, and each simulated temperature has an independent peer folder within it: for example, `MD/DEM-NVP/50 degree/` and a future `MD/DEM-NVP/10 degree/`. This FEA chat uses `FEA/sample 1/`. Unless explicitly qualified, the sample1 data/code/artifact paths below are relative to that sample folder. Project-wide rules and this README remain at the project root.

This project organizes finite-element planning, source-data inspection, and later OpenRadioss impact simulations for gel samples. The active case is `sample1`. The workspace contains raw records, derived material tables, and a candidate Starter/Engine input pair with local static checks. No OpenRadioss run or experimental model validation has been completed.

## What is currently available

| Area | Current state |
| --- | --- |
| Raw data | `sample1-compress.rtf` and `sample1-strain.rtf`; preserved as source records. |
| Derived analysis | `sample1_analysis/` contains raw-table extraction, user-authorized zeroed curves, a preflight audit, and an experimental-data plot. |
| Python utilities | Separate scripts extract data, perform approved preflight processing, and render plots. |
| Candidate model | `models/sample1/candidate_v001/`: frozen inputs for a 0.5 ms smoke test, not yet accepted by Linux Starter. |
| Solver | OpenRadioss is selected for the eventual workflow but is not available in this macOS workspace. Linux Starter/Engine checks remain pending. |
| Scientific status | No constitutive model has been calibrated and no FEA result has been validated against experiment. |

## Directory map

```text
simulation/
├── README.md                # This entry point and current capability boundary
├── AGENTS.md                # Agent, evidence, safety, and code-organization rules
├── PROJECT_RULES.md         # User-facing project safeguards and documentation requirements
├── KNOWLEDGE_BASE.md        # Confirmed facts, assumptions, decisions, and open questions
├── FEA/
│   ├── sample 1/            # Current chat's sample root
│   │   ├── sample1-*.rtf    # Raw experimental records
│   │   ├── config/
│   │   ├── derived/
│   │   ├── models/
│   │   ├── scripts/
│   │   ├── sample1_analysis/
│   │   └── *.py            # Existing sample1 utilities
│   └── sample 2/            # Separate sample2 code and data
└── MD/                     # Molecular-dynamics work; see MD/AGENTS.md
    └── <polymer-project>/  # One independent polymer system
        └── <temperature> degree/ # One independent temperature case
```

Future solver decks belong in a dedicated `models/` hierarchy and each execution in a separate `runs/<run_id>/` directory. Raw experimental records must never be mixed with solver output or overwritten by derived data.

## Current preparation utilities

`config/sample1_dryrun.json` is the canonical value record for candidate generation. The material fit and Linux server installation remain pending. Each generated model preserves its own frozen configuration and curve.

`scripts/prepare_sample1_material.py` reads the raw RTF tables and, only when invoked with `--write`, creates separate zeroed tensile/compression tables, a signed combined curve, and a provenance report. `scripts/validate_sample1_config.py` performs read-only checks of the configuration and reports fields that still prevent deck generation. Neither script calls a solver.

## Workflow and evidence levels

```text
Raw experiment files
        ↓  read-only extraction
Derived tables and documented preprocessing
        ↓  material-model review and deck preparation
Frozen solver model and bounded Starter/Engine check
        ↓  independent post-processing
Run evidence, comparison, and validation statement
```

Each level answers a different question. A curve plot does not validate a material law; a successful Starter check does not prove contact dynamics; a completed solver run does not establish agreement with an experiment.

## Current sample1 facts and open conflict

The available records identify a 20 mm × 20 mm × 1 mm sample, density 1.1 g/cm³, Poisson ratio 0.49, a 20 g steel spherical impactor concept, and tensile/compression data in MPa and mm/mm. The selected solver is OpenRadioss.

The confirmed support condition is a sample bonded over its entire bottom face to a hard substrate. The earlier four-edge-clamped, center-unsupported condition in `sample1_analysis/sample1-preflight.md` is a superseded preliminary assumption and must not be used for solver inputs.

## Working rules

Read `AGENTS.md`, `PROJECT_RULES.md`, and `KNOWLEDGE_BASE.md` before work on this project. Raw files stay unchanged. Every derived output must identify its inputs, units, transformations, and limitations. Data extraction, curve processing, model/deck creation, execution, result analysis, plotting, and reporting remain separate scripts or modules so that each step can be reviewed independently.

## Intended next milestones

1. Identify the Linux environment and install a selected OpenRadioss release when authorized.
2. Run Starter on a copy of the candidate in a new run directory; review LAW69 fitting and warnings before Engine execution.
3. Run the bounded 0.5 ms Engine smoke test; check contact, deformation and output availability.
4. Extend the time window only if the first compression maximum is not captured, and reduce speed if the thickness limit is exceeded.
5. Check material response, mesh/contact sensitivity and output sampling before preparing production figures.

These milestones are planning guidance only. They do not authorize preprocessing, model generation, solver installation, or solver execution.

## Candidate generation and local checks

Author: Codex. Created: 2026-09-20; directory instructions updated: 2026-09-21. Python 3.9 or newer, standard library only. No additional packages or solver are needed for these local commands. Run from the `simulation/` project root; quote the sample folder name:

```sh
python3 -B "FEA/sample 1/scripts/build_sample1_candidate.py"
python3 -B "FEA/sample 1/scripts/build_sample1_candidate.py" --write
python3 -B "FEA/sample 1/scripts/check_sample1_candidate.py"
```

The first command previews in memory. The second creates `models/sample1/candidate_v001/` inside the sample root and deliberately fails if that directory already exists. For an authorized revision, use `--output-dir` with a new directory under `FEA/sample 1/models/`. The third command reads the frozen candidate and prints checks without writing. An optional `--report` path creates a new JSON report exclusively; it cannot overwrite a report. Existing frozen provenance keeps its sample-relative paths. No scripts or frozen artifacts were rewritten during the documentation update.

| File | Responsibility |
| --- | --- |
| `scripts/build_sample1_candidate.py` | Build mesh, serialize fixed-width cards, freeze config/curve and record hashes; never run a solver. |
| `scripts/check_sample1_candidate.py` | Independently parse the emitted subset of cards and check geometry, references and provenance. |
| `models/sample1/candidate_v001/sample1_smoke_0000.rad` | Candidate Starter definition: geometry, materials, constraints, contact and histories. |
| `models/sample1/candidate_v001/sample1_smoke_0001.rad` | Candidate Engine controls: physical end time and output sampling. |
| `models/sample1/candidate_v001/frozen_config.json` | Values used to build this candidate; future config edits do not update this snapshot. |
| `models/sample1/candidate_v001/material_curve.csv` | Byte-for-byte copy of the approved compression calibration table. |
| `models/sample1/candidate_v001/model_manifest.json` | Source/artifact SHA256, mesh counts, ball inertia and evidence limitations. |
| `models/sample1/candidate_v001/static_check_report.json` | Local static-check result; this is not a Starter log. |

Inputs and units: JSON case configuration and an 81-point engineering compression CSV in mm/mm and MPa. Generated decks use mm, s, tonne (`Mg` in the unit cards), N and MPa. No additional smoothing, offset removal, extrapolation or local constitutive fitting occurs in deck generation. The approved preprocessing history remains in `derived/sample1_material/`.

The gel has 2,304 HA8 bricks, 3,125 nodes and a full bottom translational constraint. HA8 uses total strain and constant-pressure integration for the near-incompressible material. The rigid ball is a surface carrier with 1,536 quadrilaterals, plus its independent center node. `/RBODY` overrides carrier mass/inertia with the exact 20 g and solid-sphere inertia; it does not represent a hollow physical ball. Nominal steel elasticity and carrier thickness are numerical contact inputs, not additional gel measurements. All ball DOFs are free with initial motion along negative z.

Numerical choices are recorded in `candidate_numerics`: LAW69 Ogden with two parameter pairs and `Icheck=-3`; TYPE7 with gel top nodes as secondary, ball surface as main, minimum-side stiffness and friction zero. The initial geometric clearance is 0.10 mm; the constant numerical contact gap is 0.025 mm. Contact can therefore activate before geometric touching (about 0.0379 ms on the impact axis at the initial speed). Set time-after-contact from the computed force onset, not from the nominal flight estimate. TYPE7 stability and gap/stiffness sensitivity remain Linux checks.

The 0.5 ms impact window omits gravity after assigning the drop-equivalent velocity. This approximation, rigid substrate, perfect bond and rate-independent gel response are explicit assumptions. Default-style solid bulk viscosity and normal contact damping are recorded numerical terms; they must not be interpreted as measured material dissipation. There is no mass scaling, erosion, failure law or fitted physical viscosity.

History sampling is 1 microsecond; animations are requested every 5 microseconds. These are output intervals, not imposed integration time steps. Native animation files request displacement, velocity, contact force vectors, von Mises stress, stress/strain tensors and density. Time histories request interface normal-force components, ball center motion, centerline gel top/bottom motion and gel energy diagnostics. Native results will require conversion/reading on Linux before local figure generation; no post-processing program has been run or delivered at this stage.

Interpretation: define compressive contact force positive on the ball along +z, verifying the sign of interface `FNZ` against ball `mass * AZ` in the gravity-free window. Preserve raw signed components. Find the first post-contact minimum of ball z using its motion history, then select/refine the corresponding animation time. The front view looks along -z and the section is at y=10 mm. Von Mises output is based on the computed Cauchy stress; the fitting input is engineering stress. Sampling may need refinement for the eventual peak figure.

The 40% thickness criterion is an acceptance limit, not an implemented automatic termination or displacement constraint. Monitor centerline thickness using the paired nodes and inspect the entire deformed top surface beneath the ball in the animation data. Reject any run with local thickness below 0.60 mm; no static check can guarantee compliance. A 0.5 ms run may also end before the first maximum. Neither such a run nor this coarse mesh supports final thesis figures.

Local verification checks the serialized cards, positive Jacobians at all eight Gauss points of every gel brick, volume/mass, bottom/top node groups, sphere radius/orientation/closed topology, rigid mass override, unit cards, references, curve preservation and output requests. Source hashes also detect changes since generation. The checker is scoped to this candidate, not a complete Radioss syntax parser. Separate in-memory negative checks verify rejection of inverted bricks, wrong units, missing constraints/force output, wrong end time and duplicate nodes.

Input format 2022 is a candidate compatibility target, not a claim about the eventual installed OpenRadioss version. Before Engine execution, Starter must accept the keywords, confirm the rigid mass and report an acceptable LAW69 fit (review the fitted curve and stability as well as the documented 10% average-error guidance). Read the project-root `AGENTS.md` for directory routing, safety and evidence rules.

Official keyword references consulted on 2026-09-20:

- [LAW69 fitting and stability](https://2024.help.altair.com/2024/hwsolvers/rad/topics/solvers/rad/mat_law69_starter_r.htm)
- [Solid property and strain/pressure formulations](https://2022.help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/prop_type14_solid_starter_r.htm)
- [TYPE7 contact fields and limitations](https://2022.help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm)
- [Rigid-body mass and inertia controls](https://2025.help.altair.com/2025.1/hwsolvers/rad/topics/solvers/rad/rbody_starter_r.htm)
- [Boundary-condition field layout](https://2022.help.altair.com/2022.1/hwsolvers/rad/topics/solvers/rad/bcs_starter_r.htm)
- [Interface force histories](https://2022.help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/th_inter_starter_r.htm)
- [Node histories](https://2022.help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm)
- [Brick animation results](https://2022.help.altair.com/2022.2/hwsolvers/rad/topics/solvers/rad/anim_brick_restype_engine_r.htm)
