(function () {
  const DEFAULT_DATA = {
    statusBar: {
      time: "9:41"
    },
    route: {
      from: "上海",
      to: "北京"
    },
    calendar: {
      toolIconAsset: "listCalendar",
      toolChevronAsset: "listCalendarDown",
      items: [
        { topIconAsset: "listCalendarVacation", bottomText: "端午节", active: true, wide: true },
        { topText: "周一", bottomText: "09-25", wide: true },
        { topText: "周二", bottomText: "24" },
        { topText: "周三", bottomText: "25" },
        { topText: "周四", bottomText: "26" },
        { topText: "周五", bottomText: "27" }
      ]
    },
    modeTabs: [
      { title: "推荐", subtitle: "¥468 起", active: true },
      { title: "直达", subtitle: "18 班" },
      { title: "过夜", subtitle: "4 班" },
      { title: "中转", subtitle: "9 班" },
      { title: "飞机", subtitle: "¥820 起" }
    ],
    filters: [
      { label: "出发站" },
      { label: "到达站" },
      { label: "有票方案", active: true },
      { label: "高铁动车" },
      { label: "积分兑换" }
    ],
    anchorBanner: {
      title: "已为你找到推荐车次",
      copy: "优先展示有票、耗时和价格更合适的方案。"
    },
    cards: [
      {
        type: "direct",
        selected: true,
        tags: [
          { label: "曾经买过", tone: "gray" },
          { label: "收藏热度高", tone: "gray" }
        ],
        depTime: "07:18",
        depStation: "上海虹桥",
        arrTime: "12:56",
        arrStation: "北京南",
        duration: "5时38分",
        trainNo: "G7088",
        price: "553",
        discount: "商务座 9.1 折",
        note: "发车前 40 分钟可改签到更早车次，适合当天出差。",
        seats: [
          { label: "二等", value: "有票" },
          { label: "一等", value: "有票" },
          { label: "商务", value: "无票" }
        ]
      },
      {
        type: "direct",
        tags: [
          { label: "上次浏览", tone: "gray" }
        ],
        depTime: "08:00",
        depStation: "上海虹桥",
        arrTime: "12:28",
        arrStation: "北京南",
        duration: "4时28分",
        trainNo: "G7092",
        price: "628",
        note: "全程耗时最短，适合上午到达后直接开会。",
        seats: [
          { label: "二等", value: "有票" },
          { label: "一等", value: "有票" },
          { label: "商务", value: "有票" }
        ]
      },
      {
        type: "transfer",
        tags: [
          { label: "最少耗时", tone: "orange" },
          { label: "人均10分钟内换乘", tone: "blue" }
        ],
        depTime: "06:53",
        depStation: "上海站",
        arrTime: "09:48",
        arrStation: "北京西站",
        duration: "全程18时50分",
        transferStation: "南京南站",
        waitText: "停28分",
        price: "532",
        discount: "8.8折",
        legs: [
          {
            icon: "one",
            mode: "高铁",
            seats: [
              { label: "二等", value: "有票" },
              { label: "一等", value: "有票" },
              { label: "商务", value: "无票" }
            ]
          },
          {
            icon: "two",
            mode: "普快",
            seats: [
              { label: "硬座", value: "有票" },
              { label: "硬卧", value: "有票" },
              { label: "软卧", value: "有票" }
            ]
          }
        ]
      }
    ],
    sortTabs: [
      { label: "高级筛选", asset: "listTabAll" },
      { label: "出发最早", asset: "listTabEarly" },
      { label: "耗时最短", asset: "listTabTime" },
      { label: "价格最低", asset: "listTabPrice" }
    ],
    assets: {
      listTitleBarBack: "assets/list-title-bar-back.svg",
      listTitleBarChange: "assets/list-title-bar-change.svg",
      listTitleBarTicketGrabbing: "assets/list-title-bar-ticket-grabbing.svg",
      listTitleBarTicketShare: "assets/list-title-bar-ticket-share.svg",
      listCalendar: "assets/list-calendar.svg",
      listCalendarDown: "assets/list-calendar-down.svg",
      listCalendarVacation: "assets/list-calendar-vacation.svg",
      listCardArrow: "assets/list-card-arrow.svg",
      listCardExchange: "assets/list-card-exchange.svg",
      listCardIdentityCard: "assets/list-card-identity-card.svg",
      listCardFuxingtrain: "assets/list-card-fuxingtrain.svg",
      listCardDepartureStation: "assets/list-card-departure-station.svg",
      listCardDestination: "assets/list-card-destination.svg",
      listCardOne: "assets/list-card-one.svg",
      listCardTwo: "assets/list-card-two.svg",
      listTabAll: "assets/list-tab-all.svg",
      listTabEarly: "assets/list-tab-early.svg",
      listTabTime: "assets/list-tab-time.svg",
      listTabPrice: "assets/list-tab-price.svg"
    }
  };

  function deepMerge(base, patch) {
    if (Array.isArray(base) || Array.isArray(patch)) {
      return patch === undefined ? base : patch;
    }
    if (!isObject(base) || !isObject(patch)) {
      return patch === undefined ? base : patch;
    }
    const out = { ...base };
    Object.keys(patch).forEach((key) => {
      out[key] = key in base ? deepMerge(base[key], patch[key]) : patch[key];
    });
    return out;
  }

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function encodeAction(action) {
    if (!isObject(action)) {
      return "";
    }
    try {
      return JSON.stringify(action);
    } catch (error) {
      return "";
    }
  }

  function renderActionAttr(action) {
    const payload = encodeAction(action);
    if (!payload) {
      return "";
    }
    return ' data-demo-action="' + escapeHtml(payload) + '"';
  }

  function assetIcon(src, width, height, extraClass) {
    if (!src) {
      return "";
    }
    const className = ["asset-icon", extraClass].filter(Boolean).join(" ");
    return '<span class="' + className + '" style="width:' + width + "px;height:" + height + 'px;"><img src="' + escapeHtml(src) + '" alt="" /></span>';
  }

  function normalizeSeat(seat) {
    const label = seat && seat.label ? seat.label : "";
    const rawValue = seat && seat.value ? seat.value : "";
    const available = rawValue === "有票";
    return {
      label: label,
      value: available ? "有票" : "无票",
      tone: available ? "ok" : "warn"
    };
  }

  function cardTag(tag) {
    const tone = tag && tag.tone ? tag.tone : "gray";
    return '<span class="mini-badge ' + escapeHtml(tone) + '">' + escapeHtml(tag.label) + "</span>";
  }

  function normalizeDirectDiscount(value) {
    const text = String(value ?? "").trim();
    if (!text) {
      return "";
    }
    const foldMatch = text.match(/(\d+(?:\.\d+)?)\s*折/);
    if (foldMatch) {
      return foldMatch[1] + "折";
    }
    return /(减|优惠|券后|省|特价|直降)/.test(text) ? text : "";
  }

  function renderStatusBar(data) {
    return '' +
      '<div class="status-bar">' +
        "<span>" + escapeHtml(data.statusBar.time) + "</span>" +
        '<div class="status-right">' +
          '<div class="signal"><span></span><span></span><span></span><span></span></div>' +
          '<span class="battery"></span>' +
        "</div>" +
      "</div>";
  }

  function renderTitleBar(data) {
    const assets = data.assets;
    const backAction = data.backAction;
    return '' +
      '<div class="titlebar">' +
        '<div class="titlebar-left"><button class="header-back-btn' + (backAction ? " is-clickable" : "") + '"' + renderActionAttr(backAction) + '>' + assetIcon(assets.listTitleBarBack, 24, 24) + "</button></div>" +
        '<div class="titlebar-center"><span>' + escapeHtml(data.route.from) + "</span>" + assetIcon(assets.listTitleBarChange, 16, 16) + "<span>" + escapeHtml(data.route.to) + "</span></div>" +
        '<div class="titlebar-right">' +
          '<div class="action-stack">' + assetIcon(assets.listTitleBarTicketGrabbing, 18, 18) + "<span>抢票</span></div>" +
          '<div class="action-stack">' + assetIcon(assets.listTitleBarTicketShare, 18, 18) + "<span>分享</span></div>" +
        "</div>" +
      "</div>";
  }

  function renderCalendar(data) {
    const assets = data.assets;
    const items = data.calendar.items.map((item) => {
      const topIconAsset = item.topIconAsset || item.weekIconAsset;
      const isFestival = Boolean(topIconAsset || item.isFestival);
      const line1Text = item.topText ?? item.week ?? "";
      const line2Text = item.bottomText ?? (isFestival ? (item.note ?? item.date ?? "") : (item.date ?? item.note ?? ""));
      const wide = item.wide || String(line2Text || "").length > 3;
      const classes = ["calendar-cell"];
      if (wide) classes.push("wide");
      if (item.active) classes.push("active");
      const topParts = [];
      if (line1Text) {
        topParts.push('<span class="calendar-line-top-text">' + escapeHtml(line1Text) + "</span>");
      }
      if (topIconAsset) {
        topParts.push(assetIcon(assets[topIconAsset] || topIconAsset, 12, 12, "calendar-line-top-icon"));
      }
      return '' +
        '<div class="' + classes.join(" ") + '">' +
          '<div class="calendar-line-top">' +
            (topParts.length ? topParts.join("") : escapeHtml(line1Text)) +
          "</div>" +
          '<span class="calendar-line-bottom numeric">' + escapeHtml(line2Text) + "</span>" +
        "</div>";
    }).join("");

    const toolIconAsset = data.calendar.toolIconAsset || "listCalendar";
    const toolChevronAsset = data.calendar.toolChevronAsset || "listCalendarDown";
    return '' +
      '<div class="calendar-strip">' +
        '<div class="calendar-rail">' + items + "</div>" +
        '<div class="calendar-tools">' +
          assetIcon(assets[toolIconAsset] || toolIconAsset, 24, 24) +
          assetIcon(assets[toolChevronAsset] || toolChevronAsset, 10, 6) +
        "</div>" +
      "</div>";
  }

  function renderModeTabs(data) {
    return '<div class="mode-tabs">' +
      data.modeTabs.map((item) => {
        const classes = ["mode-tab"];
        if (item.active) classes.push("active");
        if (item.action) classes.push("is-clickable");
        return '<div class="' + classes.join(" ") + '"' + renderActionAttr(item.action) + '><strong>' + escapeHtml(item.title) + "</strong><span>" + escapeHtml(item.subtitle) + "</span></div>";
      }).join("") +
    "</div>";
  }

  function renderFilters(data) {
    return '<div class="filter-pills">' +
      data.filters.map((item) => {
        const classes = ["filter-pill"];
        if (item.active) classes.push("active");
        if (item.action) classes.push("is-clickable");
        return '<span class="' + classes.join(" ") + '"' + renderActionAttr(item.action) + '>' + escapeHtml(item.label) + "</span>";
      }).join("") +
    "</div>";
  }

  function renderDirectCard(card, data) {
    const assets = data.assets;
    const tags = (card.tags || []).map(cardTag).join("");
    const discountText = normalizeDirectDiscount(card.discount);
    const seats = (card.seats || []).map((seat, index) => {
      const normalized = normalizeSeat(seat);
      const align = index === 0 ? "left" : (index === 1 ? "center" : "right");
      return '<div class="seat-cell ' + normalized.tone + " " + align + '"><span>' + escapeHtml(normalized.label) + "</span><strong>" + escapeHtml(normalized.value) + "</strong></div>";
    }).join("");

    const cardClasses = ["train-card"];
    if (card.selected) cardClasses.push("selected");
    if (card.action) cardClasses.push("is-clickable");

    return '' +
      '<button class="' + cardClasses.join(" ") + '"' + renderActionAttr(card.action) + '>' +
        '<div class="train-shell">' +
          (tags ? '<div class="train-note-row">' + tags + "</div>" : "") +
          '<div class="train-main">' +
            '<div class="time-col"><strong class="time-value">' + escapeHtml(card.depTime) + '</strong><span class="station-name">' + escapeHtml(card.depStation) + "</span></div>" +
            '<div class="train-route">' +
              '<span class="train-duration">' + escapeHtml(card.duration) + "</span>" +
              '<div class="train-arrow-line">' + assetIcon(assets.listCardArrow, 60, 5) + "</div>" +
              '<div class="train-trainline">' +
                '<span class="train-no-code">' + escapeHtml(card.trainNo) + "</span>" +
                assetIcon(assets.listCardExchange, 12, 12) +
                assetIcon(assets.listCardIdentityCard, 14, 12) +
                assetIcon(assets.listCardFuxingtrain, 28, 12) +
              "</div>" +
            "</div>" +
            '<div class="time-col right"><strong class="time-value">' + escapeHtml(card.arrTime) + '</strong><span class="station-name">' + escapeHtml(card.arrStation) + "</span></div>" +
            '<div class="train-price-wrap">' +
              '<div class="train-price-main"><span class="currency">¥</span><strong class="price-value">' + escapeHtml(card.price) + '</strong><span class="suffix">起</span></div>' +
              (discountText ? '<div class="train-discount">' + escapeHtml(discountText) + "</div>" : "") +
            "</div>" +
          "</div>" +
          '<div class="train-seat-row">' + seats + "</div>" +
          (card.note ? '<div class="train-note">' + escapeHtml(card.note) + "</div>" : "") +
        "</div>" +
      "</button>";
  }

  function renderTransferCard(card, data) {
    const assets = data.assets;
    const tags = (card.tags || []).map(cardTag).join("");
    const groups = (card.legs || []).map((leg) => {
      const iconAsset = leg.icon === "one" ? assets.listCardOne : assets.listCardTwo;
      const firstSeat = normalizeSeat((leg.seats || [])[0] || {});
      const secondSeat = normalizeSeat((leg.seats || [])[1] || {});
      const thirdSeat = normalizeSeat((leg.seats || [])[2] || {});
      return '' +
        '<div class="transfer-seat-group">' +
          '<div class="transfer-seat-cell left ' + firstSeat.tone + '">' +
            '<span class="transfer-leg-head">' + assetIcon(iconAsset, 13, 13) + "<span>" + escapeHtml(leg.mode) + "</span></span>" +
            '<span class="transfer-seat-copy"><span>' + escapeHtml(firstSeat.label) + "</span><strong>" + escapeHtml(firstSeat.value) + "</strong></span>" +
          "</div>" +
          '<div class="transfer-seat-cell center ' + secondSeat.tone + '"><span class="transfer-seat-copy"><span>' + escapeHtml(secondSeat.label) + "</span><strong>" + escapeHtml(secondSeat.value) + "</strong></span></div>" +
          '<div class="transfer-seat-cell right ' + thirdSeat.tone + '"><span class="transfer-seat-copy"><span>' + escapeHtml(thirdSeat.label) + "</span><strong>" + escapeHtml(thirdSeat.value) + "</strong></span></div>" +
        "</div>";
    }).join("");

    return '' +
      '<div class="transfer-card' + (card.action ? " is-clickable" : "") + '"' + renderActionAttr(card.action) + '>' +
        (tags ? '<div class="transfer-badge-row">' + tags + "</div>" : "") +
        '<div class="transfer-main-grid">' +
          '<div class="transfer-time-block"><strong class="time-value">' + escapeHtml(card.depTime) + '</strong><div class="transfer-station-row"><span>' + escapeHtml(card.depStation) + "</span>" + assetIcon(assets.listCardDepartureStation, 12, 12) + "</div></div>" +
          '<div class="transfer-center-block">' +
            '<div class="transfer-duration">' + escapeHtml(card.duration) + "</div>" +
            '<div class="transfer-line-wrap"><span class="transfer-station-pill">' + escapeHtml(card.transferStation) + "</span></div>" +
            '<div class="transfer-stop-time">' + escapeHtml(card.waitText) + "</div>" +
          "</div>" +
          '<div class="transfer-time-block arrive"><strong class="time-value">' + escapeHtml(card.arrTime) + '</strong><div class="transfer-station-row">' + assetIcon(assets.listCardDestination, 12, 12) + "<span>" + escapeHtml(card.arrStation) + "</span></div></div>" +
          '<div class="transfer-price-block"><div class="transfer-price-main"><span class="currency">¥</span><strong class="price-value">' + escapeHtml(card.price) + '</strong><span class="suffix">起</span></div>' + (card.discount ? '<div class="transfer-discount">' + escapeHtml(card.discount) + "</div>" : "") + "</div>" +
        "</div>" +
        '<div class="transfer-seat-groups">' + groups + "</div>" +
      "</div>";
  }

  function renderSortBar(data) {
    return '<div class="list-sortbar">' +
      data.sortTabs.map((item) => {
        const iconSrc = data.assets[item.asset] || item.asset;
        return '<div class="sort-item' + (item.action ? " is-clickable" : "") + '"' + renderActionAttr(item.action) + '>' + assetIcon(iconSrc, 20, 20) + "<span>" + escapeHtml(item.label) + "</span></div>";
      }).join("") +
    "</div>";
  }

  function renderPage(data) {
    const cardsHtml = (data.cards || []).map((card) => {
      return card.type === "transfer" ? renderTransferCard(card, data) : renderDirectCard(card, data);
    }).join("");

    return '' +
      '<div class="list-template-phone">' +
          '<div class="list-template-scroll">' +
          '<div class="list-screen">' +
            '<div class="list-top">' +
              renderStatusBar(data) +
              renderTitleBar(data) +
              renderCalendar(data) +
              renderModeTabs(data) +
              renderFilters(data) +
            "</div>" +
            (data.anchorBanner ? '<div class="anchor-banner"><strong>' + escapeHtml(data.anchorBanner.title) + "</strong>" + escapeHtml(data.anchorBanner.copy) + "</div>" : "") +
            '<div class="list-cards">' + cardsHtml + "</div>" +
            renderSortBar(data) +
          "</div>" +
        "</div>" +
      "</div>";
  }

  function parseScriptPayload(id) {
    const node = document.getElementById(id);
    if (!node) {
      return null;
    }
    const raw = node.textContent.trim();
    if (!raw || raw === "__LIST_TEMPLATE_DATA__") {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.warn("[list-template] failed to parse data payload:", error);
      return null;
    }
  }

  const api = {
    defaults: DEFAULT_DATA,
    render(root, patch) {
      const data = deepMerge(DEFAULT_DATA, patch || {});
      root.innerHTML = renderPage(data);
      return data;
    },
    bootstrap(options) {
      const root = options && options.root;
      if (!root) {
        return null;
      }
      const patch = parseScriptPayload(options.dataScriptId);
      return api.render(root, patch);
    }
  };

  window.ListPageTemplate = api;
})();
