"""Independently inspect the serialized sample1 candidate; no solver invocation.

1. Purpose: detect geometry, connectivity, unit, reference and card-field errors.
2. I/O: candidate RAD/JSON/CSV files -> JSON stdout; --report exclusively creates
   a report. Units are mm, s, tonne, N, MPa; Jacobians are in mm^3.
3. Assumptions: the deliberately limited sample1 card subset, not a general parser.
4. Runtime: Python >=3.9 standard library. Run this file with --help.
5. Parameters: --model-dir selects a frozen candidate, --report must not exist.
6. Processing: re-read fixed-width deck fields independently of the generator;
   check all gel Gauss-point Jacobians, surface topology, IDs and source hashes.
7. Interpretation: static checks cannot establish solver acceptance, fit accuracy,
   contact stability, deformation limits or experimental validity.
8. Author: Codex. Created and updated: 2026-09-20.
9. Related: build_sample1_candidate.py; README.md (instructions and references),
   PROJECT_RULES.md and KNOWLEDGE_BASE.md. Never edits input or run files.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(line, widths, kind=float):
    values, pos = [], 0
    for width in widths:
        token = line[pos:pos+width].strip()
        values.append(kind(token or "0"))
        pos += width
    require(not line[pos:].strip(), "Unexpected trailing card fields: " + line)
    if kind is float:
        require(all(math.isfinite(v) for v in values), "Non-finite card value")
    return values


def blocks(text):
    result, current = {}, None
    for line in text.splitlines():
        require(len(line) <= 100, "Card exceeds 100 columns")
        if not line.strip() or line.startswith(("#", "$")):
            continue
        if line.startswith("/"):
            require(line not in result, "Duplicate keyword: " + line)
            current = line
            result[current] = []
        else:
            require(current is not None, "Data precede a keyword")
            result[current].append(line)
    return result


def sub(a,b):
    return tuple(x-y for x,y in zip(a,b))


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def check(starter_text,engine_text,cfg,curve):
    """Check serialized content; exposed for non-writing negative checks."""
    require(starter_text.startswith("#RADIOSS STARTER\n"),"Missing Starter header")
    st, en = blocks(starter_text), blocks(engine_text)
    require(list(st)[-1] == "/END" and list(en)[-1] == "/STOP", "Missing deck terminator")
    s,b,n = (cfg[k] for k in ("sample","impactor","candidate_numerics"))
    mesh = cfg["smoke_test_mesh"]
    begin = st["/BEGIN"]
    require(begin[0] == n["run_name"] and int(begin[1]) == n["input_format_version"],"Name/format mismatch")
    require(begin[2].split() == begin[3].split() == ["Mg","mm","s"],"Inconsistent units")
    nodes = {}
    for row in st["/NODE"]:
        ident = int(row[:10]); xyz = fields(row[10:],[20]*3)
        require(ident > 0 and ident not in nodes,"Invalid/duplicate node ID")
        nodes[ident] = xyz
    elements = {}
    for key,width in (("/BRICK/1",9),("/SHELL/2",5)):
        data = {}
        for row in st[key]:
            ident,*conn = fields(row,[10]*width,int)
            require(ident not in data and ident > 0,"Duplicate element ID")
            require(len(set(conn)) == width-1 and all(i in nodes for i in conn),"Invalid connectivity")
            data[ident] = conn
        elements[key] = data
    bricks,shells = elements.values()
    require(not set(bricks)&set(shells),"Duplicate IDs across element types")
    nx,ny,nz = [mesh[f"elements_{a}"] for a in "xyz"]
    require(len(bricks) == nx*ny*nz == mesh["total_elements"],"Incorrect gel element count")
    gel = set(i for conn in bricks.values() for i in conn)
    ball = set(i for conn in shells.values() for i in conn)
    require(not gel&ball,"Gel and ball share nodes")
    require(len(gel) == (nx+1)*(ny+1)*(nz+1),"Gel node count incorrect")
    dims = [s["length_mm"],s["width_mm"],s["thickness_mm"]]
    for a in range(3):
        require(abs(min(nodes[i][a] for i in gel)) < 1e-9 and
                math.isclose(max(nodes[i][a] for i in gel),dims[a]),"Gel bounding box incorrect")
    # Independent trilinear shape-function derivative check at all 8 Gauss points.
    signs = ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))
    determinants,faces = [],Counter()
    for conn in bricks.values():
        for f in ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
            faces[tuple(sorted(conn[j] for j in f))] += 1
        for ir in (-1,1):
            for js in (-1,1):
                for kt in (-1,1):
                    r,t,u = [v/math.sqrt(3) for v in (ir,js,kt)]
                    derivatives = [(a*(1+c*t)*(1+d*u)/8,c*(1+a*r)*(1+d*u)/8,d*(1+a*r)*(1+c*t)/8)
                                   for a,c,d in signs]
                    jac = [[sum(nodes[node][a]*derivatives[i][j] for i,node in enumerate(conn))
                            for j in range(3)] for a in range(3)]
                    determinants.append(dot(jac[0],cross(jac[1],jac[2])))
    require(min(determinants)>0,"Non-positive gel Jacobian")
    volume = sum(determinants)
    require(math.isclose(volume,math.prod(dims),rel_tol=1e-9),"Gel volume mismatch")
    require(max(faces.values()) == 2 and sum(v==1 for v in faces.values()) == 2*(nx*ny+ny*nz+nx*nz),
            "Nonconforming gel faces")
    groups = {}
    for key,rows in st.items():
        if key.startswith("/GRNOD/NODE/"):
            ids = [int(row[j:j+10]) for row in rows[1:] for j in range(0,len(row),10)]
            require(len(set(ids))==len(ids) and set(ids)<=nodes.keys(),"Invalid node group")
            groups[int(key.split("/")[-1])] = set(ids)
    require(groups[1] == {i for i in gel if abs(nodes[i][2])<1e-9},"Bonded face incomplete or wrong")
    require(groups[2] == {i for i in gel if math.isclose(nodes[i][2],dims[2])},"Wrong contact node set")
    require(groups[3] == ball,"Rigid body membership incorrect")
    bcs = st["/BCS/1"][1]
    require(bcs[:10] == "   111 000" and fields(bcs[10:],[10,10],int)==[0,1],"Incorrect bottom constraints")
    require(sum(k.startswith("/BCS/") for k in st)==1,"Unexpected extra constraints")
    rb = st["/RBODY/1"]
    rbrow = fields(rb[1],[10]*4+[20]+[10]*4)
    center_id = int(rbrow[0]); center = nodes[center_id]
    require(center_id not in gel|ball and groups[4]==ball|{center_id},"Ball velocity membership incorrect")
    require(set(nodes)==gel|ball|{center_id},"Unreferenced nodes")
    require(rbrow[3]==1 and rbrow[5]==3 and rbrow[7]==4,"Rigid mass override missing")
    require(rbrow[4] == b["mass_tonne"],"Ball mass mismatch")
    radius = b["diameter_mm"]/2
    require(all(math.isclose(v,.4*b["mass_tonne"]*radius**2,rel_tol=1e-10)
                for v in fields(rb[2],[20]*3)),"Solid sphere inertia incorrect")
    require(fields(rb[3],[20]*3)==[0.,0.,0.],"Inertia cross terms incorrect")
    require(all(math.isclose(math.dist(nodes[i],center),radius,abs_tol=1e-9) for i in ball),"Sphere radius inconsistent")
    require(math.isclose(center[0],dims[0]/2) and math.isclose(center[1],dims[1]/2),"Ball not centered")
    gap = min(nodes[i][2] for i in ball)-dims[2]
    require(math.isclose(gap,b["initial_ball_to_sample_top_surface_gap_mm"],abs_tol=1e-9),"Initial clearance incorrect")
    edges=Counter(); oriented=Counter()
    for conn in shells.values():
        p=[nodes[i] for i in conn]
        normal=cross(sub(p[1],p[0]),sub(p[2],p[0]))
        centroid=[sum(x[a] for x in p)/4 for a in range(3)]
        require(dot(normal,sub(centroid,center))>0,"Degenerate/inward ball facet")
        for a,c in zip(conn,conn[1:]+conn[:1]):
            edges[tuple(sorted((a,c)))]+=1; oriented[a,c]+=1
    require(all(v==2 for v in edges.values()) and all(oriented[a,c]==oriented[c,a] for a,c in oriented),
            "Ball surface is not closed and consistently oriented")
    require(len(shells)==6*n["ball_cube_face_subdivisions"]**2,"Ball facet count mismatch")
    vel=fields(st["/INIVEL/TRA/1"][1],[20]*3+[10]*2)
    require(vel==[0.,0.,-b["contact_speed_mm_s"],4.,0.],"Incorrect initial velocity")
    mat=st["/MAT/LAW69/1"]
    require(float(mat[1])==s["density_tonne_mm3"],"Incorrect gel density")
    require(fields(mat[2],[10,10,20,20,10,10])==[1,0,s["poisson_ratio"],1,2,-3] and int(mat[3])==1,
            "LAW69 settings/reference incorrect")
    prop=fields(st["/PROP/TYPE14/1"][1],[10]*8+[20])
    require(prop[:6]==[14,10,0,1,0,222],"Incorrect gel strain/pressure formulation")
    require(fields(st["/PART/1"][1],[10]*3,int)==[1,1,0] and
            fields(st["/PART/2"][1],[10]*3,int)==[2,2,0],"Incorrect material/property references")
    serialized=[fields(row,[20,20]) for row in st["/FUNCT/1"][1:]]
    require(len(serialized)==len(curve)==81,"Curve length mismatch")
    require(all(math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-12) for x,y in zip(serialized,curve) for a,b in zip(x,y)),
            "Material curve changed during serialization")
    require(serialized[-1]==[0,0] and serialized[0][0]==-.4 and
            all(a[0]<b[0] and a[1]<=b[1] for a,b in zip(serialized,serialized[1:])),"Curve sign/order incorrect")
    contact=st["/INTER/TYPE7/1"]
    require(fields(contact[1],[10]*10,int)==[2,1,4,0,1000,0,2,1000,0,0],"Contact membership or flags incorrect")
    require(int(st["/SURF/PART/1"][1])==2,"Ball main surface reference incorrect")
    params=fields(contact[4],[20]*5)
    require(params==[n["interface_stiffness_scale"],0.,n["interface_gap_mm"],0.,1e30],"Contact parameters incorrect")
    require(0<params[2]<gap,"Initial penalty penetration")
    require(fields(contact[5],[10]*4+[20]*3)[4]==n["interface_normal_damping"],"Contact damping mismatch")
    require(int(st["/TH/INTER/1"][2])==1 and "FNZ" in st["/TH/INTER/1"][1],"Force history missing")
    histories=st["/TH/NODE/2"]
    history_ids={int(row[:10]) for row in histories[2:]}
    require(center_id in history_ids and history_ids<=nodes.keys() and "VZ" in histories[1],"Ball motion history missing")
    require(len(history_ids)==3,"Thickness monitor nodes missing")
    top_monitor=[i for i in history_ids if i in groups[2]]
    bottom_monitor=[i for i in history_ids if i in groups[1]]
    require(len(top_monitor)==len(bottom_monitor)==1 and
            all(math.isclose(nodes[i][a],dims[a]/2) for i in top_monitor+bottom_monitor for a in (0,1)),
            "Thickness monitors are not on the impact axis")
    require(float(en[f"/RUN/{n['run_name']}/1"][0])==n["end_time_s"],"End time mismatch")
    require(float(en["/TFILE"][0])==n["history_interval_s"],"History interval mismatch")
    require(fields(en["/ANIM/DT"][0],[20,20])==[0.,n["animation_interval_s"]],"Animation interval mismatch")
    required=("/ANIM/BRICK/VONM","/ANIM/VECT/DISP","/ANIM/BRICK/TENS/STRESS","/ANIM/BRICK/TENS/STRAIN","/ANIM/BRICK/DENS")
    require(all(k in en for k in required),"Stress/geometry diagnostic output missing")
    require(not any(k.startswith(("/DT/","/AMS","/GRAV","/FAIL/","/DAMP")) for k in list(st)+list(en)),
            "Unexpected scaling, gravity, failure or external damping keyword")
    return {"gel_elements":len(bricks),"gel_nodes":len(gel),"ball_surface_elements":len(shells),
            "total_nodes":len(nodes),"bonded_nodes":len(groups[1]),"top_contact_nodes":len(groups[2]),
            "minimum_gauss_jacobian_mm3":min(determinants),"gel_volume_mm3":volume,
            "gel_mass_g":volume*s["density_tonne_mm3"]*1e6,"ball_mass_g":rbrow[4]*1e6,
            "geometric_clearance_mm":gap,"numerical_contact_gap_mm":params[2],
            "duration_ms":n["end_time_s"]*1000}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir",type=Path,default=ROOT/"models/sample1/candidate_v001")
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    report={"status":"failed","solver_executed":False,"errors":[],"warnings":[
        "Static subset checks only; Linux keyword acceptance and LAW69 fitting remain unverified.",
        "40% thickness compression is not automatically limited; reject runs exceeding it.",
        "First maximum compression may fall outside 0.5 ms.",
        "Gel dissipation is uncalibrated; numerical viscosity and contact damping are not material damping.",
        "Contact-gap, penalty stiffness, ball faceting and mesh sensitivity remain untested."]}
    try:
        directory=args.model_dir.resolve()
        manifest=json.loads((directory/"model_manifest.json").read_text())
        for name,expected in manifest["artifact_sha256"].items():
            require(Path(name).name==name,"Invalid artifact path")
            require(hashlib.sha256((directory/name).read_bytes()).hexdigest()==expected,"Artifact hash mismatch: "+name)
        for name,expected in manifest["source_sha256"].items():
            source=(ROOT/name).resolve()
            require(ROOT in source.parents,"Invalid source path")
            require(hashlib.sha256(source.read_bytes()).hexdigest()==expected,"Source changed since generation: "+name)
        cfg=json.loads((directory/"frozen_config.json").read_text())
        name=cfg["candidate_numerics"]["run_name"]
        with (directory/"material_curve.csv").open() as f:
            curve=[list(map(float,row.values())) for row in csv.DictReader(f)]
        report["checks"]=check((directory/f"{name}_0000.rad").read_text(),(directory/f"{name}_0001.rad").read_text(),cfg,curve)
        report["status"]="static_checks_passed_solver_pending"
        report["artifact_sha256"]=manifest["artifact_sha256"]
    except (ValueError,KeyError,IndexError,OSError) as exc:
        report["errors"].append(str(exc))
    output=json.dumps(report,indent=2)+"\n"
    if args.report:
        target=args.report.resolve()
        require(ROOT in target.parents,"Report must be inside FEA")
        with target.open("x",encoding="utf-8") as f:
            f.write(output)
    print(output,end="")
    sys.exit(1 if report["errors"] else 0)


if __name__=="__main__":
    main()
