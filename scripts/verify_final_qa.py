#!/usr/bin/env python3
"""Verify QA against *current bytes*, optionally require manual page approvals.

This is integrity validation, not substitute for visual or editorial inspection.
"""
import argparse
import json
import sys
from pathlib import Path
from qa_images import sha256_file, inspect


def verify(project:Path,report_file:Path,require_review=False):
    errs=[]
    project=project.resolve()
    try: report=json.loads(report_file.read_text(encoding='utf-8'))
    except Exception as exc:return [f'Unreadable QA report: {exc}']
    if report.get('project')!=str(project):errs.append('QA report belongs to a different project')
    if report.get('automated_status')!='passed' or report.get('errors'):errs.append('QA report does not show a successful structural check')
    if not report.get('strict'): errs.append('Final QA report was not run in --strict mode')
    manifest=project/'manifest.json'
    if not manifest.is_file() or report.get('manifest_sha256')!=sha256_file(manifest):errs.append('Manifest modified since QA report')
    current=inspect(project,strict=True)
    if current.get('errors'):errs.extend('Current files: '+e for e in current['errors'])
    old={item['file']:item.get('sha256') for item in report.get('pages',[]) if isinstance(item,dict) and 'file' in item}
    now={item['file']:item.get('sha256') for item in current['pages']}
    if old!=now:errs.append('Final image set changed since QA report (files/hashes mismatch)')
    if require_review:
        manual_file=project/'reviews'/'page-review.json'
        try:
            manual=json.loads(manual_file.read_text(encoding='utf-8'))
            manual_pages={p['file']:p for p in manual.get('pages',[]) if isinstance(p,dict) and 'file' in p}
            if not manual.get('reviewed_by') or not manual.get('reviewed_at'):
                errs.append('Manual reviewer and review time required')
            for page in current['pages']:
                reviewed=manual_pages.get(page['file'])
                if not reviewed:errs.append('Missing manual review: '+page['file']);continue
                if reviewed.get('sha256')!=page['sha256']:errs.append('Stale manual review: '+page['file'])
                if reviewed.get('status')!='approved':errs.append('Manual review not approved: '+page['file'])
                for field in ('source_fidelity','text_and_readability','visual_consistency','rights'):
                    if reviewed.get(field)!='checked': errs.append(f'Manual {field} not checked: {page["file"]}')
        except Exception as exc:errs.append(f'No valid manual review: {exc}')
    return errs


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('project')
    p.add_argument('--report',required=True)
    p.add_argument('--require-review',action='store_true')
    args=p.parse_args(argv)
    errs=verify(Path(args.project),Path(args.report),args.require_review)
    if errs:
        for err in errs:print('ERROR:',err)
        return 1
    print('PASS: current image hashes and strict QA report match.'+ (' Manual approval records match.' if args.require_review else ' Manual content/visual QA not required by this command.'))
    return 0

if __name__=='__main__':sys.exit(main())
