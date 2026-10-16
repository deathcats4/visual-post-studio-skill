#!/usr/bin/env python3
"""Hash-bound structural QA for independent final PNG/JPEG visual-post pages.

NOTE: No OCR or aesthetic/factual validation is performed. Strict QA requires Pillow.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

PNG_SIGNATURE=b'\x89PNG\r\n\x1a\n'
OUTPUT_SCHEMA=1


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as file:
        while True:
            chunk=file.read(1024*1024)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()


def dims(path: Path) -> tuple[int,int,str]:
    """Read dimensions only; this does not prove a complete image is decodable."""
    with path.open('rb') as f:
        start=f.read(26)
        if start.startswith(PNG_SIGNATURE) and start[12:16]==b'IHDR':
            w,h=struct.unpack('>II', start[16:24]); kind='PNG'
        elif start[:2]==b'\xff\xd8':
            kind='JPEG'; f.seek(2); w=h=0
            while True:
                marker=f.read(1)
                if not marker: break
                if marker!=b'\xff': continue
                n=f.read(1)
                while n==b'\xff': n=f.read(1)
                if not n: break
                mid=n[0]
                if mid==0xD9 or mid==0xDA: break
                if mid==0x01 or 0xD0<=mid<=0xD7: continue
                seg_len=struct.unpack('>H',f.read(2))[0]
                if seg_len<2: raise ValueError('corrupt JPEG segment')
                if mid in {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}:
                    f.read(1)
                    h,w=struct.unpack('>HH', f.read(4)); break
                f.seek(seg_len-2,1)
        else: raise ValueError('not a PNG/JPEG file')
    if w<=0 or h<=0 or w>100000 or h>100000: raise ValueError('invalid or missing image dimensions')
    return w,h,kind


def get_image_decoder():
    try:
        from PIL import Image
    except ImportError:
        return None
    return Image


def decoded_dims(path: Path, decoder) -> tuple[int,int,str]:
    with decoder.open(path) as image:
        w,h=image.size
        kind=image.format
        if kind not in {'PNG','JPEG'}:
            raise ValueError('not a PNG/JPEG file')
        if w<=0 or h<=0 or w>100000 or h>100000:
            raise ValueError('invalid image dimensions')
        image.verify()
    # verify() checks file integrity without decoding pixels; reopen before load().
    with decoder.open(path) as image:
        image.load()
    return w,h,kind


def load_manifest(project: Path):
    file=project/'manifest.json'
    try:
        manifest=json.loads(file.read_text(encoding='utf-8'))
        if not isinstance(manifest,dict): raise ValueError('manifest must be an object')
        return manifest
    except Exception as exc:
        raise ValueError(f'Cannot load manifest.json: {exc}') from exc


def inspect(project: Path, *, strict:bool=False) -> dict:
    project=Path(project).resolve()
    errors=[]; warnings=[]; pages=[]
    decoder=get_image_decoder()
    integrity_check='full_decode' if decoder is not None else 'header_only'
    if decoder is None:
        (errors if strict else warnings).append(
            'Pillow is required for full image decoding; only headers can be checked. '
            'Install with: python -m pip install -r requirements-image-qa.txt'
        )
    try: m=load_manifest(project)
    except ValueError as exc:
        errors.append(str(exc)); m={}
    src=project/'images'/'final'
    files=sorted(p for p in src.iterdir() if p.is_file() and p.suffix.lower() in {'.png','.jpg','.jpeg'}) if src.is_dir() else []
    expected=m.get('page_count')
    if not isinstance(expected,int) or isinstance(expected,bool) or expected<1:
        (errors if strict or m.get('image_generation_status')=='complete' else warnings).append(
            'manifest.page_count is not a positive integer; a completed image project must resolve an exact count'
        )
    elif len(files)!=expected:
        errors.append(f'Expected {expected} page images, found {len(files)}')
    if not files: errors.append('No final images in images/final/')
    numbers=[];seen_hash={}
    target=m.get('target_pixels')
    ratio=m.get('canvas','unspecified')
    desired_ratio=None
    if ratio!='unspecified':
        match=re.fullmatch(r'(\d+):(\d+)',str(ratio))
        if not match or not int(match[1]) or not int(match[2]): errors.append(f'Invalid canvas ratio: {ratio}')
        else: desired_ratio=int(match[1])/int(match[2])
    if target is not None and (not isinstance(target,list) or len(target)!=2 or any(type(v)!=int or v<=0 for v in target)):
        errors.append('target_pixels must be [positive_width, positive_height] or null')
        target=None
    for file in files:
        num=re.match(r'^(\d{2,3})(?:[-_].*)?\.(?:png|jpe?g)$',file.name,re.I)
        if not num: errors.append(f'Bad page filename: {file.name} (must start 01, 02...)')
        else:
            numbers.append(int(num[1]))
        try:
            w,h,fmt=decoded_dims(file,decoder) if decoder is not None else dims(file)
            size=file.stat().st_size
            digest=sha256_file(file)
            if digest in seen_hash: errors.append(f'Identical image bytes: {seen_hash[digest]} and {file.name}')
            seen_hash[digest]=file.name
            if target and [w,h]!=target:
                (errors if strict else warnings).append(f'{file.name}: {w}x{h} != requested {target[0]}x{target[1]}')
            if desired_ratio and abs((w/h)-desired_ratio)>0.0125:
                (errors if strict else warnings).append(f'{file.name}: {w}:{h} differs from ratio {ratio}')
            if size<500: warnings.append(f'{file.name} unusually small ({size} bytes)')
            pages.append({'file':file.name,'width':w,'height':h,'format':fmt,'size_bytes':size,'sha256':digest,'image_integrity':integrity_check})
        except Exception as exc: errors.append(f'{file.name}: image integrity check failed ({exc})')
    if numbers and sorted(numbers)!=list(range(1,len(files)+1)):
        errors.append(f'Page numbering not continuous/unique from 01: {sorted(numbers)}')
    if m.get('image_generation_status')!='complete':
        (errors if strict else warnings).append("manifest.image_generation_status != complete; a final deliverable must be marked complete only after actual production")
    warnings.append('Automated checks do NOT verify text, technical facts, UI authenticity, image rights, or design quality')
    report={
        'schema_version':OUTPUT_SCHEMA,
        'generated_at':datetime.now(timezone.utc).isoformat(),
        'project':str(project),
        'strict':strict,
        'image_integrity_check':integrity_check,
        'manifest_sha256':sha256_file(project/'manifest.json') if (project/'manifest.json').is_file() else None,
        'expected_count':expected,
        'pages':pages,
        'errors':errors,
        'warnings':warnings,
        'automated_status':'passed' if not errors else 'failed',
        'visual_editorial_review':'NOT_PERFORMED_BY_SCRIPT',
    }
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('project')
    p.add_argument('--report',help='Output qa-report.json path')
    p.add_argument('--strict',action='store_true')
    args=p.parse_args(argv)
    report=inspect(Path(args.project),strict=args.strict)
    if args.report:
        out=Path(args.report)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'automated_status':report['automated_status'],'errors':report['errors'],'warnings':report['warnings'],'page_count':len(report['pages'])},ensure_ascii=False,indent=2))
    return 0 if not report['errors'] else 1

if __name__=='__main__':sys.exit(main())
