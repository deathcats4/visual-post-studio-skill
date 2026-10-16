# Per-image generation/edit contract

Before *each* image-model call, provide the agent/model with the constraints below adapted to the active platform and page. Do not rely on previous image calls to remember constraints.

1. Exactly ONE independently usable full-bleed finished page per output, correct portrait/landscape orientation and requested ratio. Do not draw two variants side by side, a contact sheet, a book spread, a product mockup, or an image sitting inside a visible frame/device.
2. The page's specific communication goal, content hierarchy and **exact authorized visible copy** must be included in the image-generation/editing task so the model returns a complete designed page with its text. No unsourced headings, facts, figures, paths, citation keys, or self-referential production language. Do not silently switch from a failed image to code-generated text overlays; shorten, edit, or regenerate with the image model. A controlled-typesetting exception requires a stated fidelity/editability need and the user's approval.
3. Apply approved Visual DNA for color roles, typography, contrast, spacing, and recurring brand marks. Adapt composition according to this page's blueprint; don't repeat the previous page by inertia.
4. Preserve supplied logos/photographs/real screenshot content as evidence when requested, and avoid fabricating a success screen or UI labels. Keep real screenshot pixels intact; if the image model cannot preserve them, stop and report the issue or seek approval for a narrowly scoped source-asset exception.
5. User's crop, fit, legibility, whitespace, source geometry and copy constraints take precedence over decoration. Don't invent potentially misleading scientific/medical/financial claims.
6. If editing, change only the specified page/region; retain unaffected style and content.
7. Return and inspect the page before proceeding. If output is a grid or multiple finished pages combined, reject and regenerate; cropping a failed grid does not make it a valid independent generation.

This contract is platform-independent: size/ratio come from user or project, never always 3:4 or 1080×1440.
