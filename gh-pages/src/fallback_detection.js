/**
 * PDF.js Capability Detection
 * Decides between the pdf.js viewer and the accessible page: basic APIs, the
 * browser version, bots, and a working Web Worker.
 */

/**
 * Minimum versions for the viewer, as [major, minor]: pdf.js's own targets
 * (Chrome 118, Safari 16.4) raised to native light-dark() support, which
 * custom.css and the viewer's theme switch use (Chrome 123, Firefox 120,
 * Safari 17.5). Older browsers get the accessible page.
 */
const MIN_VERSIONS = {
  chromium: [123, 0], // Chrome, Edge, Opera, Samsung Internet, Android webviews
  firefox: [120, 0],
  webkit: [17, 5], // Safari version on macOS, iOS version on iPhone / iPad
};

function parseVersion(major, minor) {
  return [parseInt(major, 10), parseInt(minor || "0", 10)];
}

/**
 * Get the rendering engine and its version from a user agent string
 * @param {string} ua
 * @returns {{name: string, version: number[]}}
 */
function getBrowserInfo(ua) {
  // Every browser on iPhone / iPad (Safari, Chrome "CriOS", Firefox "FxiOS",
  // in-app webviews) is WebKit of the iOS version. iPadOS's default desktop
  // UA has no iPad token and is matched as Safari below.
  const iosMatch = ua.match(/\b(?:iPhone|iPad|iPod)\b.*? OS (\d+)(?:_(\d+))?/);
  if (iosMatch) {
    return { name: "webkit", version: parseVersion(iosMatch[1], iosMatch[2]) };
  }

  const firefoxMatch = ua.match(/\bFirefox\/(\d+)(?:\.(\d+))?/);
  if (firefoxMatch) {
    return {
      name: "firefox",
      version: parseVersion(firefoxMatch[1], firefoxMatch[2]),
    };
  }

  // Chromium-based browsers (Chrome, Edge, Opera, Brave, Samsung Internet,
  // Android webviews) all carry the Chromium version as Chrome/<version>
  const chromeMatch = ua.match(/\bChrome\/(\d+)(?:\.(\d+))?/);
  if (chromeMatch) {
    return {
      name: "chromium",
      version: parseVersion(chromeMatch[1], chromeMatch[2]),
    };
  }

  // Safari on macOS (and iPadOS's desktop UA): Version/<x.y> ... Safari
  const safariMatch = ua.match(/\bVersion\/(\d+)(?:\.(\d+))?.*\bSafari\//);
  if (safariMatch) {
    return {
      name: "webkit",
      version: parseVersion(safariMatch[1], safariMatch[2]),
    };
  }

  return { name: "unknown", version: [0, 0] };
}

// Search engine crawlers and link preview fetchers: the accessible page shows
// them the CV as text instead of a PDF inside an iframe (the same content, so
// it isn't cloaking). Named bots, plus the "<name>bot/<version>" convention;
// not a bare "bot", which phone names such as "CUBOT" contain.
const BOT_PATTERN =
  /googlebot|google-inspectiontool|bingbot|yandex(?:bot|images)|baiduspider|duckduckbot|slurp|applebot|petalbot|facebookexternalhit|linkedinbot|twitterbot|telegrambot|slackbot|discordbot|whatsapp|skypeuripreview|[a-z](?:bot|crawler|spider)\/\d/i;

/**
 * Check if a user agent is a known crawler or link preview bot
 * @param {string} ua
 * @returns {boolean}
 */
function isBot(ua) {
  return BOT_PATTERN.test(ua);
}

/**
 * Check if a browser meets the minimum version for the viewer
 * @param {{name: string, version: number[]}} browser
 * @returns {boolean}
 */
function isVersionSupported(browser) {
  const minVersion = MIN_VERSIONS[browser.name];
  if (!minVersion) {
    return false;
  }
  const [major, minor] = browser.version;
  return (
    major > minVersion[0] || (major === minVersion[0] && minor >= minVersion[1])
  );
}

/**
 * Test that a Web Worker can actually be created (more reliable than just
 * checking that the constructor exists)
 * @param {Window} env
 * @returns {boolean}
 */
function testWebWorkerCapability(env) {
  try {
    const testScript = 'self.postMessage("test");';
    const blob = new env.Blob([testScript], { type: "application/javascript" });
    const url = env.URL.createObjectURL(blob);
    const worker = new env.Worker(url);

    // Clean up immediately
    worker.terminate();
    env.URL.revokeObjectURL(url);

    return true;
  } catch {
    return false;
  }
}

/**
 * Check whether this browser can run the pdf.js viewer
 * @param {Window} env the window (a stand-in in tests)
 * @returns {boolean}
 */
function detectPDFjsCapabilities(env = window) {
  if (
    !env.Worker ||
    !env.ArrayBuffer ||
    !env.Uint8Array ||
    !env.Promise ||
    !env.fetch ||
    !env.URL ||
    !env.Blob
  ) {
    return false;
  }

  const ua = env.navigator?.userAgent ?? "";
  if (isBot(ua) || !isVersionSupported(getBrowserInfo(ua))) {
    return false;
  }

  return testWebWorkerCapability(env);
}

export {
  MIN_VERSIONS,
  detectPDFjsCapabilities,
  getBrowserInfo,
  isBot,
  isVersionSupported,
};
