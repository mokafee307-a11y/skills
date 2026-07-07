# 设计稳定规范（可编辑）

> 单一事实来源。组件以 **Ctrip UI Kit** 为准，详见 [uikit-reference.md](uikit-reference.md)。

## 本次覆盖

_（无项目特例时删除本节）_

---

## 1. 产品与平台

| 项 | 约定 |
|----|------|
| 产品类型 | **C 端**交易/预订类（出行、票务、订单闭环） |
| 默认平台 | **移动端 H5**（逻辑宽度 375；含 Status Bar、Home Indicator） |
| 设计系统 | **Ctrip UI Kit @1x**（Figma 组件名一字不差） |
| 语言与文案 | 简体中文；按钮用**动词**；字体样式用 Kit 文本样式名（如 `Body/M`） |

## 2. 信息架构原则

- **主路径参考**：火车票预订 — 首页 home → 列表 list → 中间页 middle（座席 / 预订方案）→ 填写页 fill → 占座页 occupy → 支付/订单详情（详见 [ota-screen-patterns.md](ota-screen-patterns.md)）。
- **导航深度**：不硬性限制；**超过 4 步须配流程图**。
- **列表 → 详情 → 操作**：列表用卡片/Cell；表单用 Form-* 系列。
- **流程页**：搜索 → 选择 → 补全 → 等待 → 订单；每步有**成功标准**。
- **设置/账号**：侧链，不占预订 Tab 主位。

## 3. 布局与栅格

### 3.1 间距

- 基准：**4px 倍数**。
- **Half Screen View / 底部浮层**：内容左右间距固定 **16px**；内容最下方到浮层底部的间距固定 **40px**。
- **Phase 1 视觉原型（HTML）**：浏览器可预览；逻辑宽 375；须遵守第 9 节**灰度色**（CSS 变量实现）。
- **Phase 2 交互增强**：在同一 HTML 或 spec.md 中补充状态与交互；非灰度仍须 `高亮` 标注。

### 3.2 区块命名

与 UI Kit 对齐：`Title Bar` · `搜索` · `Tabs` · `FormSection`（由 Form-Group / Form-Input 组成）· `CardList` · `Bottom Bar-Action` · `Bottom Bar-Tab` · `Half Screen View` · `Tips` · `Empty States`

### 3.3 布局范式

| 范式 ID | 结构（上 → 下） |
|---------|-----------------|
| L-HOME | Title Bar-Immersive → 品类 Tabs → **预订主卡**（单程/往返/通勤 + OD + 日期 + 查询）→ 工具箱 / Banner（见 ota M-HOME） |
| L-LIST | Title Bar（路线⇌）→ **日期选择·横滑** → Tabs-Stacked Icon Tabs → Switch-Filter Chip → **车次结果卡** → 底栏四排序（见 ota M-LIST） |
| L-SELECT | Title Bar → **车次摘要条** → Tabs（座席·横滑）→ **预订方案卡** / 选项区 → Bottom Bar-Action（见 ota M-SEAT-SERVICE） |
| L-FORM | Title Bar → Form-Group / Form-Input → **Bottom Bar-Action** 或 Button-Booking |
| L-WAIT | Title Bar → Tips/STATUS 文案区 → 订单摘要 → loading全局加载 |
| L-DETAIL | 状态头（占座成功+倒计时）→ **行程大单卡** → 乘客/座位 → Bottom Bar-Action（去支付）（见 ota M-OCCUPY） |
| L-SHEET | Half Screen View（含 bottomBar 变体） |

每页元信息声明：`布局范式: L-xxx`。

## 4. 组件选用规则

**只允许** [uikit-reference.md](uikit-reference.md) 中的组件；新组件标 `待规范确认`。

### 4.1 场景 → 组件（默认）

| 场景 | 使用组件 |
|------|----------|
| 页头/返回 | Title Bar 或 Title Bar-Immersive |
| 主 CTA（预订/支付） | **Button-Booking**（交互稿默认填充 **`#3263A6`** / 白字） |
| 次操作/文字链 | Button（type=secondary \| tertiary \| text） |
| 底栏价格+按钮 | **Bottom Bar-Action** |
| 主导航 | Bottom Bar-Tab |
| 搜索入口 | **搜索** |
| 筛选/座席切换 | Tabs（checkedColor=**blue**）或 Switch-Filter Chip |
| 表单项 | Form-Input / Form-Text area / Number Input |
| 单选/多选 | Single Selection-* / Multiple Selection-* |
| 开关加购 | Switch |
| 半屏筛选/说明 | Half Screen View |
| 强打断确认 | Dialog-Default（删除等危险操作用双按钮） |
| 营销弹窗 | Dialog-Marketing / Dialog-With Image（须标注） |
| 轻反馈 | Toast |
| 页内说明 | Tips（status: info \| warning \| error \| neutral） |
| 空/错态 | Empty States / Empty States-Image |
| 加载 | loading全局加载；列表首屏可用 Skeleton 语义（灰阶块） |
| 标签/促销 | Tag（交互稿默认 **outlined + 灰度**，见第 9 节） |
| 横向日历 | 日期选择 · 横滑（列表页顶部，选中品牌蓝底白字） |
| 车次列表卡 | 业务 **车次结果卡**（时刻三列 + 席别余票行，见 ota-screen-patterns） |
| 列表底栏 | Bottom Bar-Action · 四 icon（筛选/最早/最短/最低价） |
| 预订方案 | 业务 **预订方案卡**（价 + 权益 + 「订」按钮） |
| 步骤条 | 业务 **步骤进度条**（填单页，标 `待规范确认`） |

### 4.2 线框占位

统一格式：`[组件名 | 变体=值 | 文案]` — 见 uikit-reference 示例。

## 5. 交互惯例

### 5.1 操作结果

| 场景 | 行为 |
|------|------|
| 提交成功 | Toast → **跳转**下一流程页（交互表写清目标页） |
| 提交失败 | Toast 或 Form-Input status=error；保留输入 |
| 查询/筛选 | 刷新列表；无结果 → Empty States |

### 5.2 删除与危险操作

- **Dialog-Default**：取消（Button secondary）+ 危险确认（Button primary，交互稿可用 **#111** 填充区分）。
- 文案含后果说明。

### 5.3 表单

- 校验：失焦 + 提交全量；`Form-Input` status=error + errorText。
- 必填：Form-Input required=true。

### 5.4 加载

- 首屏：内容区 SKELETON（灰度 `#F0F0F0` / `#E5E5E5`）或 loading全局加载。
- 占座/出票：L-WAIT + 轮询说明。

### 5.5 弹层

- 筛选/复杂选项：**Half Screen View** 或 搜索 类型变体。
- 简单切换：**Tabs** / Switch-Filter Chip。

### 5.6 登录

- 未登录：跳转登录 + 回跳（交互表注明）。

## 6. 内容与排版

| 元素 | 规则 |
|------|------|
| 页面标题 | Title Bar 文案；样式 **Heading/S** 或 **Heading/M** |
| 正文 | **Body/M**、**Body/S** |
| 辅助说明 | **Body/XS** 或 **Paragraph/S**，色 `#888888` |
| 主按钮文案 | 动词；Booking 场景用 Button-Booking |
| Button-Booking 视觉 | 背景 **`#3263A6`**，文字 **`#FFFFFF`**；disabled 用 `#AAAAAA` / `#E5E5E5` |
| 价格强调 | **Body Emphasized/L** + `semantic.color.price`（默认 `#3263A6`；仅在用户明确要求纯灰线框时回退黑色） |
| 375px 屏幕效率 | 在符合 token 的前提下，按钮、Badge、Chip、Tab、日期卡、路线摘要优先单行；先改文案和容器，不靠无谓换行消化信息 |
| 换行处理顺序 | 先压缩文案 → 再调整宽度/间距 → 再单行截断/省略；只有长说明和票面必要信息允许自然换行 |

完整字号见 [uikit-reference.md](uikit-reference.md) 或 Kit 文本样式（PingFang SC）。

## 7. 禁止项

- 使用 UI Kit **未收录**的组件名（如自创 `NavBar`、`BTN-P`）。
- 交互稿中滥用品牌色（蓝/橙等）；仅第 9.3 允许的高亮场景。
- 同一 Bottom Bar-Action 两个并列主预订按钮。
- 仅交付 Markdown 线框、无 HTML 预览与关键屏示意图。
- Phase 2 在非默认语义色范围外使用色相，却未标 `高亮`。
- 跳过视觉原型直接写细交互。

## 8. 交付检查清单

- [ ] 组件名与 uikit-reference 一致
- [ ] 每页有布局范式 + 用户目标
- [ ] 交互稿颜色符合第 9 节
- [ ] 已交付 HTML + **GenerateImage** 的 previews/*.png（黑白为主）
- [ ] 布局符合 ota-screen-patterns 对应 M-xxx 模式
- [ ] 主路径可走通或 TBD
- [ ] Toast/跳转、Dialog 危险确认、Empty/Loading 已覆盖
- [ ] 多步骤流程有流程图

## 9. 交互稿视觉（HTML + 生图示意图）

### 9.0 总原则

| 规则 | 说明 |
|------|------|
| **默认基底灰度** | 页面基底仍以 §9.1 灰度为主，但主按钮与选中态默认可直接使用品牌蓝 |
| **语义色例外** | Button-Booking、选中态、价格可按 §9.3 直接使用语义色；其他色相仍需显式标 `高亮` |
| **线上密度** | 布局遵循 [ota-screen-patterns.md](ota-screen-patterns.md)，禁止简陋方块图 |
| **生图必调** | 与 HTML 成对交付，prompt 须含模式 ID + Kit 组件名 + grayscale |

### 9.1 默认：灰度色板（无色相）

交互稿、HTML 原型、**生图 PNG**、Figma 描述以以下 Neutral 色为基底（与 Kit Token 一致）：

| Token | Hex | 用途 |
|-------|-----|------|
| Black-1 | `#111111` | 主标题、关键数字 |
| Black-2 | `#555555` | 正文强调 |
| Black-3 | `#888888` | 次要文案、说明 |
| Black-4 | `#AAAAAA` | 占位、禁用文案 |
| Black-5 | `#C5C5C5` | 边框、分割线 |
| Black-6 | `#D5D5D5` | 浅分割线 |
| Black-7 | `#E5E5E5` | 描边、骨架深色 |
| Black-8 | `#F0F0F0` | 页面背景、骨架 |
| Black-9 | `#F5F5F5` | 浅背景、区块底 |
| White | `#FFFFFF` | 卡片、底栏背景 |
| Black70% | `rgba(0,0,0,0.7)` | 蒙层 |

### 9.2 标注方式

每个使用颜色的元素注明：`色 #111111`、`Token Black-3` 或 `Token semantic.color.selected`。  
生图 field 级高亮须在 spec 或 HTML 注释标 `高亮` + 色值；Button-Booking 与选中态可直接按语义 token 标注，无需额外申请例外。

### 9.3 允许的非灰度「高亮」（须显式标注）

以下语义默认可直接使用 token 色；除此之外的色相仍需字段旁加 **`高亮`**：

- Button-Booking / 主 CTA：`semantic.color.selected` → `#3263A6`
- Tabs、日期条、筛选选中、当前态强调：`semantic.color.selected` → `#3263A6`
- 价格/优惠/倒计时等**强转化**数字或文案：`semantic.color.price` → `#3263A6`
- 列表「**有票**」状态字（仅该二字，可用功能绿 `#00B87A` 等，须标 `高亮`）
- 占座倒计时文案（可 `高亮` 橙/红提醒）
- 运营 Banner、Dialog-Marketing（整组件标注）
- 错误/警告：Tips status=error/warning 可用对应功能色，或仍用灰度+图标（默认优先灰度+`icon/Warn`）
- 用户在本轮对话**点名**要高亮的字段

未落在上述语义默认范围、且未标注 `高亮` 的字段 **禁止** 使用蓝/橙/绿/红等色相。

### 9.4 Tabs / Tag 在交互稿中

- **Tabs**：`checkedColor=blue`（默认品牌蓝选中态）；仅在用户明确要求纯灰线框时再回退 black。
- **Tag**：优先 `type=outlined`，描边 `#C5C5C5`，文字 `#555555`；促销语义用 `高亮` + 单色例外。

---

## 维护说明

1. 更新 Figma 后重新导出 `uikit-data.json`，同步 [uikit-reference.md](uikit-reference.md)。
2. 项目特例写「本次覆盖」。
3. 灰度色板变更只改第 9.1 节。
