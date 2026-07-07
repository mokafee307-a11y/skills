# 线上 OTA 页面模式（火车票 · 参考实拍）

> 与 [uikit-reference.md](uikit-reference.md) 的 Kit 组件名组合使用。布局来自线上预订主路径实拍，生成原型时**优先复用下列区块结构**。

---

## 模式 M-HOME · 预订首页（L-HOME）

**参考**：沉浸式头图 + 主预订卡片 + 工具区 + 底 Tab。

| 区块（上→下） | UI Kit / 业务组合 | 说明 |
|---------------|-------------------|------|
| 头图区 | Title Bar-Immersive | 品牌 Slogan（如「安心订 放心行」）；右侧 `[icon/]` 优惠券等 |
| 品类 Tab | Tabs · scrollable | 机票 \| **国内·国际火车** \| 汽车 \| 船票 |
| 子品类 | Tabs · tabCount=4 | 国内 \| 欧洲 \| 韩国 \| 日本（火车选中时） |
| 预订主卡 | 搜索 + Form-Group | 白卡片圆角 12px |
| 行程类型 | Tabs · tabCount=3 | **单程** \| **往返** \| **多日通勤**（通勤场景） |
| 起终点 | 搜索 · 类型=目的地 | 大号城市名；中间 `[icon/]` 互换站点 |
| 日期 | 日期选择 | 大号日期 + 「今天/明天」语义 |
| 筛选项 | Multiple Selection-Checkbox Tag | 学生票、高铁动车 |
| 余票提示 | Tips · status=neutral | 「有票车次充足」等 |
| 优先有票 | Switch | 「优先查看有票方案」 |
| 主 CTA | Button-Booking | 文案「查询」 |
| 搜索历史 | Button · type=text | 灰色链：`南京-西安` … + 清除历史 |
| 工具箱 | 业务 CardList | 「火车百宝箱」标题 + 横向工具卡 + 四宫格入口 |
| 运营条 | Tag / Banner | 特价火车票、小时达等（可选 `高亮`） |
| 底栏 | Bottom Bar-Tab | 抢票 / 换座 / 订单 / 我的 |

---

## 模式 M-LIST · 车次列表（L-LIST）

**参考**：路线标题 + 横向日历 + 品类 Tab + 筛选 Chip + 车次卡 + 底栏排序。

| 区块（上→下） | UI Kit / 业务组合 | 说明 |
|---------------|-------------------|------|
| 顶栏 | Title Bar | 返回；标题 **`出发城市 ⇌ 到达城市`**；右侧文字+图标：**抢票**、**分享** |
| 日期条 | 日期选择 · 横向滚动 | 每日期格：周几 + 日期 + 节假日 Tag（如「休·端午节」）；选中态默认品牌蓝底白字，或蓝色强调下划线 |
| 品类 Tab | Tabs-Stacked Icon Tabs | **推荐**（附 ¥起价）\| **直达** \| **过夜** \| **中转** \| **飞机**；两行文案 |
| 筛选条 | Switch-Filter Chip · 横向滚动 | 出发站、到达站、**有票方案**、积分兑换、高铁动车 |
| 列表 | **车次结果卡**（见下） | CardList；卡间距 8px |
| 底栏 | Bottom Bar-Action · 变体=四 icon | **高级筛选** \| **出发最早** \| **耗时最短** \| **价格最低** |

### 车次结果卡（业务组合 · 线框必画）

```
┌─────────────────────────────────────────┐
│ [Tag outlined | 曾经买过]  （可选）       │
│ 06:58      8时26分      10:38      ¥532起 │
│ 上海南站    G7832 ›     北京南站    [8.8折]│
│            [icon 静行 复兴号…]             │
│ 二等·有票  一等·有票  商务·有票            │
└─────────────────────────────────────────┘
```

| 元素 | 规范 |
|------|------|
| 出发/到达时刻 | Body Emphasized/L · `#111111` |
| 站点 | Body/S · `#555555` |
| 历时 + 车次 | Body/XS · `#888888`；车次可链「经停」 |
| 价格 | Body Emphasized/L · 默认 `semantic.color.price` / `#3263A6`；促销折扣 Tag 可 `高亮` |
| 席别余票行 | 三列：席别名 + 状态「有票」；**仅「有票」二字可用 `高亮` 绿色**（线框默认灰字「有票」加粗，或标注高亮） |
| 行为标签 | Tag · outlined：曾经买过 / 上次浏览 |

---

## 模式 M-SEAT-SERVICE · 座席与服务选购（L-SELECT）

**参考**：车次摘要头 + 横向座席 Tab + 预订方案卡。

| 区块 | UI Kit | 说明 |
|------|--------|------|
| 顶栏 | Title Bar | 返回；**日期下拉**（如「10月25日 周五出发」）；**须知**、**分享** |
| 车次摘要 | 业务头图条 | 左时刻+站 \| 中历时+**G102**+经停 \| 右时刻+站；下附证件/积分/车型说明 Tips |
| 座席 Tab | Tabs · scrollable | **二等座 ¥679/抢票** \| 一等 \| 商务；选中态默认品牌蓝描边 / 蓝字 |
| 方案列表 | 业务 **预订方案卡** | 左价 + 中权益 bullet + 右 **Button-Booking「订」** |
| 底信任条 | Tips · plain | 「无需取票，刷身份证进站」；品牌 Slogan 条 |

### 预订方案卡

| 列 | 内容 |
|----|------|
| 左 | 价格大号；下挂 Tag「补贴¥2」「+保险」 |
| 中 | 权益列表（退改补偿、免登录12306 等） |
| 右 | 方形主按钮「订」 |

---

## 模式 M-FILL · 填单页（L-FORM）

**参考**：步骤条 + 行程卡 + 乘客 + 选座 + 保险 + 优惠 + 底栏。

| 区块 | UI Kit | 说明 |
|------|--------|------|
| 顶栏 | Title Bar | 返回；**步骤条** `选乘客 → 选座席 → 待预订`（业务组合，标注 `待规范确认`） |
| 行程卡 | 业务卡片 | 单程 OD、日期时刻；右侧「详情」 |
| 积分条 | Switch + Tips | 12306 积分抵扣 |
| 乘客 | Form-Group | 标题「已选 N 人」+ Button text「添加乘客」；**Multiple Selection-Checkbox Cell** 列表 |
| 联系手机 | Form-Input | 区号 + 手机号 + icon 通讯录 |
| 选座 | Form-Group + 业务座席图 | 车厢号横向 Chip；座位图 A-F；偏好 Radio |
| 保险 | Single Selection-Radio Tag · 横滑卡片 | 无保障 \| 标准 \| 尊享 |
| 优惠 | Form-Group | 优惠券、积分抵现 Switch |
| 底栏 | Bottom Bar-Action | 左总价 + 「明细」；右 **Button-Booking「立即预订」** |

---

## 模式 M-OCCUPY · 占座成功待支付（L-DETAIL + L-WAIT）

**参考**：状态头 + 倒计时 + 大单卡 + 取消 + 底栏支付。

| 区块 | UI Kit | 说明 |
|------|--------|------|
| 状态头 | Tips + icon | **占座成功**；副文案 **「请在 09:59 内完成支付」**（倒计时可 `高亮`） |
| 行程卡 | 业务卡片 | 三列：出发日期时刻站 \| 车型/经停/车次 \| 到达；分割线 |
| 乘客行 | Form-Group 只读 | 姓名、身份证脱敏、**Tag 待支付**；右：车厢座位 + 席别价 |
| 次操作 | Button · secondary | 取消订单 |
| 信任条 | Tips | 退改透明 / 售后 / 出行安心 |
| 底栏 | Bottom Bar-Action | 左 **¥总价** + 明细；右 **Button-Booking「去支付」** |

---

## 模式 M-COMMUTE · 通勤往返合一（本项目扩展）

在 **M-LIST** 基础上合并往返：

| 差异 | 说明 |
|------|------|
| 行程条 | 搜索 · 去返站点+日期 |
| 快捷条 | Form-Input ×2：坐席偏好、乘车人 |
| 列表 Tab | **去程 · 已选 Gxxx** \| **返程 · 待选择** |
| 底栏 CTA | Button-Booking「预订往返」 |
| 确认页 | M-OCCUPY 行程卡 ×2 + 返回修改 |

---

## 生图提示词要素（黑白线框）

调用 GenerateImage 时在 prompt 中**必须**包含：

1. `monochrome wireframe`, `grayscale only`, colors `#111 #555 #888 #CCC #F0F0F0 #FFFFFF`
2. 本页 **M-xxx 模式** 的区块列表（英文或中文均可）
3. 标注使用的 Kit 组件名（Title Bar, Tabs, Switch-Filter Chip, Button-Booking…）
4. `NO blue orange red except one highlighted element if specified`
5. `375px mobile OTA train booking app`, `Chinese UI`, `high fidelity layout like Ctrip`
