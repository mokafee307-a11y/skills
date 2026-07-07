# Ctrip UI Kit 组件索引

> 来源：`uikit-data.json`（Figma：Ctrip UI Kit @1x）· 导出 2026-05-27  
> 生成线框/交互稿时 **组件名必须与下表一致**（含大小写、连字符）。变体在交付物中写明。

完整原始数据：`/Users/mokafee/Desktop/uikit-data.json`（更新 Kit 后请重新导出并同步本文件）。

---

## 系统 / 壳层

| 组件名 | 说明 | 常用变体 |
|--------|------|----------|
| Status Bar | 系统状态栏 | color: black \| white |
| Home Indicator | 底部横条 | — |
| Title Bar | 标准标题栏 | leadingAction: back \| close；titleType: text \| searchBar \| tab；bgColor: white \| blue \| gray |
| Title Bar-Immersive | 沉浸式标题 | leadingAction: 返回箭头 \| 关闭按钮 |
| Bottom Bar-Tab | 底部 Tab | itemCount: 2–5 |
| Bottom Bar-Action | 底部操作栏（价格+按钮） | type: singleButton \| doubleButton \| leadingActions \| withInfo |

## 按钮

| 组件名 | 说明 | 常用变体 |
|--------|------|----------|
| Button | 通用按钮 | type: primary \| secondary \| tertiary \| text；state: default \| disabled \| pressed \| loading* |
| Button-Booking | 预订主按钮 | state: default \| disabled \| pressed；交互稿默认填充 **#3263A6** / 文字 #FFFFFF |
| Button-icon | 图标按钮 | type + state 同 Button |

## 导航 / 分类

| 组件名 | 说明 | 常用变体 |
|--------|------|----------|
| Tabs | 文字 Tab | tabCount: 2–5 \| scrollable；checkedColor: **blue**（交互稿默认）\| black |
| Tabs-Stacked Icon Tabs | 图标+文字堆叠 | 同上 |
| Tabs-Inline Icon Tabs | 行内图标 Tab | 同上 |
| 搜索 | 搜索条 | 类型: 通用 \| 问道 \| 目的地；返回箭头、搜索按钮开关 |

## 表单

| 组件名 | 说明 | 常用变体 |
|--------|------|----------|
| Form-Input | 表单项 | type: default \| withAction \| stacked \| withHelpText；status: default \| error \| focused |
| Form-Group | 表单分组 | type 等 |
| Form-Text area | 多行文本 | 独立组件 |
| Number Input | 步进数字 | number, type, editable |
| Switch | 开关 | size, status, disabled |
| Switch-Filter Chip | 筛选芯片开关 | label, status |
| Single Selection-Radio | 单选圆点 | selected, status, Disable |
| Single Selection-Radio Tag | 单选标签 | type: solid \| outlined；status: default \| selected |
| Single Selection-Radio List | 单选列表行 | 显示分割线, status |
| Single Selection-Radio Cell | 单选单元格 | radioPosition: left \| right；含 title/description |
| Multiple Selection-Checkbox | 多选 | selected, disabled |
| Multiple Selection-Checkbox Tag | 多选标签 | 同 Radio Tag |
| Multiple Selection-Checkbox Cell | 多选单元格 | checkboxPosition: left \| right |
| 日期选择 | 日期 | 独立组件 |
| 日期选择+时间-计时制 | 日期+时间 | 计时制, 单双选 |
| 时间选择-计时制 | 时间 | 计时制 |
| 时间选择-与日历组合使用 | 时间+日历 | 状态 |

## 反馈 / 弹层

| 组件名 | 说明 | 常用变体 |
|--------|------|----------|
| Dialog-Default | 标准对话框 | hasTitle, hasDescription |
| Dialog-With Image | 带图对话框 | 同上 |
| Dialog-Long Content | 长文案对话框 | — |
| Dialog-Marketing | 营销对话框 | — |
| Half Screen View | 半屏弹层 | type: Default \| With image；bottomBar: none \| singleButton \| … |
| Toast | 轻提示 | type, label |
| Tooltips | 气泡提示 | size, direction, showClose |
| Tips | 页面提示条 | type: card \| plain；status: error \| warning \| info \| neutral |
| loading全局加载 | 全局 Loading | isBlocking, label |
| Empty States | 空状态 | type: inPage \| inContainer \| inItem；button 开关 |
| Empty States-Image | 带图空状态 | type |

## 展示 / 标记

| 组件名 | 说明 | 常用变体 |
|--------|------|----------|
| Tag | 标签 | size: small \| large；type: solid \| outlined；color: *交互稿默认不用彩色* |
| Tag-Badge | 角标标签 | size, hasIcon |
| Tag-Bubble | 气泡标签 | direction |
| Tag-Pointer | 指针标签 | size, direction |
| Badge | 徽章数字 | type, label |
| Floating Button | 悬浮按钮 | size, type, shortLabel/longLabel |

## 图标

- 使用 `icon/*` 名称（如 `icon/Back`、`icon/Close`），见 JSON `icons` 数组（117 个）。
- 线框写：`[icon/Back]`，不臆造图标名。

---

## 线上 OTA 业务组合块（与 Kit 组件组合使用）

> 布局细则见 [ota-screen-patterns.md](ota-screen-patterns.md)。下列名称用于 HTML `data-uikit` 与 spec 描述；**非** Figma 独立组件，标注 `业务组合`。

| 组合块名 | 常用 Kit 子件 | 典型页面 |
|----------|---------------|----------|
| 车次结果卡 | Tag + Body 时刻列 + Tag 席别行 | M-LIST 列表 |
| 预订方案卡 | Body 价格 + Tips 权益列表 + Button-Booking「订」 | M-SEAT-SERVICE |
| 预订主卡 | Tabs + 搜索(OD) + 日期选择 + Checkbox Tag + Button-Booking | M-HOME |
| 行程大单卡 | 三列时刻 + Form-Group 乘客行 | M-OCCUPY |
| 步骤进度条 | Tips / 业务（`待规范确认`） | M-FILL |
| 底栏四排序 | Bottom Bar-Action + icon/* ×4 | M-LIST |

---

## 线框占位写法（统一）

```
[组件名 | 关键变体=值 | 文案占位]
```

示例：

```
[Title Bar | leadingAction=back | titleType=text | 车次列表]
[搜索 | 类型=通用 | 上海→北京]
[Button-Booking | state=default | 预订]
[Bottom Bar-Action | type=singleButton | ¥553 起]
[Form-Input | type=default | 乘客姓名]
[Half Screen View | type=Default | 筛选]
[Empty States | type=inPage | 暂无车次]
```
