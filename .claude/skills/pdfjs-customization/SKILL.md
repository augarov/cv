---
name: pdfjs-customization
description: Methodology for safely customizing the PDF.js viewer in gh-pages/public/pdfjs/. Use when editing viewer HTML, CSS, or JS files — toolbar icons, button layout, or any PDF.js viewer component.
paths: gh-pages/public/pdfjs/**
---

## PDF.js Customization Patterns

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

PDF.js JavaScript expects certain DOM elements to exist. Removing them causes runtime JS errors. Always hide with `display: none` instead of deleting or commenting out:

```html
<!-- Bad: deleting or commenting out -->
<!-- <button id="unusedButton">...</button> -->

<!-- Good: hide so JS doesn't error -->
<button id="unusedButton" style="display: none;">...</button>
```

### Investigation first

Before adding or modifying any viewer feature, grep the existing viewer source to find how similar features are implemented. Match naming conventions (CSS variables, class names, IDs) and existing patterns exactly.

### Verification checklist

After any modification:

- Open browser console — zero JS errors required
- Test across desktop and mobile viewport widths
- Verify accessibility attributes (`aria-*`) are preserved on modified elements
- Confirm no existing toolbar functionality is broken
