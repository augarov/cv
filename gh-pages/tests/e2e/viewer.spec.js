import { expect, test } from "@playwright/test";

import { author, collectProblems, locale, openViewer } from "./helpers.js";

test("the viewer renders the PDF without errors", async ({
  page,
  browserName,
}) => {
  const problems = collectProblems(page, browserName);

  const { frame, viewer } = await openViewer(page);
  await expect(viewer.locator(".textLayer").first()).toContainText(author);
  // Every page of the PDF is in the viewer
  const pagesCount = await frame.evaluate(
    () => window.PDFViewerApplication.pagesCount,
  );
  expect(pagesCount).toBeGreaterThan(0);
  await expect(viewer.locator(".page")).toHaveCount(pagesCount);

  expect(problems).toEqual([]);
});

test("the viewer uses the site's locale", async ({ page }) => {
  test.skip(!locale, "website.yaml sets no locale");
  const ftlRequests = [];
  page.on("request", (request) => {
    if (request.url().endsWith("/viewer.ftl")) {
      ftlRequests.push(new URL(request.url()).pathname);
    }
  });

  const { frame } = await openViewer(page);

  // pdf.js 6.4 doesn't set <html lang> in the viewer: its l10n reports the
  // language, and the site's locale file is what it loaded
  const language = await frame.evaluate(() =>
    window.PDFViewerApplication.l10n.getLanguage(),
  );
  expect(language).toBe(locale.toLowerCase());
  expect(ftlRequests).toContainEqual(
    expect.stringMatching(new RegExp(`/locale/${locale}/viewer\\.ftl$`, "i")),
  );
});

// custom.js turns PDF scripting off (CVE-2026-16633): no sandbox is loaded
test("PDF scripting is off", async ({ page }) => {
  const sandboxRequests = [];
  page.on("request", (request) => {
    if (request.url().includes("pdf.sandbox")) {
      sandboxRequests.push(request.url());
    }
  });

  const { frame } = await openViewer(page);

  expect(
    await frame.evaluate(() =>
      window.PDFViewerApplicationOptions.get("enableScripting"),
    ),
  ).toBe(false);
  expect(sandboxRequests).toEqual([]);
});
