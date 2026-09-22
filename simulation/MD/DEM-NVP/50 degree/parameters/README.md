# DEM-NVP parameter assets

Author: Codex. Created / last updated: 2026-09-21.

## Current artifact

chemical_model.json is a chemical-connectivity specification for one neutral,
hydrogen-capped [DEM-NVP]10 chain. It contains 412 explicit atoms and 421
bonds, together with stable atom names and analysis groups. It is not a GAFF2
topology, a coordinate file, or a simulation result.

The polymer graph consumes the DEM alkene and NVP vinyl double bonds to make
the saturated alternating backbone. No tacticity is assigned; this is an
atactic first-screening model.

## Required parameterization sequence

1. Create one 3D initial conformer with src/generate_initial_conformer.py in an
   authorized isolated environment containing RDKit.
2. Parameterize the whole capped chain, not separate monomers, with GAFF2 atom
   types and AM1-BCC charges through AmberTools.
3. Review all missing bonded terms reported by parmchk2. Confirm zero net
   charge, molecular mass, and final topology atom order against chemical_model.json.
4. Convert the reviewed result to GROMACS assets. Only then create topology and
   coordinate files for Packmol.

## Analysis mapping

The graph separately records DEM ester carbonyl oxygens, DEM ester alkoxy
oxygens, DEM ethyl carbons, NVP lactam carbonyl oxygens, NVP ring atoms, and
terminal hydrogens. The final GROMACS topology must preserve the graph atom
order or provide a documented index translation.

Monomer reference identities: diethyl maleate (PubChem CID 5271566) and
N-vinyl-2-pyrrolidone (PubChem CID 6917). The recorded monomer SMILES identify
the original reactants only; parameterization must use the polymerized graph.

