# Impact FEA Knowledge Base

Last updated: 2026-09-21.

## Project relocation and sample folders (2026-09-21)

The user renamed the project folder to `simulation` and reorganized finite-element files into `FEA/sample 1/` and `FEA/sample 2/`. The current chat's sample root is `/Users/mac/Documents/ChatGPT/计算/simulation/FEA/sample 1/`. All new sample1 code, data and artifacts belong there. Each future FEA sample must have its own folder under `FEA/`; never mix sample code, input data or results. Molecular-dynamics work is kept separately under `MD/`.

Project-wide `AGENTS.md`, `PROJECT_RULES.md`, `README.md` and this knowledge base remain at the `simulation/` root. Unless a path explicitly starts with `FEA/` or refers to those project-wide documents, the sample1 paths in the earlier entries below are relative to `FEA/sample 1/`. The directory move does not invalidate those sample-relative provenance paths. The 2026-09-21 task updated documentation only; existing scripts, raw data, candidate decks and historical reports were not moved or edited.

## Purpose

This document records agreed facts, assumptions, units, and decisions for the gel-impact finite-element analysis. Update it when a modelling decision is confirmed; do not use it to replace raw experimental data.

## Evidence and project organization

`README.md` is the current entry point and capability statement. `AGENTS.md` governs agent work, authorization, source protection, and verification. `PROJECT_RULES.md` remains the user-facing safety and documentation contract. Raw experimental records, derived analyses, executable solver inputs, actual solver runs, and reports have different roles and must remain separate.

Use the following evidence labels in notes and reports:

| Label | Meaning |
| --- | --- |
| Raw experimental fact | Directly present in an unmodified experiment record or a user-confirmed measurement. |
| Derived analysis | A documented transformation or calculation from a source record; it does not replace the source. |
| Modelling assumption | A chosen idealization or numerical setting that still requires review or validation. |
| Dry-run / preflight result | A data, geometry, or input check that has not run the intended contact simulation. |
| Solver result | Output from a frozen, identified solver Run; numerical completion and scientific validation are reported separately. |

The physical support condition has been confirmed by the user: the specimen is bonded over its full bottom face to a hard substrate. The earlier four-edge-clamped, centre-unsupported description in `sample1_analysis/sample1-preflight.md` is a superseded preliminary assumption, retained only as historical derived analysis and not to be used for solver inputs.

For future solver work, keep deck values in a frozen model/input directory and keep solver logs, checkpoints, outputs, and run metadata in a new dedicated Run directory. A completed Starter/Engine process, contour, or plot is not by itself experimental validation.

## Project objective

Compare crystalline control and test samples that differ in mechanical response. The primary deliverables are, for each sample at its first maximum compression displacement:

- Front-view stress contour.
- Mid-plane section stress contour.
- Ball–sample contact-force history, `F(t)`.

The first study concerns **sample1**. This is a controlled, non-penetrating simulation intended to keep material deformation below the specified limit; it is not yet a validated reproduction of a physical drop test.

## Available material data

| Item | Sample1 value or source | Notes |
| --- | --- | --- |
| Compression curve | `sample1-compress.rtf` | Nominal compression rate: 5 mm/s; engineering stress is in MPa and engineering strain is in mm/mm. |
| Tension curve | `sample1-strain.rtf` | Nominal tensile rate: 10 mm/s; engineering stress is in MPa and engineering strain is in mm/mm. |
| Density | 1.1 g/cm³ | Must be converted consistently with the solver unit system. |
| Poisson's ratio | 0.49 | Near-incompressible behaviour; element formulation must be checked for volumetric locking. |

### Experimental-data rule

The force/stress offsets at the beginning of the tensile and compression records are attributed to the instrument not being zeroed. Any processing may subtract the initial offset, but raw `.rtf` files must remain unchanged. The method and the newly created output file must be recorded before use in a simulation.

## Geometry and support condition

| Component | Current specification |
| --- | --- |
| Sample | 20 mm × 20 mm × 1 mm |
| Support | Sample bonded to a hard substrate; the earlier suspended, four-edge-clamped arrangement is superseded |
| Bond | Full bottom-face bond to the hard substrate; sample lift-off is excluded |
| Impactor | Solid steel sphere, mass 20 g |
| Steel-sphere diameter | Approximately 16.95 mm, calculated using a nominal steel density of 7.85 g/cm³; confirm the actual ball before final modelling. |
| Proposed physical drop height | 0.20 m |
| Corresponding ideal contact speed | About 1.98 m/s, if air resistance is neglected. |

Confirmed minimal idealization: a stationary rigid substrate and a perfect bond over the entire sample bottom face. Under this idealization, constrain all three displacement components of the bottom-face nodes; an explicit substrate mesh is unnecessary. This assumes negligible substrate and adhesive deformation and no debonding. Do not retain the former side-edge clamps. The steel ball may still rebound; preventing sample lift-off does not constrain ball motion.

## Simulation strategy

1. Prepare the material data, model inputs, and static checks on macOS.
2. Run OpenRadioss Starter checks and a short dynamic Engine smoke test on Linux, covering actual ball–sample contact with the same material, support, and loading definitions intended for production.
3. Use explicit dynamic impact for the intended drop-impact analysis and force history; controlled indentation is only an optional preliminary check.
4. Define the 40% deformation limit as a maximum 40% local thickness compression beneath the ball: the local thickness must remain at or above 0.60 mm from its initial 1.00 mm. Also monitor local principal strain as a diagnostic, but do not use it as the pass/fail definition.
5. Begin the first dynamic trial from a nominal 0.20 m drop, represented by an ideal initial ball speed of about 1.98 m/s at first contact. If the trial exceeds the thickness-compression limit, reduce the height and report the final adopted height in the model record and paper.

A model started at contact with zero initial velocity does **not** represent a 0.20 m drop unless gravity and the preceding fall are included.

### Confirmed smoke-test mesh

The Linux smoke test will use a structured 8-node hexahedral mesh with 24 × 24 × 4 elements (2,304 total). The in-plane element size is 0.8333 mm and the through-thickness element size is 0.25 mm. This is the sparsest approved mesh intended to exercise the Starter, Engine, ball–sample contact, force-history extraction, and requested contour-output chain. It is not a thesis-result mesh: any production contour or force-history result still requires a finer mesh and a documented mesh-sensitivity study.

### Confirmed ball initial placement

For the smoke model, the sphere bottom will start 0.10 mm above the sample top surface. Its initial velocity is 1,980.57 mm/s along negative z, which represents the ideal speed at first contact for the nominal 0.20 m drop. The small positive gap prevents an initial contact overlap; it is not part of the physical free-fall distance.

## Confirmed first material-model route

The first model will use a compression-priority `/MAT/LAW69` calibration. Its candidate input covers only the measured 0–40% engineering compression range, represented in Radioss sign convention as engineering strain and stress increasing from negative compression to zero. The raw curve remains unchanged. The candidate calibration table will use documented isotonic monotonic regression to remove only local stress reversals, followed by uniform 0.005 strain resampling. It is an equivalent, rate-independent modelling assumption for compression-dominated impact; it is not validated for tension, unloading, or strain-rate effects.

No LAW69 material parameters, Starter fit error, or solver result currently exists. Do not generate a production deck until the Linux Starter has checked the candidate curve and reported an acceptable fit.

## Confirmed output convention

Record the following explicitly in each run note:

- Contact: frictionless ball–sample contact for the first model.
- Snapshot criterion: each sample's first maximum compression displacement; record the corresponding time after first contact.
- Views: front view and a mid-plane section through the impact centre.
- Stress measure: von Mises stress in MPa; use one fixed contour range when comparing samples.
- Contact-force sign convention and units: record in each run manifest.

## Solver status

**Selected solver: OpenRadioss.** The formal analysis chain will use the same OpenRadioss version on a Linux server for Starter checks, Engine smoke tests, and production runs. This decision avoids mixing results from different solvers.

OpenRadioss was not found as a runnable solver in the current macOS working environment. The official prebuilt packages are for Linux and Windows, so a genuine OpenRadioss smoke test must run on the Linux server (or in a separately installed Linux environment). macOS will be used for input preparation, non-solver static checks, documentation, and result post-processing.

The project team will install OpenRadioss on the Linux server later. The version, installation path, and server launch/scheduler configuration remain pending; no installation is currently authorized by this planning decision.

## File-safety rule

Read and follow [PROJECT_RULES.md](PROJECT_RULES.md). In particular, do not delete, rename, move, overwrite, or modify existing files without the user's explicit instruction.

## Open questions

- The comparison sample's density, Poisson's ratio, and tensile/compression curves.
- The method for measuring local thickness compression from solver output and, if applicable, from experiments.
- OpenRadioss version, installation path, and launch/scheduler configuration on the Linux server.

## Candidate preparation authorized on 2026-09-20

The user authorized candidate input preparation and local static checks after selecting a 0.5 ms first smoke duration. The earlier 5 ms proposal is superseded. Candidate values are in `config/sample1_dryrun.json`; each model directory freezes these values and the approved compression table. This authorization does not install or execute OpenRadioss.

Implementation choices: LAW69 Ogden with two parameter pairs, `Icheck=-3`; HA8 solid elements with total-strain and constant-pressure formulation; a rigid quadrilateral sphere surface whose carrier mass is overridden by the measured ball mass and solid-sphere inertia. Steel elasticity and shell carrier thickness are nominal numerical inputs. TYPE7 uses gel top nodes against the rigid ball main surface and minimum-side stiffness. The numerical contact gap is distinct from the confirmed initial geometric clearance. The earlier statement that the geometric clearance alone resolves TYPE7 small-gap concerns was too strong; stability and contact-parameter sensitivity remain unverified.

The initial velocity is applied to all ball nodes including its center. Gravity is omitted over the short impact window; no mass scaling, physical viscosity or failure law is introduced. Numerical bulk viscosity and contact damping must not be reported as gel energy dissipation. A compression-only hyperelastic fit cannot establish damping performance or loading-rate dependence.

The candidate requests force histories and animation quantities needed for the proposed figures. The first maximum must be found after computed contact onset and may not occur before the smoke run ends. The 40% local thickness limit remains a rejection criterion, with centerline histories and full-field geometry available for later checking; it is not an automatic solver stop. Production use requires material-fit review, local thickness checks, contact/energy checks and mesh/output-time sensitivity.

Local scripts check source hashes and re-parse the emitted candidate to inspect mesh topology, all gel Gauss-point Jacobians, dimensions, mass, constraints, material references, contact settings and output requests. Local success is only preflight evidence. There are still no fitted LAW69 parameters, Linux Starter logs, Engine results or stress contours.

Preflight result (2026-09-20): `models/sample1/candidate_v001/static_check_report.json` records a pass with no static errors and explicit solver-pending warnings. The re-read gel volume is 400 mm^3, gel mass 0.44 g and rigid ball mass 20 g; all 18,432 gel Gauss-point Jacobians are positive, and all 625 bottom nodes are constrained. Six separate in-memory corruption checks were rejected as expected (inverted brick, wrong units, missing bottom constraint, missing force output, wrong end time and duplicate node). These checks do not certify the full Radioss grammar or the constitutive fit.
