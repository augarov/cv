---
name: pdfjs-customization
description: Methodology for safely customizing the PDF.js viewer in gh-pages/public/pdfjs/. Use when editing viewer HTML, CSS, or JS files — toolbar icons, button layout, or any PDF.js viewer component.
paths: gh-pages/public/pdfjs/**
---

## PDF.js Customization Patterns

### Layout: a stock release plus two files of ours

- `gh-pages/public/pdfjs/web/` is the `web/` folder of the **legacy** release zip (`pdfjs-<version>-legacy-dist.zip` from the pdf.js GitHub releases), without `compressed.tracemonkey-pldi-09.pdf`.
- `gh-pages/public/pdfjs/build` is a symlink to `node_modules/pdfjs-dist/legacy/build`: the library comes from npm. `pdfjs-dist` is pinned to the **exact** version of the viewer in `package.json` (no `^`), and `make build-website` fails when `node_modules` and `viewer.mjs` (`pdfjsVersion = …`) differ (`scripts/check-pdfjs-version.sh`).
- All customizations are in `web/custom.css`, `web/custom.js` and our icons in `web/images/` (`github-mark-white.svg`, `accessibility-icon.svg`, `theme-system.svg`, `theme-light.svg`, `theme-dark.svg`). Never edit `viewer.mjs` or `viewer.css`.
- `viewer.html` differs from stock in three lines only: `../build/pdf.min.mjs` instead of `pdf.mjs`, `<link rel="stylesheet" href="custom.css" />` after `viewer.css`, and `<script src="custom.js"></script>` before `viewer.mjs`. `viewer.html` has its own Content-Security-Policy `<meta>` (since 6.x): custom code sets styles through the CSSOM (`element.style`), never inline `style` attributes or `<style>` elements, and loads only local files.
- `custom.js` sets viewer options (locale, `.min.mjs` worker, no PDF scripting, no preferences, no sidebar) through `PDFViewerApplicationOptions` in pdf.js's `webviewerloaded` event, and adds the View Source and Accessibility Mode links and the theme group (System / Light / Dark, kept in `localStorage` as `cv-viewer-theme`). The theme sets `color-scheme` on `<html>`; viewer.css and custom.css follow it through `light-dark()`, so colors in `custom.css` use `light-dark()`, never `@media (prefers-color-scheme)`. It logs `custom.js: …` to the console when an option or element it uses doesn't exist (renamed in a new release).

### Upgrading pdf.js

1. Download and unpack `pdfjs-<version>-legacy-dist.zip` (in a scratch folder).
2. Replace `gh-pages/public/pdfjs/web/` with its `web/`; delete `compressed.tracemonkey-pldi-09.pdf`; put back `custom.css`, `custom.js` and our five icons; compare `LICENSE`.
3. Re-apply the three `viewer.html` lines above.
4. Set `"pdfjs-dist": "<version>"` (exact) in `gh-pages/package.json` and run `make install-deps-node`. Check that both sides match: `scripts/check-pdfjs-version.sh gh-pages/node_modules/pdfjs-dist/package.json gh-pages/public/pdfjs/web/viewer.mjs` (silent on success).
5. Set `MIN_VERSIONS` in `gh-pages/src/fallback_detection.js` (and its test rows) to the release's browser targets: the `ENV_TARGETS` in pdf.js's `gulpfile.mjs` at the release tag (Chrome, Safari), and for Firefox the ESR that `browserslist`'s `FIREFOX_ESR_VERSION` names in the version locked at that tag. Older browsers aren't guaranteed to run the legacy build.
6. Check the ids that `custom.css` / `custom.js` use still exist in the new `viewer.html`, then `make build-website` and `make preview-website-prod`: zero console errors (no `custom.js:` messages), desktop and narrow widths, every menu item.

### CSS icons — use mask-image, not background-image

PDF.js toolbar icons use the mask-image technique for theming. Always follow this pattern:

```css
/* Define in :root */
:root {
  --custom-icon: url("path/to/icon.svg");
}

/* Apply with mask-image */
.toolbarButton::before {
  -webkit-mask-image: var(--custom-icon);
  mask-image: var(--custom-icon);
}
```

Using `background-image` instead will not render correctly with PDF.js's theming system.

### Hide, don't delete unused elements

PDF.js JavaScript expects certain DOM elements to exist. Removing them causes runtime JS errors. Hide them by id in `custom.css` instead of editing `viewer.html`:

```css
/* custom.css */
#unusedButton {
  display: none !important;
}
```

Only elements without an id that pdf.js never looks up (such as the menu's unnamed separators) may be removed, from `custom.js`.

### Investigation first

Before adding or modifying any viewer feature, grep the existing viewer source to find how similar features are implemented. Match naming conventions (CSS variables, class names, IDs) and existing patterns exactly.

### Verification checklist

After any modification:

- Open browser console — zero JS errors required
- Test across desktop and mobile viewport widths
- Verify accessibility attributes (`aria-*`) are preserved on modified elements
- Confirm no existing toolbar functionality is broken
