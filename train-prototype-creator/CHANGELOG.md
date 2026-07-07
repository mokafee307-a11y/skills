# Changelog

## 2026-06-04 — Output Folder Picker Robustness Fix

### Changed

- Rewrote `scripts/choose_output_folder.sh` to be bash-compatible instead of relying on zsh-only builtins, so the folder picker keeps working even when another turn invokes it with `bash`.
- Updated `SKILL.md` to require direct execution of `scripts/choose_output_folder.sh` and to avoid surfacing bash/zsh mismatch details to the user.
- Updated `agents/openai.yaml` so the default prompt now nudges direct script execution instead of ambiguous shell-prefixed invocation.

### Why

Another conversation invoked the folder picker through `bash`, which exposed a zsh builtin mismatch and leaked internal shell details into the user-facing progress update. The picker should be shell-robust, and internal retry mechanics should stay out of the user-facing narration.

## 2026-06-04 — Final Demo Inner Page Template Guardrails

### Changed

- Tightened `SKILL.md` so final interaction demos must reuse `home / list / fill / occupy` page templates inside the phone preview whenever those page semantics are present, instead of inventing one-off `*-flow` page structures.
- Tightened `SKILL.md` and `interaction-spec.md` so real SVG assets must keep flowing through to the final demo whenever they exist, rather than silently falling back to text glyphs or placeholder icons.
- Documented that `interaction-demo` is only the desktop shell and coordination layer; the phone page truth source still lives in the page template manifests.

### Why

One generated deliverable reused the fixed desktop shell but still drifted inside the phone preview: page structure was rewritten as ad hoc flow blocks, home-page SVG assets degraded into text glyphs, and the tuned page CSS templates were bypassed. The shell alone is not enough guardrail; the inner pages also need template-first constraints.

## 2026-06-04 — Interaction Demo Preview Fit Fix

### Changed

- Updated `assets/templates/interaction-demo/interaction-demo-template.css` so the preview shell switches to a stacked layout on narrower windows, keeping the preview panel above the doc panel.
- Added a dedicated `phone-slot` wrapper and changed the interaction-demo phone stage to fit the full `375 × 812` device frame inside the available preview area instead of relying on stage scrolling.
- Updated `interaction-demo-template.js` to scale the phone from the real slot width and height after layout settles, reducing clipping caused by side rails and shell padding.
- Updated `interaction-spec.md` to document the new responsive shell rule: narrow windows should prioritize full-device visibility on first screen.
- Replaced the old `transform`-on-`.phone` scaling with a device-shell + fixed viewport model so the visual phone size and layout box stay consistent.
- Replaced the old `100dvh`-driven desktop shell sizing with a capped review-shell height model, so the preview shell stops trying to fill the entire browser window on desktop review setups.
- Fixed the preview-region layout so tabs and phone-stage now occupy a real fixed-height grid instead of letting the phone-stage self-size from content, which previously caused repeated shrink-on-click behavior after state rerenders.

### Why

The previous template fix only tried to keep the phone top visible. In narrower browser windows, the split shell itself still squeezed the preview area and could push the device bottom out of the first screen. The updated template now treats full-device visibility as the primary constraint, avoids false-fit behavior where the phone looked scaled down but its layout box still overflowed, and stops the desktop shell from overfilling the browser viewport by default.

## 2026-06-04 — Final Interaction Demo Shell Fixed

### Changed

- Added `assets/templates/interaction-demo/` as the fixed template package for final interaction demo HTML deliverables.
- Extracted the split-view desktop shell from the user-approved `interaction-preview-final-v2.html` into reusable template HTML, CSS, JS, and example data.
- Introduced a fixed data schema for final demos: `meta -> preview.frames -> stateRail.items[].phone -> doc.sections`.
- Updated `SKILL.md` so final demo requests now prefer `assets/templates/interaction-demo/manifest.json` instead of regenerating a new split-view shell.
- Rewrote `interaction-spec.md` to document the fixed shell, supported phone block types, supported doc section types, and validation expectations.

### Why

The final demo HTML had become a stable, user-approved artifact, but it still lived as a one-off file. Converting it into a template-first shell makes future final demos safer: the desktop framework stays fixed, while tabs, states, phone blocks, and doc sections vary through data.

## 2026-06-03 — Skill v2 restructuring

### Changed

- Rewrote `SKILL.md` from a long all-in-one rulebook into a shorter orchestration layer.
- Added a clear priority chain: user input → reference/Figma → SVG mapping → template → tokens → UI Kit/page patterns → generation rules.
- Moved detailed page scaffold rules into `references/rules/page-scaffolds.md`.
- Moved detailed list-page component constraints into `references/rules/list-components.md`.
- Kept existing templates, tokens, SVG assets, scripts, examples, and reference files unchanged.
- Added `backup/original/SKILL.original.md` for rollback.

### Why

The previous `SKILL.md` mixed stable principles, project-specific component details, execution steps, and output checks in one file. This made the skill harder for agents to follow and harder to maintain. The new structure keeps the main skill compact while preserving the detailed rules in opt-in reference files.

### Suggested next step

Run one real prototype task using the new skill. If a specific page starts ignoring a component rule, move that rule closer to the template or renderer rather than expanding `SKILL.md` again.

## V3 Preview Copy & Product Language Upgrade

- 保留原 skill name：`train-prototype-creator`。
- 新增 `references/ux-writing.md`：约束用户可见文案，要求把需求语言翻译成用户收益、用户结果和用户行动。
- 新增 `references/copy-review.md`：生成后检查 preview 文案，拦截“支持/按日期筛选/固定入口/Half Screen View/SVG/token”等系统语言进入用户界面。
- 更新 `SKILL.md`：新增用户语言优先、预览纯净优先、Preview / Spec 分离、Copy Review 自检。
- 明确 375px 手机预览区域只展示用户应该看到的产品内容；IA、成功标准、SVG 记录、token 等进入 spec、注释或设计师说明区。
