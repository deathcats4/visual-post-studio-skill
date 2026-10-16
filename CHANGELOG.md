# Changelog

## Unreleased

- 默认由图像模型直接生成包含文字的完整图页，并先覆盖全部指定来源。

## 3.0.2 (2026-10-13)

- Add a source-only development workflow: explicit file saves validate HEAD plus those files, run regression tests, commit only the intended change, and sync managed installations from the committed revision.
- Record source path, commit, version and runtime hashes in local installation receipts. Reject replacement of modified or unmanaged copies; stage deployments and restore the previous copy if replacement fails.
- Pin deployment and release snapshots to their recorded commits; stop saves if the source changes during validation. Provide explicit backup-before-reinstall recovery for locally edited managed copies.
- Add committed-source release building with public/development ZIPs and test/hash evidence, preserving existing releases and excluding local installation state.
- Isolate release builds from test side effects: generate the development ZIP directly from Git and build the runtime from a fresh committed snapshot, excluding generated caches and temporary edits.
- Keep maintenance scripts, development instructions, cases, tests and hooks out of runtime packages through an explicit production-script list.
- Add Chinese UI metadata and case records for the prior four repaired failure classes, with real visual acceptance cases explicitly pending.
- Add regression coverage for candidate isolation, preserved unrelated work, failure recovery, installation updates and release boundaries. No new claim of end-to-end visual quality validation.

## 3.0.1 (2026-10-13)

- Strict final-image QA now verifies PNG/JPEG files and loads their pixels with Pillow, rejecting truncated files and corrupt PNG chunks instead of accepting plausible headers.
- Final verification repeats the decode check against current files. Reports label full decoding versus header-only inspection; missing Pillow explicitly fails strict QA.
- Require an exact positive integer page count for strict QA and projects marked complete; unresolved counts remain valid during drafting.
- Recursively exclude common image assets throughout `styles/` from public runtime packages, including nested paths and SVG, and remove matching style references. Explicit image-inclusive packages retain those assets.
- Validate project pixel input and all style reference paths before creating output directories, so rejected inputs allow corrected retries without partial scaffolds or tracebacks.
- Include the image-QA dependency file in both runtime package variants and report decoder readiness in preflight. Clarify the legacy header-only validator and automated review limits.
- Store optional environment notes under `metadata` for compatibility with the local Codex skill validator, while retaining dependency instructions in the workflow and user docs.
- Add 13 regression tests covering these failure cases and preserved draft/image-inclusive behavior; all 25 tests pass locally.

## 3.0.0 (2026-10-13)

- Reworked from a prompt-oriented workflow to multi-route, modular production logic.
- Added Visual DNA distinct from narrative and page geometry, inspired by lessons from `scholar-ppt-cn` architecture without copying PPTX-specific behavior.
- Added content-driven page families/variants and editable planning/Visual DNA templates.
- Added per-image model-call contract and QA escalation protocol.
- Added preflight, real file/hash-bound image QA, strict report verification and optional actual manual review gate.
- Added separate runtime ZIP packaging tool, omitting test/dev files and optionally excluding sample images.
- Kept generic creation, source adaptation, online style discovery, local edits, and no-image planning routes.
- Added tests for report invalidation after edits, duplicate images, runtime packaging and cross-topic neutrality.
- No claim of universal agent/image-model compatibility or automated subjective visual assessment.

## 2.2.0

- Added public design-reference discovery, template versus inspiration policy.

## 2.1.0

- First working general-purpose Agent Skill bundle with optional styles and scripts.
