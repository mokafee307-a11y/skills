# image-gen skill

用自然语言描述内容，调用 gpt-image-2 API 生成图片，支持多种艺术风格模版和多张参考图。

---

## 目录结构

```
image-gen-skill/
├── README.md
└── image-gen/
    ├── skill.md                  ← skill 主文件
    ├── generate_image.py         ← API 调用脚本（Python 版）
    ├── generate_image.sh         ← API 调用脚本（curl 版，无需 Python）
    ├── image-gen-config.json     ← API 配置文件（需填写）
    ├── templates/                ← 模版目录，每个 .md 文件为一个风格模版
    │   ├── 01_anime_portrait.md  — 动漫人物肖像
    │   ├── 02_oil_painting.md    — 古典油画
    │   ├── 03_cyberpunk_city.md  — 赛博朋克都市
    │   ├── 04_watercolor_sketch.md — 水彩手绘
    │   └── 05_studio_photo.md   — 专业写真
    └── samples/                  ← 各模版参考图片（可选）
```

---

## 安装

### 1. 将 skill 复制到 Claude Code 技能目录

```bash
cp -r /path/to/image-gen-skill/image-gen ~/.claude/skills/image-gen
```

> 如果你克隆了这个仓库到桌面，路径示例：
>
> ```bash
> cp -r ~/Desktop/image-gen-skill/image-gen ~/.claude/skills/image-gen
> ```

### 2. 填写 API 配置

编辑 `~/.claude/skills/image-gen/image-gen-config.json`：

```json
{
  "api_key": "你的 API Key",
  "api_key_id": "你的 API Key ID",
  "base_url": "http://your-api-endpoint/llm",
  "timeout_seconds": 300
}
```


| 字段                | 说明                  |
| ----------------- | ------------------- |
| `api_key`         | 鉴权密钥                |
| `api_key_id`      | API 账号 ID，会拼入请求路径   |
| `base_url`        | API 网关地址（不含末尾斜杠）    |
| `timeout_seconds` | 请求超时秒数，默认 300，可按需调大 |


### 3. 确认依赖

skill 优先使用 Python，无 Python 时自动回退到 curl：

```bash
# 检查 Python
python3 --version

# 安装 requests（Python 用户必须）
pip3 install requests

# 或确认 curl 可用（无需额外安装）
curl --version
```

---

## 使用

### 第一步：在终端打开 Claude Code

```bash
ada
```

### 第二步：调用 skill

#### 交互模式（逐步引导）

```
/image-gen
```

skill 会依次询问：选择风格模版 → 描述图片内容 → 提供参考图路径。

#### 一键模式（参数齐全时直接生图）

```
/image-gen 【模版名】 描述文字 /path/to/ref1.png /path/to/ref2.png
```


| 部分  | 格式                                    | 示例                                      |
| --- | ------------------------------------- | --------------------------------------- |
| 模版名 | 用 `【】` 包裹，支持部分匹配；`【0】` 或 `【自由】` 为自由生图 | `【动漫】`、`【油画】`、`【自由】`                    |
| 描述  | 自然语言，描述图片内容、场景、风格细节                   | `粉色头发的女孩，樱花背景`                          |
| 参考图 | 绝对路径，多张用空格分隔                          | `/Users/me/ref1.png /Users/me/ref2.jpg` |


三项均填写时跳过问答，直接调用 API。

#### 使用示例

```bash
# 交互模式，逐步引导
/image-gen

# 动漫风格，单张参考图
/image-gen 【动漫】 粉色头发的女孩，樱花背景 /Users/me/photo.jpg

# 自由生图，两张参考图
/image-gen 【自由】 ins旅行手账撕纸拼贴风海报，西班牙夏季主题 /Users/me/ref1.png /Users/me/ref2.png
```

生成的图片默认保存到 `~/Desktop/image-gen-YYYYMMDD-HHMMSS.png`。

---

## 内置模版


| 编号  | 名称     | 适用场景            |
| --- | ------ | --------------- |
| 1   | 动漫人物肖像 | 人物照片转日系动漫插画     |
| 2   | 古典油画   | 欧洲古典油画质感        |
| 3   | 赛博朋克都市 | 霓虹城市、科幻未来风      |
| 4   | 水彩手绘   | 风景、植物、生活场景      |
| 5   | 专业写真   | 商务头像、证件照、社交媒体头图 |
| 0   | 自由生图   | 不使用风格模版，完全自定义   |


---

## 自定义模版

在 `~/.claude/skills/image-gen/templates/` 下新建 `.md` 文件，格式：

```markdown
---
id: my_style
name: 我的风格
description: 一句话简介，显示在模版菜单中
size: 1024x1024
quality: high
---

这里写 system prompt，描述图片风格要求。
支持多行，可以写得很详细。
```


| 字段        | 可选值                                              |
| --------- | ------------------------------------------------ |
| `size`    | `1024x1024` / `1792x1024` / `1024x1792` / `auto` |
| `quality` | `high` / `auto`                                  |


保存后下次调用 `/image-gen` 时自动出现在菜单，无需重启。

---

## 常见问题


| 现象                              | 解决方法                                                            |
| ------------------------------- | --------------------------------------------------------------- |
| `CONFIG_MISSING`                | 检查 `~/.claude/skills/image-gen/image-gen-config.json` 是否存在并填写正确 |
| api_key 报错                      | 确认 `api_key` 字段不是占位符 `YOUR_API_KEY_HERE`                        |
| `ModuleNotFoundError: requests` | 执行 `pip3 install requests`                                      |
| 请求超时                            | 增大配置中的 `timeout_seconds`，或检查网络连接                                |
| 图片路径不存在                         | 使用绝对路径，确认文件存在                                                   |
| 429 限流                          | 稍等片刻后重试                                                         |


