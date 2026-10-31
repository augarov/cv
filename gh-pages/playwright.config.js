/**
 * Browser tests (layer 3b): the built site in dist/, served by `vite preview`
 * under the base path, in desktop browsers and emulated phones. Run through
 * `make test-website-e2e`, which builds the site and installs the browsers.
 */
import { defineConfig, devices } from "@playwright/test";

import viteConfig from "./vite.config.js";

// Not vite preview's default 4173, which make preview-website-prod uses
const PORT = 4174;
const ORIGIN = `http://127.0.0.1:${PORT}`;
const CI = Boolean(process.env.CI);

export default defineConfig({
  testDir: "tests/e2e",
  forbidOnly: CI,
  retries: CI ? 1 : 0,
  // The HTML report is uploaded by CI when a test fails
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: ORIGIN + viteConfig.base,
    trace: "retain-on-failure",
  },
  // Always a new server: an old one could serve another build
  webServer: {
    command: `pnpm exec vite preview --host 127.0.0.1 --port ${PORT} --strictPort`,
    url: ORIGIN + viteConfig.base,
    reuseExistingServer: false,
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
    { name: "pixel", use: { ...devices["Pixel 7"] } },
    // iOS 18.7: "iPhone 15" is iOS 17.5, below the viewer's minimum (iOS 18,
    // fallback_detection.js), so it gets the accessible page
    { name: "iphone", use: { ...devices["iPhone 17"] } },
  ],
});
