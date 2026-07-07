# Figma MCP 连接说明（train-prototype-creator）

> Agent **不能**代替你完成 OAuth；需在 Cursor 里启用后**完全重启 Cursor**，再在对话中粘贴 Figma 链接。

## 方式 A：官方 Figma MCP（推荐）

与本仓库已配置的 [`.cursor/mcp.json`](../.cursor/mcp.json) 一致：

```json
{
  "mcpServers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

### 步骤

1. 打开 **Cursor → Settings → Features → Model Context Protocol**
2. 确认列表中有 **figma**（来自项目 `.cursor/mcp.json` 或你加到 `~/.cursor/mcp.json` 的配置）
3. 若提示登录，按指引用 Figma 账号 **OAuth 授权**
4. **完全退出并重启 Cursor**（仅 Reload Window 有时不够）
5. 新开 Agent 对话，在输入框下方 **Available Tools** 中应出现 Figma 相关工具（如 `get_design_context`、`get_screenshot` 等）
6. 将黑白线框文件的 **Frame 链接**（右键 Copy link）粘贴到对话

### 验证是否连上

对 Agent 说：「用 Figma MCP 读取这个链接的 get_design_context」并贴上链接。  
若仍报「无此工具」，说明 MCP 未加载成功，查看 **Output → MCP Logs**。

---

## 方式 B：Personal Access Token（备选）

若公司网络无法使用 `mcp.figma.com`，可用社区服务 **figma-developer-mcp**（需 [Figma Personal Access Token](https://help.figma.com/hc/en-us/articles/8085703771159-Manage-personal-access-tokens)）：

在 `~/.cursor/mcp.json` 增加：

```json
{
  "mcpServers": {
    "Framelink Figma": {
      "command": "npx",
      "args": ["-y", "figma-developer-mcp", "--stdio"],
      "env": {
        "FIGMA_API_KEY": "${env:FIGMA_API_KEY}"
      }
    }
  }
}
```

终端执行：`export FIGMA_API_KEY="你的token"` 后重启 Cursor。

---

## 连接成功后 train-prototype-creator 流程

1. `get_design_context` + `get_screenshot` 读取全流程 Frame  
2. 更新 `figma-wireframe-reference.md`（页面 ID ↔ Frame ↔ UI Kit 映射）  
3. 按 Figma 重搭 `wireframes/*-preview.html` 并生图  

---

## 你需要发什么链接

- **文件** 或 **某一 Frame** 的链接均可；建议主路径每屏各一条，或一个「全流程」父 Frame 链接  
- 链接格式示例：`https://www.figma.com/design/FILE_KEY/...?node-id=123-456`
