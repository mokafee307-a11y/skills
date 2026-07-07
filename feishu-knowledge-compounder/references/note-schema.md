# Note Schema

## Goal

Distill one substantial AI conversation into a reusable capability asset for Feishu.

The payload should not record the chat process. It should help a teammate quickly decide why the asset matters and what they can reuse directly:

- Direct team value
- New reusable assets
- New or improved methodology
- Belief changes
- A generated knowledge evolution map
- Next actions
- Related assets
- Reference cases
- Source provenance

## Required Keys

- `title`
- `tldr`
- `core_outputs`
- `methodology`
- `evolution`
- `next_actions`
- `related_assets`
- `references`
- `source`
- `contributor`
- `tags`

## Optional Routing Keys

- `conversation_date`
- `agent`
- `source_context`
- `reminder`

## Canonical JSON Shape

```json
{
  "title": "AI 辅助交互原型工作流",
  "conversation_date": "2026-06-10",
  "tags": ["AI 工作流", "交互原型", "设计资产"],
  "agent": "codex",
  "tldr": {
    "topic": "AI 辅助交互原型工作流",
    "new_this_round": "建立 SVG 映射规范",
    "value": "提升原型还原度"
  },
  "core_outputs": [
    "HTML 模板规范",
    "SVG 映射规范",
    "Token 体系"
  ],
  "methodology": {
    "name": "AI 交互原型生产流",
    "steps": [
      "定义页面类型",
      "匹配模板",
      "注入 Token",
      "映射 SVG",
      "生成页面",
      "验证 Demo"
    ]
  },
  "evolution": {
    "previous_belief": "Prompt 决定质量",
    "current_belief": "Template + Token 决定质量"
  },
  "next_actions": [
    {
      "todo": "首页模板化",
      "priority": "high"
    },
    {
      "todo": "补齐 Token 体系",
      "priority": "medium"
    }
  ],
  "related_assets": [
    {
      "title": "飞书知识复利工作流",
      "relation": "复用同一套资产沉淀与复盘入口规则"
    }
  ],
  "references": [
    {
      "name": "Figma Make",
      "why": "参考其模板化生成机制"
    }
  ],
  "source": {
    "type": "conversation",
    "name": "Codex 对话",
    "date": "2026-06-10"
  },
  "contributor": {
    "name": "贡献者姓名",
    "open_id": "ou_xxx"
  },
  "source_context": "一次围绕 AI 交互原型生成质量与可复用资产建设的对话。",
  "reminder": "下一轮优先把首页模板和 Token 体系补齐，再验证 SVG 映射规范是否提升还原度。"
}
```

## Writing Rules

- Do not summarize the discussion. Extract only future-reusable information.
- Optimize for a teammate who did not read the original conversation. They care about value and reusable assets, not how the conversation unfolded.
- Treat one knowledge entry as one reusable theme task. A topic should represent something the user is likely to revisit, continue, or review again.
- Keep `title` stable across conversations on the same long-running theme so Feishu can merge them into one topic record.
- Keep `title` abstract enough to survive multiple rounds of iteration. Prefer `对象/场景 + 核心任务` or `主题 + 能力方向`, such as `AI 辅助交互原型工作流` or `飞书知识复利工作流`.
- Put round-specific details into `tldr.new_this_round`, `core_outputs`, `evolution`, or `next_actions`, not into the title.
- Use `tags` as the only classification field. Keep at most 3 labels and choose the ones most tied to the stable asset theme; do not add `domain` to new notes.
- `tldr.topic` names the asset theme. `tldr.new_this_round` states the single most important reusable addition. `tldr.value` states what value this gives the team.
- Write `core_outputs` as a short “拿来即用” list, such as templates, specs, mappings, token systems, checklists, rubrics, scripts, prompts, or component libraries. Prefer 2-5 items. Use asset names or short command phrases, not long insight sentences.
- Do not put discussion recaps, arguments, or process history into `core_outputs`.
- Write `methodology` only when the conversation creates or improves a repeatable way of working. Each step should be an action plus a concrete object.
- Write `evolution` only when the user's belief changed. Capture the before and after sharply.
- The helper derives `知识演化图谱` from value, reusable assets, methodology, evolution, next actions, and related assets. Do not add a separate note key unless the graph needs a deliberate manual override.
- Write `next_actions` as checklist items with priorities. Prefer 1-3 concrete tasks over a long advisory list.
- Write `related_assets` only for existing assets worth cross-referencing. Do not invent assets just to fill the field.
- Write `references` as cases, products, tools, docs, examples, or benchmarks worth reusing. Do not default to book recommendations.
- Write `source` as provenance: conversation, article, document, product, or user-provided file. Use `type`, `name`, optional `url`, and absolute `date` when available.
- Write `contributor` as the person who contributed the reusable asset. Prefer Feishu `open_id` so the Base `贡献者` field can link to the employee directly. In a team setup, each teammate should configure `FEISHU_CONTRIBUTOR_OPEN_ID` and optionally `FEISHU_CONTRIBUTOR_NAME`; if omitted, the helper falls back to `FEISHU_NOTIFY_OPEN_ID`.
- Do not include `discussion_points` in new notes. The helper still accepts it only for legacy compatibility.
- Do not use `...` or `…` to stand in for content anywhere in the note.
- Do not use Markdown emphasis markers such as `**重点**` or `__重点__` inside note fields.
- Avoid using `等`、`等等`、`诸如此类` as a lazy substitute for concrete content.
- Use absolute dates like `2026-06-10` when dates matter.

## Compatibility Notes

The helper script still accepts `workflow` as an alias for method steps, `source_context` as a source fallback, plus legacy keys such as `summary`, `key_insights`, `mental_models`, `blind_spots`, `actions`, `recommended_books`, `讨论问题`, `核心洞察`, `心智模型`, `知识缺口`, `行动建议`, and `阅读建议`.

Legacy fields are converted into the new asset-oriented document layout when possible, but prefer the canonical keys above for new notes.

The Feishu Base main table must stay aligned with the document structure. Current asset documents map to `贡献者`、`来源`、`3 秒速览`、`知识演化图谱`、`可直接复用`、`方法论`、`认知演进`、`下一步行动`、`关联资产` and `参考案例`. When the document sections change, update the main-table fields in the helper script at the same time; do not add a document-only section or a Base-only field without a deliberate compatibility reason.
