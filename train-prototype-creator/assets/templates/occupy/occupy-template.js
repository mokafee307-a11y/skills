(function () {
  const INLINE_ICONS = {
    sparkle: '<svg viewBox="0 0 24 24"><path d="m12 2 1.8 4.2L18 8l-4.2 1.8L12 14l-1.8-4.2L6 8l4.2-1.8ZM19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9ZM5 15l.8 1.8L7.6 18l-1.8.8L5 20.6l-.8-1.8L2.4 18l1.8-.8Z"/></svg>',
    chevronLeft: '<svg viewBox="0 0 24 24"><path d="M15 5 8 12l7 7"/></svg>',
    chevronDown: '<svg viewBox="0 0 24 24"><path d="m7 10 5 5 5-5"/></svg>',
    success: '<svg viewBox="0 0 24 24"><path d="m5 12 4 4 10-10"/></svg>'
  };

  const DEFAULT_DATA = {
    statusBar: {
      time: "9:41"
    },
    titleBar: {
      backAsset: "occupyBack"
    },
    orderStatus: {
      iconAsset: "occupyOrderStatusSuccess",
      title: "占座成功",
      subtitle: "请在09分59秒内完成支付"
    },
    ticketCard: {
      departure: {
        date: "3月21日 周日",
        time: "05:53",
        station: "上海虹桥站"
      },
      middle: {
        model: "CRH2B型",
        journeyAsset: "occupyTicketCardTransit",
        trainNo: "G4833",
        arrowAsset: "occupyTicketCardArrow"
      },
      arrival: {
        date: "周日 3月21日",
        time: "06:12",
        station: "北京南站"
      },
      passenger: {
        name: "梁小章",
        identity: "身份证 372330********0079",
        state: "待支付"
      },
      seat: {
        label: "二等座 ¥50",
        value: "02车厢01C号"
      }
    },
    extraSections: [],
    cancelButtonLabel: "取消订单",
    paybar: {
      amount: "245.5",
      coupon: "已优惠¥10",
      detailsLabel: "明细",
      detailsChevronAsset: "sharedAmountDetailsArrowDownward",
      buttonLabel: "去支付"
    },
    assets: {
      occupyBack: "assets/occupy-back.svg",
      occupyOrderStatusSuccess: "assets/occupy-order-status-success.svg",
      occupyTicketCardArrow: "assets/occupy-ticket-card-arrow.svg",
      occupyTicketCardPoi: "assets/occupy-ticket-card-poi.svg",
      occupyTicketCardTransit: "assets/occupy-ticket-card-transit.svg",
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

  function renderOrderHeader(data) {
    const assets = data.assets || {};
    const titleBar = data.titleBar || {};
    const orderStatus = data.orderStatus || {};
    const iconSrc = resolveAsset(assets, orderStatus.iconAsset);
    const state = orderStatus.state || "success";
    const isLoading = state === "loading";
    return '' +
      '<div class="occupy-header">' +
        renderStatusBar(data) +
        '<div class="occupy-titlebar"><div class="titlebar-left">' + renderBackButton(resolveAsset(assets, titleBar.backAsset), titleBar.backAction) + "</div></div>" +
        '<div class="occupy-success">' +
          '<div class="success-mark ' + escapeHtml(state) + ' ' + (iconSrc ? "asset-mode" : "") + '">' + (isLoading ? '<span class="loading-ring"></span>' : (iconSrc ? assetIcon(iconSrc, 37, 37) : inlineIcon("success"))) + "</div>" +
          "<div><strong>" + escapeHtml(orderStatus.title || "") + "</strong><span>" + escapeHtml(orderStatus.subtitle || "") + "</span></div>" +
        "</div>" +
      "</div>";
  }

  function renderStationLine(label, assets) {
    return '<div class="station-line"><span>' + escapeHtml(label || "") + "</span>" + assetIcon(resolveAsset(assets, "occupyTicketCardPoi"), 13, 13) + "</div>";
  }

  function renderTicketCard(data) {
    const assets = data.assets || {};
    const ticket = data.ticketCard || {};
    const departure = ticket.departure || {};
    const middle = ticket.middle || {};
    const arrival = ticket.arrival || {};
    const passenger = ticket.passenger || {};
    const seat = ticket.seat || {};
    const cardAction = ticket.action;

    return '' +
      '<div class="ticket-card' + (cardAction ? " is-clickable" : "") + '"' + renderActionAttr(cardAction) + '>' +
        '<div class="ticket-top">' +
          '<div class="ticket-col"><div>' + escapeHtml(departure.date || "") + "</div><strong>" + escapeHtml(departure.time || "") + "</strong>" + renderStationLine(departure.station, assets) + "</div>" +
          '<div class="ticket-middle"><div>' + escapeHtml(middle.model || "") + '</div><div class="journey-info">' + assetIcon(resolveAsset(assets, middle.journeyAsset), 103, 20) + '</div><div class="train-code-line"><span>' + escapeHtml(middle.trainNo || "") + "</span>" + assetIcon(resolveAsset(assets, middle.arrowAsset), 10, 10) + "</div></div>" +
          '<div class="ticket-col right"><div>' + escapeHtml(arrival.date || "") + "</div><strong>" + escapeHtml(arrival.time || "") + "</strong>" + renderStationLine(arrival.station, assets) + "</div>" +
        "</div>" +
        '<div class="ticket-bottom">' +
          '<div class="ticket-passenger">' +
            '<div class="ticket-passenger-head"><strong>' + escapeHtml(passenger.name || "") + "</strong></div>" +
            '<div class="ticket-passenger-identity">' + escapeHtml(passenger.identity || "") + "</div>" +
            '<div class="state">' + escapeHtml(passenger.state || "") + "</div>" +
          "</div>" +
          '<div class="seat"><span>' + escapeHtml(seat.label || "") + "</span><strong>" + escapeHtml(seat.value || "") + "</strong></div>" +
        "</div>" +
      "</div>";
  }

  function renderExtraSections(data) {
    return (data.extraSections || []).map((section) => {
      if (section.html) {
        return section.html;
      }
      return '<div class="occupy-extra-card' + (section.action ? " is-clickable" : "") + '"' + renderActionAttr(section.action) + '>' +
        (section.title ? "<strong>" + escapeHtml(section.title) + "</strong>" : "") +
        (section.copy ? "<p>" + escapeHtml(section.copy) + "</p>" : "") +
      "</div>";
    }).join("");
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
      '<div class="occupy-template-phone">' +
        '<div class="occupy-template-scroll">' +
          '<div class="occupy-screen">' +
            renderOrderHeader(data) +
            renderTicketCard(data) +
            renderExtraSections(data) +
            '<button class="ghost-cta' + (data.cancelAction ? " is-clickable" : "") + '" type="button"' + renderActionAttr(data.cancelAction) + '>' + escapeHtml(data.cancelButtonLabel || "") + "</button>" +
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
    if (!raw || raw === "__OCCUPY_TEMPLATE_DATA__") {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.warn("[occupy-template] failed to parse data payload:", error);
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

  window.OccupyPageTemplate = api;
})();
