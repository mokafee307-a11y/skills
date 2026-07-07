(function () {
  const PHONE_DEVICE_WIDTH = 381;
  const PHONE_DEVICE_HEIGHT = 818;
  const DEFAULT_DATA = {
    meta: {
      pageTitle: "火车票交互预览",
      previewHeaderTitle: "页面预览",
      docHeaderTitle: "交互说明",
      previewActions: [],
      docActions: [
        { id: "copy-doc", label: "复制说明" },
        { id: "toggle-edit", label: "修改" },
        { id: "export-pdf", label: "导出 PDF", tone: "primary" },
        { id: "share-package", label: "分享", tone: "primary" }
      ],
      toastText: "已复制"
    },
    preview: {
      frames: []
    },
    doc: {
      sections: []
    }
  };

  const uiState = {
    frameId: null,
    stateId: null
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

  function ensureArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function encodeDemoAction(action) {
    if (!isObject(action)) {
      return "";
    }
    try {
      return JSON.stringify(action);
    } catch (error) {
      return "";
    }
  }

  function renderDemoActionAttr(action) {
    const payload = encodeDemoAction(action);
    if (!payload) {
      return "";
    }
    return ' data-demo-action="' + escapeHtml(payload) + '"';
  }

  function renderClickClass(action) {
    return isObject(action) ? " is-clickable" : "";
  }

  function resolvePhoneTemplate(phone) {
    return phone && isObject(phone.template) ? phone.template : null;
  }

  function resolveTemplateRenderer(kind) {
    if (typeof window === "undefined" || !kind) {
      return null;
    }
    const registry = {
      home: window.HomePageTemplate,
      list: window.ListPageTemplate,
      middle: window.MiddlePageTemplate,
      fill: window.FillPageTemplate,
      occupy: window.OccupyPageTemplate
    };
    return registry[kind] || null;
  }

  function findActiveFrame(frames, frameId) {
    return ensureArray(frames).find((item) => item.id === frameId)
      || ensureArray(frames).find((item) => item.active)
      || ensureArray(frames)[0]
      || null;
  }

  function findActivePhoneState(frame, stateId) {
    const items = ensureArray(frame && frame.stateRail && frame.stateRail.items);
    return items.find((item) => item.id === stateId)
      || items.find((item) => item.active)
      || items[0]
      || null;
  }

  function renderActionButtons(actions, scope) {
    return ensureArray(actions).map((action) => {
      const classes = ["btn"];
      if (action.tone === "primary") classes.push("primary");
      return '<button class="' + classes.join(" ") + '" data-action-scope="' + escapeHtml(scope) + '" data-action-id="' + escapeHtml(action.id || "") + '">' + escapeHtml(action.label || "") + "</button>";
    }).join("");
  }

  function renderShell(data) {
    return '' +
      '<main class="app-shell">' +
        '<section class="panel preview-panel">' +
          '<header class="panel-header">' +
            "<h1>" + escapeHtml(data.meta.previewHeaderTitle || "") + "</h1>" +
            '<div class="toolbar">' + renderActionButtons(data.meta.previewActions, "preview") + "</div>" +
          "</header>" +
          '<div class="preview-stack">' +
            '<div id="interaction-preview-region"></div>' +
          "</div>" +
        "</section>" +
        '<section class="panel doc-panel">' +
          '<header class="doc-header">' +
            "<h1>" + escapeHtml(data.meta.docHeaderTitle || "") + "</h1>" +
            '<div class="toolbar">' + renderActionButtons(data.meta.docActions, "doc") + "</div>" +
          "</header>" +
          '<div class="doc-scroll">' +
            '<article class="doc-content" id="docContent">' + renderDocSections(data.doc.sections) + "</article>" +
          "</div>" +
        "</section>" +
      "</main>" +
      '<div class="toast" id="toast">' + escapeHtml(data.meta.toastText || "已复制") + "</div>";
  }

  function renderPreviewRegion(data, frame, phoneState) {
    return '' +
      '<nav class="tabs" aria-label="页面切换">' + renderTabs(data.preview.frames, frame && frame.id) + "</nav>" +
      '<div class="phone-stage" id="phoneStage">' +
        renderStateRail(frame, phoneState) +
        '<div class="phone-slot" id="phoneSlot">' +
          '<div class="phone-fit" id="phoneFit">' +
            '<div class="phone" id="phone">' +
              '<div class="phone-viewport">' +
                '<div class="phone-screen">' + renderPhone(phoneState && phoneState.phone) + "</div>" +
              "</div>" +
            "</div>" +
          "</div>" +
        "</div>" +
      "</div>";
  }

  function renderTabs(frames, activeFrameId) {
    return ensureArray(frames).map((frame) => {
      const classes = ["tab"];
      if (frame.id === activeFrameId) classes.push("active");
      return '<button class="' + classes.join(" ") + '" data-frame-id="' + escapeHtml(frame.id || "") + '">' + escapeHtml(frame.label || "") + "</button>";
    }).join("");
  }

  function renderStateRail(frame, activeState) {
    const title = frame && frame.stateRail && frame.stateRail.title ? frame.stateRail.title : "状态切换";
    const items = ensureArray(frame && frame.stateRail && frame.stateRail.items).map((item) => {
      const classes = [];
      if (activeState && item.id === activeState.id) classes.push("active");
      return '<button class="' + classes.join(" ") + '" data-state-id="' + escapeHtml(item.id || "") + '">' + escapeHtml(item.label || "") + "</button>";
    }).join("");

    return '' +
      '<aside class="state-rail" aria-label="同页面状态切换">' +
        '<div class="state-rail-title">' + escapeHtml(title) + "</div>" +
        items +
      "</aside>";
  }

  function renderPhone(phone) {
    const template = resolvePhoneTemplate(phone);
    if (template) {
      return '<div class="phone-template-root" data-phone-template-kind="' + escapeHtml(template.kind || "") + '"></div>';
    }
    const data = phone || {};
    const statusBar = data.statusBar || {};
    const appTitleRow = data.appTitleRow || {};
    const bottomNav = ensureArray(data.bottomNav);
    return '' +
      '<div class="phone-content">' +
        '<div class="status"><span>' + escapeHtml(statusBar.left || "") + '</span><span>' + escapeHtml(statusBar.right || "") + "</span></div>" +
        '<div class="app-body">' +
          renderAppTitleRow(appTitleRow) +
          renderPhoneBlocks(data.blocks) +
        "</div>" +
        renderBottomNav(bottomNav) +
      "</div>";
  }

  function renderAppTitleRow(appTitleRow) {
    if (!appTitleRow || !appTitleRow.title) {
      return "";
    }
    const msgClasses = ["msg"];
    if (!appTitleRow.showAlertDot) msgClasses.push("no-dot");
    return '' +
      '<div class="app-title-row">' +
        '<div class="app-title">' + escapeHtml(appTitleRow.title) + "</div>" +
        '<div class="' + msgClasses.join(" ") + renderClickClass(appTitleRow.action) + '"' + renderDemoActionAttr(appTitleRow.action) + '>' + escapeHtml(appTitleRow.messageGlyph || "▢") + "</div>" +
      "</div>";
  }

  function renderPhoneBlocks(blocks) {
    return ensureArray(blocks).map((block) => renderPhoneBlock(block)).join("");
  }

  function renderPhoneBlock(block) {
    if (!block || !block.type) {
      return "";
    }
    if (block.type === "commute-card") {
      return renderCommuteCard(block.data || {});
    }
    if (block.type === "icon-grid-section") {
      return renderIconGridSection(block.data || {});
    }
    if (block.type === "card-grid-section") {
      return renderCardGridSection(block.data || {});
    }
    if (block.type === "text-card-section") {
      return renderTextCardSection(block.data || {});
    }
    return "";
  }

  function mountPhoneTemplate(root, phone) {
    const template = resolvePhoneTemplate(phone);
    if (!template) {
      return;
    }
    const host = root.querySelector(".phone-template-root");
    if (!host) {
      return;
    }
    const renderer = resolveTemplateRenderer(template.kind);
    if (!renderer || typeof renderer.render !== "function") {
      host.innerHTML = '<div class="phone-template-missing">未加载 ' + escapeHtml(template.kind || "unknown") + " 页面模板</div>";
      return;
    }
    renderer.render(host, template.data || {});
    host.setAttribute("data-phone-template-mounted", template.kind || "");
  }

  function renderCommuteCard(data) {
    const metaRow = ensureArray(data.metaRow);
    const infoItems = ensureArray(data.infoItems);
    return '' +
      '<section class="commute-card' + renderClickClass(data.action) + '"' + renderDemoActionAttr(data.action) + '>' +
        '<div class="commute-head">' +
          '<div><strong>' + escapeHtml(data.headerTitle || "") + "</strong><span>" + escapeHtml(data.headerSubtitle || "") + "</span></div>" +
          '<div class="saved">' + escapeHtml(data.savedLabel || "") + "</div>" +
        "</div>" +
        '<div class="route-card">' +
          '<div class="route">' +
            '<div class="city">' + escapeHtml(data.from || "") + "</div>" +
            '<div class="rail">' + escapeHtml(data.centerLabel || "rail") + "</div>" +
            '<div class="city right">' + escapeHtml(data.to || "") + "</div>" +
          "</div>" +
          '<div class="meta-row">' +
            "<span>" + escapeHtml(metaRow[0] || "") + "</span>" +
            "<span>" + escapeHtml(metaRow[1] || "") + "</span>" +
            "<span>" + escapeHtml(metaRow[2] || "") + "</span>" +
          "</div>" +
          '<div class="info-grid">' +
            infoItems.map((item) => {
              return '<div class="info"><label>' + escapeHtml(item.label || "") + "</label><strong>" + escapeHtml(item.value || "") + "</strong></div>";
            }).join("") +
          "</div>" +
          '<button class="primary-cta' + renderClickClass(data.primaryCtaAction) + '" type="button"' + renderDemoActionAttr(data.primaryCtaAction) + '>' + escapeHtml(data.primaryCta || "") + "</button>" +
        "</div>" +
      "</section>";
  }

  function renderIconGridSection(data) {
    return '' +
      '<h2 class="section-title">' + escapeHtml(data.title || "") + "</h2>" +
      '<section class="quick-grid">' +
        ensureArray(data.items).map((item) => {
          return '<div class="quick' + renderClickClass(item.action) + '"' + renderDemoActionAttr(item.action) + '><i>' + escapeHtml(item.icon || "") + "</i>" + escapeHtml(item.label || "") + "</div>";
        }).join("") +
      "</section>";
  }

  function renderCardGridSection(data) {
    return '' +
      '<h2 class="section-title">' + escapeHtml(data.title || "") + "</h2>" +
      '<section class="recommend">' +
        ensureArray(data.items).map((item) => {
          return '<div class="rec' + renderClickClass(item.action) + '"' + renderDemoActionAttr(item.action) + '><strong>' + escapeHtml(item.title || "") + "</strong><span>" + escapeHtml(item.copy || "") + "</span></div>";
        }).join("") +
      "</section>";
  }

  function renderTextCardSection(data) {
    return '' +
      '<h2 class="section-title">' + escapeHtml(data.title || "") + "</h2>" +
      '<section class="text-card-list">' +
        ensureArray(data.items).map((item) => {
          return '<div class="text-card' + renderClickClass(item.action) + '"' + renderDemoActionAttr(item.action) + '><strong>' + escapeHtml(item.title || "") + "</strong><span>" + escapeHtml(item.copy || "") + "</span></div>";
        }).join("") +
      "</section>";
  }

  function renderBottomNav(items) {
    return '' +
      '<nav class="bottom-nav">' +
        ensureArray(items).map((item) => {
          const classes = ["nav-item"];
          if (item.active) classes.push("active");
          if (isObject(item.action)) classes.push("is-clickable");
          return '<div class="' + classes.join(" ") + '"' + renderDemoActionAttr(item.action) + '>' + (item.showDot === false ? "" : "<b></b>") + escapeHtml(item.label || "") + "</div>";
        }).join("") +
      "</nav>";
  }

  function parseDemoAction(node) {
    if (!node) {
      return null;
    }
    const raw = node.getAttribute("data-demo-action");
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (error) {
      return null;
    }
  }

  function renderDocSections(sections) {
    return ensureArray(sections).map((section) => {
      const variantClass = section.variant ? " " + escapeHtml(section.variant) : "";
      return '' +
        '<section class="doc-section">' +
          '<div class="section-head">' +
            '<div class="section-icon">' + escapeHtml(section.index || "") + "</div>" +
            "<h2>" + escapeHtml(section.title || "") + "</h2>" +
          "</div>" +
          renderDocSectionBody(section, variantClass) +
        "</section>";
    }).join("");
  }

  function renderDocSectionBody(section, variantClass) {
    if (section.type === "decision") {
      return '<div class="decision">' +
        ensureArray(section.items).map((item) => {
          return '' +
            '<div class="decision-item">' +
              '<div class="decision-mark">' + escapeHtml(item.mark || "") + "</div>" +
              "<div><h3>" + escapeHtml(item.title || "") + "</h3><p>" + escapeHtml(item.body || "") + "</p></div>" +
            "</div>";
        }).join("") +
      "</div>";
    }
    if (section.type === "flow") {
      return '<div class="flow' + variantClass + '">' +
        ensureArray(section.items).map((item) => {
          return '' +
            '<div class="step">' +
              '<div class="num">' + escapeHtml(item.num || "") + "</div>" +
              "<div><h3>" + escapeHtml(item.title || "") + "</h3><p>" + escapeHtml(item.body || "") + "</p></div>" +
            "</div>";
        }).join("") +
      "</div>";
    }
    if (section.type === "state-grid") {
      return '<div class="state-grid' + variantClass + '">' +
        ensureArray(section.items).map((item) => {
          const dot = item.color ? '<span class="color-dot ' + escapeHtml(item.color) + '"></span>' : "";
          return '' +
            '<div class="state">' +
              '<div class="state-title">' + dot + escapeHtml(item.title || "") + "</div>" +
              "<p>" + escapeHtml(item.body || "") + "</p>" +
            "</div>";
        }).join("") +
      "</div>";
    }
    return "";
  }

  function fitPhone(root) {
    const phoneSlot = root.querySelector("#phoneSlot");
    if (!phoneSlot) return;
    const availableH = phoneSlot.clientHeight - 4;
    const availableW = phoneSlot.clientWidth - 4;
    if (availableH <= 0 || availableW <= 0) return;
    const rawScale = Math.min(1, availableH / PHONE_DEVICE_HEIGHT, availableW / PHONE_DEVICE_WIDTH);
    const safeScale = Number.isFinite(rawScale) && rawScale > 0 ? rawScale : 1;
    root.style.setProperty("--phone-scale", safeScale.toFixed(3));
  }

  function scheduleFit(root) {
    if (!root || typeof window === "undefined") {
      return;
    }
    if (root._interactionDemoFitRaf) {
      window.cancelAnimationFrame(root._interactionDemoFitRaf);
    }
    root._interactionDemoFitRaf = window.requestAnimationFrame(() => {
      fitPhone(root);
      root._interactionDemoFitRaf = null;
    });
  }

  function fitAll() {
    const roots = document.querySelectorAll('[data-interaction-demo-root="true"]');
    roots.forEach((root) => scheduleFit(root));
  }

  function showToast(root, text) {
    const toast = root.querySelector("#toast");
    if (!toast) return;
    toast.textContent = text;
    toast.classList.add("show");
    window.clearTimeout(showToast._timer);
    showToast._timer = window.setTimeout(() => {
      toast.classList.remove("show");
    }, 1600);
  }

  async function copyDoc(root) {
    const doc = root.querySelector("#docContent");
    if (!doc) return;
    const text = doc.innerText.trim();
    try {
      await navigator.clipboard.writeText(text);
      showToast(root, "说明文本已复制");
    } catch (error) {
      const range = document.createRange();
      range.selectNodeContents(doc);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      document.execCommand("copy");
      selection.removeAllRanges();
      showToast(root, "说明文本已复制");
    }
  }

  function sanitizePdfText(text) {
    return String(text || "")
      .replace(/[·•▲]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function cjkHex(text) {
    const bytes = [];
    Array.from(sanitizePdfText(text)).forEach((char) => {
      let code = char.codePointAt(0);
      if (code > 0xffff) {
        code = 0x25a1;
      }
      bytes.push(((code >> 8) & 0xff).toString(16).padStart(2, "0"));
      bytes.push((code & 0xff).toString(16).padStart(2, "0"));
    });
    return bytes.join("").toUpperCase();
  }

  function pdfAscii(text) {
    return String(text || "")
      .replace(/\\/g, "\\\\")
      .replace(/\(/g, "\\(")
      .replace(/\)/g, "\\)");
  }

  function textUnits(text) {
    return Array.from(String(text || "")).reduce((sum, char) => {
      return sum + (/[\x00-\x7F]/.test(char) ? 0.58 : 1);
    }, 0);
  }

  function wrapPdfText(text, maxUnits) {
    const source = Array.from(sanitizePdfText(text));
    const lines = [];
    let current = "";
    source.forEach((char) => {
      if (current && textUnits(current + char) > maxUnits) {
        lines.push(current);
        current = "";
      }
      current += char;
    });
    if (current) lines.push(current);
    return lines;
  }

  function collectPdfSections(root) {
    const doc = root.querySelector("#docContent");
    const sections = [];
    if (!doc) {
      return { title: document.title || "交互说明", sections };
    }
    doc.querySelectorAll(".doc-section").forEach((section) => {
      const index = section.querySelector(".section-icon")?.textContent?.trim() || "";
      const title = section.querySelector(".section-head h2")?.textContent?.trim() || "";
      const items = [];
      const stepNodes = section.querySelectorAll(".step");
      const stateNodes = section.querySelectorAll(".state");
      const decisionNodes = section.querySelectorAll(".decision-item");
      const sourceNodes = stepNodes.length ? stepNodes : (stateNodes.length ? stateNodes : decisionNodes);
      sourceNodes.forEach((node) => {
        const prefix = node.querySelector(".num, .decision-mark")?.textContent?.trim() || "";
        const itemTitle = node.querySelector("h3, .state-title")?.textContent?.trim() || "";
        const body = node.querySelector("p")?.textContent?.trim() || "";
        items.push({ prefix, title: itemTitle, body });
      });
      sections.push({ index, title, items });
    });
    return { title: document.title || "交互说明", sections };
  }

  function buildPdf(model) {
    const pageWidth = 595;
    const pageHeight = 842;
    const marginX = 48;
    const marginTop = 54;
    const marginBottom = 48;
    const contentWidth = pageWidth - marginX * 2;
    const pages = [];
    let ops = [];
    let y = pageHeight - marginTop;

    function newPage() {
      if (ops.length) {
        pages.push(ops);
      }
      ops = [];
      y = pageHeight - marginTop;
    }

    function ensureSpace(height) {
      if (y - height < marginBottom) {
        newPage();
      }
    }

    function rect(x, bottom, width, height, gray) {
      ops.push(gray + " g " + x + " " + bottom + " " + width + " " + height + " re f");
    }

    function textCjk(text, size, x, baseline, gray) {
      ops.push((gray || "0") + " g BT /F1 " + size + " Tf 1 0 0 1 " + x + " " + baseline + " Tm <" + cjkHex(text) + "> Tj ET");
    }

    function textAscii(text, size, x, baseline, gray) {
      ops.push((gray || "0") + " g BT /F2 " + size + " Tf 1 0 0 1 " + x + " " + baseline + " Tm (" + pdfAscii(text) + ") Tj ET");
    }

    textCjk(sanitizePdfText(model.title).replace("交互预览", "交互说明"), 18, marginX, y, "0");
    y -= 34;

    model.sections.forEach((section) => {
      ensureSpace(58);
      rect(marginX, y - 34, contentWidth, 34, "0.94");
      textAscii(section.index, 13, marginX + 16, y - 22, "0");
      textCjk(section.title, 14, marginX + 54, y - 22, "0");
      y -= 48;

      section.items.forEach((item) => {
        const titleText = [item.prefix || "", item.title].filter(Boolean).join("  ");
        const titleLines = wrapPdfText(titleText, 35);
        const bodyLines = wrapPdfText(item.body, 42);
        const cardHeight = 18 + titleLines.length * 15 + bodyLines.length * 14 + 14;
        ensureSpace(cardHeight + 10);
        rect(marginX, y - cardHeight, contentWidth, cardHeight, "0.985");
        let lineY = y - 23;
        titleLines.forEach((line) => {
          textCjk(line, 11, marginX + 16, lineY, "0");
          lineY -= 15;
        });
        bodyLines.forEach((line) => {
          textCjk(line, 10, marginX + 16, lineY, "0.28");
          lineY -= 14;
        });
        y -= cardHeight + 10;
      });

      y -= 6;
    });

    newPage();
    const objects = [];
    const addObject = (body) => {
      objects.push(body);
      return objects.length;
    };

    addObject("");
    addObject("");
    const fontDescriptorId = addObject("<< /Type /FontDescriptor /FontName /STSong-Light /Flags 6 /FontBBox [0 -200 1000 900] /ItalicAngle 0 /Ascent 880 /Descent -120 /CapHeight 880 /StemV 80 >>");
    const cidFontId = addObject("<< /Type /Font /Subtype /CIDFontType0 /BaseFont /STSong-Light /CIDSystemInfo << /Registry (Adobe) /Ordering (GB1) /Supplement 5 >> /FontDescriptor " + fontDescriptorId + " 0 R /DW 1000 >>");
    const cjkFontId = addObject("<< /Type /Font /Subtype /Type0 /BaseFont /STSong-Light /Encoding /UniGB-UCS2-H /DescendantFonts [" + cidFontId + " 0 R] >>");
    const asciiFontId = addObject("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
    const pageIds = [];

    pages.forEach((pageOps, index) => {
      const footer = "0.55 g BT /F2 9 Tf 1 0 0 1 " + (pageWidth - marginX - 18) + " 28 Tm (" + (index + 1) + ") Tj ET";
      const content = pageOps.concat(footer).join("\n");
      const contentId = addObject("<< /Length " + content.length + " >>\nstream\n" + content + "\nendstream");
      const pageId = addObject("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 " + pageWidth + " " + pageHeight + "] /Resources << /Font << /F1 " + cjkFontId + " 0 R /F2 " + asciiFontId + " 0 R >> >> /Contents " + contentId + " 0 R >>");
      pageIds.push(pageId);
    });

    objects[0] = "<< /Type /Catalog /Pages 2 0 R >>";
    objects[1] = "<< /Type /Pages /Kids [" + pageIds.map((id) => id + " 0 R").join(" ") + "] /Count " + pageIds.length + " >>";

    let pdf = "%PDF-1.4\n";
    const offsets = [0];
    objects.forEach((body, index) => {
      offsets.push(pdf.length);
      pdf += (index + 1) + " 0 obj\n" + body + "\nendobj\n";
    });
    const xrefOffset = pdf.length;
    pdf += "xref\n0 " + (objects.length + 1) + "\n";
    pdf += "0000000000 65535 f \n";
    for (let i = 1; i <= objects.length; i += 1) {
      pdf += String(offsets[i]).padStart(10, "0") + " 00000 n \n";
    }
    pdf += "trailer\n<< /Size " + (objects.length + 1) + " /Root 1 0 R >>\nstartxref\n" + xrefOffset + "\n%%EOF";
    return new Blob([pdf], { type: "application/pdf" });
  }

  function downloadPdf(root) {
    const model = collectPdfSections(root);
    const blob = buildPdf(model);
    const url = URL.createObjectURL(blob);
    const filename = ((document.title || "interaction-demo").replace(/[\\/:*?"<>|]+/g, "-") || "interaction-demo") + ".pdf";
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1200);
    showToast(root, "PDF已下载到浏览器默认路径");
  }

  function textBytes(text) {
    return new TextEncoder().encode(String(text || ""));
  }

  function dosDateTime(date) {
    const year = Math.max(1980, date.getFullYear());
    const dosTime = (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
    const dosDate = ((year - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate();
    return { dosTime, dosDate };
  }

  const crcTable = (() => {
    const table = new Uint32Array(256);
    for (let n = 0; n < 256; n += 1) {
      let c = n;
      for (let k = 0; k < 8; k += 1) {
        c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      }
      table[n] = c >>> 0;
    }
    return table;
  })();

  function crc32(bytes) {
    let c = 0xffffffff;
    for (let i = 0; i < bytes.length; i += 1) {
      c = crcTable[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
    }
    return (c ^ 0xffffffff) >>> 0;
  }

  function u16(value) {
    return [value & 255, (value >>> 8) & 255];
  }

  function u32(value) {
    return [value & 255, (value >>> 8) & 255, (value >>> 16) & 255, (value >>> 24) & 255];
  }

  function concatBytes(parts) {
    const total = parts.reduce((sum, part) => sum + part.length, 0);
    const out = new Uint8Array(total);
    let offset = 0;
    parts.forEach((part) => {
      out.set(part, offset);
      offset += part.length;
    });
    return out;
  }

  function base64ToBytes(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }

  function makeZip(files) {
    const localParts = [];
    const centralParts = [];
    let offset = 0;
    const now = dosDateTime(new Date());
    files.forEach((file) => {
      const nameBytes = textBytes(file.name);
      const bytes = file.bytes instanceof Uint8Array ? file.bytes : textBytes(file.bytes || "");
      const crc = crc32(bytes);
      const local = concatBytes([
        new Uint8Array([0x50, 0x4b, 0x03, 0x04]),
        new Uint8Array(u16(20)),
        new Uint8Array(u16(0x0800)),
        new Uint8Array(u16(0)),
        new Uint8Array(u16(now.dosTime)),
        new Uint8Array(u16(now.dosDate)),
        new Uint8Array(u32(crc)),
        new Uint8Array(u32(bytes.length)),
        new Uint8Array(u32(bytes.length)),
        new Uint8Array(u16(nameBytes.length)),
        new Uint8Array(u16(0)),
        nameBytes,
        bytes
      ]);
      localParts.push(local);
      const central = concatBytes([
        new Uint8Array([0x50, 0x4b, 0x01, 0x02]),
        new Uint8Array(u16(20)),
        new Uint8Array(u16(20)),
        new Uint8Array(u16(0x0800)),
        new Uint8Array(u16(0)),
        new Uint8Array(u16(now.dosTime)),
        new Uint8Array(u16(now.dosDate)),
        new Uint8Array(u32(crc)),
        new Uint8Array(u32(bytes.length)),
        new Uint8Array(u32(bytes.length)),
        new Uint8Array(u16(nameBytes.length)),
        new Uint8Array(u16(0)),
        new Uint8Array(u16(0)),
        new Uint8Array(u16(0)),
        new Uint8Array(u16(0)),
        new Uint8Array(u32(0)),
        new Uint8Array(u32(offset)),
        nameBytes
      ]);
      centralParts.push(central);
      offset += local.length;
    });
    const centralSize = centralParts.reduce((sum, part) => sum + part.length, 0);
    const end = concatBytes([
      new Uint8Array([0x50, 0x4b, 0x05, 0x06]),
      new Uint8Array(u16(0)),
      new Uint8Array(u16(0)),
      new Uint8Array(u16(files.length)),
      new Uint8Array(u16(files.length)),
      new Uint8Array(u32(centralSize)),
      new Uint8Array(u32(offset)),
      new Uint8Array(u16(0))
    ]);
    return new Blob([concatBytes(localParts.concat(centralParts, [end]))], { type: "application/zip" });
  }

  function cleanFilename(name) {
    return String(name || "interaction-demo").replace(/[\\/:*?"<>|]+/g, "-").replace(/\s+/g, "-");
  }

  async function fetchBytes(url) {
    try {
      const res = await fetch(url);
      if (!res.ok) return null;
      return new Uint8Array(await res.arrayBuffer());
    } catch (error) {
      return null;
    }
  }

  async function collectAssetFiles() {
    const embeddedNode = document.getElementById("lui-share-embedded-assets");
    const files = [];
    const included = new Set();
    if (embeddedNode) {
      try {
        const embedded = JSON.parse(embeddedNode.textContent || "{}");
        Object.keys(embedded).forEach((name) => {
          if (!embedded[name]) return;
          files.push({ name, bytes: base64ToBytes(embedded[name]) });
          included.add(name);
        });
      } catch (error) {}
    }
    const urls = Array.from(document.images).map((img) => img.currentSrc || img.src).filter(Boolean);
    const unique = Array.from(new Set(urls));
    for (const url of unique) {
      const bytes = await fetchBytes(url);
      if (!bytes) continue;
      let name = "assets/" + decodeURIComponent((new URL(url, location.href).pathname.split("/").pop() || "asset.svg"));
      name = name.replace(/[\\:*?"<>|]+/g, "-");
      if (included.has(name)) continue;
      files.push({ name, bytes });
    }
    return files;
  }

  function serializedHtml() {
    const clone = document.documentElement.cloneNode(true);
    clone.querySelectorAll(".toast.show").forEach((node) => node.classList.remove("show"));
    clone.querySelectorAll('[contenteditable="true"]').forEach((node) => node.setAttribute("contenteditable", "false"));
    return "<!DOCTYPE html>\n" + clone.outerHTML;
  }

  async function buildSharePackage(root) {
    const doc = root.querySelector("#docContent");
    const dataNode = document.getElementById("interaction-demo-data");
    const title = cleanFilename(document.title || "interaction-demo");
    const files = [
      { name: title + ".html", bytes: textBytes(serializedHtml()) },
      { name: "docs/interaction-notes.txt", bytes: textBytes(doc ? doc.innerText.trim() : "") },
      { name: "data/interaction-demo-data.json", bytes: textBytes(dataNode ? dataNode.textContent.trim() : "{}") },
      { name: "README.txt", bytes: textBytes("打开 " + title + ".html 可查看完整交互预览；docs/interaction-notes.txt 为右侧交互说明。") }
    ];
    const assetFiles = await collectAssetFiles();
    return { blob: makeZip(files.concat(assetFiles)), title };
  }

  function downloadPackage(blob, fileName) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1500);
  }

  async function trySystemShare(blob, fileName) {
    if (!navigator.share || !navigator.canShare || typeof File !== "function") return false;
    try {
      const file = new File([blob], fileName, { type: "application/zip" });
      if (!navigator.canShare({ files: [file] })) return false;
      await navigator.share({ title: document.title || "交互预览", text: "火车票交互预览包", files: [file] });
      return true;
    } catch (error) {
      console.warn("[share-package] system share unavailable, falling back to download:", error);
      return false;
    }
  }

  async function sharePackage(root) {
    try {
      showToast(root, "正在打包预览内容");
      const pkg = await buildSharePackage(root);
      const fileName = pkg.title + "-share-package.zip";
      if (await trySystemShare(pkg.blob, fileName)) {
        showToast(root, "已打开系统分享");
        return;
      }
      downloadPackage(pkg.blob, fileName);
      showToast(root, "分享包已下载，可继续转发");
    } catch (error) {
      console.error("[share-package] failed:", error);
      showToast(root, "打包失败，请重试");
    }
  }

  function toggleEdit(root) {
    const doc = root.querySelector("#docContent");
    const btn = root.querySelector('[data-action-id="toggle-edit"]');
    if (!doc || !btn) return;
    const editing = doc.getAttribute("contenteditable") === "true";
    doc.setAttribute("contenteditable", editing ? "false" : "true");
    btn.textContent = editing ? "修改" : "完成";
    if (!editing) {
      doc.focus();
      showToast(root, "已进入编辑模式");
    } else {
      showToast(root, "修改已保留在当前页面");
    }
  }

  function handleAction(root, actionId) {
    if (actionId === "copy-doc") {
      copyDoc(root);
      return;
    }
    if (actionId === "toggle-edit") {
      toggleEdit(root);
      return;
    }
    if (actionId === "export-pdf") {
      downloadPdf(root);
      return;
    }
    if (actionId === "share-package") {
      sharePackage(root);
    }
  }

  function runDemoAction(root, data, action) {
    if (!isObject(action) || !action.type) {
      return;
    }
    if (action.type === "toast") {
      showToast(root, action.text || data.meta.toastText || "已复制");
      return;
    }
    if (action.type === "set-frame" || action.type === "navigate") {
      if (action.frameId) {
        uiState.frameId = action.frameId;
      }
      uiState.stateId = action.stateId !== undefined ? action.stateId : null;
      updatePreview(root, data);
      if (action.toastText) {
        showToast(root, action.toastText);
      }
      return;
    }
    if (action.type === "set-state") {
      if (action.stateId) {
        uiState.stateId = action.stateId;
        updatePreview(root, data);
        if (action.toastText) {
          showToast(root, action.toastText);
        }
      }
    }
  }

  function bindStaticActions(root) {
    root.querySelectorAll("[data-action-id]").forEach((node) => {
      node.addEventListener("click", () => handleAction(root, node.getAttribute("data-action-id")));
    });
  }

  function bindPhoneActions(root, data) {
    const region = root.querySelector("#interaction-preview-region");
    if (!region) {
      return;
    }
    region.querySelectorAll("[data-demo-action]").forEach((node) => {
      node.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        runDemoAction(root, data, parseDemoAction(node));
      });
    });
  }

  function bindPreviewActions(root, data) {
    root.querySelectorAll("[data-frame-id]").forEach((node) => {
      node.addEventListener("click", () => {
        uiState.frameId = node.getAttribute("data-frame-id");
        const frame = findActiveFrame(data.preview.frames, uiState.frameId);
        const stateItem = findActivePhoneState(frame, null);
        uiState.stateId = stateItem ? stateItem.id : null;
        updatePreview(root, data);
      });
    });
    root.querySelectorAll("[data-state-id]").forEach((node) => {
      node.addEventListener("click", () => {
        uiState.stateId = node.getAttribute("data-state-id");
        updatePreview(root, data);
      });
    });
  }

  function updatePreview(root, data) {
    const frame = findActiveFrame(data.preview.frames, uiState.frameId);
    const stateItem = findActivePhoneState(frame, uiState.stateId);
    if (frame) uiState.frameId = frame.id;
    if (stateItem) uiState.stateId = stateItem.id;
    const region = root.querySelector("#interaction-preview-region");
    if (!region) return;
    region.innerHTML = renderPreviewRegion(data, frame, stateItem);
    mountPhoneTemplate(region, stateItem && stateItem.phone);
    bindPreviewActions(root, data);
    bindPhoneActions(root, data);
    scheduleFit(root);
  }

  function parseScriptPayload(id) {
    const node = document.getElementById(id);
    if (!node) {
      return null;
    }
    const raw = node.textContent.trim();
    if (!raw || raw === "__INTERACTION_DEMO_DATA__") {
      return null;
    }
    try {
      return JSON.parse(raw);
    } catch (error) {
      console.warn("[interaction-demo-template] failed to parse data payload:", error);
      return null;
    }
  }

  const api = {
    defaults: DEFAULT_DATA,
    render(root, patch) {
      const data = deepMerge(DEFAULT_DATA, patch || {});
      root.setAttribute("data-interaction-demo-root", "true");
      root.innerHTML = renderShell(data);
      const activeFrame = findActiveFrame(data.preview.frames, uiState.frameId);
      uiState.frameId = activeFrame ? activeFrame.id : null;
      const activeState = findActivePhoneState(activeFrame, uiState.stateId);
      uiState.stateId = activeState ? activeState.id : null;
      updatePreview(root, data);
      bindStaticActions(root);
      if (typeof document !== "undefined" && data.meta && data.meta.pageTitle) {
        document.title = data.meta.pageTitle;
      }
      scheduleFit(root);
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

  if (typeof window !== "undefined" && !window.__interactionDemoTemplateResizeBound) {
    window.addEventListener("resize", fitAll);
    window.addEventListener("load", fitAll);
    window.__interactionDemoTemplateResizeBound = true;
  }

  window.InteractionDemoTemplate = api;
})();
