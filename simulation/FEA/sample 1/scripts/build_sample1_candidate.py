"""Generate the sample1 candidate only; never launch OpenRadioss.

1. Purpose: create reviewable Starter/Engine decks and a provenance manifest.
2. I/O: JSON configuration and approved CSV -> RAD, frozen JSON/CSV, JSON manifest.
   Units: mm, s, tonne, N, MPa; engineering strain is dimensionless.
3. Assumptions: compression-only LAW69; bonded bottom; frictionless rigid ball.
4. Runtime: Python >=3.9 standard library. Run this file with --help; default
   is a no-write preview. --write requires a new model directory.
5. Parameters: config/sample1_dryrun.json is canonical; positive geometry and
   times, 0 < nu < 0.5, mesh counts positive integers, candidate scope only.
6. Processing: copy approved curve without refitting; create mesh and fixed-width
   cards. Use exclusive creation and SHA256 provenance; never overwrite a model.
7. Interpretation: candidate input, not a solver check or physical validation.
   z points upward; velocity is negative z; stress output is Cauchy stress.
8. Author: Codex. Created and updated: 2026-09-20.
9. Related: scripts/check_sample1_candidate.py, README.md, KNOWLEDGE_BASE.md,
   PROJECT_RULES.md; official keyword references are in README.md.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "models/sample1/candidate_v001"


def ints(*values):
    return "".join(f"{v:10d}" for v in values)


def reals(*values):
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Non-finite real field")
    return "".join(f"{v:20.12g}" for v in values)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def generate(config, curve_bytes):
    """Return deck text and mesh metadata; do not write or fit material data."""
    s, b, n = (config[k] for k in ("sample", "impactor", "candidate_numerics"))
    m, law = config["smoke_test_mesh"], config["material_model"]
    if not law["solver_deck_generation_allowed"] or law["generation_scope"] != "candidate_only_not_production":
        raise ValueError("Candidate generation must be authorized in the configuration")
    nx, ny, nz = (m[f"elements_{a}"] for a in "xyz")
    q = n["ball_cube_face_subdivisions"]
    if any(type(v) is not int or v <= 0 for v in (nx, ny, nz, q)) or q % 2:
        raise ValueError("Positive mesh counts and even ball subdivisions required")
    dims = (s["length_mm"], s["width_mm"], s["thickness_mm"])
    if min(dims) <= 0 or not 0 < s["poisson_ratio"] < .5:
        raise ValueError("Invalid geometry or Poisson ratio")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,70}", n["run_name"]):
        raise ValueError("Unsafe or invalid run name")
    gap = b["initial_ball_to_sample_top_surface_gap_mm"]
    if not 0 < n["interface_gap_mm"] < gap:
        raise ValueError("Numerical contact gap must be smaller than initial clearance")
    if not 0 < n["history_interval_s"] <= n["animation_interval_s"] < n["end_time_s"]:
        raise ValueError("Invalid output intervals")
    if n["mass_scaling"] or n["gravity_in_short_impact_window"]:
        raise ValueError("This candidate generator supports no mass scaling or gravity")
    curve = [(float(r["engineering_strain_mm_per_mm"]), float(r["engineering_stress_mpa"]))
             for r in csv.DictReader(io.StringIO(curve_bytes.decode("utf-8")))]
    if (len(curve) != 81 or curve[0][0] != -.4 or curve[-1] != (0., 0.) or
            any(not math.isfinite(x) for row in curve for x in row) or
            any(x1 >= x2 or y1 > y2 for (x1, y1), (x2, y2) in zip(curve, curve[1:]))):
        raise ValueError("Expected the approved monotone 81-point compression table")

    nodes, bricks, shells = {}, {}, {}
    def gid(i, j, k):
        return 1 + i + (nx + 1) * (j + (ny + 1) * k)
    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                nodes[gid(i, j, k)] = (dims[0]*i/nx, dims[1]*j/ny, dims[2]*k/nz)
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                bricks[len(bricks)+1] = tuple(gid(i+a, j+c, k+d) for a,c,d in
                    ((0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)))
    gel_node_count = len(nodes)
    bottom = [gid(i,j,0) for j in range(ny+1) for i in range(nx+1)]
    top = [gid(i,j,nz) for j in range(ny+1) for i in range(nx+1)]
    radius = b["diameter_mm"]/2
    center = (dims[0]/2, dims[1]/2, dims[2]+gap+radius)
    center_id = len(nodes)+1
    nodes[center_id] = center
    cube_ids = {}
    # Project six shared-edge cube faces onto a sphere, avoiding polar triangles.
    for axis in range(3):
        other = [a for a in range(3) if a != axis]
        for side in (-1, 1):
            face = {}
            for j in range(q+1):
                for i in range(q+1):
                    key = [0,0,0]
                    key[axis] = side*q
                    key[other[0]], key[other[1]] = 2*i-q, 2*j-q
                    key = tuple(key)
                    if key not in cube_ids:
                        node = len(nodes)+1
                        cube_ids[key] = node
                        norm = math.sqrt(sum(v*v for v in key))
                        nodes[node] = tuple(center[a]+radius*key[a]/norm for a in range(3))
                    face[i,j] = cube_ids[key]
            for j in range(q):
                for i in range(q):
                    conn = [face[i,j],face[i+1,j],face[i+1,j+1],face[i,j+1]]
                    # x-z face has the opposite parametric orientation to x-y/y-z.
                    if side * (1 if axis != 1 else -1) < 0:
                        conn.reverse()
                    shells[len(bricks)+len(shells)+1] = tuple(conn)
    ball_nodes = sorted(cube_ids.values())
    inertia = .4*b["mass_tonne"]*radius**2
    lines = ["#RADIOSS STARTER", "# CANDIDATE ONLY; Linux Starter and Engine have not run.",
             "# Units: mm s tonne N MPa. See frozen_config.json and model_manifest.json.",
             "/BEGIN", n["run_name"], ints(n["input_format_version"]),
             f"{'Mg':>20}{'mm':>20}{'s':>20}", f"{'Mg':>20}{'mm':>20}{'s':>20}",
             "/NODE", "# node_ID: I10; x,y,z: 3E20"]
    lines += [ints(i)+reals(*p) for i,p in nodes.items()]
    lines += ["/MAT/LAW69/1", "sample1 compression-only Ogden candidate", reals(s["density_tonne_mm3"]),
              "# law_ID fct_blk nu Fscale_blk N_pair Icheck",
              ints(law["law_id"],0)+reals(s["poisson_ratio"],1.)+ints(law["ogden_parameter_pairs"],law["icheck"]),
              ints(1), "/FUNCT/1", "Engineering strain mm/mm versus engineering stress MPa"]
    lines += [reals(*p) for p in curve]
    lines += ["/PROP/TYPE14/1", "HA8 total strain constant pressure gel",
              ints(n["solid_formulation"],n["solid_strain_formulation"],0,n["constant_pressure_flag"],0,
                   n["solid_integration_points"],0,0)+reals(0.),
              reals(n["quadratic_bulk_viscosity"],n["linear_bulk_viscosity"],0.,0.,0.), reals(0.),
              "/PART/1", "sample1 gel", ints(1,1,0), "/BRICK/1"]
    lines += [ints(i,*c) for i,c in bricks.items()]
    lines += ["# Rigid contact carrier only: exact mass and inertia override its shell mass.",
              "/MAT/LAW1/2", "Nominal steel contact carrier", reals(b["nominal_steel_density_tonne_mm3"]),
              reals(n["ball_carrier_young_modulus_mpa"],n["ball_carrier_poisson_ratio"]),
              "/PROP/TYPE1/2", "Rigid ball surface carrier", ints(1,4,2,2,0,0)+reals(0.),
              reals(0.,0.,0.,0.,0.), ints(0,0)+reals(n["ball_carrier_shell_thickness_mm"],5/6)+ints(0,0),
              "/PART/2", "Rigid solid sphere represented by surface and exact inertia", ints(2,2,0), "/SHELL/2"]
    lines += [ints(i,*c) for i,c in shells.items()]
    def group(ident, title, ids):
        lines.extend([f"/GRNOD/NODE/{ident}",title])
        lines.extend(ints(*ids[j:j+10]) for j in range(0,len(ids),10))
    group(1,"Bonded bottom nodes",bottom)
    group(2,"Gel top contact nodes",top)
    group(3,"Rigid ball secondary nodes",ball_nodes)
    group(4,"Initial velocity all ball nodes including center",[center_id]+ball_nodes)
    lines += ["/BCS/1", "Perfect bond bottom translations only", f"{'111 000':>10}"+ints(0,1),
              "/RBODY/1", "20g ball exact mass and solid sphere inertia",
              ints(center_id,0,0,1)+reals(b["mass_tonne"])+ints(3,0,n["rigid_body_icog"],0),
              reals(inertia,inertia,inertia),reals(0.,0.,0.),ints(0,0,0),
              "/INIVEL/TRA/1", "Ball initial downward velocity", reals(0.,0.,-b["contact_speed_mm_s"])+ints(4,0),
              "/SURF/PART/1", "Rigid ball main contact surface", ints(2),
              "/INTER/TYPE7/1", "Frictionless ball main gel secondary",
              ints(2,1,n["interface_stiffness_flag"],0,1000,0,2,1000,0,0),
              reals(1.,0.,0.)+ints(0,0,0),
              reals(0.,1.e30,.4,0.)+ints(1,3),
              reals(n["interface_stiffness_scale"],config["contact"]["friction_coefficient"],n["interface_gap_mm"],0.,1.e30),
              ints(0,0,0,1000)+reals(n["interface_normal_damping"],1.,.2),
              ints(0,0)+reals(0.)+ints(2,0,0)+reals(1.)+ints(0),
              "/TH/INTER/1", "Ball gel contact forces", "".join(f"{v:>10}" for v in ("FNX","FNY","FNZ")), ints(1),
              "/TH/NODE/2", "Ball center and gel center thickness", "".join(f"{v:>10}" for v in ("DX","DY","DZ","VX","VY","VZ","AZ")),
              ints(center_id,0)+"ball_center", ints(gid(nx//2,ny//2,nz),0)+"gel_top_center",
              ints(gid(nx//2,ny//2,0),0)+"gel_bottom_center", "/TH/PART/3", "Gel energy diagnostic", f"{'DEF':>10}", ints(1), "/END"]
    engine = ["# Candidate smoke Engine. Physical duration 0.5 ms; no solver has run.",
              f"/RUN/{n['run_name']}/1",reals(n["end_time_s"]),f"/VERS/{n['input_format_version']}",
              "/PRINT/-1000", "/TFILE",reals(n["history_interval_s"]),
              "/ANIM/DT",reals(0.,n["animation_interval_s"]),
              "/ANIM/VECT/DISP", "/ANIM/VECT/VEL", "/ANIM/VECT/CONT",
              "/ANIM/BRICK/VONM", "/ANIM/BRICK/TENS/STRESS", "/ANIM/BRICK/TENS/STRAIN",
              "/ANIM/BRICK/DENS", "/STOP"]
    metadata = {"gel_nodes":gel_node_count,"gel_bricks":len(bricks),"rigid_surface_nodes":len(ball_nodes),
                "rigid_surface_shells":len(shells),"ball_center_node":center_id,
                "ball_center_mm":center,"ball_inertia_tonne_mm2":inertia,
                "gel_top_center_node":gid(nx//2,ny//2,nz),"gel_bottom_center_node":gid(nx//2,ny//2,0),
                "initial_geometric_contact_time_s":gap/b["contact_speed_mm_s"],
                "initial_penalty_activation_estimate_s":(gap-n["interface_gap_mm"])/b["contact_speed_mm_s"],
                "initial_ball_kinetic_energy_N_mm":.5*b["mass_tonne"]*b["contact_speed_mm_s"]**2}
    return "\n".join(lines)+"\n", "\n".join(engine)+"\n", metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write",action="store_true")
    parser.add_argument("--output-dir",type=Path,default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    config_path = ROOT / "config/sample1_dryrun.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    curve_path = ROOT / config["material_model"]["candidate_input"]
    curve_bytes = curve_path.read_bytes()
    starter, engine, mesh = generate(config,curve_bytes)
    name = config["candidate_numerics"]["run_name"]
    files = {f"{name}_0000.rad":starter.encode(),f"{name}_0001.rad":engine.encode(),
             "frozen_config.json":config_bytes,"material_curve.csv":curve_bytes}
    sources = [config_path,curve_path,Path(__file__),ROOT/"scripts/check_sample1_candidate.py",
               ROOT/config["source_data"]["compression_rtf"],ROOT/config["source_data"]["tension_rtf"]]
    manifest = {"status":"candidate_not_solver_verified", "generated_utc":datetime.now(timezone.utc).isoformat(),
                "mesh":mesh,"source_sha256":{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in sources},
                "artifact_sha256":{p:digest(data) for p,data in files.items()},
                "limitations":["Linux Starter fit and keyword checks pending", "No Engine execution",
                    "No physical gel dissipation or rate dependence calibrated",
                    "40 percent compression is an acceptance criterion, not an automatic stop",
                    "0.5 ms may not include first maximum compression",
                    "TYPE7 contact gap, damping and rigid surface resolution require sensitivity checks"]}
    if args.write:
        output = args.output_dir.resolve()
        if ROOT/"models" not in output.parents:
            raise ValueError("Output must be a new directory below FEA/models")
        output.mkdir(parents=True,exist_ok=False)
        files["model_manifest.json"] = (json.dumps(manifest,indent=2)+"\n").encode()
        for relative,data in files.items():
            with (output/relative).open("xb") as f:
                f.write(data)
        print(f"Created candidate: {output}")
    else:
        print("PREVIEW ONLY: no files written")
    print(json.dumps(mesh,indent=2))


if __name__ == "__main__":
    main()
