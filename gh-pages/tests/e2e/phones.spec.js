import { expect, test } from "@playwright/test";

import { openViewer } from "./helpers.js";

// The narrowest common phones (iPhone SE: 320, most phones: 375 and up), in
// both orientations. Tap target sizes are axe's target-size rule
// (axe.spec.js, which also runs on the phone projects)
const VIEWPORTS = [
  { width: 320, height: 568 },
  { width: 568, height: 320 },
  { width: 375, height: 667 },
  { width: 667, height: 375 },
];

function horizontalOverflow(frame) {
  return frame.evaluate(
    () =>
      document.documentElement.scrollWidth -
      document.documentElement.clientWidth,
  );
}

test.beforeEach(({ isMobile }) => {
  test.skip(!isMobile, "phones only");
});

for (const viewport of VIEWPORTS) {
  const size = `${viewport.width}×${viewport.height}`;

  test(`${size}: the accessible page doesn't scroll sideways`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await page.goto("?accessibility=true");
    await expect(page.locator("#accessibleContainer")).toBeVisible();
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
  });

  test(`${size}: the viewer doesn't scroll sideways`, async ({ page }) => {
    await page.setViewportSize(viewport);
    const { frame } = await openViewer(page);
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
    // The viewer's own page: its toolbar fits; the PDF pages scroll inside
    // #viewerContainer, not the document
    expect(await horizontalOverflow(frame)).toBeLessThanOrEqual(0);
  });
}
