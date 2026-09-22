"""Perform read-only validation of the sample1 dry-run configuration.

1. Purpose and intended result:
   Check that confirmed case values are internally consistent and identify fields that
   still prevent material-card or OpenRadioss deck generation.
2. Inputs and outputs:
   Input is `config/sample1_dryrun.json`; output is a JSON report written to standard
   output only. No files are created or changed.
3. Prerequisites and assumptions:
   Python 3 standard library. This checks project conventions, not OpenRadioss syntax.
4. Software requirements and run instructions:
   Run `python3 FEA/scripts/validate_sample1_config.py` from any directory.
5. Key parameters:
   Checks geometry in mm, density in tonne/mm^3, mass in tonne, speed in mm/s, and the
   specified 40% local-thickness limit.
6. Data-processing rules:
   No source data are read, transformed, or written.
7. Result interpretation:
   A valid report means configuration arithmetic is consistent. It does not mean that a
   constitutive law is calibrated or that an OpenRadioss input deck will run.
8. Author and dates:
   Author: Codex. Created: 2026-09-18. Last modified: 2026-09-18.
9. Related files:
   `config/sample1_dryrun.json`, `scripts/prepare_sample1_material.py`, `README.md`,
   `PROJECT_RULES.md`, and `KNOWLEDGE_BASE.md` in the FEA project root.
"""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "sample1_dryrun.json"


def require(condition: bool, message: str, errors: list[str]) -> None:
    """Append a concise error instead of allowing a partial configuration to pass."""
    if not condition:
        errors.append(message)


def validate(config: dict) -> dict:
    """Validate confirmed values and report deliberate pending fields separately."""
    errors: list[str] = []
    warnings: list[str] = []
    sample = config["sample"]
    impactor = config["impactor"]
    limit = config["deformation_limit"]
    contact = config["contact"]
    outputs = config["outputs"]

    require(sample["length_mm"] > 0 and sample["width_mm"] > 0 and sample["thickness_mm"] > 0,
            "Sample dimensions must be positive.", errors)
    require(sample["density_tonne_mm3"] > 0, "Sample density must be positive.", errors)
    require(0.0 < sample["poisson_ratio"] < 0.5, "Poisson ratio must be between 0 and 0.5.", errors)
    require(impactor["mass_tonne"] > 0 and impactor["diameter_mm"] > 0,
            "Impactor mass and diameter must be positive.", errors)
    require(contact["ball_sample"] == "frictionless" and contact["friction_coefficient"] == 0.0,
            "The confirmed first model requires frictionless ball-sample contact.", errors)
    require(abs(limit["minimum_allowed_thickness_mm"] - sample["thickness_mm"] * 0.6) < 1e-12,
            "Minimum thickness must equal 60% of initial sample thickness.", errors)
    require(outputs["snapshot"] == "first_local_minimum_of_ball_vertical_position_after_first_contact",
            "Snapshot must be the first maximum compression displacement.", errors)

    material_status = config["material_model"]["status"]
    if material_status == "pending_calibration":
        warnings.append("Material model is pending calibration; do not generate a solver deck.")
    elif material_status == "compression_priority_calibration_table_pending_starter_verification":
        warnings.append("A compression-priority LAW69 candidate curve exists, but Starter fit verification is still required.")
    elif material_status != "starter_fit_verified":
        warnings.append(f"Material-model status is unrecognized: {material_status}. Do not generate a solver deck.")
    if outputs["stress_scalar"] == "pending_selection":
        warnings.append("Stress scalar for contours is pending selection.")
    if any("pending" in view for view in outputs["views"]):
        warnings.append("Camera orientation and centre-section plane are pending definition.")
    if config["execution"]["version"] == "pending_installation":
        warnings.append("Linux OpenRadioss installation and launch command are pending.")

    return {
        "case_id": config["case_id"],
        "configuration_status": "invalid" if errors else "internally_consistent_with_pending_fields",
        "errors": errors,
        "warnings": warnings,
        "solver_deck_generation_allowed": config["material_model"]["solver_deck_generation_allowed"],
    }


def main() -> None:
    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    print(json.dumps(validate(config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
