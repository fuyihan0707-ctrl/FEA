# DEM–NVP 50 °C MD Agent Guide

## Scope

This directory is a small, non-crosslinked aqueous solution model of a strictly alternating diethyl maleate (DEM)–N-vinylpyrrolidone (NVP) copolymer at 323.15 K. It is a mechanism-screening model, not a direct representation of the experimental molecular weight, turbidity, or macroscopic phase boundary.

## Directory responsibilities

| Location | Responsibility |
| --- | --- |
| `config/` | Canonical, editable case values. |
| `src/` | Small construction and validation utilities; each has one responsibility. |
| `parameters/` | User-supplied, versioned force-field topology, atom mapping, and coordinates. |
| `mdp/` | GROMACS control files only. |
| `analysis/` | Independent analysis specifications and scripts. |
| `build/` | Generated Packmol input and coordinates; never source data. |
| `runs/<run_id>/` | One immutable simulation attempt and its frozen input/version/log evidence. |

## Rules

- Do not create polymer force-field parameters by concatenating monomer topologies. The saturated polymer backbone, termini, charge model, atom names, and bonded terms must be supplied and reviewed together.
- Do not run GROMACS, Packmol, AmberTools, or install software without the user's explicit instruction.
- Create a new `runs/<run_id>/` for every execution; never overwrite an existing run.
- Keep the topology atom-mapping manifest with the force field. Analysis groups must use that manifest rather than guessed atom names.
- State whether each output is a configuration check, a construction artifact, a numerical result, or a physical interpretation.

