# Visual-post QA and delivery contract

## What can be automatically tested

- PNG/JPEG files pass integrity verification and full pixel decoding with Pillow, with an exact positive integer page count and continuous page IDs.
- Expected dimensions and aspect ratios if specified.
- File data changes invalidate old QA reports (SHA-256 per page + manifest).
- Duplicate *bytes* between two finished pages flagged as suspicious.
- Manifest and report names, paths, basic structure, version consistency.

`python scripts/qa_images.py PROJECT --report PROJECT/reviews/qa-report.json --strict`

Then `python scripts/verify_final_qa.py PROJECT --report PROJECT/reviews/qa-report.json`.

Install the decoding dependency from the skill root with `python -m pip install -r requirements-image-qa.txt`. Preflight reports `strict_image_qa_ready`. Without Pillow, strict QA fails; non-strict inspection labels its result `header_only` and cannot establish that the complete image is readable. With Pillow, reports record `full_decode`; final verification repeats this check against current files.

An unresolved `manifest.page_count` is allowed only while drafting without strict QA. Resolve it to a positive integer before marking production complete or accepting the final images.

These tests do NOT prove that pages are beautifully composed, correct Chinese wording, exact code, actual screenshots, faithful figures, or legally usable. Do not claim they do.

## Visual and source review (human or actually performed multimodal inspection)

Compare final pages at full size and phone-thumbnail size. Mark each page in `reviews/page-review.json` using the template; do not auto-populate successful visual claims. Check:

- the generation method followed the approved path: complete pages, including on-image text, came from the image-generation/editing model; any controlled-typesetting exception was explained and approved;
- all named source materials were read and the planned reader workflow is covered across the pages; the cover states the actual user topic rather than an adjacent tool/project frame;
- facts versus source index; screenshot UI labels; file paths, version numbers, math and code;
- text overflow, glyph mistakes, typos, alignment, scale and reading order;
- page uniqueness and hierarchy versus Visual DNA; no lazy identical consecutive layouts;
- source media fidelity, data chart labels, no invented screenshots, numbers or UI successes;
- external reference license and required credits; personal information masked only where appropriate;
- published image and final checked file correspond.

If `--require-review` is used, verification will demand genuine `approved` statuses from `reviews/page-review.json` matching each final page's SHA-256. Approval is a manual declaration, **not** machine proof. Re-run checks and update review hashes on every edit; do not backdate or carry approvals across changes.

## Failure policy

Correct the failed page only; re-run the final QA. No hidden reconstruction or modification of approved unrelated pages. If necessary tools unavailable, report skipped checks explicitly and avoid implying checks passed.
