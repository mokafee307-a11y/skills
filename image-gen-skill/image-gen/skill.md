---
name: image-gen
description: "AI 图片生成 skill。展示风格模版供用户选择，或直接一键调用。支持多张参考图，调用 gpt-image-2 API 生成图片。用法: /image-gen [【模版名】] [描述] [图片路径...]"
argument-hint: "[【模版名】] [描述] [/path/to/ref1.png ...]"
allowed-tools: ["Bash"]
---

# Image Gen Skill

## 提示词机制说明

本 skill 使用**双层提示词**结构：

| 层级 | 来源 | 作用 |
|------|------|------|
| **系统提示词** | 模版 MD 文件的 body（frontmatter 以下全部内容） | 定义图片的整体艺术风格，由模版固定提供 |
| **用户提示词** | 用户输入的描述 | 描述图片的具体内容、主体、场景细节 |

合并格式：
```
{system_prompt}. User request: {user_input}
```

自由生图模式（选 0）不使用任何 system_prompt，只发送用户输入。

---

## 第一步：配置检查

```bash
cat ~/.claude/skills/image-gen/image-gen-config.json 2>/dev/null || echo "CONFIG_MISSING"
```

如果输出 `CONFIG_MISSING` 或 `api_key` 仍是 `YOUR_API_KEY_HERE`，告知用户填写后再试，**停止执行**。

同时从配置读取超时时间（`timeout_seconds`，默认 300）备用。

## 第二步：检测运行环境

```bash
command -v python3 &>/dev/null && echo "HAS_PYTHON" || echo "NO_PYTHON"
command -v curl &>/dev/null && echo "HAS_CURL" || echo "NO_CURL"
```

- `HAS_PYTHON` → 记 `RUNNER=python`，使用 `generate_image.py`
- `NO_PYTHON` + `HAS_CURL` → 记 `RUNNER=shell`，使用 `generate_image.sh`
- 两者都无 → 告知用户安装 curl，**停止执行**

## 第三步：解析调用参数（一键模式 vs 交互模式）

### 一键模式
用户调用时若提供了参数，格式为：
```
/image-gen 【模版名】 描述文字 /path/to/ref1.png /path/to/ref2.png
```

解析规则：
- `【模版名】`：被 `【】` 包裹的词，匹配模版的 `name` 字段（支持部分匹配，如 `【动漫】` 匹配 `动漫人物肖像`）；`【自由】` 或 `【0】` 表示自由生图
- 图片路径：参数中所有以 `/` 或 `~/` 开头、或后缀为 `.png/.jpg/.jpeg/.webp` 的部分，收集为 `IMAGE_PATHS` 列表
- 其余文字：作为用户内容描述 `USER_DESC`

若以上三项均已从参数中解析出来（模版 + 描述 + 至少一张图），**跳过第四步直接进入第五步**。

### 交互模式
参数不完整时，进入逐步交互流程（见第四步）。

## 第四步：交互收集缺失信息

按需补充，已从参数中解析到的项目跳过：

### 4a. 读取并展示模版菜单

```bash
ls ~/.claude/skills/image-gen/templates/*.md 2>/dev/null | sort
```

逐个读取每个 MD 文件的 frontmatter，提取 `name` 和 `description`，按序号展示：

```
请选择一个图片模版，或选择自由生图：

  [1] 动漫人物肖像 — 将人物照片转换为日系动漫插画风格，色彩鲜艳，线条细腻
  [2] 古典油画     — 模拟欧洲古典油画质感，厚重笔触，光影细腻，艺术感强烈
  [3] 赛博朋克都市 — 霓虹灯光、雨夜街头、科幻未来感，适合城市场景和人物改造
  [4] 水彩手绘     — 清新淡雅的水彩画风格，适合风景、植物、生活场景
  [5] 专业写真     — 商业级人像摄影风格，精修光影，适合头像、商务照
  [0] 自由生图     — 不使用模版，直接根据你的描述个性化生图

请输入编号：
```

等待用户输入。

### 4b. 用户内容描述

若未提供，询问：
```
请描述图片内容（主体、场景、细节等）：
```

### 4c. 输入图片路径

若未提供，询问：
```
请提供输入图片路径，多张用空格分隔（例如 /path/a.jpg /path/b.png）：
```

图片为**必填项**，用户未提供时等待输入，不可跳过。将输入按空格拆分为 `IMAGE_PATHS` 列表。

## 第五步：解析模版，构建最终 prompt

### 读取 MD 模版

```bash
cat ~/.claude/skills/image-gen/templates/<对应文件>.md
```

模版格式为标准 frontmatter MD：
```markdown
---
id: xxx
name: 模版名
description: 简介
size: 1024x1024
quality: high
---

这里是 system_prompt 的全部内容，可以是多行文本。
```

frontmatter 以下（第二个 `---` 之后）的所有内容（去除首尾空白）即为 `SYSTEM_PROMPT`。
同时从 frontmatter 读取 `size` 和 `quality`。

### 构建 prompt

**使用模版：**
```
{SYSTEM_PROMPT}. User request: {USER_DESC}
```

**自由生图（选 0）：**
```
{USER_DESC}
```

## 第六步：调用脚本（前台阻塞，等待返回）

生成带时间戳的输出路径：
```bash
OUTPUT=~/Desktop/image-gen-$(date +%Y%m%d-%H%M%S).png
```

**重要：必须在前台同步执行，等待 API 返回后才继续。不得使用后台执行（不加 `&`，不使用 `run_in_background`）。**

**Python（RUNNER=python）：**
```bash
python3 ~/.claude/skills/image-gen/generate_image.py \
  --prompt "最终prompt" \
  --image "/图片路径1" \
  --image "/图片路径2" \
  --output "$OUTPUT" \
  --size "模版size 或 auto" \
  --quality "模版quality 或 auto"
```

每张图片单独一个 `--image` 参数，有几张加几个。

**curl（RUNNER=shell）：**
```bash
bash ~/.claude/skills/image-gen/generate_image.sh \
  --prompt "最终prompt" \
  --image "/图片路径1" \
  --image "/图片路径2" \
  --output "$OUTPUT" \
  --size "模版size 或 auto" \
  --quality "模版quality 或 auto"
```

超时时间由 `image-gen-config.json` 中的 `timeout_seconds` 控制（默认 300 秒）。

## 第七步：输出结果

成功：
```
✅ 生成完成！
   模版：{模版名称 或 "自由生图"}
   运行方式：{Python 或 curl}
   系统提示词：{SYSTEM_PROMPT 或 "无（自由生图）"}
   用户提示词：{USER_DESC}
   参考图（{N}张）：{IMAGE_PATHS}
   保存路径：{输出文件完整路径}
```

失败时显示错误并给出排查建议：
- api_key / api_key_id 有误 → 检查 image-gen-config.json
- 图片路径不存在 → 确认文件路径
- Python requests 缺失 → `pip3 install requests`
- curl 不可用 → `brew install curl` 或 `apt install curl`
- 超时 → 增大 `timeout_seconds` 或检查网络
- 网络错误 → 确认 base_url 是否可访问
