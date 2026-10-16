#!/usr/bin/env python3
"""Validate the static Agent Skills bundle structure and optional style references."""
import argparse
import json
import re
import sys
from pathlib import Path


def check(root):
    root=Path(root).resolve()
    issues=[]
    f=root/'SKILL.md'
    if not f.is_file():
        return ['Missing SKILL.md']
    body=f.read_text(encoding='utf-8')
    m=re.match(r'\A---\r?\n(.*?)\r?\n---\r?\n',body,re.S)
    if not m:
        issues.append('SKILL.md missing YAML frontmatter')
        return issues
    raw=m.group(1)
    vals={}
    for line in raw.splitlines():
        if re.match(r'^[a-z][a-z-]*:',line):
            k,v=line.split(':',1)
            vals[k]=v.strip().strip('"\'')
    name=vals.get('name','')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name) or len(name)>64:
        issues.append(f'Invalid skill name: {name}')
    if root.name != name:
        issues.append(f'Root folder {root.name} does not match skill name {name}')
    desc=vals.get('description','')
    if not desc or len(desc)>1024:
        issues.append('Skill description missing/too long')
    if len(body.splitlines())>500:
        issues.append('SKILL.md exceeds 500 lines; use progressive disclosure')
    for fname in re.findall(r'(?:references|templates)/[a-z0-9-]+\.md',body):
        if not (root/fname).is_file():
            issues.append(f'Missing referenced file: {fname}')
    styles=root/'styles'
    for s in styles.iterdir() if styles.is_dir() else []:
        if not s.is_dir():
            continue
        if not (s/'style.md').is_file():
            issues.append(f'Missing style.md in {s.name}')
        j=s/'style.json'
        if j.exists():
            try:
                data=json.loads(j.read_text(encoding='utf-8'))
                if data.get('id')!=s.name:
                    issues.append(f'Style ID mismatch in {j}')
                for img in data.get('references',[]):
                    if not (s/img).is_file():
                        issues.append(f'Missing style image: {s.name}/{img}')
            except Exception as ex:
                issues.append(f'Invalid {j}: {ex}')
    if not (root/'README.md').is_file():
        issues.append('Missing README.md')
    return issues


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',nargs='?',default='.')
    args=p.parse_args(argv)
    issues=check(args.root)
    if issues:
        print('\n'.join('ERROR: '+e for e in issues))
        return 1
    print('PASS: Agent Skills frontmatter, required resources, style references')
    return 0

if __name__=='__main__':
    sys.exit(main())
