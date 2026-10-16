#!/usr/bin/env python3
"""Scaffold a reusable visual style pack; the image-reading Agent writes its actual style rules.

This script does NOT "learn" images or grant public redistribution rights.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path


def new_style(args):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.id):
        raise ValueError("--id must be lowercase kebab-case, e.g. paper-notes")
    root = Path(args.out).expanduser().resolve() / args.id
    if root.exists():
        raise FileExistsError(f"Style exists: {root}. Refusing to overwrite an existing style pack.")
    inputs = []
    for i, ref in enumerate(args.reference or [], start=1):
        src = Path(ref).expanduser().resolve()
        if not src.is_file() or src.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError(f"Reference {src} is not an existing PNG/JPEG/WebP image")
        inputs.append((src, f"reference-{i:02d}{src.suffix.lower()}"))
    (root / "examples").mkdir(parents=True)
    for src, dest in inputs:
        shutil.copy2(src, root / "examples" / dest)
    (root / "style.md").write_text(
        "# " + args.id + " — User-defined style\n\n"
        "> Agent: Visually inspect every image in examples/ before completing this file. "
        "This stub is not evidence that images have already been analyzed.\n\n"
        "## Invariants\n\n- TODO: typography and contrast\n- TODO: colors and spacing relationships\n- TODO: image treatment\n\n"
        "## Variants\n\n- TODO: multiple layout types\n- Topic, brand and page count are NOT fixed\n\n"
        "## Avoid\n\n- Do not copy the original images' signature, logo or text\n",
        encoding="utf-8",
    )
    (root / "style.json").write_text(json.dumps({
        "id": args.id, "default": False, "topic_locked": False, "brand_locked": False,
        "image_analysis_status": "pending_agent_inspection",
        "references": ["examples/" + dst for _, dst in inputs]
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "attribution.md").write_text(
        "# Sources and permissions\n\n"
        "The reference images were supplied for the current task. Public redistribution permission: **UNCONFIRMED**.\n"
        "Record author/source/license here before adding this style pack to a public repository.\n",
        encoding="utf-8",
    )
    print(root)
    return root


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True, help="Style ID, lowercase kebab-case")
    p.add_argument("--out", default="styles", help="Styles parent directory")
    p.add_argument("--reference", action="append", help="Reference image (repeatable)")
    args = p.parse_args(argv)
    try:
        new_style(args)
    except (ValueError, FileExistsError, PermissionError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
