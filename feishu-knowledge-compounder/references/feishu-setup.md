# Feishu Setup

## Goal

Prepare one Feishu app so the skill can:

1. Create or update a Feishu Base.
2. Insert structured knowledge rows.
3. Send reminder messages.

## Identity Modes

This skill supports two Feishu calling modes:

1. App identity via `tenant_access_token`
2. User identity via `user_access_token`

Use app identity when you want a fully automated system with no user login dependency.

Use user identity when your app does not yet have the required app scopes for Base operations, but you do have user-identity authorization and a valid `user_access_token`.

## One-Time Setup

1. Create a self-built app in the Feishu Open Platform.
2. Enable the bot capability if you want to send reminders through the app message API.
3. Add permissions for Base creation or record writes.
4. Give the app document access to the Base or target folder.
5. Export the environment variables before running the helper script.

## Minimum Permissions

Use these permissions for the Base workflow:

- `base:app:create` or `bitable:app`
- `base:table:create` or `bitable:app`
- `base:record:create` or `bitable:app`

Use these permissions for reminder delivery through the app message API:

- `im:message`
- or `im:message:send_as_bot`

If you only want reminder delivery through a group custom bot webhook, you can skip the IM message permissions and use a webhook instead.

## Document Access

The helper script uses `tenant_access_token`.

That means:

- The app must have document permissions to the target Base.
- If you create a new Base inside a folder, the folder must already be accessible to the app.
- If folder-based creation fails, create the Base in the root or use an app-created folder.
- If the app creates the Base in its own space, the human user may still need an explicit collaborator grant before the Base opens in the Feishu UI.

### Important: folder access is stricter than Base access

Creating a Base with `folder_token` is not the same as writing to an existing Base.

- For an existing Base, the fastest path is usually: create the Base manually in Feishu, then use `... -> 更多 -> 添加文档应用` to grant the app `可管理`.
- For a folder, Feishu requires the app to have folder-level cloud-drive access first. In practice this often means:
  - the app needs the relevant Drive API scope
  - the app bot must be reachable by the folder owner
  - the target folder must be shared to a group that contains the app bot

If you only need the final knowledge base to live in a specific folder, the manual-create-then-add-app route is usually the least fragile option.

## Environment Variables

Start from the example file in the skill root:

```bash
cp .env.example .env
```

Then fill only the variables you actually plan to use.

The helper script auto-loads `.env` from the current directory or the skill root, so after you create `.env` you can run the script directly.

### Required for Base creation and syncing

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

### Optional alternative for user-identity calls

```bash
export FEISHU_USER_ACCESS_TOKEN="u_xxx"
```

If `FEISHU_USER_ACCESS_TOKEN` is present, the script uses it directly for Base operations instead of creating a `tenant_access_token`.

### Recommended after bootstrap

```bash
export FEISHU_COMPOUNDER_CONFIG="/absolute/path/to/feishu-config.json"
```

If you do not use a config file, provide these directly:

```bash
export FEISHU_BASE_APP_TOKEN="app_xxx"
export FEISHU_CONVERSATIONS_TABLE_ID="tbl_xxx"
export FEISHU_GAPS_TABLE_ID="tbl_xxx"
export FEISHU_READING_TABLE_ID="tbl_xxx"
```

### Optional for creating a new Base in a folder

```bash
export FEISHU_BASE_FOLDER_TOKEN="fld_xxx"
```

### Optional for controlling where tutorial documents are created

```bash
# Preferred: pass a folder URL, wiki URL, or a docx URL that already belongs to a wiki node
export FEISHU_DOC_PARENT_URL="https://trip.larkenterprise.com/wiki/wiki_xxx"

# Optional direct token fallback
export FEISHU_DOC_PARENT_TOKEN="wik_xxx"
```

Notes:

- If `FEISHU_DOC_PARENT_URL` points to a folder, tutorial docs are created in that folder.
- If it points to a wiki page, tutorial docs are created as child pages under that knowledge node.
- If it points to a `docx` URL, this only works when the document already belongs to a wiki node. A plain standalone doc cannot be used as a parent container.
- Wiki-parent mode requires wiki permissions such as `wiki:node:read` and `wiki:node:create`, or `wiki:wiki`.

### Reminder via app message API

Use one target style:

```bash
export FEISHU_NOTIFY_OPEN_ID="ou_xxx"
```

or

```bash
export FEISHU_NOTIFY_CHAT_ID="oc_xxx"
```

The script automatically infers `open_id` or `chat_id` from these variables.

### Contributor attribution for team use

Shared team setup keeps the Feishu app, Base, document root, and table config in the skill. Each teammate only needs a personal contributor identity:

```bash
export FEISHU_CONTRIBUTOR_OPEN_ID="ou_xxx"
export FEISHU_CONTRIBUTOR_NAME="姓名"
```

When a teammate uses the skill for the first time and this personal config is missing, ask with this message:

```text
Hey 朋友，欢迎使用「飞书知识复利」小助手。

团队共用的知识库已经准备好了。开始之前，我需要先认识一下你，好让后续沉淀的知识资产能正确关联到你的贡献。

请回复：

飞书姓名：xxx
open_id：ou_xxx
是否接收推送：是 / 否

收到后我会自动完成配置。之后你沉淀的每一份经验，都会进入团队能力资产库，并保留为你的长期贡献。
```

If the user chooses to receive reminders, also set `FEISHU_NOTIFY_OPEN_ID` to the same `open_id`. If contributor identity is omitted, the script falls back to `FEISHU_NOTIFY_OPEN_ID`.

### Reminder via custom bot webhook

```bash
export FEISHU_NOTIFY_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

If the custom bot uses a signing secret, also set:

```bash
export FEISHU_NOTIFY_WEBHOOK_SECRET="xxx"
```

## Recommended First Run

1. Check what is still missing:

```bash
python3 scripts/feishu_compounder.py doctor
```

2. Bootstrap the Base:

```bash
python3 scripts/feishu_compounder.py bootstrap \
  --base-name "AI 知识复利系统" \
  --config-out ./feishu-config.json
```

3. Verify connectivity after bootstrap:

```bash
python3 scripts/feishu_compounder.py doctor --ping --config ./feishu-config.json
```

If the Base writes successfully but your own account still cannot open the page, grant your user account back onto the Base:

```bash
python3 scripts/feishu_compounder.py grant-access \
  --config ./feishu-config.json
```

4. Then sync a distilled note:

```bash
python3 scripts/feishu_compounder.py sync \
  --config ./feishu-config.json \
  --note-json ./note.json \
  --notify
```

5. After you have accumulated some entries, turn the existing Base back into reminders:

```bash
python3 scripts/feishu_compounder.py review \
  --config ./feishu-config.json \
  --notify
```

## Troubleshooting

- If Base creation returns a permission error, verify the app can edit the target folder or create the Base in the root.
- If `folder_token` creation fails with a folder permission error, prefer creating an empty Base manually in that folder and then adding the app as a document application with `可管理`.
- If the Base was created successfully but opens with a permission request in the UI, run `grant-access` to add your `open_id` as a collaborator.
- If reminder sending fails with an IM permission error, verify the bot capability is enabled and the target user or group is in scope.
- If webhook delivery fails, verify the webhook URL, secret, and message size.
- If syncing fails after bootstrap, make sure the config file still points to the correct `app_token` and table IDs.
