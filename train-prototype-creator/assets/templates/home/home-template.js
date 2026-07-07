(function () {
  const INLINE_ICONS = {
    sparkle: '<svg viewBox="0 0 24 24"><path d="m12 2 1.8 4.2L18 8l-4.2 1.8L12 14l-1.8-4.2L6 8l4.2-1.8ZM19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9ZM5 15l.8 1.8L7.6 18l-1.8.8L5 20.6l-.8-1.8L2.4 18l1.8-.8Z"/></svg>',
    seat: '<svg viewBox="0 0 24 24"><path d="M7 12V7a2 2 0 0 1 2-2h1a2 2 0 0 1 2 2v5"/><path d="M5 12h12a2 2 0 0 1 2 2v2H5v-4Z"/><path d="M7 16v2M17 16v2"/></svg>',
    user: '<svg viewBox="0 0 24 24"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z"/><path d="M5 20a7 7 0 0 1 14 0"/></svg>'
  };

  const DEFAULT_DATA = {
    statusBar: {
      time: "9:41"
    },
    hero: {
      backAsset: "homeBack",
      backWidth: 32,
      backHeight: 32
    },
    traffic: {
      mini: {
        asset: "homePlane",
        label: "机票"
      },
      primaryTabs: [
        { label: "国内·国际火车", active: true },
        { label: "汽车" },
        { label: "船票" }
      ],
      regions: [
        { label: "国内", active: true },
        { label: "欧洲" },
        { label: "韩国" },
        { label: "日本" }
      ],
      tripTypes: [
        { label: "单程", active: true },
        { label: "往返" },
        { label: "多程" }
      ]
    },
    search: {
      from: "北京",
      to: "西安",
      switchAsset: "homeSwitch",
      dateValue: "12月20日",
      dateLabel: "今天",
      checks: [
        { label: "学生票", checked: false },
        { label: "高铁动车", checked: false }
      ],
      stateLabel: "有票车次充足",
      stateTone: "ok",
      toggleLabel: "优先查看有票方案",
      toggleAsset: "homeCheckboxUnselected",
      benefitTag: null,
      queryLabel: "查询",
      history: [
        "南京-西安",
        "北京-上海",
        "乌鲁木齐南-伊犁"
      ],
      historyClearLabel: "清除历史"
    },
    bodySections: [
      {
        title: "火车百宝箱",
        minor: "全部",
        type: "toolbox",
        data: {
          minorChevronAsset: "homeArrowSmall",
          cards: [
            {
              title: "在线换座",
              copy: "靠窗下铺连座随心换",
              tag: "换座"
            },
            {
              title: "开售查询",
              copy: "查询提前买"
            },
            {
              title: "火车超能力",
              copy: "充能免费送"
            }
          ],
          links: [
            "抢票攻略",
            "携童出行",
            "退改须知",
            "省钱任务"
          ]
        }
      }
    ],
    bottomTabs: [
      { asset: "homeTabTicketGrabbing", label: "抢票", active: true },
      { asset: "homeTabChangeSeat", label: "在线换座" },
      { asset: "homeTabOrder", label: "我的订单" },
      { asset: "homeTabPersonal", label: "个人中心" }
    ],
    floatingSheet: null,
    assets: {
      homeBack: "assets/home-back.svg",
      homePlane: "assets/home-tab-flight.svg",
      homeSwitch: "assets/home-switch.svg",
      homeArrowSmall: "assets/home-arrow-small.svg",
      homeCheckboxSelected: "assets/home-checkbox-select.svg",
      homeCheckboxUnselected: "assets/home-checkbox-unselect.svg",
      homeTabTicketGrabbing: "assets/home-tab-ticket-grabbing.svg",
      homeTabChangeSeat: "assets/home-tab-change-seat.svg",
      homeTabOrder: "assets/home-tab-order.svg",
      homeTabPersonal: "assets/home-tab-personal.svg"
    }
  };

  const LOCKED_SEARCH_CHECK_LABELS = ["学生票", "高铁动车"];

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

  function normalizeLockedSearchChecks(checks) {
    const source = Array.isArray(checks) ? checks : [];
    const locked = LOCKED_SEARCH_CHECK_LABELS.map((label, index) => {
      const baseItem = DEFAULT_DATA.search.checks[index] || {};
      const incomingItem = isObject(source[index]) ? source[index] : {};
      return {
        ...baseItem,
        ...incomingItem,
        label,
        checked: incomingItem.checked === true,
        uncheckedAsset: incomingItem.uncheckedAsset || baseItem.uncheckedAsset || "homeCheckboxUnselected",
        checkedAsset: incomingItem.checkedAsset || baseItem.checkedAsset || "homeCheckboxSelected"
      };
    });
    const extras = source
      .slice(LOCKED_SEARCH_CHECK_LABELS.length)
      .filter((item) => isObject(item))
      .map((item) => ({ ...item }));
    return locked.concat(extras);
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

  function renderTraffic(data) {
    const traffic = data.traffic || {};
    const assets = data.assets || {};
    const primary = (traffic.primaryTabs || []).map((item) => {
      const classes = ["traffic-item"];
      if (item.active) classes.push("on");
      return '<div class="' + classes.join(" ") + '">' + escapeHtml(item.label) + "</div>";
    }).join("");
    const regions = (traffic.regions || []).map((item) => {
      return "<span" + (item.active ? ' class="on"' : "") + ">" + escapeHtml(item.label) + "</span>";
    }).join("");
    const tripTypes = (traffic.tripTypes || []).map((item) => {
      return "<span" + (item.active ? ' class="on"' : "") + ">" + escapeHtml(item.label) + "</span>";
    }).join("");
    const mini = traffic.mini || {};
    const miniAsset = resolveAsset(assets, mini.asset);

    return '' +
      '<div class="home-traffic">' +
        '<div class="traffic-row">' +
          '<div class="traffic-mini">' +
            assetIcon(miniAsset, 14, 14) +
            '<span class="traffic-mini-label">' + escapeHtml(mini.label || "") + "</span>" +
          "</div>" +
          primary +
        "</div>" +
        '<div class="region-row">' + regions + "</div>" +
        '<div class="trip-row">' + tripTypes + "</div>" +
      "</div>";
  }

  function renderChecks(search, assets) {
    const checks = normalizeLockedSearchChecks(search.checks);
    return '<div class="search-checks">' +
      checks.map((item) => {
        const isChecked = item.checked === true;
        const iconSrc = resolveAsset(
          assets,
          isChecked ? (item.checkedAsset || "homeCheckboxSelected") : (item.uncheckedAsset || "homeCheckboxUnselected")
        );
        return '<span class="circle-check">' +
          assetIcon(iconSrc, 13, 13) +
          "<span>" + escapeHtml(item.label) + "</span>" +
        "</span>";
      }).join("") +
    "</div>";
  }

  function renderHistory(search) {
    const entries = (search.history || []).map((item) => "<span>" + escapeHtml(item) + "</span>").join("");
    return '<div class="history-row">' + entries + "<span>" + escapeHtml(search.historyClearLabel || "") + "</span></div>";
  }

  function normalizeBenefitTag(tag) {
    if (!tag) {
      return null;
    }
    if (typeof tag === "string") {
      return { label: tag };
    }
    return isObject(tag) ? tag : null;
  }

  function renderBenefitTag(search) {
    const tag = normalizeBenefitTag(search.benefitTag);
    if (!tag || !tag.label) {
      return "";
    }
    const classes = ["search-benefit-tag"];
    if (tag.tone) {
      classes.push(tag.tone);
    }
    return '<span class="' + classes.map(escapeHtml).join(" ") + '">' + escapeHtml(tag.label) + "</span>";
  }

  function renderSearch(data) {
    const search = data.search || {};
    const assets = data.assets || {};
    const toggleAsset = resolveAsset(assets, search.toggleAsset || "homeCheckboxUnselected");
    const stateTone = search.stateTone || "ok";
    const switchAsset = resolveAsset(assets, search.switchAsset || "homeSwitch");
    const queryAction = search.queryAction;
    const hasBenefitTag = Boolean(renderBenefitTag(search));

    return '' +
      '<div class="search-form' + (hasBenefitTag ? " has-benefit-tag" : "") + '">' +
        renderBenefitTag(search) +
        '<div class="od-row">' +
          '<div class="city-name">' + escapeHtml(search.from || "") + "</div>" +
          '<button class="swap-btn" type="button">' + assetIcon(switchAsset, 30, 30) + "</button>" +
          '<div class="city-name right">' + escapeHtml(search.to || "") + "</div>" +
        "</div>" +
        '<div class="search-divider"></div>' +
        '<div class="search-meta">' +
          '<div class="search-date"><strong>' + escapeHtml(search.dateValue || "") + "</strong><span>" + escapeHtml(search.dateLabel || "") + "</span></div>" +
          renderChecks(search, assets) +
        "</div>" +
        '<div class="search-state">' +
          '<strong class="' + escapeHtml(stateTone) + '">' + escapeHtml(search.stateLabel || "") + "</strong>" +
          '<span class="toggle-line">' + assetIcon(toggleAsset, 13, 13) + escapeHtml(search.toggleLabel || "") + "</span>" +
        "</div>" +
        '<button class="query-btn' + (queryAction ? " is-clickable" : "") + '" type="button"' + renderActionAttr(queryAction) + '>' + escapeHtml(search.queryLabel || "查询") + "</button>" +
        renderHistory(search) +
      "</div>";
  }

  function renderHeader(data) {
    const hero = data.hero || {};
    const assets = data.assets || {};
    const heroAsset = resolveAsset(assets, hero.backAsset);
    return '' +
      '<div class="home-top">' +
        renderStatusBar(data) +
        (heroAsset
          ? '<div class="hero-back" style="margin-bottom:12px;">' + assetIcon(heroAsset, hero.backWidth || 32, hero.backHeight || 32) + "</div>"
          : "") +
        '<div class="home-search-shell">' +
          '<div class="search-card">' +
            renderTraffic(data) +
            renderSearch(data) +
          "</div>" +
        "</div>" +
      "</div>";
  }

  function renderSectionHeader(title, minorMarkup) {
    return '' +
      '<div class="section-title">' +
        "<span>" + escapeHtml(title || "") + "</span>" +
        '<span class="minor">' + (minorMarkup || "") + "</span>" +
      "</div>";
  }

  function renderQuickBooking(section, data) {
    const sectionData = section.data || {};
    const assets = data.assets || {};
    const journey = sectionData.journey || {};
    const settings = (sectionData.settings || []).map((item) => {
      const iconMarkup = item.iconAsset
        ? assetIcon(resolveAsset(assets, item.iconAsset), 18, 18)
        : inlineIcon(item.icon || "seat");
      const chevron = resolveAsset(assets, item.chevronAsset || "homeArrowSmall");
      return '' +
        '<div class="setting-row' + (item.action ? " is-clickable" : "") + '"' + renderActionAttr(item.action) + '>' +
          iconMarkup +
          '<div class="setting-copy"><strong>' + escapeHtml(item.title || "") + "</strong><span>" + escapeHtml(item.value || "") + "</span></div>" +
          '<span class="setting-arrow">' + assetIcon(chevron, 9, 9) + "</span>" +
        "</div>";
    }).join("");

    return '' +
      renderSectionHeader(section.title, escapeHtml(section.minor || "")) +
      '<div class="quick-card">' +
        '<div class="quick-top">' +
          "<div>" +
            '<div class="quick-kicker">' + escapeHtml(sectionData.kicker || "") + "</div>" +
            '<div class="quick-train"><strong>' + escapeHtml(sectionData.trainNo || "") + '</strong><span class="status-pill ' + escapeHtml(sectionData.statusTone || "ok") + '">' + escapeHtml(sectionData.statusLabel || "") + "</span></div>" +
            "<p>" + escapeHtml(sectionData.copy || "") + "</p>" +
          "</div>" +
          '<div class="quick-price"><small>' + escapeHtml(sectionData.priceLabel || "") + "</small><strong>¥" + escapeHtml(sectionData.price || "") + "</strong></div>" +
        "</div>" +
        '<div class="quick-journey">' +
          '<div class="journey-col"><strong>' + escapeHtml(journey.depTime || "") + "</strong><span>" + escapeHtml(journey.depStation || "") + "</span></div>" +
          '<div class="journey-axis"><span>' + escapeHtml(journey.duration || "") + '</span><div class="line"></div><span>' + escapeHtml(journey.meta || "") + "</span></div>" +
          '<div class="journey-col right"><strong>' + escapeHtml(journey.arrTime || "") + "</strong><span>" + escapeHtml(journey.arrStation || "") + "</span></div>" +
        "</div>" +
        '<div class="quick-setting-list">' + settings + "</div>" +
        '<button class="quick-cta ' + escapeHtml(sectionData.ctaClass || "") + (sectionData.ctaAction ? " is-clickable" : "") + '" type="button"' + renderActionAttr(sectionData.ctaAction) + '>' + escapeHtml(sectionData.ctaLabel || "") + "</button>" +
        '<div class="quick-hint">' + escapeHtml(sectionData.hint || "") + "</div>" +
      "</div>";
  }

  function renderToolbox(section, data) {
    const sectionData = section.data || {};
    const assets = data.assets || {};
    const minorParts = [];
    if (section.minor) {
      minorParts.push(escapeHtml(section.minor));
    }
    const chevron = resolveAsset(assets, sectionData.minorChevronAsset || "homeArrowSmall");
    if (chevron) {
      minorParts.push(assetIcon(chevron, 9, 9));
    }
    const cards = (sectionData.cards || []).map((item) => {
      return '' +
        '<div class="tool-item">' +
          '<strong>' + escapeHtml(item.title || "") + "</strong>" +
          "<span>" + escapeHtml(item.copy || "") + "</span>" +
          (item.tag ? '<span class="tool-tag">' + escapeHtml(item.tag) + "</span>" : "") +
        "</div>";
    }).join("");
    const links = (sectionData.links || []).map((item) => "<span>" + escapeHtml(item) + "</span>").join("");

    return '' +
      renderSectionHeader(section.title, minorParts.join("")) +
      '<div class="toolbox-card">' +
        '<div class="tool-grid">' + cards + "</div>" +
        '<div class="tool-links">' + links + "</div>" +
      "</div>";
  }

  function renderGenericSection(section) {
    if (section.html) {
      return section.html;
    }
    const sectionData = section.data || {};
    const list = (sectionData.items || []).map((item) => {
      return '<div class="generic-list-item">' + escapeHtml(item) + "</div>";
    }).join("");
    return '' +
      renderSectionHeader(section.title, escapeHtml(section.minor || "")) +
      '<div class="generic-card">' +
        (sectionData.copy ? '<div class="generic-copy">' + escapeHtml(sectionData.copy) + "</div>" : "") +
        (list ? '<div class="generic-list">' + list + "</div>" : "") +
      "</div>";
  }

  function renderBodySection(section, index, total, data) {
    const classes = ["section", "home-section"];
    if (section.type === "quick-booking") {
      classes.push("quick-section");
    }
    if (index === total - 1) {
      classes.push("trailing");
    }

    let content = "";
    if (section.type === "quick-booking") {
      content = renderQuickBooking(section, data);
    } else if (section.type === "toolbox") {
      content = renderToolbox(section, data);
    } else {
      content = renderGenericSection(section, data);
    }

    return '<section class="' + classes.join(" ") + '">' + content + "</section>";
  }

  function renderBottomTabs(data) {
    const assets = data.assets || {};
    return '' +
      '<div class="home-tabbar">' +
        (data.bottomTabs || []).map((item) => {
          const classes = ["item"];
          if (item.active) classes.push("active");
          if (item.action) classes.push("is-clickable");
          return '<div class="' + classes.join(" ") + '"' + renderActionAttr(item.action) + '>' +
            assetIcon(resolveAsset(assets, item.asset), item.iconWidth || 24, item.iconHeight || 24) +
            "<span>" + escapeHtml(item.label || "") + "</span>" +
          "</div>";
        }).join("") +
      "</div>";
  }

  function renderFloatingSheet(data) {
    const sheet = data.floatingSheet;
    if (!sheet || sheet.show === false) {
      return "";
    }
    const dates = (sheet.dates || []).map((item) => {
      const classes = ["home-sheet-date"];
      if (item.active) classes.push("active");
      if (item.action) classes.push("is-clickable");
      return '<button class="' + classes.join(" ") + '" type="button"' + renderActionAttr(item.action) + '><span>' + escapeHtml(item.week || "") + "</span><strong>" + escapeHtml(item.date || "") + "</strong></button>";
    }).join("");
    const trip = sheet.trip || {};
    const settings = (sheet.settings || []).map((item) => {
      return '<div class="home-sheet-info-row"><span>' + escapeHtml(item.label || "") + "</span><strong>" + escapeHtml(item.value || "") + "</strong></div>";
    }).join("");

    return '' +
      '<div class="home-sheet-backdrop' + (sheet.dismissAction ? " is-clickable" : "") + '"' + renderActionAttr(sheet.dismissAction) + '></div>' +
      '<div class="home-sheet">' +
        '<div class="home-sheet-handle"></div>' +
        '<div class="home-sheet-head"><div><strong>' + escapeHtml(sheet.title || "") + "</strong><span>" + escapeHtml(sheet.subtitle || "") + "</span></div></div>" +
        '<div class="home-sheet-dates">' + dates + "</div>" +
        '<div class="home-sheet-trip">' +
          '<div class="home-sheet-trip-row"><strong>' + escapeHtml(trip.trainNo || "") + "</strong><span>" + escapeHtml(trip.seat || "") + "</span></div>" +
          '<div class="home-sheet-route">' +
            '<div class="home-sheet-station"><strong>' + escapeHtml(trip.fromTime || "") + "</strong><span>" + escapeHtml(trip.fromStation || "") + "</span></div>" +
            '<div class="home-sheet-axis"><span>' + escapeHtml(trip.duration || "") + '</span><div class="home-sheet-axis-line"></div></div>' +
            '<div class="home-sheet-station right"><strong>' + escapeHtml(trip.toTime || "") + "</strong><span>" + escapeHtml(trip.toStation || "") + "</span></div>" +
          "</div>" +
        "</div>" +
        '<div class="home-sheet-info">' + settings + "</div>" +
        '<button class="home-sheet-cta' + (sheet.ctaAction ? " is-clickable" : "") + '" type="button"' + renderActionAttr(sheet.ctaAction) + '>' + escapeHtml(sheet.cta || "") + "</button>" +
      '</div>';
  }

  function renderPage(data) {
    const sections = (data.bodySections || []).map((section, index, list) => {
      return renderBodySection(section, index, list.length, data);
    }).join("");

    return '' +
      '<div class="home-template-phone">' +
        '<div class="home-template-scroll">' +
          '<div class="home-screen">' +
            renderHeader(data) +
            sections +
            renderBottomTabs(data) +
            renderFloatingSheet(data) +
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
    if (!raw || raw === "__HOME_TEMPLATE_DATA__") {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.warn("[home-template] failed to parse data payload:", error);
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

  window.HomePageTemplate = api;
})();
