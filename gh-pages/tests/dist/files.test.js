import assert from "node:assert/strict";
import { lstatSync, readdirSync } from "node:fs";
import { describe, it } from "node:test";

import { distPath, isDistFile, manifest, readDist } from "./helpers.js";

const VIEWER_DIR = "pdfjs/web";

function filesIn(relative, extension) {
  return readdirSync(distPath(relative)).filter((f) => f.endsWith(extension));
}

describe("cv.pdf", () => {
  // The page builds the viewer's ?file= and the download links from base + "cv.pdf"
  it("is a PDF", () => {
    assert.equal(readDist("cv.pdf", "latin1").slice(0, 5), "%PDF-");
  });
});

describe("pdf.js", () => {
  it("the viewer page the site opens is there", () => {
    // main.js: `${base}pdfjs/web/viewer.html`
    assert.ok(isDistFile(`${VIEWER_DIR}/viewer.html`));
  });

  it("build/ is copied, not a symlink (Vite followed it into node_modules)", () => {
    assert.ok(lstatSync(distPath("pdfjs/build")).isDirectory());
  });

  it("the worker custom.js sets is there", () => {
    const customJs = readDist(`${VIEWER_DIR}/custom.js`);
    const [, workerSrc] =
      customJs.match(/setOption\(\s*options,\s*"workerSrc",\s*"([^"]+)"/) ?? [];

    assert.ok(workerSrc, "no workerSrc in custom.js");
    assert.ok(isDistFile(`${VIEWER_DIR}/${workerSrc}`), workerSrc);
  });

  // pdf.js's defaults for cMapUrl, standardFontDataUrl, wasmUrl and iccUrl
  for (const [dir, extension] of [
    ["cmaps", ".bcmap"],
    ["standard_fonts", ".pfb"],
    ["wasm", ".wasm"],
    ["iccs", ".icc"],
  ]) {
    it(`${dir}/ has ${extension} files`, () => {
      assert.ok(filesIn(`${VIEWER_DIR}/${dir}`, extension).length > 0);
    });
  }

  it("the locale files for en-US (the fallback) and the site's locale are there", () => {
    const locales = JSON.parse(readDist(`${VIEWER_DIR}/locale/locale.json`));
    // pdf.js looks locales up in lower case
    const wanted = [
      "en-us",
      ...(manifest.lang ? [manifest.lang.toLowerCase()] : []),
    ];

    for (const lang of wanted) {
      assert.ok(locales[lang], `${lang} not in locale.json`);
      assert.ok(
        isDistFile(`${VIEWER_DIR}/locale/${locales[lang]}`),
        locales[lang],
      );
    }
  });
});
