import { expect, test } from "@playwright/test";

import { BASE } from "../dist/helpers.js";

// custom.js adds View Source and Accessibility Mode from the viewer's query
// string (sourceUrl, accessibilityModeUrl) only for http(s) URLs, so a
// crafted link to viewer.html can't run script on this origin
const UNSAFE = [
  "javascript:alert(1)",
  " JavaScript:alert(1)",
  "data:text/html,<script>alert(1)</script>",
  "vbscript:msgbox(1)",
];

function viewerUrl(sourceUrl, accessibilityModeUrl) {
  const params = new URLSearchParams({
    file: `${BASE}cv.pdf`,
    sourceUrl,
    accessibilityModeUrl,
  });
  return `pdfjs/web/viewer.html?${params}`;
}

// The viewer page on its own (not in the site's iframe), as a crafted link
// would open it
async function openViewerPage(page, url) {
  await page.goto(url);
  await page.waitForFunction(() => window.PDFViewerApplication?.pdfDocument);
  await page.locator("#secondaryToolbarToggleButton").click();
  await expect(page.locator("#secondaryToolbar")).toBeVisible();
}

for (const unsafe of UNSAFE) {
  test(`no menu link for ${JSON.stringify(unsafe)}`, async ({ page }) => {
    const dialogs = [];
    page.on("dialog", async (dialog) => {
      dialogs.push(dialog.message());
      await dialog.dismiss();
    });

    await openViewerPage(page, viewerUrl(unsafe, unsafe));

    await expect(page.locator("#viewSource")).toHaveCount(0);
    await expect(page.locator("#accessibilityMode")).toHaveCount(0);
    expect(dialogs).toEqual([]);
  });
}

// The same parameters with safe values do add the links
test("http(s) and relative URLs add the menu links", async ({ page }) => {
  await openViewerPage(
    page,
    viewerUrl("https://example.com/source", `${BASE}?accessibility=true`),
  );

  await expect(page.locator("#viewSource")).toHaveAttribute(
    "href",
    "https://example.com/source",
  );
  await expect(page.locator("#accessibilityMode")).toHaveAttribute(
    "href",
    new RegExp(`${BASE.replaceAll("/", "\\/")}\\?accessibility=true$`),
  );
});
