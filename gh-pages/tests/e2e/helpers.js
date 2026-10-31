/**
 * Shared by the browser tests. Expected values come from the built site
 * (dist/ and the rendered src/template_params.js), so the tests pass for
 * every CV.
 */
import { expect } from "@playwright/test";

import { getTemplateParams } from "../../src/template_params.js";
import { indexTags, metaContent } from "../dist/helpers.js";

// The CV's name, from the built page
const [author] = metaContent(indexTags, "name", "author");

// website.yaml's locale and source_url, as main.js passes them to the viewer
const { locale, sourceUrl } = getTemplateParams();

// WebKit reports a style-src-attr CSP violation for the zoom <select> of the
// stock viewer.html (line 327 in pdf.js 6.4.299): no script sets a style
// attribute there, nothing is visibly unstyled, and Chromium and Firefox
// report nothing, so it's WebKit's own rendering of the <select>
function isKnownIssue(browserName, message) {
  return (
    browserName === "webkit" &&
    message.location().url.includes("/pdfjs/web/viewer.html") &&
    message
      .text()
      .startsWith("Refused to apply a stylesheet because its hash, its nonce,")
  );
}

/**
 * Collect console errors, uncaught exceptions and failed requests of the page
 * and its frames (the viewer runs in an iframe). Check the returned array at
 * the end of the test.
 */
function collectProblems(page, browserName) {
  const problems = [];
  page.on("console", (message) => {
    if (message.type() === "error" && !isKnownIssue(browserName, message)) {
      problems.push(`console: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => problems.push(`pageerror: ${error.message}`));
  page.on("requestfailed", (request) =>
    problems.push(`failed: ${request.url()} ${request.failure()?.errorText}`),
  );
  page.on("response", (response) => {
    if (response.status() >= 400) {
      problems.push(`${response.status()}: ${response.url()}`);
    }
  });
  return problems;
}

/**
 * Open the site in viewer mode and wait until the PDF is loaded. Returns the
 * viewer's frame (for evaluate) and a locator scoped to it.
 */
async function openViewer(page, url = "./") {
  await page.goto(url);
  const viewer = page.frameLocator("#pdfViewerIframe");
  await expect(viewer.locator(".page").first()).toBeVisible();
  const frame = page.frame({ url: /\/pdfjs\/web\/viewer\.html/ });
  await frame.waitForFunction(() => window.PDFViewerApplication?.pdfDocument);
  return { frame, viewer };
}

/** Open the viewer's menu (the » button) and wait for it. */
async function openMenu(viewer) {
  await viewer.locator("#secondaryToolbarToggleButton").click();
  await expect(viewer.locator("#secondaryToolbar")).toBeVisible();
}

export { author, collectProblems, locale, openMenu, openViewer, sourceUrl };
