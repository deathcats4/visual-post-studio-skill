#!/usr/bin/env python3
"""Report local capabilities without claiming hosted tools exist."""
import argparse, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path


def check():
    try:
        from PIL import Image
        pillow_available=callable(Image.open)
    except ImportError:
        pillow_available=False
    return {
        'schema_version': 1,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(),
        'python_compatible': sys.version_info >= (3, 9),
        'optional_Pillow': pillow_available,
        'local_png_jpeg_header_check': True,
        'full_image_decode_available': pillow_available,
        'strict_image_qa_ready': sys.version_info >= (3, 9) and pillow_available,
        'image_generation_tool': 'unknown: determined by host agent, not by this script',
        'online_reference_search': 'unknown: determined by host agent, not by this script',
        'human_visual_qa': 'requires actual inspection; cannot be inferred',
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', help='JSON report path')
    args=p.parse_args()
    result=check()
    data=json.dumps(result, ensure_ascii=False, indent=2)+'\n'
    if args.output:
        dst=Path(args.output)
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(data,encoding='utf-8')
    print(data)
    return 0 if result['python_compatible'] else 1

if __name__=='__main__':
    sys.exit(main())
