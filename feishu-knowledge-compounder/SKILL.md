---
name: feishu-knowledge-compounder
description: 将有价值的 AI 对话沉淀为可持续复用的飞书能力资产库。适用于把对话提炼为新增资产、方法论、认知演进、下一步行动和参考案例，写入飞书并通过提醒推动持续迭代。
---

# Feishu Knowledge Compounder

## Overview

Convert one AI conversation into a reusable Feishu capability asset instead of letting the insight disappear in the chat log. Sync the asset into one canonical Feishu Base table whose fields mirror the asset document structure, then optionally send a follow-up reminder through Feishu.

## Workflow

1. Decide the operation mode: `沉淀新资产`、`更新旧资产`、`查询已有资产`、`维护结构/schema`.
2. Distill the current conversation into the JSON schema in [references/note-schema.md](references/note-schema.md).
3. Run the helper script to create or reuse the Feishu Base, sync the distilled note, refresh its capability asset document, and optionally send a reminder.
4. Report what was saved, which document was refreshed, and what the next 1-3 actions should be.

## Operation Modes

### 1. 沉淀新资产

Use when a conversation produces a new reusable capability theme. Create one stable topic title, extract the asset fields, include `source`, and add `related_assets` only when there are existing assets worth connecting.

### 2. 更新旧资产

Use when the conversation continues an existing theme. Keep the same `title`, update `tldr.new_this_round`, append new `core_outputs` / `methodology` / `evolution` / `next_actions`, and preserve the existing document through upsert.

### 3. 查询已有资产

Use when the user asks what has already been accumulated. Read the canonical `对话沉淀` table first, then open the linked asset documents from `摘要` when detail is needed.

### 4. 维护结构/schema

Use when changing the asset document structure or Base fields. The document structure is the source of truth; after changing it, update the Base schema, note schema, record builder, record migration, document renderer, and dashboard references in the same pass.

## Setup Once

Read [references/feishu-setup.md](references/feishu-setup.md) before first use.

The script auto-loads `.env` from the current directory or the skill root, so you do not need to manually `export` variables every time.

Use `scripts/feishu_compounder.py bootstrap` to create or reuse a Feishu Base with one canonical table:

- `对话沉淀`

The old `不足追踪` and `阅读队列` tables are legacy/optional. They are no longer part of the default knowledge-compounding path because the canonical table already carries `下一步行动` and `参考案例`. If you need those old tables for historical data, set `FEISHU_CREATE_LEGACY_TABLES=true` before bootstrap or keep their existing table IDs in the config.

Prefer writing the bootstrap result to a config file so later syncs do not need table IDs by hand.

Example:

```bash
python3 scripts/feishu_compounder.py bootstrap \
  --base-name "AI 知识复利系统" \
  --config-out ./feishu-config.json
```

If the user already has a Feishu Base, pass `--app-token` to attach the tables there instead of creating a new Base.

If the Base was created by the app identity and the user cannot open it in the Feishu UI, run `grant-access` to explicitly grant the user's `open_id` back to the Base:

```bash
python3 scripts/feishu_compounder.py grant-access \
  --config ./feishu-config.json
```

By default, `grant-access` uses `FEISHU_NOTIFY_OPEN_ID` and grants `full_access`.

If the user insists that the Base must live in a specific Feishu folder, be careful:

- Creating directly with `folder_token` requires folder-level app access, which is stricter than ordinary Base write access.
- When folder-based bootstrap fails, the most reliable fallback is: have the user create an empty Base manually in that folder, add the app as a document application with `可管理`, then continue by attaching tables or migrating data into that Base.

## Team Member Onboarding

For shared team usage, treat the Feishu app, Base, document root, and table config as shared infrastructure. Treat contributor identity and personal reminder preference as per-user configuration.

Before the first `sync` for a new user, check whether `FEISHU_CONTRIBUTOR_OPEN_ID` and `FEISHU_CONTRIBUTOR_NAME` are configured in the current runtime. If either is missing, pause and ask with this exact message:

```text
Hey 朋友，欢迎使用「飞书知识复利」小助手。

团队共用的知识库已经准备好了。开始之前，我需要先认识一下你，好让后续沉淀的知识资产能正确关联到你的贡献。

请回复：

飞书姓名：xxx
open_id：ou_xxx
是否接收推送：是 / 否

收到后我会自动完成配置。之后你沉淀的每一份经验，都会进入团队能力资产库，并保留为你的长期贡献。
```

After the user replies, configure the local runtime:

- `FEISHU_CONTRIBUTOR_NAME`: the user's Feishu display name.
- `FEISHU_CONTRIBUTOR_OPEN_ID`: the user's Feishu `open_id`.
- `FEISHU_NOTIFY_OPEN_ID`: set to the same `open_id` only when the user chooses to receive push reminders.

## Distill the Conversation

Create a compact but reusable asset payload before calling the script.

The note is not a meeting summary. For a team reader, it should answer: why should I care, what can I reuse directly, what method can I follow, and what should happen next. Do not preserve the conversation just because it happened.

Always capture:

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

Add `conversation_date`, `agent`, `source_context`, and `reminder` only when they sharpen routing, review, or follow-up. Use `tags` for the 3 most core topic labels; do not create a separate `domain` field for new notes.

Canonical shape:

```json
{
  "title": "AI 辅助交互原型工作流",
  "tldr": {
    "topic": "AI 辅助交互原型工作流",
    "new_this_round": "建立 SVG 映射规范",
    "value": "提升原型还原度"
  },
  "core_outputs": ["HTML 模板规范", "SVG 映射规范", "Token 体系"],
  "methodology": {
    "name": "AI 交互原型生产流",
    "steps": ["定义页面类型", "匹配模板", "注入 Token", "映射 SVG", "生成页面", "验证 Demo"]
  },
  "evolution": {
    "previous_belief": "Prompt 决定质量",
    "current_belief": "Template + Token 决定质量"
  },
  "next_actions": [
    {"todo": "首页模板化", "priority": "high"},
    {"todo": "补齐 Token 体系", "priority": "medium"}
  ],
  "related_assets": [
    {"title": "飞书知识复利工作流", "relation": "复用同一套资产沉淀与复盘入口规则"}
  ],
  "references": [
    {"name": "Figma Make", "why": "参考其模板化生成机制"}
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
  "tags": ["AI 工作流", "原型生成", "设计资产"]
}
```

Write compactly, but never fake compactness with omissions:

- Do not use `...` or `…` in `tldr`, `core_outputs`, `methodology`, `evolution`, `next_actions`, `related_assets`, `references`, `source`, `source_context`, tutorial text, or dashboard text.
- Do not put Markdown emphasis markers such as `**重点**` or `__重点__` into note fields. Feishu tutorial blocks render plain text, so the markers can leak into the document and make the sentence harder to read.
- “简化” means rewriting the source into complete short sentences that still say the thing clearly. It does not mean cutting the sentence short and leaving an ellipsis.
- If a detail matters, compress it into concrete wording. If it does not matter, remove it cleanly instead of leaving a placeholder.
- Do not let `等`、`等等`、`诸如此类` carry important missing content by themselves. Name the actual category or drop the detail.
- Before running `sync`, scan the note JSON. If any `...` or `…` remains, rewrite that field before saving to Feishu. The helper script rejects note JSON that still contains ellipsis placeholders.

Keep the payload opinionated and concrete:

- Optimize for a teammate who opens the document cold and spends 30 seconds deciding whether it is useful.
- Put reader value before conversation history. The document should make sense even if the reader never saw the original chat.
- `tldr.value` must answer “what value does this give the team?” not “what did we talk about?”.
- `tldr.new_this_round` should name the reusable addition, not recap the discussion path.
- `core_outputs` must be a short “拿来即用” list. Prefer 2-5 items, each as a reusable asset name or short command phrase. Avoid long explanatory sentences.
- Do not put insights, arguments, process history, or meeting-note style takeaways into `core_outputs`. Move them to `methodology` or `evolution` only if they become reusable.

- Treat one knowledge entry as one reusable theme task. The smallest unit should not be one chat turn or one isolated insight. It should be one task or theme that the user is likely to revisit, continue, or review again.
- Use a stable `title` for the same long-running theme so `对话沉淀` can keep updating one topic record instead of creating duplicates.
- Keep `title` abstract enough to survive multiple rounds of iteration. Prefer `对象/场景 + 核心任务` or `主题 + 能力方向`, such as `AI 知识沉淀工作流`, `飞书知识复利工作流`, `AI 辅助交互原型工作流`.
- Do not put temporary details into `title`, such as tool names, file names, output formats, iteration markers, or this-round-only wording like `prototype-creator`, `HTML预览`, `v2`, `本次改稿`, `已完整落地`.
- Put round-specific details into `tldr.new_this_round`, `core_outputs`, `evolution`, or `next_actions`, not into the title itself.
- When one conversation contains both a business case and a reusable workflow/method, prefer the workflow/method as the theme title if that is the real reusable asset. Put the business case into tags or `source_context`.
- Keep `tags` to at most 3 labels. Choose the labels most tied to the stable asset theme, not every tool, format, temporary project, or side topic mentioned in the conversation.
- A good topic record should let the user answer three questions in under 30 seconds:
  - What task am I continuously working on?
  - What reusable asset or method did this round add?
  - What should I do next?
- If a note is only a single loose thought with no likely follow-up, merge it into an existing theme instead of creating a new topic.
- If one note contains several unrelated problems, split it into multiple topic records instead of forcing them into one title.
- Do not include `discussion_points` in new notes. Future retrieval cares about what was produced, not what was discussed.
- Use `contributor` to attribute the person who contributed this knowledge asset. Prefer Feishu `open_id` so the Base `贡献者` field can link to the employee directly. In a shared team setup, each teammate should configure `FEISHU_CONTRIBUTOR_OPEN_ID` and optionally `FEISHU_CONTRIBUTOR_NAME`; if omitted, the helper falls back to `FEISHU_NOTIFY_OPEN_ID`.
- Use `tldr` for a 3-second read: `topic`, `new_this_round`, and `value`.
- Write `core_outputs` as reusable assets: templates, specs, mappings, tokens, checklists, UI kits, scripts, prompts, evaluation rubrics, or named deliverables. The document renderer treats these as “可直接复用”, so each item should be short enough to scan.
- Write `methodology` only when the conversation creates or improves a repeatable way of working. Steps should be actionable verbs plus concrete objects.
- The helper accepts `workflow` as a compatibility alias, but canonical new notes should put the repeatable process in `methodology.steps`.
- Write `evolution` when the user's belief changed. Capture the before/after sharply; this is where compounding happens.
- Write `next_actions` as checklist items, not consulting-style gaps. Prefer 1-3 actions with `high`, `medium`, or `low` priority.
- Write `related_assets` as links to existing capability assets only. Do not invent a related page just to make the graph look connected.
- Write `references` as cases, tools, products, docs, or examples worth reusing. Do not default to book recommendations.
- Write `source` as provenance: conversation, article, document, product, or user-provided file. Keep it short; it is for trust and later retrieval, not for summarizing content.

Default extraction prompt:

```text
请提取：
1. 对团队的直接价值
2. 可直接复用的资产
3. 可照做的方法论
4. 关键认知变化
5. 下一步行动
6. 来源
7. 贡献者
8. 标签（最多 3 个）
9. 可关联的已有资产

不要记录讨论过程。
不要记录聊天内容。
不要把核心资产写成长句复盘。
不要新增领域字段，分类信息统一写入标签，且只保留最核心的 3 个。
只记录未来可复用的信息。
```

Use the built-in template command when you want a starting schema:

```bash
python3 scripts/feishu_compounder.py template
```

## Sync the Note

Write the note JSON to a local file, then sync it to Feishu.

Example:

```bash
python3 scripts/feishu_compounder.py sync \
  --config ./feishu-config.json \
  --note-json ./note.json \
  --notify
```

What `sync` does:

1. Upsert one topic record in `对话沉淀` based on the normalized theme title instead of always creating a new row.
2. Keep the Base fields isomorphic with the document structure: `摘要`、`贡献者`、`来源`、`TLDR主题`、`本次新增`、`价值`、`核心资产`、`方法论`、`认知演进`、`知识演化图谱`、`下一步行动`、`关联资产`、`参考案例`, plus routing metadata.
3. Whenever the document structure changes, run schema sync too: update `TABLE_SPECS["conversations"]`, `build_records()`, `normalize_conversation_record_fields()`, document renderers, and the migration/pruning logic together.
4. Backfill useful old fields into the new canonical fields, then prune old main-table fields such as `讨论问题`、`摘要正文`、`工作流`、`核心洞察`、`心智模型`、`知识缺口`、`行动建议`、`阅读建议`、`原始上下文`.
5. Do not mirror new `next_actions` into `不足追踪`, and do not turn `references` into `阅读队列` rows. Those tables are legacy/optional only.
6. Reuse the existing topic document in place when `摘要` already points to one; only create a new asset document when this topic has no document URL yet.
7. Generate the document as a reusable capability asset with provenance metadata including `贡献者`, plus `3 秒速览`、`知识演化图谱`、`可直接复用`、`方法论`、`认知演进`、`下一步行动`、`关联资产` and `参考案例`.
8. Refresh one dynamic Feishu dashboard document so the overview always follows the latest conversation sedimentation.
9. Automatically send one Feishu completion push after sync when a reminder target is configured.

Legacy reading queue expectations:

- `在线地址` should always be present. If a reliable book page cannot be found, write `暂无网络链接`.
- `封面图` should always be present. If no reliable cover is available, use the default cover asset.
- `阅读队列` remains available for older notes that still use `recommended_books`, but new notes should prefer `references`.

The completion push uses different copy for new versus updated topics:

- New topic: `你新增了一条知识资产：《主题名》`
- Updated topic: `你更新了一条知识资产：《主题名》`

If a document root is configured, the completion push should include both:

- the specific topic document URL
- the `知识复利系统入口` URL so the user can click back to the main overview or parent entry

When a topic already exists, `sync` keeps the latest `同步时间`, merges old domains into `标签`, prunes `标签` to the 3 most topic-relevant labels, and accumulates the reusable asset fields into the same topic record.
`摘要` is reserved for the asset document URL and must use the link text `查看详情`.

Dashboard behavior:

- The dashboard is a dedicated Feishu `docx` document, not another Base table.
- It should be reused in place on every refresh. Do not create a new dashboard document each time.
- If the user has specified a target file/folder/dashboard location, never silently fall back to another location when the target is not writable or not directly supported. Stop and ask the user whether to continue with a fallback target first.
- The dashboard should help the user quickly scan:
  - total sedimented topics / rounds
  - value extraction by design stage
  - conservative time-saved estimate
  - recent high-frequency topics
  - one encouragement line
  - a compact next-focus list
- Design-stage aggregation can be heuristic. Prefer stable stages such as `问题定义`、`方法搭建`、`方案设计`、`原型验证`、`协作交付`、`复盘沉淀`.
- If `feishu-config.json` includes `dashboard_target_url`, treat that as the user’s preferred dashboard destination and do not override it silently.
- If `feishu-config.json` includes `document_root_url`, use it in Feishu push messages as the clickable `知识复利系统入口`.
- If the user asks to rebuild only the dashboard without syncing a new note, use `refresh-dashboard`.

Tutorial documents can be routed three ways:

- Set `FEISHU_DOC_PARENT_URL` to a Feishu folder URL to create docs inside that folder.
- Set `FEISHU_DOC_PARENT_URL` to a Feishu wiki URL to create docs as child pages under that knowledge node.
- Set `FEISHU_DOC_PARENT_URL` to a `docx` URL only when that document already belongs to a wiki node; the script resolves the backing wiki node first, then creates the child page there.

If the target is a plain standalone `docx` document outside wiki, it cannot act as a parent container. In that case, use a folder URL or a wiki URL instead.

Use `--dry-run` first when you want to inspect the payload without touching Feishu.

## Check Setup

Use `doctor` before the first real run or whenever you are unsure which piece is missing.

Examples:

```bash
python3 scripts/feishu_compounder.py doctor
python3 scripts/feishu_compounder.py doctor --ping --config ./feishu-config.json
```

`doctor` reports whether the local `.env`, app credentials, config file, reminder target, and optional live Feishu connectivity are ready.

## Repair Access

Use `grant-access` when the skill can write to the Base but the human user still sees a permission request in the Feishu UI.

Example:

```bash
python3 scripts/feishu_compounder.py grant-access \
  --config ./feishu-config.json \
  --perm full_access
```

What `grant-access` does:

1. Read the Base token from the config or environment.
2. Use the Feishu Drive permission API to add a collaborator.
3. Return the granted collaborator and the Base URL so the user can reopen it immediately.

## Send Reminder Only

Use `send-reminder` when the knowledge rows are already saved and the user only wants a follow-up nudge.

Example:

```bash
python3 scripts/feishu_compounder.py send-reminder \
  --note-json ./note.json
```

## Review Existing Knowledge

Use `review` to generate a reminder from the current Feishu knowledge base instead of a fresh note JSON.

Example:

```bash
python3 scripts/feishu_compounder.py review \
  --config ./feishu-config.json \
  --notify
```

What `review` does:

1. Read recent rows from `对话沉淀`.
2. Prefer the canonical `下一步行动` field as the follow-up source.
3. Optionally include legacy `不足追踪` and `阅读队列` rows when those tables still exist in the config.
4. Compose one concise review message and optionally send it to Feishu.

## Upgrade Reading Queue

Use `upgrade-reading` when the user wants the `阅读队列` table to feel more like a visual bookshelf than a raw list.

Example:

```bash
python3 scripts/feishu_compounder.py upgrade-reading \
  --config ./feishu-config.json
```

What `upgrade-reading` does:

1. Ensure the reading table has `推荐次数`、`封面图`、`在线地址`、`提及频率`、`精华标签` fields.
2. Create or reuse a `阅读画册` gallery view.
3. Merge duplicate books into a single card and accumulate their `推荐次数`.
4. Keep `提及频率` aligned with the merged recommendation count.
5. Refresh the dashboard doc so the bookshelf metrics stay in sync.

## Refresh Dashboard

Use `refresh-dashboard` when the user wants to rebuild the overview doc from the current Feishu tables without creating a new knowledge note.

Example:

```bash
python3 scripts/feishu_compounder.py refresh-dashboard \
  --config ./feishu-config.json
```

What `refresh-dashboard` does:

1. Read current rows from `对话沉淀`, plus optional legacy rows from `不足追踪` and `阅读队列` when those table IDs exist.
2. Aggregate the data into headline metrics and stage-based value summaries.
3. Create the dashboard doc on first run, then keep updating that same document in place.
5. Backfill cover, link, and tag metadata from [references/book-metadata.json](references/book-metadata.json).

If the user wants to overwrite existing covers or links, rerun it with `--refresh-covers` or `--refresh-metadata`.

After this upgrade, future `sync` runs will upsert repeated books instead of creating duplicate rows.

## Upgrade Conversation Topics

Use `upgrade-conversations` when the user wants `对话沉淀` to behave like a topic knowledge base instead of a chat log.

Example:

```bash
python3 scripts/feishu_compounder.py upgrade-conversations \
  --config ./feishu-config.json
```

What `upgrade-conversations` does:

1. Ensure `标签` and `对话Agent` are multi-select fields, merge legacy `领域` values into `标签`, prune `标签` to 3 core labels, then prune the old `领域` field.
2. Ensure the canonical main-table fields match the capability document structure.
3. Migrate `摘要` into a URL field when needed.
4. Backfill old fields into `TLDR主题`、`本次新增`、`价值`、`核心资产`、`方法论`、`下一步行动`、`参考案例`.
5. Prune legacy main-table fields after backfill unless `FEISHU_KEEP_LEGACY_CONVERSATION_FIELDS=true`.
6. Merge same-theme conversation rows into one topic record and keep only the most recent `同步时间`.

## Upgrade Conversation Docs

Use `upgrade-conversation-docs` when the user wants every topic card in `对话沉淀` to point to a reusable capability asset document instead of a plain text summary.

Example:

```bash
python3 scripts/feishu_compounder.py upgrade-conversation-docs \
  --config ./feishu-config.json \
  --notify
```

What `upgrade-conversation-docs` does:

1. Read the merged topic rows from `对话沉淀`.
2. Generate one capability asset document per topic from `贡献者`、`TLDR主题`、`本次新增`、`价值`、`核心资产`、`方法论`、`认知演进`、`知识演化图谱`、`下一步行动` and `参考案例`, with legacy fallback from old summary and insight fields. In the document, `核心资产` is displayed as `可直接复用` and capped into a short team-readable list.
3. Apply the sedimented topic title to both the Feishu document title and the `对话沉淀` topic title, using `沉淀主题｜能力资产`.
4. Keep the document body from repeating the topic title; the body starts with metadata and `3 秒速览`, while the page title carries the topic.
5. Write the document URL back into `摘要` with the link text `查看详情`.
6. When `--notify` is passed, send a Feishu completion push with the refreshed document links.

If this command reports a permission warning, the app still needs document permissions such as `docx:document` or `docx:document:create`.

## Migrate Between Bases

Use `migrate` when the user needs to move the existing knowledge system into a different Base.

Example:

```bash
python3 scripts/feishu_compounder.py migrate \
  --from-config ./old-config.json \
  --to-config ./new-config.json
```

What `migrate` does:

1. Read the source Base tables from the old config.
2. Ensure the canonical target table exists in the destination Base. Legacy tables are created only when the source config actually has them.
3. Copy rows from `对话沉淀`, plus legacy `不足追踪` / `阅读队列` rows only when those tables are present.

## Reasoning Rules

Do not promise a hidden "after every chat" hook that does not exist. A skill can be used after each substantial conversation, but fully automatic follow-up requires an external scheduler or automation.

If the user explicitly wants recurring reminders:

1. Save the latest note JSON or make sure the Feishu Base already contains the relevant rows.
2. If automation tools are available, create a recurring automation that runs `review --notify` against the existing Base.
3. Keep recurring reminders narrow: the current topic, the next concrete action, and any reference case that genuinely informs that action.

## Output Standard

After using the script, report:

1. Where the note was stored.
2. Which capability asset document was created or refreshed.
3. The next 1-3 concrete actions.
4. Whether a reminder was sent and through which Feishu channel.

## Resources

- `scripts/feishu_compounder.py`: Bootstrap the Base, sync notes, and send reminders.
- `references/feishu-setup.md`: One-time Feishu app, permission, and environment setup.
- `references/note-schema.md`: Canonical JSON schema and example payload.
