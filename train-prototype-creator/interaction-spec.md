# 最终交互演示 Shell 与固定 Schema

当输出物是**最终交互演示 HTML**，且需要：

- 左侧页面预览
- 右侧交互说明
- 顶部页签切换
- 同页状态切换 rail
- 固定手机舞台

则默认不再自由搭桌面外壳，而是优先复用：

```text
assets/templates/interaction-demo/
  manifest.json
  interaction-demo-template.html
  interaction-demo-template.css
  interaction-demo-template.js
  interaction-demo-data.example.json
```

这套模板的来源是用户确认过的最终参考稿 `interaction-preview-final-v2.html`。  
后续所有“最终交互演示”类产物，默认都应视为**同一套外壳，只换数据**。

---

## 1. 固定外壳

以下结构默认固定，不应在新任务里重新发明：

```text
app-shell
├── preview-panel
│   ├── panel-header
│   └── preview-stack
│       ├── tabs
│       └── phone-stage
│           ├── state-rail
│           └── phone-slot
│               └── phone-fit
│                   └── phone
│                       └── phone-viewport
│                           └── phone-screen
└── doc-panel
    ├── doc-header
    └── doc-scroll
        └── doc-content
```

### 不应改动的骨架规则

- 左右双栏布局固定：宽窗口下左侧预览、右侧说明；窄窗口下允许自动切成上下布局，但预览区优先置顶。
- 预览区固定为：标题栏 → 页签栏 → 手机舞台。
- 手机舞台固定为：状态切换 rail + 手机预览。
- 说明区固定为：标题栏 → 可滚动文档区。
- 桌面预览外壳采用 review-shell 策略：优先使用 capped height，而不是永久绑定 `100dvh` 撑满浏览器；在 14 英寸 MacBook Pro 评审场景下，默认按约 `740px` 的壳体上限高度生成，再与当前视口高度取更小值。
- 预览区内部必须使用稳定的两段式高度结构：页签栏固定高度，手机舞台占剩余高度；不要让手机舞台继续依赖内容高度自撑，否则状态切换重渲染后会出现越点越小的递归缩放。
- 手机尺寸固定为 `375 × 812`。
- 手机内容画布固定为 `375 × 812`，外层设备壳体允许包含描边厚度；缩放时以整机容器完整可见为准。
- 手机舞台默认按**整机完整可见**优先缩放，目标是让整台手机容器在当前预览区首屏内完整落下，而不是只保证顶部可见。
- 当浏览器窗口较窄时，状态切换 rail 可转为顶部横向布局，让更多空间让给手机容器；不应依赖舞台滚动来补足首屏可见性。
- 手机预览只展示产品界面；说明、IA、token、SVG 记录不进入手机屏幕内部。

---

## 2. 固定数据结构

最终演示 HTML 的数据层默认使用以下结构：

```json
{
  "meta": {
    "pageTitle": "string",
    "previewHeaderTitle": "string",
    "docHeaderTitle": "string",
    "previewActions": [
      { "id": "string", "label": "string", "tone": "default|primary" }
    ],
    "docActions": [
      { "id": "string", "label": "string", "tone": "default|primary" }
    ],
    "toastText": "string"
  },
  "preview": {
    "frames": [
      {
        "id": "string",
        "label": "string",
        "active": true,
        "stateRail": {
          "title": "string",
          "items": [
            {
              "id": "string",
              "label": "string",
              "active": true,
              "phone": {
                "template": {
                  "kind": "home|list|fill|occupy|other",
                  "data": {}
                }
              }
            }
          ]
        }
      }
    ]
  },
  "doc": {
    "sections": [
      {
        "index": "01",
        "title": "方案目标",
        "type": "decision|flow|state-grid",
        "variant": "optional",
        "items": []
      }
    ]
  }
}
```

### 核心原则

- 页签切换使用 `preview.frames[]`。
- 同页状态切换使用 `frame.stateRail.items[]`。
- 命中 `home / list / fill / occupy` 的手机页，必须优先通过 `phone.template.kind + phone.template.data` 变化。
- `phone.blocks[]` 只允许作为回退机制，供非核心手机页或说明型插图页使用。
- 右侧说明只通过 `doc.sections[]` 变化。
- 右侧交互说明结构固定为 5 段，标题和顺序不得变化：`01 用户场景`、`02 方案目标`、`03 交互流程`、`04 交互状态说明`、`05 边界场景（如有）`。
- 若没有边界场景，也必须保留第 05 段，并写「暂无新增边界」；不得删除该段或新增第 6 段。
- 不要把页面差异写成第二套 HTML 外壳。

### 最终演示内页组合规则

- `interaction-demo` 只负责桌面外壳、切页、状态切换和说明区；它不是四类核心手机页的真源。
- 当某个 frame / state 的手机内容语义命中 `home / list / fill / occupy` 时，必须继续复用对应的页面模板包：
  - `assets/templates/home/manifest.json`
  - `assets/templates/list/manifest.json`
  - `assets/templates/fill/manifest.json`
  - `assets/templates/occupy/manifest.json`
- 推荐写法：

```json
{
  "phone": {
    "template": {
      "kind": "list",
      "data": {
        "route": { "from": "昆山南", "to": "上海虹桥" },
        "cards": []
      }
    }
  }
}
```

- `phone.blocks[]` 只应用于：
  - 非核心手机页
  - 说明性插图页
  - 尚未模板化的新页面语义
  - 已明确属于页面 flexible area 的自由区域
- 不允许只固定桌面外壳，却在手机内部重新创造一次性 page block 结构，例如：
  - `home-quick-flow`
  - `list-anchor-flow`
  - `occupy-flow`
- 如果新的手机页结构确实稳定且可复用，应先升级成正式页面模板或正式 block 类型，再进入最终演示 schema；不要把一次性 page flow 留在最终产物里。
- 当页面模板已要求图标走 SVG 资产时，最终演示必须把命中的 SVG 路径注入模板数据；禁止退回到文字图标、字符箭头或纯 CSS 占位图形。

---

## 3. 回退 Block 类型

仅当手机页未命中正式页面模板时，才允许使用以下 block：

### `commute-card`

用于首页主卡、摘要主卡、确认前摘要等“主入口卡片”。

仅在本轮需求明确涉及通勤、常买车次、快捷下单或固定乘车人偏好时使用。若需求是积分、优惠、保险、选座、筛选、抢票等其他主题，不要复用该 block 的通勤示例语义；应改用核心页面模板的数据槽位，或新增贴合本轮目标的轻量 block。

```json
{
  "type": "commute-card",
  "data": {
    "headerTitle": "通勤快捷购票",
    "headerSubtitle": "常买车次 · 快速下单",
    "savedLabel": "已为你保存设置",
    "from": "昆山南",
    "to": "上海虹桥",
    "centerLabel": "rail",
    "metaRow": ["G7006", "07:32 → 08:04", "二等座优先"],
    "infoItems": [
      { "label": "乘车人", "value": "梁晨" }
    ],
    "primaryCta": "确认购票"
  }
}
```

### `icon-grid-section`

用于常用服务、快捷入口、轻量工具区。

```json
{
  "type": "icon-grid-section",
  "data": {
    "title": "常用服务",
    "items": [
      { "icon": "票", "label": "车票订单" }
    ]
  }
}
```

### `card-grid-section`

用于推荐内容、营销卡、双列推荐区。

```json
{
  "type": "card-grid-section",
  "data": {
    "title": "热门推荐",
    "items": [
      { "title": "餐饮·特产", "copy": "精选好物在旅途" }
    ]
  }
}
```

### `text-card-section`

用于说明型卡片、状态承接说明、流程解释等。

```json
{
  "type": "text-card-section",
  "data": {
    "title": "异常承接",
    "items": [
      { "title": "用户无需重新填写", "copy": "继续保留乘车人、座席偏好和原始路线。" }
    ]
  }
}
```

### 扩展规则

- 优先扩展 block `data`，不要先改 CSS 外壳。
- 若确实需要新增 block 类型，先写入模板渲染器，再写入示例数据。
- 不要在数据里直接塞整段 `phone html` 作为常规做法。

---

## 4. 交互说明固定结构

最终演示 HTML 的 `doc.sections[]` 必须只包含以下 5 段：

```json
[
  { "index": "01", "title": "用户场景", "type": "decision", "items": [] },
  { "index": "02", "title": "方案目标", "type": "decision", "items": [] },
  { "index": "03", "title": "交互流程", "type": "flow", "variant": "compact-flow", "items": [] },
  { "index": "04", "title": "交互状态说明", "type": "state-grid", "items": [] },
  { "index": "05", "title": "边界场景（如有）", "type": "state-grid", "items": [] }
]
```

约束：

- 禁止新增第 6 段，禁止改名、改序或把页面清单、资产记录、技术说明放进右侧交互说明。
- `01 用户场景` 写用户是谁、何时触发、痛点是什么。
- `02 方案目标` 写本方案要达成的用户结果和体验原则。
- `03 交互流程` 写从入口到结果的步骤。
- `04 交互状态说明` 写主要状态、按钮行为和页面反馈。
- `05 边界场景（如有）` 写异常、空态、失败、不可用、权限或登录等边界；若无新增边界，写「暂无新增边界」。

---

## 5. 说明区支持的 Section 类型

### `decision`

用于“问题 / 方案 / 价值”或原则清单。

```json
{
  "index": "01",
  "title": "方案目标",
  "type": "decision",
  "items": [
    { "mark": "?", "title": "问题", "body": "..." }
  ]
}
```

### `flow`

用于流程步骤说明。

```json
{
  "index": "02",
  "title": "用户流程",
  "type": "flow",
  "variant": "compact-flow",
  "items": [
    { "num": "1", "title": "进入首页", "body": "..." }
  ]
}
```

### `state-grid`

用于状态说明、页面改动清单等网格卡片。

```json
{
  "index": "04",
  "title": "状态说明",
  "type": "state-grid",
  "items": [
    { "title": "正常态", "body": "...", "color": "green" }
  ]
}
```

---

## 6. 交互与行为

模板内已固定支持以下桌面操作：

- `copy-doc`
- `toggle-edit`
- `export-pdf`：必须通过前端生成 PDF Blob 并触发 `<a download>`，让文件进入浏览器默认下载路径；禁止调用 `window.print()` 或打开系统打印 / 打印机面板。
- `share-package`：必须在 `导出 PDF` 右侧显示，点击后前端打包当前预览 HTML、交互说明、数据 JSON 与已加载图片资源为 ZIP；支持系统分享时优先调起分享，不支持时下载 ZIP 供二次转发。
- 页签切换
- 状态切换
- 手机缩放自适应

这类行为应继续由模板 JS 承载，不要在每次任务里重新手写一套。

---

## 7. 执行规则

当用户要求“最终交互演示 HTML”时，默认执行顺序：

```text
读取 interaction-spec.md
→ 命中 assets/templates/interaction-demo/manifest.json
→ 固定外壳
→ 注入 frames / states / phone blocks / doc sections
→ 导出最终 HTML
```

禁止项：

- 禁止跳过 `interaction-demo` 模板，直接新写一份左右分栏外壳。
- 禁止把说明区与手机预览混成同一个产品界面。
- 禁止为了改一个页签或一个状态，复制第二套完整 HTML 外壳。
- 禁止在手机预览内展示 token、SVG、页面模式、需求拆解等内部信息。

---

## 7. 推荐验证

至少做以下检查：

- `manifest.json`、示例数据 JSON 可解析。
- `interaction-demo-template.js` 语法通过。
- 模板渲染后存在固定类名：
  - `app-shell`
  - `preview-panel`
  - `doc-panel`
  - `tabs`
  - `state-rail`
  - `phone`
  - `doc-section`
- 页签切换后只更新预览区，不重写整个文档区。
