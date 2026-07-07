# SVG 资产映射

仅当用户提供或提到 `SVG` 资产、映射表、锁定组件时读取本文件。

## 目录与所有权

- 默认资产目录：`assets/svg/`
- 默认映射表：`assets/svg/asset-map.toml`
- `asset-map.toml` 视为 **user-owned**：后续运行默认只读不改，除非用户明确要求更新它。

## 标准页面标识

当原型涉及当前这组火车票 5 个一级页面时，页面标识固定为：

- `home`：火车首页
- `list`：火车列表页
- `middle`：火车中间页
- `fill`：火车填写页
- `occupy`：火车占座页
- `shared`：不限制使用页面的公共图标资源

后续 `SVG` 文件名、映射表 `key`、`page` 字段、输出记录默认统一使用这套标识，不再混用别名。

## 命名约定补充

- 文件名以 `home-` / `list-` / `middle-` / `fill-` / `occupy-` 开头时，默认视为**页面资源**。
- 文件名**不包含 page 前缀**时，默认视为 `shared` 公共资源，可跨页面复用。
- 若资源文件名存在空格、大小写或特殊字符，允许在 `source` 中保留原文件名，同时在 `output_name` 中写规范化后的输出名。

## 处理顺序

1. 读取 `assets/svg/asset-map.toml`
2. 运行 `python3 scripts/validate_asset_map.py`
3. 先匹配 `key / page / component / location / figma_node`
4. 命中且文件存在：复制到输出根目录 `wireframes/assets/` 并在 HTML/CSS 中引用
5. 未命中或缺失：按 `fallback_order` 执行
6. 若是 `lock = "hard"` 且 `required = true`：默认暂停并向用户确认，不得手绘替代

## 建议字段

- `key`：稳定键，建议 `page.component.location`
- `page`：页面标识，如 `home` / `list` / `middle` / `fill` / `occupy` / `shared`
- `component`：组件名，如 `direct-card` / `calendar` / `title-bar`
- `location`：组件内位置，如 `back-button` / `middle-arrow`
- `selector_hint`：给代理的人类可读说明
- `figma_node`：可选，写 Figma node id
- `source`：SVG 源文件路径，通常为 `./assets/svg/*.svg`
- `output_name`：复制到 `wireframes/assets/` 后的文件名
- `lock`：`hard` / `soft` / `free`
- `required`：`true` 时缺失会阻塞硬锁定输出
- `priority`：数字越大越优先
- `notes`：补充说明

## 输出记录要求

在 HTML 页头或 `prototypes/*-spec.md` 中追加 `SVG资产复用` 段落，至少记录：

- `key`
- `source`
- `output_name`
- `lock`
- `fallback`

## 回退规则

- `hard`：优先用用户 SVG；缺失时默认暂停确认
- `soft`：优先用用户 SVG；缺失时可回退到 Figma 导出或轻度 CSS
- `free`：可不依赖映射，允许自由生成
