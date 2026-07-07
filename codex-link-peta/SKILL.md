---
name: codex-link-peta
description: 为 Codex 项目接入自定义 API 网关或 OpenAI 兼容 base URL，安全保存 API key，注册或复用自定义 provider，把当前项目默认模型设置为 `claude-sonnet-4-6` 或用户指定模型，并完成验证。适用于用户明确要求“配置 base url / api key / model”“接网关”“切换当前项目默认模型”“固定到 claude-sonnet-4-6”“改成其他 API 模型如 image-2”或直接说“执行 codex-link-peta”时。注意：这个 skill 修改的是配置，影响后续 turn 或新线程，不会热切换当前这一条回复已经在使用的模型。对 agent 模型会额外同步用户级兜底模型，避免其他未落在当前项目目录下的新对话回退到未授权模型。
---

# Codex Link Peta

## Workflow

1. 收集输入。

首次接入时，优先拿到：

- `base_url`
- `api_key`
- 可选 `model`

默认假设：

- `model = "claude-sonnet-4-6"`
- `project_dir = 当前工作目录`

后续如果只是切换当前项目模型，且 provider 已经接好，可以只提供 `model`。

如果用户只说“执行”或“运行 codex-link-peta”，按下面的优先级处理：

- 如果机器上已经存在可用的 provider 配置，直接把当前项目默认模型写成 `claude-sonnet-4-6`
- 同时把用户级兜底聊天模型同步为 `claude-sonnet-4-6`，让其他新线程默认也落到这个模型
- 如果用户同时给了 `model`，使用用户指定模型
- 如果既没有现成 provider，又没有给 `base_url` 和 `api_key`，再向用户补这两个输入

2. 运行脚本，不要手工改配置，除非脚本无法覆盖特殊场景。

```bash
python3 scripts/setup_provider.py \
  --project-dir "$PWD" \
  --base-url "http://example.com/v1" \
  --api-key "sk-..." \
  --model "claude-sonnet-4-6"
```

只切换当前项目模型时：

```bash
python3 scripts/setup_provider.py \
  --project-dir "$PWD" \
  --model "image-2"
```

3. 明确告知用户作用域。

始终说明这两个边界：

- 当前项目的默认模型写入 `project_dir/.codex/config.toml`
- provider 与认证写入 `~/.codex/config.toml`
- 如果是 agent 兼容模型，用户级 `~/.codex/config.toml` 中的兜底 `model` 也会同步，避免其他新线程继续掉回旧的未授权模型

这是 Codex 的配置层限制，不是 skill 的限制。项目级 `.codex/config.toml` 不能覆盖 `model_provider`、`model_providers` 或 `openai_base_url`。

4. 汇报结果。

至少报告：

- 使用的 provider id
- 写入或复用的 keychain service
- 项目配置文件路径
- 用户级配置文件路径
- `codex doctor` 是否读到了目标 `model` 和 `model_provider`
- 是否完成 smoke test
- 明确提醒：当前这条回复本身仍然使用触发该 turn 时的线程模型

## Behavior Rules

- 首次接入时，优先要求 `base_url` 和 `api_key`，然后运行脚本完成全链路接入。
- 如果用户没有指定模型，默认使用 `claude-sonnet-4-6`。
- 如果用户明确指定其他模型，例如 `image-2`，照样写入当前项目配置。
- 如果模型是 agent 兼容模型，默认同时同步用户级兜底模型，避免项目外或 projectless 新线程继续沿用旧的未授权默认模型；也就是说，调用这个 skill 后，后续大多数新线程都会默认走这个模型。
- 如果模型明显不是 Codex 对话型 agent 模型，例如 `image-2`，允许配置，但要主动说明：配置已写入，smoke test 会跳过，后续能否直接用于 Codex 对话取决于该模型是否支持 Codex agent 工作流。
- 如果用户反馈“skill 已执行但其他对话还是 403 / Forbidden”，优先排查该线程是否仍固定在旧模型；这通常是旧线程仍在使用触发前的线程模型，或用户级兜底模型还没有同步。
- 在 macOS 上，优先把 API key 写入 Keychain，不要把 key 明文写进仓库。
- 在修改 `~/.codex/config.toml` 前，保留脚本自动生成的备份路径，并在结果里告诉用户。
- 如果脚本已经足够完成任务，不要再手工重复编辑同一批配置。
- 如果用户只是问“当前线程正在用什么模型/模式”，先回答当前线程状态，再补充说明这个 skill 只能修改后续 turn 或新线程的配置，不能热切换本条回复已经在用的模型。
- 如果用户只说“执行”，优先直接运行脚本，不要把“执行”理解成空操作。

## Script

使用 [scripts/setup_provider.py](scripts/setup_provider.py) 完成：

- 备份用户级 Codex 配置
- 生成或复用 provider id
- 在 macOS Keychain 中保存 API key
- 更新 `~/.codex/config.toml` 中的 `model_provider` 与 provider 配置
- 对 agent 兼容模型同步 `~/.codex/config.toml` 中的兜底 `model`
- 将当前项目标记为 trusted
- 写入当前项目 `.codex/config.toml` 的默认模型
- 运行当前项目的 `codex doctor --json`
- 对 agent 兼容模型额外运行一次 projectless 的 `codex doctor --json`
- 在适合时运行一次 `codex exec` smoke test

## Output Expectations

- 回答简洁，优先告诉用户是否已经可用。
- 如果脚本跳过了 smoke test，要明确写原因。
- 如果用户切到了非 agent 模型，不要假装已经验证“对话可用”。
