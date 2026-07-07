(function () {
  const DEFAULT_DATA = {
    statusBar: { time: "9:41" },
    titlebar: {
      dateText: "10月25日 周五出发",
      backAsset: "back",
      arrowAsset: "titlebarArrow",
      noticeAsset: "notice",
      shareAsset: "share",
      noticeLabel: "须知",
      shareLabel: "分享"
    },
    train: {
      fromTime: "06:37",
      fromStation: "上海虹桥站",
      duration: "6时01分",
      trainNo: "G102",
      stopLabel: "经停",
      toTime: "12:38",
      toStation: "北京南站",
      features: [
        { label: "可刷证进站", help: true },
        { label: "支持12306积分兑换", help: true },
        { label: "复兴号" }
      ],
      arrowAsset: "trainArrow",
      helpAsset: "help",
      smallArrowAsset: "smallArrow"
    },
    seats: [
      { name: "二等座", price: "679", status: "抢票", active: true },
      { name: "一等座", price: "876", status: "抢票" },
      { name: "商务座", price: "876", status: "抢票" },
      { name: "无座", price: "876", status: "抢票" }
    ],
    sellCards: [
      {
        type: "high",
        price: "574",
        subsidy: "已补贴 ¥2",
        extra: "+¥49携程全能保障",
        benefits: [
          { iconAsset: "xiang", strong: "退改补偿", text: "最多省¥40" },
          { dotTone: "green", text: "视频音乐会员6选1" },
          { text: "免登录12306账号" },
          { text: "国内酒店6折起", tail: "共6项", tailAsset: "unfold" }
        ],
        button: "订"
      },
      {
        type: "middle",
        price: "576",
        extra: "+¥30优享预订",
        help: true,
        benefits: [{ text: "全天随时可出票" }, { text: "免登录12306账号" }],
        button: "订"
      },
      {
        type: "low",
        price: "576",
        benefits: [{ text: "12306购票" }, { text: "需登录12306账号" }],
        button: "订"
      },
      {
        type: "save",
        price: "573",
        label: "省钱预订",
        comparePrice: "576",
        compareLabel: "原价预订",
        savingText: "下单后预订酒店+一日游，本单立减¥30",
        button: "订"
      }
    ],
    trustTip: {
      text: "无需取票，直接刷身份证进站",
      help: true
    },
    assets: {
      back: "assets/list-title-bar-back.svg",
      titlebarArrow: "assets/middle-titlebar-arrow-downward.svg",
      notice: "assets/middle-titlebar-notice.svg",
      share: "assets/shared-title-bar-ticket-share.svg",
      trainArrow: "assets/middle-train-arrow.svg",
      smallArrow: "assets/shared-arrow-small.svg",
      help: "assets/shared-icon-qanda.svg",
      xiang: "assets/middle-sellcard-xiang.svg",
      unfold: "assets/middle-selling-card-unfold.svg",
      vs: "assets/middle-selling-card-vs.svg",
      saveMoney: "assets/middle-selling-card-save-money.svg"
    }
  };

  function isObject(value) {
    return value && typeof value === "object" && !Array.isArray(value);
  }

  function deepMerge(base, override) {
    if (!isObject(base)) return override;
    const result = { ...base };
    Object.keys(override || {}).forEach((key) => {
      const next = override[key];
      if (isObject(next) && isObject(result[key])) {
        result[key] = deepMerge(result[key], next);
      } else {
        result[key] = next;
      }
    });
    return result;
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function resolveAsset(assets, keyOrPath) {
    if (!keyOrPath) return "";
    return assets[keyOrPath] || keyOrPath;
  }

  function assetIcon(src, width, height, className) {
    if (!src) return "";
    const size = width && height ? ' style="width:' + Number(width) + 'px;height:' + Number(height) + 'px"' : "";
    return '<span class="asset-icon ' + escapeHtml(className || "") + '"' + size + '><img src="' + escapeHtml(src) + '" alt="" /></span>';
  }

  function renderActionAttr(action) {
    if (!action) return "";
    return " data-demo-action='" + escapeHtml(JSON.stringify(action)) + "'";
  }

  function renderStatusBar(statusBar) {
    return '' +
      '<div class="middle-statusbar">' +
        '<span>' + escapeHtml(statusBar.time || "9:41") + "</span>" +
        '<span class="middle-status-icons"><i></i><i></i><i></i></span>' +
      "</div>";
  }

  function renderTitlebar(data) {
    const assets = data.assets || {};
    const titlebar = data.titlebar || {};
    return '' +
      '<header class="middle-titlebar" data-template-part="middle-titlebar">' +
        '<button class="middle-back" type="button"' + renderActionAttr(titlebar.backAction) + '>' + assetIcon(resolveAsset(assets, titlebar.backAsset), 24, 24) + "</button>" +
        '<button class="middle-date-trigger" type="button"' + renderActionAttr(titlebar.dateAction) + '>' +
          '<span>' + escapeHtml(titlebar.dateText || "") + "</span>" +
          assetIcon(resolveAsset(assets, titlebar.arrowAsset), 11, 6, "middle-title-arrow") +
        "</button>" +
        '<div class="middle-title-actions">' +
          renderTitleAction(titlebar.noticeLabel, resolveAsset(assets, titlebar.noticeAsset), titlebar.noticeAction) +
          renderTitleAction(titlebar.shareLabel, resolveAsset(assets, titlebar.shareAsset), titlebar.shareAction) +
        "</div>" +
      "</header>";
  }

  function renderTitleAction(label, asset, action) {
    return '' +
      '<button class="middle-title-action" type="button"' + renderActionAttr(action) + '>' +
        assetIcon(asset, 18, 18) +
        '<span>' + escapeHtml(label || "") + "</span>" +
      "</button>";
  }

  function renderTrain(data) {
    const assets = data.assets || {};
    const train = data.train || {};
    const featureItems = (train.features || []).map((item) => {
      return '' +
        '<span class="middle-train-feature">' +
          escapeHtml(item.label || "") +
          (item.help ? assetIcon(resolveAsset(assets, item.helpAsset || train.helpAsset || "help"), 11, 11, "middle-help") : "") +
        "</span>";
    }).join('<span class="middle-feature-divider"></span>');

    return '' +
      '<section class="middle-train" data-template-part="middle-train">' +
        '<div class="middle-station left"><strong>' + escapeHtml(train.fromTime || "") + "</strong><span>" + escapeHtml(train.fromStation || "") + "</span></div>" +
        '<div class="middle-train-center">' +
          '<span class="middle-duration">' + escapeHtml(train.duration || "") + "</span>" +
          assetIcon(resolveAsset(assets, train.arrowAsset), 80, 9, "middle-train-arrow") +
          '<button class="middle-train-number" type="button"' + renderActionAttr(train.stopAction) + '>' +
            '<span>' + escapeHtml(train.trainNo || "") + "</span>" +
            '<span>' + escapeHtml(train.stopLabel || "") + "</span>" +
            assetIcon(resolveAsset(assets, train.smallArrowAsset), 9, 9) +
          "</button>" +
        "</div>" +
        '<div class="middle-station right"><strong>' + escapeHtml(train.toTime || "") + "</strong><span>" + escapeHtml(train.toStation || "") + "</span></div>" +
        '<div class="middle-train-features">' + featureItems + "</div>" +
      "</section>";
  }

  function renderSeatTabs(data) {
    const seats = data.seats || [];
    return '' +
      '<section class="middle-zuoxi" data-template-part="middle-zuoxi">' +
        '<div class="middle-seat-scroller">' +
          seats.map((seat) => {
            const classes = ["middle-seat-card"];
            if (seat.active) classes.push("active");
            if (seat.disabled) classes.push("disabled");
            return '' +
              '<button class="' + classes.join(" ") + '" type="button"' + renderActionAttr(seat.action) + '>' +
                '<strong>' + escapeHtml(seat.name || "") + "</strong>" +
                '<span><em>¥' + escapeHtml(seat.price || "") + "</em><i>" + escapeHtml(seat.status || "") + "</i></span>" +
                (seat.active ? '<b class="middle-seat-check"></b>' : "") +
              "</button>";
          }).join("") +
        "</div>" +
      "</section>";
  }

  function renderBenefit(item, assets) {
    const parts = [];
    if (item.iconAsset) {
      parts.push(assetIcon(resolveAsset(assets, item.iconAsset), 16, 16, "middle-benefit-icon"));
    } else {
      parts.push('<span class="middle-benefit-dot ' + escapeHtml(item.dotTone || "") + '"></span>');
    }
    parts.push('<span>' + (item.strong ? '<strong>' + escapeHtml(item.strong) + "</strong> " : "") + escapeHtml(item.text || "") + "</span>");
    if (item.tail) {
      parts.push('<span class="middle-benefit-tail">' + escapeHtml(item.tail) + (item.tailAsset ? assetIcon(resolveAsset(assets, item.tailAsset), 6, 6) : "") + "</span>");
    }
    return '<li>' + parts.join("") + "</li>";
  }

  function renderSellCard(card, data) {
    const assets = data.assets || {};
    const type = card.type || "middle";
    if (type === "save") {
      return renderSaveCard(card, assets);
    }
    return '' +
      '<article class="middle-sell-card ' + escapeHtml(type) + '" data-template-part="sell-card" data-sell-card-type="' + escapeHtml(type) + '">' +
        '<div class="middle-sell-price">' +
          '<div><small>¥</small><strong>' + escapeHtml(card.price || "") + "</strong></div>" +
          (card.subsidy ? '<span class="middle-subsidy">' + escapeHtml(card.subsidy || "") + "</span>" : "") +
          (card.extra ? '<p>' + escapeHtml(card.extra || "") + (card.help ? assetIcon(resolveAsset(assets, card.helpAsset || "help"), 11, 11, "middle-help") : "") + "</p>" : "") +
        "</div>" +
        '<ul class="middle-benefits">' + (card.benefits || []).map((item) => renderBenefit(item, assets)).join("") + "</ul>" +
        '<button class="middle-book-btn" type="button"' + renderActionAttr(card.action) + '>' + escapeHtml(card.button || "订") + "</button>" +
      "</article>";
  }

  function renderSaveCard(card, assets) {
    return '' +
      '<article class="middle-sell-card save" data-template-part="sell-card" data-sell-card-type="save">' +
        '<div class="middle-save-compare">' +
          '<div class="middle-save-price primary"><div><small>¥</small><strong>' + escapeHtml(card.price || "") + "</strong></div><span>" + escapeHtml(card.label || "") + "</span></div>" +
          assetIcon(resolveAsset(assets, card.vsAsset || "vs"), 21, 45, "middle-vs") +
          '<div class="middle-save-price compare"><div><small>¥</small><strong>' + escapeHtml(card.comparePrice || "") + "</strong></div><span>" + escapeHtml(card.compareLabel || "") + "</span></div>" +
        "</div>" +
        '<button class="middle-book-btn" type="button"' + renderActionAttr(card.action) + '>' + escapeHtml(card.button || "订") + "</button>" +
        '<div class="middle-save-tip">' + assetIcon(resolveAsset(assets, card.saveMoneyAsset || "saveMoney"), 47, 14) + '<span>' + escapeHtml(card.savingText || "") + "</span>" + (card.help ? assetIcon(resolveAsset(assets, card.helpAsset || "help"), 11, 11, "middle-help") : "") + "</div>" +
      "</article>";
  }

  function renderSellCards(data) {
    return '<section class="middle-sell-list">' + (data.sellCards || []).map((card) => renderSellCard(card, data)).join("") + "</section>";
  }

  function renderTrustTip(data) {
    const assets = data.assets || {};
    const trustTip = data.trustTip || {};
    if (!trustTip.text) return "";
    return '' +
      '<div class="middle-trust-tip">' +
        '<span>' + escapeHtml(trustTip.text || "") + "</span>" +
        (trustTip.help ? assetIcon(resolveAsset(assets, trustTip.helpAsset || "help"), 11, 11, "middle-help") : "") +
      "</div>";
  }

  function render(root, inputData) {
    const data = deepMerge(DEFAULT_DATA, inputData || {});
    root.innerHTML = '' +
      '<div class="middle-template-phone">' +
        '<div class="middle-screen">' +
          '<div class="middle-top-bg"></div>' +
          renderStatusBar(data.statusBar || {}) +
          renderTitlebar(data) +
          renderTrain(data) +
          renderSeatTabs(data) +
          renderSellCards(data) +
          renderTrustTip(data) +
          '<div class="middle-home-indicator"></div>' +
        "</div>" +
      "</div>";
  }

  function bootstrap(options) {
    const root = options.root;
    const script = options.dataScriptId ? document.getElementById(options.dataScriptId) : null;
    let data = {};
    if (script && script.textContent.trim() && !script.textContent.includes("__MIDDLE_TEMPLATE_DATA__")) {
      try {
        data = JSON.parse(script.textContent);
      } catch (error) {
        console.warn("Invalid middle template JSON", error);
      }
    }
    render(root, data);
  }

  window.MiddlePageTemplate = {
    render,
    bootstrap
  };
})();
