# Production routes & communication gates

Route selection is automatic. Separate decisions about **content source**, **visual reference**, **deliverable** and **production technique**; do not collapse them into one fixed pipeline.

| User says | Deliverable | Image-model action | Stop point |
|---|---|---|---|
| "只做策划/文案/分镜" | planning files/text | none | after plan |
| "直接生成 5 张图" | five independent images | per-page calls | final QA, unless material ambiguity |
| "先试试看风格" | 1–2 independent visual pilots | pilot calls | pilot approval |
| "按刚才的图继续" | new independent pages | inherit approved DNA | after batch or final as user requested |
| "只改第 N 页这里" | edited affected page only | image edit | after that edit |
| "找参考/搜模板" | sourced short list or reusable style summary | no generation unless requested | after discovery or direct generation if explicit |
| "学这张图的风格" | Visual DNA, optionally original new page | only if requested | style delivery or image output |

When scope is substantial and authorization is unclear, use one concise production summary: output, source, visual system, page count/aspect if resolved, first action, and next approval gate. Do not ask for repeated sign-offs for a scope already confirmed. Do not force a full storyboard for single localized edits.

Content-first planning can proceed without downloading a default style reference. If reference is requested but unavailable, note limitation and keep content planning separate. No background auto-publishing.

## Production-specific policies

- New multi-page: source/evidence -> planning (message + assets + density) -> Visual DNA (if applicable) -> family/variant mapping -> generate independent pages -> inspect -> QA.
- Continuation: approved pages + approved DNA are visual authority; new source material is content authority. Derive new variants; do not mechanically copy old interior-page coordinates.
- Edit: preserve everything outside approved edit boundary. Record affected page IDs and exact change; no silent re-render of accepted pages.
- Online discovery: visual inspiration versus actual editable file are different products, with different license/availability checks.
- High-stakes evidence: authentic screenshots, photographs, code and charts are source assets, not prompts for plausible recreations.
