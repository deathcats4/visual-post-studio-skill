#!/usr/bin/env python3
"""Create minimal shareable runtime (or optional-source examples) from a dev checkout."""
import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

RUNTIME_FILES=['SKILL.md','README.md','QUICKSTART.md','LICENSE','requirements-image-qa.txt']
RUNTIME_DIRS=['references','templates','styles']
RUNTIME_SCRIPTS=['new_project.py','new_style_pack.py','package_skill.py','preflight.py',
                 'qa_images.py','validate_project.py','validate_skill.py','verify_final_qa.py']
IMAGE_SUFFIXES={'.png','.jpg','.jpeg','.webp','.gif','.bmp','.tif','.tiff','.svg','.avif','.heic','.heif','.ico','.apng'}


def package(root:Path,destination:Path,with_references:bool=False):
    root=root.resolve()
    destination=destination.resolve()
    if destination.exists():raise FileExistsError(f'Destination exists: {destination}')
    if destination==root or root in destination.parents:raise ValueError('Destination must be outside source root')
    temp=destination.parent/(destination.stem+'-stage')
    if temp.exists():raise FileExistsError(f'Work directory already exists: {temp}')
    if not (root/'SKILL.md').is_file():raise ValueError('Root is not a Skill (missing SKILL.md)')
    stage=temp/'visual-post-studio'
    try:
        stage.mkdir(parents=True)
        for filename in RUNTIME_FILES:
            shutil.copy2(root/filename,stage/filename)
        for name in RUNTIME_DIRS:
            src=root/name
            if not src.is_dir():raise ValueError('Missing runtime directory: '+name)
            shutil.copytree(src,stage/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
        (stage/'scripts').mkdir()
        for name in RUNTIME_SCRIPTS:
            shutil.copy2(root/'scripts'/name,stage/'scripts'/name)
        if (root/'agents').is_dir():
            shutil.copytree(root/'agents',stage/'agents',ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
        if not with_references:
            for style_file in (stage/'styles').rglob('style.json'):
                data=json.loads(style_file.read_text(encoding='utf-8'))
                data['references']=[ref for ref in data.get('references',[]) if Path(ref).suffix.lower() not in IMAGE_SUFFIXES]
                data['example_images_excluded']=True
                style_file.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            for path in (stage/'styles').rglob('*'):
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:path.unlink()
        with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob('*')):
                if path.is_file():archive.write(path,path.relative_to(temp))
    finally:shutil.rmtree(temp,ignore_errors=True)
    return destination


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]))
    p.add_argument('--output',required=True)
    p.add_argument('--include-example-images',action='store_true')
    args=p.parse_args(argv)
    try:
        out=package(Path(args.root),Path(args.output),args.include_example_images)
        print(f'PACKAGED: {out} ({out.stat().st_size} bytes)')
        return 0
    except (ValueError,FileExistsError,OSError) as exc:
        print('ERROR:',exc,file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
