import { expect, test } from "@playwright/test";

import { BASE } from "../dist/helpers.js";

// Chromium reports the manifest it parsed and why the site couldn't be
// installed through the DevTools protocol; other browsers have no such API
test.beforeEach(({ browserName }) => {
  test.skip(browserName !== "chromium", "Chromium's DevTools protocol only");
});

test("the site is installable", async ({ page }) => {
  await page.goto("./");
  const cdp = await page.context().newCDPSession(page);

  const manifest = await cdp.send("Page.getAppManifest");
  expect(manifest.url).toMatch(new RegExp(`^[^?#]*${BASE}.*\\.webmanifest$`));
  expect(manifest.errors).toEqual([]);

  const { installabilityErrors } = await cdp.send(
    "Page.getInstallabilityErrors",
  );
  expect(installabilityErrors).toEqual([]);

  // id, start_url and scope resolve under the site's base path, so the app
  // opens the CV and stays in it
  const { origin } = new URL(page.url());
  const { id, start_url: startUrl, scope } = JSON.parse(manifest.data);
  for (const [key, value] of Object.entries({ id, startUrl, scope })) {
    expect(new URL(value, manifest.url).href, key).toBe(origin + BASE);
  }
});
