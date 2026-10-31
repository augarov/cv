import { expect, test } from "@playwright/test";

import { indexTags, metaContent } from "../dist/helpers.js";

// The CV's name, from the built page
const [author] = metaContent(indexTags, "name", "author");

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

// Console errors, uncaught exceptions and failed requests of the page and
// its frames (the viewer runs in an iframe)
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

test("the viewer renders the PDF without errors", async ({
  page,
  browserName,
}) => {
  const problems = collectProblems(page, browserName);

  await page.goto("./");
  const viewer = page.frameLocator("#pdfViewerIframe");
  await expect(viewer.locator(".page").first()).toBeVisible();
  await expect(viewer.locator(".textLayer").first()).toContainText(author);

  expect(problems).toEqual([]);
});
