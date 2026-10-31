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
    // Minified: the options argument is renamed
    const customJs = readDist(`${VIEWER_DIR}/custom.js`);
    const [, workerSrc] =
      customJs.match(/setOption\(\s*\w+,\s*"workerSrc",\s*"([^"]+)"/) ?? [];

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

  // vite-plugins/pdfjs-viewer.js
  it("files the viewer never loads are left out", () => {
    const files = readdirSync(distPath("pdfjs"), { recursive: true });
    const unused = files.filter((f) =>
      /\.map$|^build\/pdf(\.worker)?\.mjs$|sandbox|debugger|\.d\.mts$/.test(f),
    );

    assert.deepEqual(unused, []);
  });

  it("only en-US and the site's locale are left in locale.json", () => {
    const locales = JSON.parse(readDist(`${VIEWER_DIR}/locale/locale.json`));

    assert.ok(Object.keys(locales).length <= 3, Object.keys(locales).join());
  });

  it("viewer.mjs is minified and keeps its license and version", () => {
    const viewer = readDist(`${VIEWER_DIR}/viewer.mjs`);

    assert.ok(viewer.split("\n").length < 100);
    assert.match(viewer, /@licstart/);
    assert.match(viewer, /pdfjsVersion = \d/);
  });

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
