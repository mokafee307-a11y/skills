(function () {
  const INLINE_ICONS = {
    sparkle: '<svg viewBox="0 0 24 24"><path d="m12 2 1.8 4.2L18 8l-4.2 1.8L12 14l-1.8-4.2L6 8l4.2-1.8ZM19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9ZM5 15l.8 1.8L7.6 18l-1.8.8L5 20.6l-.8-1.8L2.4 18l1.8-.8Z"/></svg>',
    chevronLeft: '<svg viewBox="0 0 24 24"><path d="M15 5 8 12l7 7"/></svg>',
    chevronDown: '<svg viewBox="0 0 24 24"><path d="m7 10 5 5 5-5"/></svg>'
  };

  const DEFAULT_DATA = {
    statusBar: {
      time: "9:41"
    },
    titleBar: {
      backAsset: "fillBack",
      steps: ["选乘客", "选座位", "去预订"],
      actions: [
        { asset: "fillTitleBarService", label: "客服" },
        { asset: "fillTitleBarNotice", label: "须知" }
      ]
    },
    journeySummary: {
      tripType: "单程",
      route: "上海虹桥-香港西九龙",
      date: "07-10",
      time: "06:12",
      detailLabel: "详情",
      detailChevronAsset: "fillArrowDownBlue",
      subtext: "卧铺 ¥255.5 + 优享预订 ¥30",
      favorite: {
        show: false,
        saved: false,
        defaultLabel: "保存行程",
        savedLabel: "已保存行程",
        iconOffAsset: "homeCheckboxUnselected",
        iconOnAsset: "homeCheckboxSelected"
      }
    },
    pointsBar: {
      label: "积分余额：",
      highlight: "6874≈68.74元",
      switchOn: false
    },
    passengerCard: {
      countLabel: "已选：1人",
      addLabel: "添加乘客",
      addAsset: "fillPassengerAdd",
      deleteAsset: "fillPassengerDelete",
      passenger: {
        name: "梁小章",
        ticketType: "成人票",
        identity: "二代身份证 320************309"
      },
      phone: {
        label: "手机号码",
        countryCode: "+86",
        value: "183 1234 5653",
        contactsAsset: "fillPassengerContacts"
      }
    },
    seatCard: {
      title: "选座位",
      legendLabel: "座席图示",
      railLabel: "选「出站快车厢」上下车更快捷",
      carriageProduct: {
        title: "指定车厢",
        strikePrice: "¥12/人",
        priceNote: "积分特价¥7",
        cells: [
          { label: "01" },
          { label: "02" },
          { label: "03" },
          { label: "04", fast: true, tagAsset: "fillSeatFast" },
          { label: "05", subLabel: "餐车", restaurant: true },
          { label: "06", fast: true, tagAsset: "fillSeatFast" },
          { label: "07" },
          { label: "08" },
          { label: "09" }
        ]
      },
      seatMapProduct: {
        title: "在线选座",
        priceNote: "1 / 1",
        leftWindowLabel: "靠\n窗",
        aisleLabel: "过\n道",
        rightWindowLabel: "靠\n窗",
        seats: ["A", "B", "C", "D", "F"]
      },
      choiceProduct: {
        choices: [
          {
            title: "靠车门",
            highlight: "上下车更方便",
            price: "积分特价¥10/人",
            strikePrice: "¥15/人",
            selected: false
          },
          {
            title: "远离车门",
            highlight: "远离卫生间",
            price: "积分特价¥10/人",
            strikePrice: "¥15/人",
            selected: false
          }
        ]
      }
    },
    serviceCard: {
      title: "候车等待，订个贵宾厅更舒适",
      mainLabel: "贵宾厅 / 餐食厅套餐",
      price: "¥10/份",
      subLeft: "茶点零食 · 租车券 · 30天过期自动退",
      subRight: "积分已抵¥35/份"
    },
    insuranceCard: {
      title: "火车意外组合险",
      subtitle: "出行添保障, 家人更安心",
      noticeLabel: "投保须知",
      options: [
        {
          title: "无保障",
          price: "已放弃保障",
          copy: ["默认不增加购买步骤"],
          asset: "fillInsuranceNone",
          extraAsset: "fillInsuranceNoneRed",
          selected: true
        },
        {
          title: "标准保障",
          price: "20元/人",
          copy: ["意外最高赔90万", "延误最高赔50元"],
          asset: "fillInsuranceStandard",
          selected: false
        },
        {
          title: "尊享保障",
          price: "30元/人",
          copy: ["意外最高赔100万", "延误最高赔50元"],
          asset: "fillInsuranceAdvanced",
          selected: false
        }
      ],
      footnote: "本模块为投保页面，由携程保险代理有限公司管理并运营。为确保您已读投保须知等内容，并知晓保险以保险公司和产品条款内容为准。"
    },
    paybar: {
      amount: "245.5",
      coupon: "已优惠¥10",
      detailsLabel: "明细",
      detailsChevronAsset: "sharedAmountDetailsArrowDownward",
      buttonLabel: "立即预订"
    },
    assets: {
      fillBack: "assets/fill-back.svg",
      fillTitleBarService: "assets/fill-title-bar-service.svg",
      fillTitleBarNotice: "assets/list-title-bar-ticket-share.svg",
      fillArrowDownBlue: "assets/fill-arrow-down-blue.svg",
      fillPassengerAdd: "assets/fill-passenger-add.svg",
      fillPassengerContacts: "assets/fill-passenger-contacts.svg",
      fillPassengerDelete: "assets/fill-passenger-delete.svg",
      fillSeatFast: "assets/fill-seat-fast.svg",
      fillInsuranceNone: "assets/fill-insurance-none.svg",
      fillInsuranceNoneRed: "assets/fill-insurance-none-red.svg",
      fillInsuranceStandard: "assets/fill-insurance-standard.svg",
      fillInsuranceAdvanced: "assets/fill-insurance-advanced.svg",
      homeCheckboxSelected: "assets/home-checkbox-select.svg",
      homeCheckboxUnselected: "assets/home-checkbox-unselect.svg",
      sharedAmountDetailsArrowDownward: "assets/shared-amount-details-arrow-downward.svg"
    }
  };

  function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

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

  function resolveAsset(assets, keyOrPath) {
    if (!keyOrPath) {
      return "";
    }
    return assets && assets[keyOrPath] ? assets[keyOrPath] : keyOrPath;
  }

  function assetIcon(src, width, height, extraClass) {
    if (!src) {
      return "";
    }
    const className = ["asset-icon", extraClass].filter(Boolean).join(" ");
    return '<span class="' + className + '" style="width:' + width + "px;height:" + height + 'px;"><img src="' + escapeHtml(src) + '" alt="" /></span>';
  }

  function inlineIcon(name, extraClass) {
    const svg = INLINE_ICONS[name];
    if (!svg) {
      return "";
    }
    const className = ["icon", extraClass].filter(Boolean).join(" ");
    return '<span class="' + className + '">' + svg + "</span>";
  }

  function renderStatusBar(data) {
    return '' +
      '<div class="status-bar">' +
        "<span>" + escapeHtml(data.statusBar.time) + "</span>" +
        '<div class="status-right">' +
          '<div class="signal"><span></span><span></span><span></span><span></span></div>' +
          inlineIcon("sparkle") +
          '<span class="battery"></span>' +
        "</div>" +
      "</div>";
  }

  function renderBackButton(src, action) {
    return '<button class="header-back-btn' + (action ? " is-clickable" : "") + '" type="button"' + renderActionAttr(action) + '>' +
      (src ? assetIcon(src, 24, 24) : inlineIcon("chevronLeft")) +
    "</button>";
  }

  function renderTitleBar(data) {
    const assets = data.assets || {};
    const titleBar = data.titleBar || {};
    const steps = (titleBar.steps || []).map((step, index) => {
      const parts = ["<span>" + escapeHtml(step) + "</span>"];
      if (index < titleBar.steps.length - 1) {
        parts.push('<span class="dot">→</span>');
      }
      return parts.join("");
    }).join("");
    const actions = (titleBar.actions || []).map((item) => {
      return '<div class="title-mini' + (item.action ? " is-clickable" : "") + '"' + renderActionAttr(item.action) + '>' +
        assetIcon(resolveAsset(assets, item.asset), item.iconWidth || 18, item.iconHeight || 18) +
        "<span>" + escapeHtml(item.label || "") + "</span>" +
      "</div>";
    }).join("");

    return '' +
      '<div class="fill-titlebar">' +
        '<div class="titlebar-left">' + renderBackButton(resolveAsset(assets, titleBar.backAsset), titleBar.backAction) + "</div>" +
        '<div class="steps">' + steps + "</div>" +
        '<div class="right">' + actions + "</div>" +
      "</div>";
  }

  function renderJourneySummary(data) {
    const assets = data.assets || {};
    const summary = data.journeySummary || {};
    const favorite = summary.favorite || {};
    const favoriteSaved = Boolean(favorite.saved);
    const favoriteVisible = favorite.show === true;
    const favoriteLabel = favoriteSaved ? (favorite.savedLabel || favorite.defaultLabel || "") : (favorite.defaultLabel || "");
    const favoriteIcon = resolveAsset(
      assets,
      favoriteSaved ? (favorite.iconOnAsset || "homeCheckboxSelected") : (favorite.iconOffAsset || "homeCheckboxUnselected")
    );

    return '' +
      '<div class="journey-summary">' +
        '<div class="journey-line">' +
          '<span class="oneway-tag">' + escapeHtml(summary.tripType || "") + "</span>" +
          '<span class="journey-route">' + escapeHtml(summary.route || "") + "</span>" +
          '<span class="journey-date">' + escapeHtml(summary.date || "") + "</span>" +
          '<span class="journey-time">' + escapeHtml(summary.time || "") + "</span>" +
          '<button class="detail-link' + (summary.detailAction ? " is-clickable" : "") + '" type="button"' + renderActionAttr(summary.detailAction) + '>' +
            escapeHtml(summary.detailLabel || "") +
            (summary.detailChevronAsset ? assetIcon(resolveAsset(assets, summary.detailChevronAsset), 10, 10) : "") +
          "</button>" +
        "</div>" +
        '<div class="journey-sub">' + escapeHtml(summary.subtext || "") + "</div>" +
        (favoriteVisible ? '<button class="favorite-inline ' + (favoriteSaved ? "saved" : "") + (favorite.action ? " is-clickable" : "") + '" type="button"' + renderActionAttr(favorite.action) + '>' +
          assetIcon(favoriteIcon, 15, 15, "favorite-checkbox-icon") +
          "<span>" + escapeHtml(favoriteLabel) + "</span>" +
        "</button>" : "") +
      "</div>";
  }

  function renderPointsBar(data) {
    const points = data.pointsBar || {};
    const switchClass = ["switch"];
    if (points.switchOn) switchClass.push("on");
    return '' +
      '<div class="points-bar">' +
        '<span>' + inlineIcon("sparkle") + " " + escapeHtml(points.label || "") + "<strong>" + escapeHtml(points.highlight || "") + "</strong></span>" +
        '<span class="' + switchClass.join(" ") + '"></span>' +
      "</div>";
  }

  function renderPassengerCard(data) {
    const assets = data.assets || {};
    const passengerCard = data.passengerCard || {};
    const passenger = passengerCard.passenger || {};
    const phone = passengerCard.phone || {};
    return '' +
      '<div class="fill-card flush-top">' +
        '<div class="passenger-header"><strong>' + escapeHtml(passengerCard.countLabel || "") + '</strong><button class="passenger-add' + (passengerCard.addAction ? " is-clickable" : "") + '" type="button"' + renderActionAttr(passengerCard.addAction) + '>' +
          assetIcon(resolveAsset(assets, passengerCard.addAsset), 16, 16) +
          "<span>" + escapeHtml(passengerCard.addLabel || "") + "</span>" +
        "</button></div>" +
        '<div class="passenger-main">' +
          assetIcon(resolveAsset(assets, passengerCard.deleteAsset), 18, 18) +
          '<div class="passenger-main-copy">' +
            '<div class="passenger-name-row"><strong>' + escapeHtml(passenger.name || "") + '</strong>' +
              (passenger.ticketType ? '<span class="ticket-type">' + escapeHtml(passenger.ticketType) + "</span>" : "") +
            "</div>" +
            '<span class="passenger-identity">' + escapeHtml(passenger.identity || "") + "</span>" +
          "</div>" +
        "</div>" +
        '<div class="phone-row"><span>' + escapeHtml(phone.label || "") + "</span><div>" + escapeHtml(phone.countryCode || "") + "</div><div>" + escapeHtml(phone.value || "") + '</div><span class="phone-contact">' + assetIcon(resolveAsset(assets, phone.contactsAsset), 20, 20) + "</span></div>" +
      "</div>";
  }

  function renderSeatLetter(letter) {
    return '' +
      '<span class="seat-svg">' +
        '<span class="seat-svg-top"></span>' +
        '<span class="seat-svg-base"></span>' +
        "<b>" + escapeHtml(letter) + "</b>" +
      "</span>";
  }

  function renderCarriageCells(carriageProduct, assets) {
    return (carriageProduct.cells || []).map((cell) => {
      const classes = ["carriage-cell"];
      if (cell.restaurant) classes.push("restaurant");
      const lines = [escapeHtml(cell.label || "")];
      if (cell.subLabel) {
        lines.push("<small>" + escapeHtml(cell.subLabel) + "</small>");
      }
      return '<div class="' + classes.join(" ") + '">' +
        lines.join("") +
        (cell.fast && cell.tagAsset ? assetIcon(resolveAsset(assets, cell.tagAsset), 31, 17, "fast-tag-svg") : "") +
      "</div>";
    }).join("");
  }

  function renderSeatCard(data) {
    const assets = data.assets || {};
    const seatCard = data.seatCard || {};
    const carriageProduct = seatCard.carriageProduct || {};
    const seatMapProduct = seatCard.seatMapProduct || {};
    const choiceProduct = seatCard.choiceProduct || {};
    const choices = (choiceProduct.choices || []).map((choice) => {
      return '<div class="seat-choice' + (choice.action ? " is-clickable" : "") + '"' + renderActionAttr(choice.action) + '>' +
        '<strong>' + escapeHtml(choice.title || "") + (choice.highlight ? "<em>" + escapeHtml(choice.highlight) + "</em>" : "") + "</strong>" +
        '<div class="price">' + escapeHtml(choice.price || "") + (choice.strikePrice ? "<del>" + escapeHtml(choice.strikePrice) + "</del>" : "") + "</div>" +
        '<span class="radio ' + (choice.selected ? "selected" : "") + '"></span>' +
      "</div>";
    }).join("");

    return '' +
      '<div class="fill-card">' +
        '<div class="seat-header"><strong>' + escapeHtml(seatCard.title || "") + "</strong><span style=\"font-size:12px;color:#6e93b1;\">" + escapeHtml(seatCard.legendLabel || "") + "</span></div>" +
        '<div class="seat-rail">' + escapeHtml(seatCard.railLabel || "") + "</div>" +
        '<div class="carriage-box">' +
          '<div class="seat-product-card">' +
            '<div class="carriage-top"><span class="product-title">' + escapeHtml(carriageProduct.title || "") + '</span><span class="price-note">' + (carriageProduct.strikePrice ? "<del>" + escapeHtml(carriageProduct.strikePrice) + "</del>" : "") + escapeHtml(carriageProduct.priceNote || "") + "</span></div>" +
            '<div class="carriage-row">' + renderCarriageCells(carriageProduct, assets) + "</div>" +
          "</div>" +
          '<div class="seat-product-card">' +
            '<div class="carriage-top"><span class="product-title">' + escapeHtml(seatMapProduct.title || "") + '</span><span class="price-note">' + escapeHtml(seatMapProduct.priceNote || "") + "</span></div>" +
            '<div class="seat-map">' +
              '<div class="window">' + escapeHtml(seatMapProduct.leftWindowLabel || "") + "</div>" +
              renderSeatLetter((seatMapProduct.seats || [])[0] || "A") +
              renderSeatLetter((seatMapProduct.seats || [])[1] || "B") +
              renderSeatLetter((seatMapProduct.seats || [])[2] || "C") +
              '<div class="window">' + escapeHtml(seatMapProduct.aisleLabel || "") + "</div>" +
              renderSeatLetter((seatMapProduct.seats || [])[3] || "D") +
              renderSeatLetter((seatMapProduct.seats || [])[4] || "F") +
              '<div class="window">' + escapeHtml(seatMapProduct.rightWindowLabel || "") + "</div>" +
            "</div>" +
          "</div>" +
          '<div class="seat-product-card"><div class="seat-choice-row">' + choices + "</div></div>" +
        "</div>" +
      "</div>";
  }

  function renderServiceCard(data) {
    const service = data.serviceCard || {};
    return '' +
      '<div class="service-card">' +
        '<div class="service-title">' + escapeHtml(service.title || "") + "</div>" +
        '<div class="service-main"><span>' + escapeHtml(service.mainLabel || "") + '</span><span class="price">' + escapeHtml(service.price || "") + "</span></div>" +
        '<div class="service-sub"><span>' + escapeHtml(service.subLeft || "") + '</span><span>' + escapeHtml(service.subRight || "") + "</span></div>" +
      "</div>";
  }

  function renderInsuranceCard(data) {
    const assets = data.assets || {};
    const insurance = data.insuranceCard || {};
    const options = (insurance.options || []).map((item) => {
      const copy = Array.isArray(item.copy) ? item.copy.map((line) => escapeHtml(line)).join("<br />") : escapeHtml(item.copy || "");
      return '' +
        '<div class="insurance-item ' + (item.selected ? "selected" : "") + (item.action ? " is-clickable" : "") + '"' + renderActionAttr(item.action) + '>' +
          '<div class="insurance-badge">' + assetIcon(resolveAsset(assets, item.asset), 35, item.asset === "fillInsuranceNone" ? 37 : 38) + "</div>" +
          (item.extraAsset ? '<div class="insurance-badge-extra">' + assetIcon(resolveAsset(assets, item.extraAsset), 12, 12) + "</div>" : "") +
          "<strong>" + escapeHtml(item.title || "") + "</strong>" +
          '<div class="price">' + escapeHtml(item.price || "") + "</div>" +
          "<p>" + copy + "</p>" +
          '<div class="insurance-radio"></div>' +
        "</div>";
    }).join("");

    return '' +
      '<div class="insurance-card">' +
        '<div class="insurance-head"><strong>' + escapeHtml(insurance.title || "") + (insurance.subtitle ? "<span>" + escapeHtml(insurance.subtitle) + "</span>" : "") + "</strong><span class=\"note\">" + escapeHtml(insurance.noticeLabel || "") + "</span></div>" +
        '<div class="insurance-grid">' + options + "</div>" +
        '<div class="insurance-foot">' + escapeHtml(insurance.footnote || "") + "</div>" +
      "</div>";
  }

  function renderPaybar(data) {
    const assets = data.assets || {};
    const paybar = data.paybar || {};
    const detailIcon = resolveAsset(assets, paybar.detailsChevronAsset);
    return '' +
      '<div class="paybar">' +
        '<div class="pay-left"><small>¥</small><strong>' + escapeHtml(paybar.amount || "") + '</strong>' +
          (paybar.coupon ? '<span class="coupon-tag">' + escapeHtml(paybar.coupon) + "</span>" : "") +
          '<span class="pay-meta' + (paybar.detailsAction ? " is-clickable" : "") + '"' + renderActionAttr(paybar.detailsAction) + '>' + escapeHtml(paybar.detailsLabel || "") + (detailIcon ? assetIcon(detailIcon, 16, 16) : inlineIcon("chevronDown")) + "</span>" +
        "</div>" +
        '<button class="pay-btn' + (paybar.buttonAction ? " is-clickable" : "") + '" type="button"' + renderActionAttr(paybar.buttonAction) + '>' + escapeHtml(paybar.buttonLabel || "") + "</button>" +
      "</div>";
  }

  function renderPage(data) {
    return '' +
      '<div class="fill-template-phone">' +
        '<div class="fill-template-scroll">' +
          '<div class="fill-screen">' +
            '<div class="fill-top">' +
              renderStatusBar(data) +
              renderTitleBar(data) +
              renderJourneySummary(data) +
            "</div>" +
            renderPointsBar(data) +
            renderPassengerCard(data) +
            renderSeatCard(data) +
            renderServiceCard(data) +
            renderInsuranceCard(data) +
            renderPaybar(data) +
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
    if (!raw || raw === "__FILL_TEMPLATE_DATA__") {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.warn("[fill-template] failed to parse data payload:", error);
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

  window.FillPageTemplate = api;
})();
