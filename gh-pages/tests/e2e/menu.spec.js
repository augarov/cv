import { expect, test } from "@playwright/test";

import { collectProblems, openMenu, openViewer, sourceUrl } from "./helpers.js";

const THEME_KEY = "cv-viewer-theme";

function colorScheme(frame) {
  return frame.evaluate(() => document.documentElement.style.colorScheme);
}

test("View Source opens the source URL in a new tab", async ({ page }) => {
  test.skip(!sourceUrl, "website.yaml sets no source_url");
  const { viewer } = await openViewer(page);
  await openMenu(viewer);

  const link = viewer.locator("#viewSource");
  await expect(link).toBeVisible();
  await expect(link).toHaveAttribute("href", new URL(sourceUrl).href);
  await expect(link).toHaveAttribute("target", "_blank");
  await expect(link).toHaveAttribute("rel", "noopener noreferrer");
});

test("Accessibility Mode opens the accessible page in the whole window", async ({
  page,
}) => {
  const { viewer } = await openViewer(page);
  await openMenu(viewer);

  await viewer.locator("#accessibilityMode").click();

  await expect(page).toHaveURL(/[?&]accessibility=true\b/);
  await expect(page.locator("#accessibleContainer")).toBeVisible();
  await expect(page.locator("#pdfViewerContainer")).toBeHidden();
});

// A second page of the same browser session stands in for a reload: it reads
// the same localStorage, and WebKit would report the requests a reload
// cancels as failed
test("the theme switch sets color-scheme and is remembered", async ({
  context,
  page,
  browserName,
}) => {
  const problems = collectProblems(page, browserName);
  const { frame, viewer } = await openViewer(page);
  await openMenu(viewer);
  await expect(viewer.locator("#themeSystem")).toHaveAttribute(
    "aria-checked",
    "true",
  );
  expect(await colorScheme(frame)).toBe("");

  await viewer.locator("#themeDark").click();
  await expect(viewer.locator("#themeDark")).toHaveAttribute(
    "aria-checked",
    "true",
  );
  expect(await colorScheme(frame)).toBe("dark");
  expect(problems).toEqual([]);

  const next = await context.newPage();
  const nextProblems = collectProblems(next, browserName);
  const opened = await openViewer(next);
  expect(await colorScheme(opened.frame)).toBe("dark");
  await openMenu(opened.viewer);
  await expect(opened.viewer.locator("#themeDark")).toHaveAttribute(
    "aria-checked",
    "true",
  );

  // Back to the system setting
  await opened.viewer.locator("#themeSystem").click();
  expect(await colorScheme(opened.frame)).toBe("");
  expect(
    await opened.frame.evaluate((key) => localStorage.getItem(key), THEME_KEY),
  ).toBe("system");
  expect(nextProblems).toEqual([]);
});

test("the viewer works when storage throws", async ({ page, browserName }) => {
  // As with blocked site data: reading localStorage throws, in every frame
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new DOMException("The operation is insecure.", "SecurityError");
      },
    });
  });
  const problems = collectProblems(page, browserName);

  const { frame, viewer } = await openViewer(page);
  await openMenu(viewer);
  await expect(viewer.locator("#themeSystem")).toHaveAttribute(
    "aria-checked",
    "true",
  );
  // The theme still applies, it just isn't remembered
  await viewer.locator("#themeLight").click();
  expect(await colorScheme(frame)).toBe("light");

  // pdf.js reads its stored preferences at startup; it catches the error,
  // logs "initialize: <error>" and goes on with the defaults
  // (PDFViewerApplication.initialize in viewer.mjs)
  expect(
    problems.filter((p) => !p.startsWith("console: initialize: ")),
  ).toEqual([]);
});
