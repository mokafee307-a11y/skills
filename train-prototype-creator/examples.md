# 样例：车次列表（Ctrip UI Kit）

> 交付物形态见 [wireframes/commute-ticket-booking-preview.html](wireframes/commute-ticket-booking-preview.html)（通勤购票 · **v1.0 可交互最终版**，默认「交互演示」走通全流程）。  
> 交互说明：[prototypes/commute-ticket-booking-spec.md](prototypes/commute-ticket-booking-spec.md)

## 视觉原型 — P02 车次列表（HTML 中的一屏）

**布局范式**：L-LIST  
**用户目标**：选定车次进入选购  
**成功标准**：进入 P03

### 组件结构（对应 HTML `data-page-id`）

| 区块 | UI Kit 组件 | 说明 |
|------|-------------|------|
| 顶栏 | Title Bar | leadingAction=back |
| 条件 | 搜索 | 类型=通用 |
| 筛选 | Switch-Filter Chip | 复杂条件 → Half Screen View |
| 列表 | 业务卡片 + Single Selection-Radio Cell | 点击进入选购 |

### 示意图

导出路径示例：`wireframes/previews/P02-train-list.png`

---

## 交互说明摘录（可选 spec.md）

### 视觉标注

| 元素 | 样式 | 颜色 |
|------|------|------|
| 标题 | Heading/M | #111111 |
| 搜索摘要 | Body/M | #555555 |
| 价格 | Body Emphasized/L | #3263A6 |
| Button-Booking | — | #3263A6 底 · #FFFFFF 字 |

### 交互表

| ID | UI Kit 组件 | 触发 | 动作 | 目标 | 反馈 | 异常 |
|----|-------------|------|------|------|------|------|
| P02-I01 | 卡片行 | click | navigate | P03 | — | — |
| P02-I02 | icon/Filter | click | open | Half Screen View | — | — |
| P02-I03 | route_enter | — | api_call | 列表 | SKELETON | Empty States |

### 状态矩阵

| 状态 | 表现 |
|------|------|
| 加载 | Skeleton #F0F0F0 / #E5E5E5 |
| 空 | Empty States inPage |
| 错误 | Empty States + Button secondary「重试」 |
