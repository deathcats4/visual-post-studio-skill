---
name: visual-post-studio
description: Plan, research, art-direct, generate, revise, and verify visual posts and multi-page image carousels for any topic and platform. Start from an idea or adapt documents, learn styles from examples or discover references online, make independent page images, preserve user evidence, and run image-level QA. Use for graphic posts, tutorial cards, information visuals, covers, social carousels, style studies, and localized image edits.
license: MIT
metadata:
  version: "3.0.2"
  language: zh-CN/en
  compatibility: Agent Skills-capable hosts with file/vision access; image output requires a connected image generation/editing tool. Local scripts require Python 3.9+; strict final-image QA also requires Pillow.
---

# Visual Post Studio

Universal visual-post *production workflow*, not a fixed subject, account, aspect ratio, palette or page count. Prioritize the user's request and existing approvals. Do not infer a mandatory format, seven-page story, named author, example subject or particular app.

## 1. Select the task path internally

Read `references/production-routes.md` when scope is more than a straightforward edit or idea list. Route by output intent, not by topic:

- **Plan**: ideas, scripts, brief, content extraction, planning table, storyboard, or prompts only. Stop before image generation.
- **Create**: one or more finished images from scratch or supplied text/materials. Create actual images when an image tool exists, not prompt-only substitutes.
- **Explore**: user wants style comparisons or visual pilot pages. Discover/analyze references, generate requested independent visual samples, and stop if approval is requested.
- **Continue**: expand an approved page set. Inherit its Visual DNA and edit permissions; plan new page compositions by content.
- **Revise**: edit only named image(s)/region(s), preserving all other approved files and content.
- **Style discovery**: find inspiration or *verified* editable templates online when authorized and tools exist. Read `references/style-discovery.md`.
- **Style learning**: analyze user images, extracted examples, or an existing style pack; create an editable Visual DNA description. Do not claim weight training.

For complex or costly work, briefly state output, source authority, visual-reference relationship, planned approach, next stop, and deliverables **before costly work**. If the user already explicitly said “directly produce / continue,” execute without a redundant approval turn. Ask one question only for a material ambiguity. Do not surface internal route names, family IDs or other project jargon unless requested.

## 2. Content authority & planning

For no-source creation, read `references/content-planning.md`; gather or verify external facts when necessary and possible. For supplied files/transcripts/screenshots, treat them as source evidence. Maintain a compact source/evidence index: `fact or instruction -> source -> certainty -> target pages`. No invented interface labels, measurements, citations, test results, claims of success or visual evidence. Label creative inferences, placeholders and missing assets clearly.

Build a page-by-page production plan using `templates/production-plan.md` when generating more than one page or handling complex assets. Plan **communication tasks** before design coordinates: audience benefit, key message, exact visible copy, source assets, geometry, fidelity policy, information density, and possible layout direction. Do not simply chop a long source into equal blocks. Page roles (cover, process, steps, comparison, photo-story, checklist, data, etc.) are optional, not an ordered template. See `references/storyboard.md` and `references/page-families.md`.

For source-based tutorials, first read all materials the user names and map the complete supported workflow to pages; do not build the whole carousel around only the most salient subtopic. Base the cover promise on the user's actual reader task, not a surrounding project, account, or tool name unless it is central to that task. Separate observed demonstrations from recommended steps, and identify missing authentic UI or evidence assets before generation.

## 3. Style: Visual DNA != content geometry

When user supplies visuals or chooses a pack, read `references/visual-dna.md`. Extract colors, typography roles, spacing, framing, texture, image treatment, visual hierarchy, recurring components, footer practices, and variation boundaries into `templates/visual-dna.md`.

**Visual DNA describes how pages belong together. It must not dictate the factual narrative or force every page into the old reference's layout.** Choose each page's layout from communication task, number and shape of assets, information density, readability and neighboring-page rhythm. Create suitable layout families with variants only as much as the task needs. Do not force 3+ variants or a seven-page plan for a 1–3-page post.

Styles in `styles/` are **optional inspiration packs**. No mandatory house look. A requested style or approved page set takes precedence over presets. For online discovery distinguish publicly visible *inspiration* from actual reusable *editable templates*, track source URL, creator, usage rights, and avoid copying protected compositions. If search is unavailable, disclose it; never invent found references or licenses.

## 4. Image production

Read `references/image-production.md` and `references/image-call-contract.md` before generating. By default, use the available image-generation/editing model to create each complete finished page, including its layout, illustrations, and authorized on-image text. Do not generate decorative background art and then use code to set the page text. If wording or legibility fails, simplify the page and edit or regenerate it with the image model. Use code-based typesetting only when the user explicitly requests editable typesetting or exact source fidelity genuinely requires it; explain the reason and get approval before switching. **Each output page is one independent, full-canvas, front-facing image.** No contact sheet, split A/B poster, screenshot of a device displaying the page, composite of several finished pages, or pretend source screenshot. Montages are allowed only as *additional review artifacts* assembled from already separated final images.

Send a distinct task to the image model for each page: exact content, communication objective, chosen layout family/variant, approved Visual DNA, required source media and exclusion constraints. Use realistic factual material only from verified inputs. For edits, modify the requested region alone. Preserve authentic source screenshots and figures as evidence; never ask the model to invent a real interface or result. If the image model cannot retain exact source details, stop and surface the limitation or ask to use a narrowly scoped source-faithful exception.

If the user requests full production, prefer a brief 1–2-page pilot for *uncertain* visual systems or costly runs, then continue in small batches if confirmed. If already approved or user expressly authorizes the full set, continue without a mandatory pilot stop. Never claim an unavailable image tool ran. If the tool outputs approximate dimensions, confirm actual pixels and perform an authorized, non-destructive resize/export when possible.

## 5. QA, file integrity & delivery

Read `references/qa-protocol.md`. Review each result before advancing: factual grounding, actual evidence preservation, visible text and terminology, page legibility, design consistency without repeated lazy skeletons, individual-image integrity, and user constraints. If a page fails, redo that page only.

Where local execution is available:

```bash
python -m pip install -r requirements-image-qa.txt
python scripts/preflight.py --output preflight.json
python scripts/new_project.py --slug demo --topic "any topic" --out projects --pages 5 --canvas 3:4 --pixels 1080x1440
python scripts/qa_images.py projects/demo --report projects/demo/reviews/qa-report.json --strict
python scripts/verify_final_qa.py projects/demo --report projects/demo/reviews/qa-report.json
```

Strict QA requires fully decodable PNG/JPEG files and an exact positive integer `manifest.page_count`. Drafts may leave the count unresolved. Without Pillow, non-strict checks inspect headers only and label that limitation; strict checks fail. See `references/qa-protocol.md` for the acceptance rules.

The automated tools check file integrity, dimensions, naming, duplication, hashes and report freshness; they **cannot establish editorial correctness, text accuracy, UI authenticity, aesthetic quality or publication rights**. Record a real human/visual review separately using `templates/page-review.json`. Use `--require-review` at final verification only after the manual visual/content review was actually done. Any edited image invalidates its old hash-bound QA until rerun.

When no file tools exist, make the strongest available manual/visual checks and clearly report any unavailable test. Deliver independent image files, requested previews and source notes. On-image titles and instructions belong in the generated pages; social publication title/body/tags belong to the separate copywriting Skill and are not drafted here. Do not publish without authorization or imply uploaded/downloadable assets exist if not verified.

## 6. Read only applicable references

- `references/production-routes.md`: route selection, approvals and task scope
- `references/content-planning.md`: from-zero vs source-based content grounding
- `references/storyboard.md`: editorial sequencing and page planning
- `references/visual-dna.md`: extracting and locking portable style identity
- `references/page-families.md`: flexible page compositions, families and variants
- `references/style-discovery.md`: online visual discovery and licensed templates
- `references/style-learning.md`: style cards and reference image analysis
- `references/image-production.md`: image creation and correction decisions
- `references/image-call-contract.md`: repeated per-call constraints
- `references/qa-protocol.md`: QA and edit-bound integrity
- `references/permissions.md`: asset reuse, credit and public sharing
- `templates/`: content plan, DNA, page prompts, source index and manual QA
- `styles/`: optional user-extensible style packs; `editorial-tech` is merely a sample style
- `scripts/`: optional production preflight, image QA, hash verification, packaging and project scaffolding
