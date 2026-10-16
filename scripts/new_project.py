#!/usr/bin/env python3
"""Create an independent working directory for any visual post.

Python 3.9+, standard library only. Does not generate images.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", s.lower().strip())
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        raise ValueError("--slug must contain Latin letters or numbers (e.g. my-post)")
    return s


def parse_pixels(value):
    if not value:
        return None
    m = re.fullmatch(r"(\d+)[x×](\d+)", value.strip())
    if not m or int(m[1]) <= 0 or int(m[2]) <= 0:
        raise argparse.ArgumentTypeError("Use WxH, e.g. 1080x1440")
    return [int(m[1]), int(m[2])]


def create(args):
    slug = slugify(args.slug)
    target_pixels = parse_pixels(args.pixels)
    base = Path(args.out).expanduser().resolve()
    project = base / slug
    if project.exists():
        raise FileExistsError(f"Project exists: {project}. Choose another slug; existing work is never overwritten.")
    project.mkdir(parents=True)
    for sub in ["sources", "storyboard", "visual-dna", "production", "prompts", "images/final", "images/drafts", "reviews", "publish"]:
        (project / sub).mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "topic": args.topic,
        "slug": slug,
        "platform": args.platform,
        "mode": args.mode,
        "page_count": None if args.pages == "auto" else int(args.pages),
        "canvas": args.canvas,
        "target_pixels": target_pixels,
        "style": args.style,
        "brand": None,
        "image_generation_status": "not_started",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pages": [],
    }
    (project / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (project / "storyboard" / "README.md").write_text("# Storyboard\n\nUse the skill's templates/storyboard.md. Draft first, then update manifest.page_count.\n", encoding="utf-8")
    (project / 'production' / 'README.md').write_text('# Production plan\n\nUse templates/production-plan.md to map each page to a communication goal and source geometry.\n', encoding='utf-8')
    (project / "reviews" / "README.md").write_text("# Reviews\n\nAdd visual and factual QA notes. Automated PNG validation is not editorial approval.\n", encoding="utf-8")
    print(project)
    return project


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--topic", default="未定主题", help="Topic (may be tentative)")
    p.add_argument("--slug", required=True, help="Safe Latin project folder name")
    p.add_argument("--out", default="projects", help="Parent directory")
    p.add_argument("--platform", default="unspecified", help="Not locked to Xiaohongshu")
    p.add_argument("--mode", choices=["scratch", "adapt", "reference", "edit", "plan_only"], default="scratch")
    p.add_argument("--pages", default="auto", help="auto or positive integer")
    p.add_argument("--canvas", default="unspecified", help="Aspect ratio such as 3:4, 1:1, 9:16")
    p.add_argument("--pixels", help="Exact target image pixels e.g. 1080x1440")
    p.add_argument("--style", default="auto", help="auto or preset:<id> or reference-images")
    args = p.parse_args(argv)
    if args.pages != "auto" and (not args.pages.isdigit() or int(args.pages) < 1):
        p.error("--pages must be 'auto' or a positive integer")
    if args.canvas != "unspecified":
        ratio = re.fullmatch(r"(\d+):(\d+)", args.canvas)
        if not ratio or not int(ratio[1]) or not int(ratio[2]):
            p.error("--canvas must be 'unspecified' or a positive ratio like 3:4")
    try:
        create(args)
    except (ValueError, argparse.ArgumentTypeError, FileExistsError, PermissionError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
