# Analysis contract for the 50 °C pilot

**Author:** Codex. **Created / last updated:** 2026-09-21.

Every analysis requires `parameters/atom_mapping.json`, which must name the DEM ester oxygen atoms, NVP lactam carbonyl oxygen, DEM ethyl atoms, and chain/molecule identifiers in the final topology. Never infer analysis atom names from a generic GAFF2 topology.

| Output | Primary question | Normalization / convention | First-pilot decision use |
| --- | --- | --- | --- |
| `hydration_dem_ester` | Are DEM ester acceptors dehydrated? | Waters within a documented cutoff per ester oxygen and per repeat pair. | Compare 50 °C with later low-T case. |
| `hydration_nvp_lactam` | Is NVP carbonyl hydration retained or reduced? | Waters per lactam oxygen and per repeat pair. | Distinguish selective dehydration. |
| `Rg_chain` and `SASA_polymer` | Do chains compact and expose less surface? | One value per chain; report distribution and time blocks. | Screen conformational response. |
| `contacts_DEM_DEM`, `contacts_DEM_NVP`, `contacts_NVP_NVP` | Which interchain interactions grow? | Contacts per pair of chains; exclude same-chain pairs. | Test hydrophobic DEM association. |
| `largest_cluster_fraction` | Do chains associate in the small box? | Largest cluster chain count divided by 4. | Detect association only, never macroscopic phase separation. |

Hydration and contact cutoffs must be recorded in the run analysis manifest and held fixed across temperatures. The trajectory has 20 ps frames, suitable for distributions/block means; it is not suitable for a reliable water-residence or hydrogen-bond lifetime analysis. `S(q)`, binodal estimates, and images of phase domains are out of scope for this 3.2 nm screening box.
