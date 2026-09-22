#!/usr/bin/env python3
"""Report the local prerequisites for this GROMACS project without changing state.

Purpose: record whether Python, GROMACS, and Packmol commands are discoverable
before a run. Inputs: optional executable command names. Output: JSON on stdout.
The script does not install, download, write files, pack coordinates, or run MD.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gmx-command", default="gmx")
    parser.add_argument("--packmol-command", default="packmol")
    args = parser.parse_args()
    report = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "gromacs_command": args.gmx_command,
        "gromacs_path": shutil.which(args.gmx_command),
        "packmol_command": args.packmol_command,
        "packmol_path": shutil.which(args.packmol_command),
        "status": "ready_for_version_check"
        if shutil.which(args.gmx_command) and shutil.which(args.packmol_command)
        else "missing_required_executables",
        "next_step": "After both paths are present, record gmx --version and Packmol version in a new run manifest.",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

