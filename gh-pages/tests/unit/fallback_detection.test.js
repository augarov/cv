import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  MIN_VERSIONS,
  detectPDFjsCapabilities,
  getBrowserInfo,
  isBot,
  isVersionSupported,
} from "../../src/fallback_detection.js";

// Real user agent strings: [description, UA, engine, version, viewer?]
const USER_AGENTS = [
  // Chromium
  [
    "Chrome, Windows",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "chromium",
    [141, 0],
    true,
  ],
  [
    "Chrome, macOS",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "chromium",
    [141, 0],
    true,
  ],
  [
    "Chrome, Android",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
    "chromium",
    [141, 0],
    true,
  ],
  [
    "Edge, Windows",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
    "chromium",
    [141, 0],
    true,
  ],
  [
    "Opera, Windows",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0",
    "chromium",
    [140, 0],
    true,
  ],
  [
    "Samsung Internet, Android",
    "Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/28.0 Chrome/130.0.0.0 Mobile Safari/537.36",
    "chromium",
    [130, 0],
    true,
  ],
  [
    "Android webview (Telegram, LinkedIn in-app)",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Build/AP2A.240805.005; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.51 Mobile Safari/537.36",
    "chromium",
    [140, 0],
    true,
  ],
  [
    "Chrome 123 (minimum)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.58 Safari/537.36",
    "chromium",
    [123, 0],
    true,
  ],
  [
    "Chrome 122 (below)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36",
    "chromium",
    [122, 0],
    false,
  ],
  [
    "Chrome 109 (last on Windows 7)",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "chromium",
    [109, 0],
    false,
  ],
  [
    "Googlebot (evergreen Chromium; a bot, see isBot)",
    "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.122 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "chromium",
    [141, 0],
    true,
  ],
  // Firefox
  [
    "Firefox, Windows",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "firefox",
    [144, 0],
    true,
  ],
  [
    "Firefox, Android",
    "Mozilla/5.0 (Android 14; Mobile; rv:144.0) Gecko/144.0 Firefox/144.0",
    "firefox",
    [144, 0],
    true,
  ],
  [
    "Firefox 120 (minimum)",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "firefox",
    [120, 0],
    true,
  ],
  [
    "Firefox ESR 115 (below)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "firefox",
    [115, 0],
    false,
  ],
  // WebKit
  [
    "Safari, macOS",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Safari/605.1.15",
    "webkit",
    [26, 0],
    true,
  ],
  [
    "Safari 17.5 (minimum)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "webkit",
    [17, 5],
    true,
  ],
  [
    "Safari 17.4 (below, minor version counts)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "webkit",
    [17, 4],
    false,
  ],
  [
    "iPadOS Safari (desktop UA, no iPad token)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15",
    "webkit",
    [18, 6],
    true,
  ],
  [
    "Safari, iPhone",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1",
    "webkit",
    [18, 6],
    true,
  ],
  [
    "iPhone iOS 17.4 (below)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "webkit",
    [17, 4],
    false,
  ],
  [
    "iOS without a minor version",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "webkit",
    [18, 0],
    true,
  ],
  [
    "Chrome, iPhone (CriOS: WebKit of the iOS version)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/141.0.7390.96 Mobile/15E148 Safari/604.1",
    "webkit",
    [18, 6],
    true,
  ],
  [
    "Chrome, old iPhone (CriOS current, iOS 16.7)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/138.0.7204.156 Mobile/15E148 Safari/604.1",
    "webkit",
    [16, 7],
    false,
  ],
  [
    "Firefox, iPhone (FxiOS)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/144.0 Mobile/15E148 Safari/605.1.15",
    "webkit",
    [18, 6],
    true,
  ],
  [
    "Edge, iPad (EdgiOS)",
    "Mozilla/5.0 (iPad; CPU OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 EdgiOS/141.0.3537.71 Mobile/15E148 Safari/605.1.15",
    "webkit",
    [17, 6],
    true,
  ],
  [
    "Instagram in-app, iPhone (no Safari token)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 380.0.0.29.109 (iPhone15,3; iOS 18_5; en_GB; en-GB; scale=3.00; 1290x2796; 735253658)",
    "webkit",
    [18, 5],
    true,
  ],
  // Unknown: the accessible page
  ["curl", "curl/8.7.1", "unknown", [0, 0], false],
  ["empty user agent", "", "unknown", [0, 0], false],
  [
    "Bingbot (no browser token)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "unknown",
    [0, 0],
    false,
  ],
  [
    "Internet Explorer 11",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "unknown",
    [0, 0],
    false,
  ],
];

describe("getBrowserInfo / isVersionSupported", () => {
  for (const [description, ua, name, version, viewer] of USER_AGENTS) {
    it(`${description}: ${name} ${version.join(".")}, ${viewer ? "viewer" : "accessible page"}`, () => {
      const info = getBrowserInfo(ua);

      assert.deepEqual(info, { name, version });
      assert.equal(isVersionSupported(info), viewer);
    });
  }
});

// Crawlers and link preview fetchers: the accessible page
const BOTS = [
  "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.122 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
  "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
  "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.122 Mobile Safari/537.36 (compatible; Google-InspectionTool/1.0)",
  "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm) Chrome/141.0.7390.122 Safari/537.36",
  "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
  "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
  "DuckDuckBot/1.1; (+http://duckduckgo.com/duckduckbot.html)",
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)",
  "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
  "LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com)",
  "Twitterbot/1.0",
  "TelegramBot (like TwitterBot)",
  "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)",
  "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)",
  "WhatsApp/2.23.20.0",
  "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
  "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
];

// Browsers whose UA contains "bot" or similar without being a bot
const NOT_BOTS = [
  "Mozilla/5.0 (Linux; Android 10; CUBOT X30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
  "Mozilla/5.0 (Linux; Android 12; CUBOT_KINGKONG_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
  ...USER_AGENTS.filter(([description]) => !/bot/i.test(description)).map(
    ([, ua]) => ua,
  ),
];

describe("isBot", () => {
  for (const ua of BOTS) {
    it(`bot: ${ua}`, () => {
      assert.equal(isBot(ua), true);
      assert.equal(
        detectPDFjsCapabilities(fakeWindow({ navigator: { userAgent: ua } })),
        false,
      );
    });
  }

  for (const ua of NOT_BOTS) {
    it(`not a bot: ${ua || "(empty)"}`, () => {
      assert.equal(isBot(ua), false);
    });
  }
});

describe("MIN_VERSIONS", () => {
  it("covers native light-dark() support (custom.css, the theme switch)", () => {
    assert.deepEqual(MIN_VERSIONS, {
      chromium: [123, 0],
      firefox: [120, 0],
      webkit: [17, 5],
    });
  });

  it("a newer major with a smaller minor is supported", () => {
    assert.equal(
      isVersionSupported({ name: "webkit", version: [18, 0] }),
      true,
    );
  });
});

/** A stand-in window with the APIs the check needs; override to remove some. */
function fakeWindow(overrides = {}) {
  const revoked = [];
  class FakeWorker {
    constructor(url) {
      this.url = url;
    }
    terminate() {}
  }
  return {
    revoked,
    Worker: FakeWorker,
    ArrayBuffer,
    Uint8Array,
    Promise,
    fetch: () => {},
    Blob,
    URL: {
      createObjectURL: () => "blob:test",
      revokeObjectURL: (url) => revoked.push(url),
    },
    navigator: {
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
    },
    ...overrides,
  };
}

describe("detectPDFjsCapabilities", () => {
  it("a current browser with every API gets the viewer", () => {
    const env = fakeWindow();

    assert.equal(detectPDFjsCapabilities(env), true);
    // The test worker's object URL is released (not the worker object)
    assert.deepEqual(env.revoked, ["blob:test"]);
  });

  for (const api of [
    "Worker",
    "ArrayBuffer",
    "Uint8Array",
    "Promise",
    "fetch",
    "URL",
    "Blob",
  ]) {
    it(`without ${api}: the accessible page`, () => {
      assert.equal(
        detectPDFjsCapabilities(fakeWindow({ [api]: undefined })),
        false,
      );
    });
  }

  it("a Worker that throws (blocked by policy): the accessible page", () => {
    const Worker = class {
      constructor() {
        throw new Error("SecurityError");
      }
    };

    assert.equal(detectPDFjsCapabilities(fakeWindow({ Worker })), false);
  });

  it("an old browser with every API: the accessible page", () => {
    const navigator = {
      userAgent:
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    };

    assert.equal(detectPDFjsCapabilities(fakeWindow({ navigator })), false);
  });

  it("no navigator: the accessible page", () => {
    assert.equal(
      detectPDFjsCapabilities(fakeWindow({ navigator: undefined })),
      false,
    );
  });
});
