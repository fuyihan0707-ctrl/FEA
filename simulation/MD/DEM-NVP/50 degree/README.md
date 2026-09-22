# DEM–NVP alternating copolymer in water, 50 °C

**Author:** Codex. **Created / last updated:** 2026-09-21.

## Purpose and intended result

This project prepares a low-cost, non-crosslinked aqueous simulation of four neutral, strictly alternating `[DEM-NVP]10` chains at 323.15 K (50 °C). It is intended to screen high-temperature dehydration, chain compaction, and interchain association. It cannot by itself establish the experimental LCST, phase boundary, optical whiteness, or macroscopic coexistence.

## Physical model and key parameters

| Parameter | Value | Meaning and valid use |
| --- | ---: | --- |
| Polymer sequence | `[DEM-NVP]10` | 20 structural units per chain; strict alternation. |
| Chain count | 4 | The smallest multichain system that can report interchain association. |
| Polymer mass fraction | 0.60 | `m_polymer / (m_polymer + m_water)`; excludes salt. |
| Temperature | 323.15 K | 50 °C high-temperature screening condition. |
| Pressure | 1.0 bar | Isotropic NPT target after initial NVT relaxation. |
| Initial box | 3.2 nm cube | A near-density packing starting point, not an equilibrium volume. |
| Water model | TIP3P | Required to match the first GAFF2 screening route. |
| Force field | GAFF2 / AM1-BCC candidate | Pending polymerized-chain validation; do not claim quantitative LCST prediction. |

`src/calculate_composition.py` calculates **420 TIP3P waters** using the formula/mass assumptions in `config/pilot_323K.json`. The water count becomes final only after the polymer topology reports its exact molecular mass. The current hydrogen-capped-chain estimate is 11,341.02 g mol⁻¹ for all four chains and gives 59.98 wt% polymer with 420 waters.

## Inputs and outputs

Inputs are the JSON case configuration, a validated polymer topology (`.top`/`.itp`), one-chain coordinate file, and a force-field atom-mapping manifest. The construction utility writes a Packmol input file; it does not generate polymer coordinates. A completed run will create a new `runs/<run_id>/` directory containing frozen configuration, topology references, GROMACS version, commands, logs, trajectory, energies, and result inventory.

The first analysis outputs are per-repeat or per-chain quantities: hydration number around DEM ester oxygen atoms, hydration around NVP lactam carbonyl oxygen, hydrophobic DEM–DEM contacts, radius of gyration, polymer SASA, and the largest interchain cluster fraction. These are the outputs that can be meaningfully measured in this small box. Low-q structure factor and visual phase domains are deferred because a 3.2 nm box cannot support a macroscopic phase-separation claim.

## Prerequisites and modelling assumptions

Install a compatible GROMACS release and Packmol on the Linux server only when authorized. The first parameterization route is GAFF2 with AM1-BCC charges for a **polymerized saturated oligomer**, plus TIP3P water. The polymer is neutral and non-crosslinked; no counterions are included in this first model. The molecular-weight mismatch is intentional: 20 structural units is a reduced model for local mechanisms, so finite-size effects must be stated in every interpretation.

`parameters/chemical_model.json` is now the reviewable explicit-atom connectivity and analysis map for the hydrogen-capped `[DEM-NVP]10` chain. It contains no force-field types or partial charges. Before packing, create and review the following additional files under `parameters/`:

```text
parameters/
├── chemical_model.json              # 412-atom polymer connectivity and analysis mapping
├── topology/dem_nvp_alt10.itp       # polymerized, capped chain; molecule name DEMNVP10
├── topology/system.top              # includes force field, chain and water definitions
├── coordinates/dem_nvp_alt10.pdb    # one relaxed chain conformation
├── coordinates/tip3p_water.pdb      # one water molecule matching topology atom order
└── atom_mapping.json                # DEM/NVP atoms and analysis groups
```

## Software and commands

Python 3.9+ standard library is sufficient for the configuration utilities. The intended Linux executables are `gmx` (GROMACS 2023+ preferred) and `packmol`; exact versions will be frozen in each run manifest. No simulation command in this repository auto-installs software or launches a job.

From this directory, inspect the configuration without writing files:

```sh
python3 -B src/check_environment.py
python3 -B src/validate_config.py
python3 -B src/calculate_composition.py
python3 -B src/build_polymer_graph.py
```

After RDKit has been installed in an authorized isolated environment, create a new single-chain construction directory. This produces only an initial geometry and atom-order record; it is not parameterized or equilibrated:

```sh
python3 -B src/generate_initial_conformer.py --output-dir build/rdkit_alt10_seed13054
```

After the topology/coordinates are available, preview the Packmol text:

```sh
python3 -B src/build_packmol_input.py
```

Writing a generated Packmol input requires an explicit path and refuses to overwrite it:

```sh
python3 -B src/build_packmol_input.py --write build/packmol.inp
```

## MDP stages and data processing rules

`mdp/em.mdp`, `mdp/nvt_200ps.mdp`, `mdp/npt_2ns.mdp`, and `mdp/production_20ns.mdp` use 2 fs steps, constrained bonds to hydrogen, PME electrostatics, 1.0 nm real-space cutoffs, and 20 ps compressed-trajectory spacing. They are candidate controls that require a topology/GROMACS compatibility check before use. Analyses must discard the explicitly documented equilibration interval, normalize hydration/contact counts by group or chain, and retain blockwise time series rather than reporting a single unqualified average.

## Interpretation conventions and limitations

An increase in polymer–polymer DEM contacts together with lower local water coordination supports a dehydration/association mechanism. It does not prove bulk demixing. `largest_cluster_fraction` is the number of chains in the largest cluster divided by four. Contacts must exclude atoms from the same chain. DEM and NVP lack the N–H donor used in PNIPAM discussions; this study should emphasize water interactions with ester/lactam acceptors and hydrophobic DEM association, not assumed polymer–polymer hydrogen-bond networks.

## Related documents and evidence boundary

This directory follows the project organization principles in [`../../AGENTS.md`](../../AGENTS.md) and [`../../PROJECT_RULES.md`](../../PROJECT_RULES.md). It is independent of the impact FEA model. GROMACS options should be checked against the installed-version manual before production. No topology, coordinate, Packmol build, GROMACS run, or physical result exists yet.
