# Molecular-Dynamics Directory Rules

## Scope and directory boundary

All molecular-dynamics work belongs under simulation/MD/. Each polymer system is an independent project directory. Each temperature is an independent, peer directory within that polymer project. Do not mix force fields, coordinates, run evidence, analyses, or temperature-specific configuration between temperature directories.

```text
MD/
└── <polymer-project>/
    ├── 10 degree/
    ├── 50 degree/
    └── ...
```

For example, the current high-temperature pilot is MD/DEM-NVP/50 degree/. A future 10 °C DEM–NVP calculation must be created at MD/DEM-NVP/10 degree/, never inside 50 degree/.

## Required contents of a temperature directory

A temperature directory owns its canonical configuration, topology/coordinate references or copies, MDP controls, construction utilities, analysis scripts/specifications, and independent runs/<run_id>/ evidence. Its README must state temperature in K and °C, the polymer sequence, concentration, force field, water model, and output interpretation limits.

Shared code is permitted only when it has one stable responsibility and is explicitly referenced by each temperature directory. A temperature-specific result, build file, or solver run must never be stored in a shared directory.

## File safety and evidence

Do not overwrite completed runs. Do not install software or run Packmol/GROMACS without explicit authorization. Retain raw inputs and freeze the configuration, topology references, executable version, command, logs, and output inventory for every simulation attempt.

