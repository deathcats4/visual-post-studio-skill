#!/usr/bin/env python3
"""Static PNG checks for a visual-post-studio project.

Python 3.9+ stdlib only. Cannot check OCR text, visual quality or factual accuracy.
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def image_dims(path: Path):
    with path.open("rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("not a valid PNG IHDR")
    w, h = struct.unpack(">II", header[16:24])
    if not (w > 0 and h > 0):
        raise ValueError("invalid PNG dimensions")
    return w, h


def check(project, strict=False):
    project = Path(project)
    manifest_file = project / "manifest.json"
    if not manifest_file.is_file():
        return [f"Missing manifest: {manifest_file}"], []
    try:
        m = json.loads(manifest_file.read_text(encoding="utf-8"))
    except Exception as ex:
        return [f"Invalid manifest.json: {ex}"], []
    files = sorted((project / "images" / "final").glob("*.png"))
    errors, warnings = [], []
    if not files:
        errors.append("No final PNG images in images/final/ (planned-only work is not a completed image deliverable).")
        return errors, warnings
    expected_count = m.get("page_count")
    if expected_count is not None and len(files) != expected_count:
        errors.append(f"Expected {expected_count} independent PNG files, found {len(files)}.")
    nums = []
    for p in files:
        mt = re.match(r"^(\d{2,3})(?:[-_].*)?\.png$", p.name, flags=re.I)
        if not mt:
            errors.append(f"Page filename should begin with 01, 02, ...: {p.name}")
        else:
            nums.append(int(mt[1]))
        try:
            w,h = image_dims(p)
        except Exception as ex:
            errors.append(f"{p.name}: {ex}")
            continue
        target = m.get("target_pixels")
        if target:
            if [w,h] != target:
                (errors if strict else warnings).append(f"{p.name}: pixels {w}x{h} != requested {target[0]}x{target[1]}")
        ar = m.get("canvas", "unspecified")
        if ar != "unspecified":
            try:
                a,b = (int(s) for s in ar.split(":"))
                diff = abs(w/h - a/b)
                if diff > 0.0125:
                    (errors if strict else warnings).append(f"{p.name}: ratio {w}:{h} differs from {ar}")
            except (ValueError, ZeroDivisionError):
                errors.append(f"Bad canvas ratio: {ar}")
        if w/h > 1.5 and m.get("canvas") in {"3:4", "9:16"}:
            errors.append(f"{p.name}: landscape image for a portrait project; check for collage/contact sheet")
    if nums and sorted(nums) != list(range(1,len(nums)+1)):
        errors.append(f"Numbered pages must be continuous from 01: {sorted(nums)}")
    if m.get("image_generation_status") != "complete":
        warnings.append("manifest.image_generation_status is not 'complete'; confirm actual production status.")
    warnings.append("Visual design, screenshot authenticity and factual correctness need human/model review; this check only validates structure/dimensions.")
    return errors, warnings


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project", help="Project folder containing manifest.json")
    p.add_argument("--strict", action="store_true", help="Require exact target pixels and canvas")
    args = p.parse_args(argv)
    errors, warnings = check(args.project, args.strict)
    for e in errors:
        print("ERROR:",e)
    for w in warnings:
        print("NOTE:", w)
    if errors:
        print("FAILED")
        return 1
    print("PASSED structural PNG checks (NOT an editorial/fact check)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
