import { expect, test } from "@playwright/test";

import { BASE } from "../dist/helpers.js";
import { author, collectProblems } from "./helpers.js";

// Browsers below the viewer's minimums (fallback_detection.js) and a crawler
const OLD_OR_BOT_USER_AGENTS = {
  "Chrome 124":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "Firefox 152":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
  "Safari 17.6":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
  "iOS 17.5":
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
  Googlebot:
    "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
};

// The viewer and the PDF are loaded only when the viewer is shown (main.js)
function collectViewerRequests(page) {
  const requests = [];
  page.on("request", (request) => {
    const { pathname } = new URL(request.url());
    if (pathname.startsWith(`${BASE}pdfjs/`) || pathname === `${BASE}cv.pdf`) {
      requests.push(pathname);
    }
  });
  return requests;
}

async function expectAccessiblePage(page, { viewerButton }) {
  await expect(page.locator("#accessibleContainer")).toBeVisible();
  await expect(page.locator("#pdfViewerContainer")).toBeHidden();
  await expect(page.locator("h1")).toContainText(author.split(" ")[0]);
  // "Open in PDF Viewer" only where the viewer would work
  const button = page.locator("#cvOpenInPdfViewerButton");
  await (viewerButton
    ? expect(button).toBeVisible()
    : expect(button).toBeHidden());
}

for (const query of ["?accessibility=true", "?a11y=1"]) {
  test(`${query} shows the accessible page, and its button the viewer`, async ({
    page,
    browserName,
  }) => {
    const problems = collectProblems(page, browserName);
    const viewerRequests = collectViewerRequests(page);

    await page.goto(query);
    await expectAccessiblePage(page, { viewerButton: true });
    expect(viewerRequests).toEqual([]);
    expect(problems).toEqual([]);

    await page.locator("#cvOpenInPdfViewerButton").click();
    await expect(page.locator("#pdfViewerContainer")).toBeVisible();
    await expect(page.locator("#accessibleContainer")).toBeHidden();
  });
}

for (const [name, userAgent] of Object.entries(OLD_OR_BOT_USER_AGENTS)) {
  test(`${name} gets the accessible page`, async ({ browser, browserName }) => {
    const context = await browser.newContext({ userAgent });
    const page = await context.newPage();
    const problems = collectProblems(page, browserName);
    const viewerRequests = collectViewerRequests(page);

    await page.goto(test.info().project.use.baseURL);
    await expectAccessiblePage(page, { viewerButton: false });
    expect(viewerRequests).toEqual([]);
    expect(problems).toEqual([]);
    await context.close();
  });
}

test("without JavaScript the accessible page shows", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  const viewerRequests = collectViewerRequests(page);

  await page.goto(test.info().project.use.baseURL);
  await expectAccessiblePage(page, { viewerButton: false });
  expect(viewerRequests).toEqual([]);
  await context.close();
});

test("the accessible page's links work", async ({ page, request }) => {
  await page.goto("?accessibility=true");

  const links = await page
    .locator("#accessibleContainer a[href]")
    .evaluateAll((anchors) =>
      anchors.map((a) => ({ href: a.href, target: a.target, rel: a.rel })),
    );
  expect(links.length).toBeGreaterThan(0);
  for (const { href, target, rel } of links) {
    const url = new URL(href);
    expect(["http:", "https:", "mailto:", "tel:"]).toContain(url.protocol);
    // Links into the site resolve; outside ones aren't fetched
    if (url.origin === new URL(page.url()).origin) {
      expect((await request.get(href)).status(), href).toBe(200);
    }
    if (target === "_blank" && url.origin !== new URL(page.url()).origin) {
      expect(rel, href).toContain("noopener");
    }
  }
  // The download link is the PDF the viewer shows
  await expect(page.locator("#cvDownloadButton")).toHaveAttribute(
    "href",
    new RegExp(`${BASE}cv\\.pdf$`),
  );
});
