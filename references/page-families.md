# Flexible page families and variants

Layout families are a *design reasoning vocabulary*, not a library of compulsory fixed templates.

## Two-level choice

1. **Communication intent**: hook, explanation, demonstration, evidence, comparison, story beat, selection guide, checklist, proof, summary, etc.
2. **Composition**: choose family and distinct variant from required content + source asset shape + text density + mobile readability + rhythm against neighboring pages.

Example families (extend freely):

- Hero: oversize headline, dominant photo, kinetic typography, split-cover
- Process: linear chain, branching diagram, stage ladder, radial network
- Instruction: screenshot hero + labels, steps with cropped details, split screen, before/after action
- Comparison: paired panels, matrix, superimposed contrast, annotated deltas
- Evidence: full-figure spotlight, overview/detail, original photo with captions, charts
- Editorial: quote-led story, image-and-pullquote, multi-image magazine, notebook spread
- Utility: checklist, decision tree, cheatsheet, recipe/packing list
- Closing: key insight, next action, small reference list, follow-up question

Never prescribe that every family have a certain number of variants for a very short job. A 1-page task needs only one candidate; a longer carousel should consciously vary visible skeletons. A consistent DNA is not identical placement.

## Page blueprint

Per page record: page_id, job, exact verified copy, asset IDs, geometry, chosen family, proposed variant, alternative variant if useful, reasoning, density, source fidelity risks, output ratio and exact pixels if requested.

Source asset disposition: preserve as-is / crop safely / show overview + zoom / split across pages / replace only with verified source / request higher resolution / omit. Do not recreate charts or real UI as evidence. For exact code, values, axes, or labels, first use the authentic source image or ask the image model to preserve the source; use controlled rendering only for a specific approved fidelity exception, never as the default way to add all page text.

Only introduce complex family IDs or variants as internal metadata. Do not expose them to the end user without request.
