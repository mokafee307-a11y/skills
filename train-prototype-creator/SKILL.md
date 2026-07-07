---
name: train-prototype-creator
description: >-
  Generates OTA train-booking interaction prototypes with reusable templates,
  Ctrip UI Kit specs, mapped SVG assets, design tokens, openable 375px HTML
  previews, and key-screen PNG previews. Use for train-prototype-creator,
  prototype-creator, wireframes, 线框, prototypes, 原型, OTA booking flows,
  train booking flows, or UI Kit-aligned screen specs.
---

# Train Prototype Creator

生成接近线上 OTA 火车票体验的信息密度原型。默认产物是：**可打开的 375px HTML 预览 + 关键屏 PNG 示意图 + 可选交互说明**。

本 Skill 的职责是调度：优先复用模板、tokens、组件和用户资产，避免每次从零重写页面。

## 1. 核心原则

1. **用户输入优先**：用户本轮明确要求 > Figma / 参考图 > SVG 映射 > 模板 > design tokens > UI Kit / 页面模式 > 通用生成规则。
2. **模板优先**：若 `assets/templates/{page}/manifest.json` 存在，必须优先读取并复用模板包，不要从描述重新手写整页。
3. **资产优先**：若存在 `assets/svg/asset-map.toml`，必须读取并校验；硬锁定图标 / 组件优先使用映射 SVG，不得手绘替代。
4. **Token 优先**：若存在 `assets/config/design-tokens.json`，颜色、字号、间距、圆角、描边、阴影等优先来自 token。
5. **组件优先**：页面差异优先通过数据、组件参数和状态表达；不要为少量文案或状态变化复制一整份页面结构。
6. **线上形态优先**：布局、信息密度、区块顺序参考 `ota-screen-patterns.md`，不能退化成简陋灰块。
7. **局部修改优先**：用户只要求改某一块时，只改对应槽位；不要借机重写整页。
8. **可验证交付优先**：HTML 必须可打开，PNG 与 HTML 的屏幕结构必须一致。
9. **用户语言优先**：预览页面中的文案必须表达用户收益、用户结果和用户行动；禁止把需求说明、系统能力或实现逻辑直接写给用户看。
10. **预览纯净优先**：用户可见预览只展示产品界面；设计说明、IA、成功标准、SVG 记录、token、页面模式等内部信息进入 spec / 注释 / debug，不直接显示在手机界面中。
11. **屏幕效率优先**：在符合字号 token 的前提下，优先通过短文案、容器让位、单行策略和信息分层减少非必要换行；不要把按钮、badge、chip、短标签、日期、路线摘要等轻量信息轻易挤成两行。
12. **最终演示外壳优先**：当用户要求“最终交互演示 HTML”、“左右分栏预览 + 说明”或给出类似最终交付 HTML 作为参考时，优先命中 `assets/templates/interaction-demo/manifest.json` 与 `interaction-spec.md`，固定外壳只注入数据，不再重新设计桌面框架。
13. **最终演示内页模板优先**：当最终交互演示里的手机页语义命中 `home / list / middle / fill / occupy` 时，必须继续命中对应的 `assets/templates/{page}/manifest.json` 作为内页真源；不要只固定桌面外壳，却在手机内部重新手写一套 `*-flow` 结构和 CSS。
14. **双写同步优先**：当当前对话已经存在正在评审的预览产物时，后续确认执行的修改必须同时回写到 Skill 真源（模板、规则、示例数据、文档）与本次预览产物；除非用户明确说明只改其中一处。
15. **反馈溯源优先**：用户对预览提出任何修改意见后，必须先自查问题是否源于 Skill 内部约束、模板 manifest、固定 CSS / JS、示例数据、design tokens、页面规则、组件规则、SVG 映射或文案规则；若是源头问题，必须先优化 Skill 真源，再用优化后的 Skill 重新更新当前预览和受影响 PNG。
16. **嵌入居中优先**：核心页面模板独立打开可保留展示留白；但嵌入最终演示 shell、iframe 或手机舞台时，内页必须启用固定 6px padding 的嵌入模式（如 `body.phone-embed`），手机壳深色边框默认 5px，且外层舞台尺寸必须包含该 padding，避免手机壳被裁切、偏移、黑框过粗或看起来歪斜。
17. **内屏底角裁切优先**：若页面存在底部固定栏、tabbar、sortbar、paybar 或 sticky bottom 组件，必须显式继承手机内屏底部圆角并设置必要的 overflow 裁切，避免左下 / 右下角在预览中呈现直角。
18. **交互说明固定优先**：最终交互演示 HTML 右侧「交互说明」只能包含 5 段，且顺序固定为 `01 用户场景`、`02 方案目标`、`03 交互流程`、`04 交互状态说明`、`05 边界场景（如有）`；没有边界场景时保留第 05 段并写「暂无新增边界」。
19. **常规预订主路径优先**：买票预订常规核心路径固定为 `home 首页 → list 列表页 → middle 中间页 → fill 填写页 → occupy 占座页`；生成完整购票流程、状态跳转或最终交互演示时，不得跳过 `middle`，除非用户明确要求简化或该业务链路不含座席 / 预订方案选择。
20. **业务语义判定优先**：模板存在不等于业务语义适配。复用模板前必须先判断本轮目标、用户决策点、页面职责和明确非目标；若模板示例语义与本轮目标不一致，只复用结构 / 组件能力，不复用示例业务文案、默认数据和无关槽位。
21. **决策位优先**：若用户目标是提升转化、点击、票量、预订意愿或订前利益感知，优先强化用户正在做决定的位置，如首页查询卡、列表车次卡、中间页方案卡、填写页金额确认和底部支付栏；不要默认新增二屏大卡片或解释型运营位，除非用户明确要求教育说明或首屏决策位无法承载。
22. **旧语义排除优先**：从既有模板、示例数据或上一次产物延展时，必须列出并清除与本轮无关的旧业务词和旧组件槽位。例如本轮不是通勤 / 收藏 / 常用车次需求时，不得出现「通勤」「常买车次」「快捷预订」「保存为常用车次」「乘车人和坐席偏好」等语义残留。

## 2. 启动流程

1. **确认输出根目录**
   - 若用户已给保存路径，直接使用。
   - 若在本地 macOS GUI 环境，先直接执行 `scripts/choose_output_folder.sh`，以 stdout 的 POSIX 路径为输出根目录；不要硬编码成 `bash scripts/...` 或向用户解释 shell 差异。
   - 仅当脚本失败、用户取消、无 GUI 权限、`osascript` 不可用或非 macOS 环境时，再文字询问保存地址。
   - 若脚本需要重试，只向用户说明“我正在重新尝试打开目录选择器”或“我将改为文字询问保存地址”；不要暴露 bash/zsh、内建命令或其他内部执行细节。
   - 不要默认写到 Skill 目录、桌面或当前工作目录。
2. **读取输入约束**
   - 若用户提供 Figma 文件、node 链接或页面参考图，先提炼不可变约束：结构、图标、渐变、关键组件、文案层级。
   - 若用户补充本轮规则，写入 HTML 页头「本次覆盖」或 `prototypes/*-spec.md`。
   - 先内化本轮「业务语义边界」：业务目标、关键用户决策点、每页职责、明确非目标、禁止继承的旧业务词。
   - 若目标是票量 / 转化 / 订前利益感知，先判断应放在决策位还是教育位；默认不新增二屏大卡片，除非它有独立用户价值。
3. **读取基础规范**
   - 必读：`design-spec.md`、`uikit-reference.md`、`ota-screen-patterns.md`。
   - 若存在：读取 `assets/config/design-tokens.json`。
   - 若存在 SVG 映射：读取 `assets/svg/asset-map.toml` 与 `references/svg-asset-mapping.md`，运行 `python3 scripts/validate_asset_map.py`。
4. **选择页面类型与模板**
   - 识别页面为 `home / list / middle / fill / occupy / interaction-demo / other`。
   - 若用户要的是最终交互演示 HTML、评审稿、汇报稿或“左侧预览 + 右侧说明”分栏交付，先读取 `interaction-spec.md`，再优先命中 `assets/templates/interaction-demo/manifest.json`。
   - 若最终交互演示中的某个 frame / state 实际对应 `home / list / middle / fill / occupy` 页面，继续读取对应页面 manifest、CSS、JS、示例数据，并以该页面模板作为手机内部结构真源。
   - 若命中核心页面，先读取 `references/rules/page-scaffolds.md`。
   - 若命中列表页或车次卡片，读取 `references/rules/list-components.md`。
   - 生成任何用户可见文案前，读取 `references/ux-writing.md`；交付前按 `references/copy-review.md` 自检。
   - 若存在对应模板 manifest，读取 manifest、模板入口、CSS、JS、示例数据，并优先使用。
5. **处理信息不足**
   - 最多追问 3 个真正阻塞的问题。
   - 不影响生成的缺口标记为 `TBD`，继续完成原型。

## 3. 默认生成链路

按以下顺序处理，除非用户明确要求推翻：

```text
用户输入 / 参考稿
→ 业务语义边界与非目标排除
→ SVG 映射与锁定资产
→ 最终演示外壳或页面模板 manifest
→ design tokens
→ 页面基座
→ 组件规则
→ 数据注入
→ 局部规则生成
→ UX Writing 转译
→ Copy Review 自检
→ HTML 预览
→ PNG 示意图
→ 自检与说明
```

### 禁止项

- 模板存在时，禁止跳过模板直接重写整页 HTML/CSS。
- 若已命中 `assets/templates/interaction-demo/manifest.json`，禁止重新设计左右分栏桌面外壳、手机舞台、state rail 或文档区骨架。
- 若已命中 `assets/templates/interaction-demo/manifest.json`，禁止在右侧交互说明里新增第 6 段、改名或改序；说明区只能输出 `01 用户场景`、`02 方案目标`、`03 交互流程`、`04 交互状态说明`、`05 边界场景（如有）`。
- 若最终交互演示中的手机页语义已命中 `home / list / middle / fill / occupy`，禁止再发明 `home-quick-flow`、`list-anchor-flow`、`middle-flow`、`occupy-flow` 一类一次性 page block 结构；应复用对应页面模板并只注入数据。
- 禁止只修当前预览产物而不回写对应 Skill 真源；也禁止只改 Skill 真源却放任当前评审预览继续过时。
- 禁止为了少量文案、tag、价格或状态差异复制整页结构。
- 禁止在页面层重复定义已经属于组件层或 token 层的样式。
- 禁止伪造“已复用用户 SVG”；若映射缺失或文件不可用，必须说明回退。
- 若输出目录中已存在命中的 SVG 资产，禁止在最终 HTML 内退回使用文字占位、emoji、箭头字符或裸 `<i>` 形状代替这些图标。
- 禁止在用户要求按彩色 Figma / 参考稿还原时强制黑白化锁定区域。
- 禁止将“支持、按日期筛选、固定入口、Half Screen View、SVG、token、M-LIST”等系统语言直接展示在用户可见预览文案中。
- 禁止把 PRD / 需求描述原句直接当作 banner、卡片说明、浮层说明或空状态文案。
- 禁止让历史模板或示例数据里的旧业务语义泄漏到新需求中；尤其是通勤、收藏、常用车次、快捷预订、乘车人偏好等只在用户本轮点名时才可出现。
- 当需求是订前利益感知、价格优惠、票量提升或方案转化时，禁止把核心利益点默认放到首页二屏大卡片里；应先尝试主查询卡、筛选项、车次卡、方案卡和价格栏。

### 允许整页重写的例外

仅在以下情况允许整页重写，并在输出中说明原因：

- 当前页面没有对应模板，且不能从已有模板扩展。
- 当前页面类型与现有页面基座根本不兼容。
- 用户明确要求重做整页结构或推翻当前方案。
- 现有模板 / 组件无法通过 token、数据、参数或局部扩展表达需求。

## 4. 视觉策略

默认生成**低保真、黑白线框为主**的原型：

- 背景、卡片、普通文字、描边、未强调按钮：灰度优先，参考 `design-spec.md` §9.1。
- Button-Booking、选中态与价格默认使用 `semantic.color.selected` / `semantic.color.price`，即品牌蓝 `#3263A6`；若模板或参考稿已有固定样式，以模板 / 参考稿为准。
- 高亮信息按语义 token：positive / discount / warning。
- 全页高亮克制，默认不超过 3 处。

若用户提供带取色的 Figma / 彩色参考页并要求还原，以下锁定元素不得强制黑白化：页面头部渐变、title bar、日历组件、底部按钮、直达/中转车次卡片、票面信息、参考稿明确锁定的图标。

## 5. 参考稿与 SVG 资产

当存在 Figma / 参考图：

- `icon/` 前缀图层、组件或编组视为特定图标，必须按参考路径复用，不得替换、重绘、简化。
- title bar 标题必须按画板中轴视觉居中，优先使用 `left: 50% + translateX(-50%)` 或等价方案。
- 若 `ota-screen-patterns.md` 与用户参考稿冲突，以用户参考稿为准；页面模式只用于补足缺失结构。

当存在 `assets/svg/asset-map.toml`：

- `asset-map.toml` 视为 user-owned，默认只读不改，除非用户要求更新。
- 资源优先级：用户 SVG 映射 > Figma MCP / localhost 导出资产 > 手写 CSS / SVG。
- `lock = "hard"` 或 `required = true` 的资源缺失时，暂停并确认，不得静默降级。
- 命中映射的 SVG 默认复制到输出根目录 `wireframes/assets/`，HTML/CSS/JS 引用复制后的文件。
- HTML 页头或 spec 必须记录 `SVG资产复用`：key、source、output_name、lock、fallback。

## 6. 页面基座与组件细则

主 Skill 只保留调度原则；具体稳定规则放在独立文件：

- 核心页面基座：`references/rules/page-scaffolds.md`
- 列表页日历、车次卡片、坐席、价格、tag：`references/rules/list-components.md`
- 中间页预订方案卡 / sell-card：`references/rules/middle-sell-card.md`
- SVG 映射说明：`references/svg-asset-mapping.md`
- Figma MCP 接入：`references/figma-mcp-setup.md`

执行时按需读取，不要把所有细则一次性塞进主上下文。


## 7. 用户可见文案与预览纯净度

预览页面必须先像真实 App，再像设计文档。生成页面文案时，必须先把需求语言翻译成用户语言：

```text
需求 / 实现描述
→ 用户场景
→ 用户收益
→ 短标题
→ 一句话说明
```

执行要求：

- 生成用户可见标题、副标题、banner、空状态、按钮、toast 前，先参考 `references/ux-writing.md`。
- 交付前使用 `references/copy-review.md` 检查所有用户可见文案。
- 若文案在解释系统如何工作，而不是告诉用户有什么好处，必须重写。
- 若出现测试日期、内部状态、组件位置、技术词或页面模式，且不是票面 / 行程必要信息，必须删除或改写。
- 文案默认短句化：入口 2–6 字，标题 4–14 字，说明 12–24 字。

### 7.1 Preview / Spec 分离

`wireframes/*-preview.html` 里的 375px 手机界面只展示用户应该看到的产品内容。以下信息不得直接显示在手机界面中：

- IA、页面目标、成功标准、设计说明。
- SVG 资产复用记录、token、lock、fallback、manifest。
- 页面模式 ID、UI Kit 组件名、data-uikit 调试标记。
- 需求拆解、实现方式、数据结构、系统能力说明。

这些内容允许输出到：

- `prototypes/*-spec.md`
- HTML 注释
- 非手机界面的设计师说明区
- changelog / debug 记录

若同一个 HTML 同时包含设计师工作区与手机预览，必须用视觉结构明确区分；手机预览内部仍必须保持用户视角纯净。

### 7.2 文案打回示例

错误：

```text
收藏高频车次，临近出发按日期回看
车次卡右上角可轻量收藏；右下固定入口随时查看已收藏车次，并按 2026-06-03、2026-06-02 等收藏日期筛选。
```

应改为：

```text
我的常用车次
快速找到之前关注的车次，下次购票更方便。
```

### 7.3 文案密度与换行控制

在 375px 手机预览里，换行不是默认布局手段。满足 token 的前提下，先把屏幕效率做满。

执行顺序：

- 先缩短用户可见文案，不把 PRD 原句直接塞进标题、badge、button、chip、pill。
- 再调整容器宽度、左右占比、gap、padding，让短信息优先单行。
- 再用 `white-space: nowrap`、单行截断、省略、说明下沉等方式处理。
- 只有票面必要信息、长说明、空状态正文、用户必须细读的段落才允许自然换行。

默认应优先单行的元素：

- 按钮、badge、chip、tab、短标签、日期胶囊、价格、路线摘要、车次号 + 站点组合。

禁止：

- 在字号仍符合 token 时，放任 badge、主按钮、短说明因为布局粗糙而频繁换行。
- 通过随意缩小到 token 之外的字号来“解决”换行问题。
- 为了保留完整需求说明，让标题、副标题或摘要出现 2–3 行冗余折行。

## 8. 交付物

### Phase 1：视觉原型，默认必交付

路径均相对用户确认的输出根目录：

```text
wireframes/
  {项目名}-preview.html
  assets/                    # 复制后的用户 SVG / Figma 导出资产
  previews/
    {页面ID}-{简述}.png
```

HTML 必含：

- 项目信息、页面清单、IA、每屏目标 / 成功标准。
- 每屏 `data-uikit` 标注。
- 屏间导航或切换入口。
- 本次覆盖规则、TBD、SVG 资产复用记录。

PNG 必须：

- 覆盖主路径核心屏。
- 与 HTML 同屏、同结构。
- 若不一致，优先修改 HTML 或重新生成 PNG。

### Phase 2：交互增强，用户确认后再做

可选增强：

- 主路径点击。
- 禁用态、空态、加载态、错误态切换。
- `prototypes/{项目名}-spec.md`：流程表、状态矩阵、交互表、路由、组件行为。

## 9. 生图 Prompt 要求

每个 PNG 的 prompt 需要包含：

- 页面模式 ID，如 `M-HOME`、`M-LIST`。
- `375px mobile, Chinese, OTA train booking`。
- Kit 组件名 5–10 个。
- 视觉策略：默认 `low-fidelity wireframe`, `grayscale first`, `high fidelity layout`, `no decorative color`。
- 允许色：selected / price blue 与语义高亮 token。
- 若参考彩色稿：明确 `preserve header gradient / title bar / calendar / ticket cards / ticket info`。
- 若命中 SVG 映射：明确 `reuse mapped user SVG assets for locked components/icons first`, `do not redraw mapped icons`。

## 10. 自检清单

交付前检查：

- [ ] 已确认输出根目录。
- [ ] 已完成业务语义边界判断：目标、决策点、非目标和禁止继承的旧业务词。
- [ ] 已读取必需规范：design-spec、uikit-reference、ota-screen-patterns。
- [ ] 若存在模板 manifest，已优先复用模板，而不是重写整页。
- [ ] 若本次输出属于最终交互演示 HTML，已优先复用 `assets/templates/interaction-demo/manifest.json` 的固定外壳与 schema，而不是手写新的 split-view 框架。
- [ ] 若本次输出属于最终交互演示 HTML，右侧交互说明只有 5 段：`01 用户场景`、`02 方案目标`、`03 交互流程`、`04 交互状态说明`、`05 边界场景（如有）`。
- [ ] 若最终交互演示中包含 `home / list / middle / fill / occupy`，手机内部已继续复用对应页面模板，而不是生成一次性 page flow 结构。
- [ ] 若本次是完整买票预订流程，主路径已按 `home → list → middle → fill → occupy` 串联；若跳过 `middle`，已在 spec 中说明用户明确要求或业务原因。
- [ ] 若本轮是用户对既有预览提出修改意见，已完成反馈溯源；必要时已先优化 Skill 真源，再更新当前预览与受影响 PNG。
- [ ] 若命中 SVG 资产映射，HTML / CSS / JS 中已优先引用真实 SVG，而不是文字图标或字符占位。
- [ ] 若复用模板 / 示例数据，已清除与本轮无关的旧业务语义、默认文案和无关槽位。
- [ ] 若目标是票量、转化或订前利益感知，核心利益点已优先落在决策位，而不是默认新增二屏解释卡。
- [ ] 若存在 design tokens，已优先复用 token。
- [ ] 若存在 SVG 映射，已校验并记录复用结果。
- [ ] 若提供 Figma / 参考图，锁定元素未被自由发挥或误黑白化。
- [ ] 每屏对应页面模式或标记为 `other/TBD`。
- [ ] 组件名称来自 UI Kit 或在 spec 中说明新增原因。
- [ ] 已读取 `references/ux-writing.md`，并完成用户可见文案转译。
- [ ] 已按 `references/copy-review.md` 检查 Preview 文案，没有把需求语言、实现逻辑或内部术语直接展示给用户。
- [ ] 已检查 375px 预览中的按钮、badge、chip、tab、路线摘要等轻量文本；在符合 token 的前提下，没有明显可避免的换行。
- [ ] 手机预览区域没有出现 IA、成功标准、SVG 复用记录、token、页面模式、组件名等内部信息。
- [ ] 每屏主要模块都服务本轮需求；若某块删掉后不影响用户理解本轮目标，应删除或替换。
- [ ] HTML 可打开，375px 宽预览正常。
- [ ] PNG 已生成且与 HTML 结构一致。
- [ ] 页面差异主要由数据、组件状态、token 或局部扩展表达。
- [ ] 主路径可走通；加载 / 空 / 错有示意或 TBD。

## 11. 修订规则

- 用户提出修改意见后，先做「反馈溯源」：
  - 判断问题是否由模板结构、固定 CSS、renderer JS、示例数据、tokens、页面 / 组件规则、SVG 映射或文案规则造成。
  - 若是一次性产物问题，只修当前预览；若可能复现到后续项目，必须同步修 Skill 真源。
  - 修完 Skill 真源后，用更新后的模板 / 规则重新生成或更新当前预览，不能继续基于旧规则补丁式修图。
- 改布局：优先改模板、数据、tokens、组件参数；只对模板未覆盖区域局部补生成。
- 改视觉：优先改 token；不要在页面里散落硬编码值。
- 改图标：优先改 SVG 映射或资产文件；不要手绘替代锁定图标。
- 改交互：更新 HTML 行为与 `prototypes/*-spec.md`，确保导航一致。
- 修订后重新导出 HTML，并重新生成受影响 PNG。

## 参考文件

- [design-spec.md](design-spec.md) — 视觉、色板、禁止项
- [uikit-reference.md](uikit-reference.md) — UI Kit 组件词典
- [ota-screen-patterns.md](ota-screen-patterns.md) — 线上页面模式
- [interaction-spec.md](interaction-spec.md) — 最终交互演示 shell、固定 schema 与文件结构
- [references/rules/page-scaffolds.md](references/rules/page-scaffolds.md) — 核心页面基座
- [references/rules/list-components.md](references/rules/list-components.md) — 列表页组件细则
- [references/svg-asset-mapping.md](references/svg-asset-mapping.md) — SVG 映射机制
- [references/ux-writing.md](references/ux-writing.md) — 用户可见文案转译规则
- [references/copy-review.md](references/copy-review.md) — Preview 文案审查清单
