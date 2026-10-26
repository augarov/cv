/*
 * Customizations of the stock pdf.js viewer. viewer.html only loads this file
 * and custom.css, so upgrading pdf.js means replacing web/ with a new release
 * (see the pdfjs-customization skill).
 *
 * Query parameters (all optional): locale, sourceUrl (the "View Source" link)
 * and accessibilityModeUrl (the "Accessibility Mode" link).
 *
 * The menu's theme group (system, light, dark) sets color-scheme on <html>,
 * which viewer.css and custom.css follow through light-dark(); the choice is
 * kept in localStorage.
 */
"use strict";

(function () {
  // Names are case-insensitive, as in pdf.js
  const params = new Map();
  for (const [key, value] of new URLSearchParams(document.location.search)) {
    params.set(key.toLowerCase(), value);
  }

  // Resolve a link from the query string; only http(s) URLs are allowed,
  // so a crafted ?sourceurl=javascript:... can't run script on this origin
  function safeLinkUrl(value) {
    const url = value ? URL.parse(value, document.baseURI) : null;
    return url && (url.protocol === "http:" || url.protocol === "https:")
      ? url.href
      : null;
  }

  // A renamed option or element in a new pdf.js release shows up in the
  // console instead of failing silently
  function setOption(options, name, value) {
    if (options.get(name) === undefined) {
      console.error(`custom.js: pdf.js has no option "${name}"`);
      return;
    }
    options.set(name, value);
  }

  function byId(id) {
    const element = document.getElementById(id);
    if (!element) {
      console.error(`custom.js: no element #${id} in viewer.html`);
    }
    return element;
  }

  function setOptions(options) {
    // There's no preferences UI; stored preferences would also override the
    // options below
    setOption(options, "disablePreferences", true);
    setOption(options, "workerSrc", "../build/pdf.worker.min.mjs");
    setOption(options, "sandboxBundleSrc", "../build/pdf.sandbox.min.mjs");
    // The views manager (sidebar) is hidden: never open it for a PDF's page mode
    setOption(options, "sidebarViewOnLoad", 0); // SidebarView.NONE
    const locale = params.get("locale");
    if (locale) {
      setOption(options, "localeProperties", { lang: locale });
    }
  }

  function separator(...classes) {
    const element = document.createElement("div");
    element.classList.add("horizontalToolbarSeparator", ...classes);
    return element;
  }

  function menuLink(id, label, href, target) {
    const link = document.createElement("a");
    link.id = id;
    link.className = "toolbarButton labeled";
    link.tabIndex = 0;
    link.href = href;
    link.target = target;
    link.rel = "noopener noreferrer";
    link.title = label;
    const span = document.createElement("span");
    span.textContent = label;
    link.append(span);
    return link;
  }

  // Theme: "system" leaves color-scheme to viewer.css ("light dark"), so the
  // system setting decides. Storage can be unavailable (private windows,
  // blocked site data): the theme then just isn't remembered.
  const THEME_KEY = "cv-viewer-theme";
  const THEMES = [
    { id: "themeSystem", value: "system", label: "System Theme" },
    { id: "themeLight", value: "light", label: "Light Theme" },
    { id: "themeDark", value: "dark", label: "Dark Theme" },
  ];

  function storedTheme() {
    try {
      const value = localStorage.getItem(THEME_KEY);
      return THEMES.some((theme) => theme.value === value) ? value : "system";
    } catch {
      return "system";
    }
  }

  function applyTheme(value) {
    document.documentElement.style.colorScheme =
      value === "system" ? "" : value;
  }

  function saveTheme(value) {
    try {
      localStorage.setItem(THEME_KEY, value);
    } catch {
      // Not remembered; the theme still applies to this page
    }
  }

  // A radio group like pdf.js's own scroll and spread mode groups
  function themeButtons() {
    const group = document.createElement("div");
    group.id = "themeButtons";
    group.setAttribute("role", "radiogroup");
    group.setAttribute("aria-label", "Theme");
    const buttons = THEMES.map(({ id, value, label }) => {
      const button = document.createElement("button");
      button.id = id;
      button.className = "toolbarButton labeled";
      button.type = "button";
      button.tabIndex = 0;
      button.title = label;
      button.setAttribute("role", "radio");
      const span = document.createElement("span");
      span.textContent = label;
      button.append(span);
      button.addEventListener("click", () => {
        applyTheme(value);
        saveTheme(value);
        check(value);
      });
      return button;
    });
    function check(value) {
      buttons.forEach((button, index) => {
        const checked = THEMES[index].value === value;
        button.classList.toggle("toggled", checked);
        button.setAttribute("aria-checked", String(checked));
      });
    }
    check(storedTheme());
    group.append(...buttons);
    return group;
  }

  // Download stays on the toolbar at every width; print moves to the menu on
  // narrow screens, as in the stock viewer
  function customizeToolbar() {
    const download = byId("downloadButton");
    const printGroup = byId("printButton")?.parentElement;
    if (!download || !printGroup) {
      return;
    }
    const group = document.createElement("div");
    group.className = "toolbarHorizontalGroup";
    printGroup.after(group);
    group.append(download);
    group.nextElementSibling?.classList.remove("hiddenMediumView");
  }

  // The menu: print (narrow screens), presentation mode, theme, view source,
  // document properties, accessibility mode. custom.css hides the rest; its
  // unnamed separators are replaced by ours.
  function customizeMenu() {
    const menu = byId("secondaryToolbarButtonContainer");
    const presentationMode = byId("presentationMode");
    const documentProperties = byId("documentProperties");
    if (!menu || !presentationMode || !documentProperties) {
      return;
    }
    for (const element of menu.querySelectorAll(
      ":scope > .horizontalToolbarSeparator:not([id])",
    )) {
      element.remove();
    }
    menu
      .querySelector(":scope > .visibleMediumView")
      ?.after(separator("visibleMediumView"));
    const presentationSeparator = separator();
    presentationSeparator.id = "presentationSeparator";
    presentationMode.after(presentationSeparator);
    presentationSeparator.after(themeButtons(), separator());

    const sourceUrl = safeLinkUrl(params.get("sourceurl"));
    if (sourceUrl) {
      documentProperties.before(
        menuLink("viewSource", "View Source", sourceUrl, "_blank"),
      );
    }
    const accessibilityModeUrl = safeLinkUrl(
      params.get("accessibilitymodeurl"),
    );
    if (accessibilityModeUrl) {
      documentProperties.after(
        menuLink(
          "accessibilityMode",
          "Accessibility Mode",
          accessibilityModeUrl,
          "_top",
        ),
      );
    }
  }

  // Before viewer.mjs runs, so the page never shows in the wrong theme first
  applyTheme(storedTheme());

  // viewer.mjs dispatches "webviewerloaded" on the parent document (the
  // viewer's own one when it isn't in a frame, or when the parent is on another
  // origin) after reading the DOM and before applying the options
  let eventTarget = document;
  try {
    eventTarget = parent.document;
  } catch {
    // The parent is on another origin: pdf.js falls back to this document too
  }
  eventTarget.addEventListener("webviewerloaded", (event) => {
    if (event.detail?.source !== window) {
      return;
    }
    setOptions(window.PDFViewerApplicationOptions);
    customizeToolbar();
    customizeMenu();
  });
})();
