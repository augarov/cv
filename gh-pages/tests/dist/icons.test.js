import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";

import pngjs from "pngjs";

import {
  BASE,
  distPath,
  indexTags,
  linksByRel,
  manifest,
  manifestPath,
  metaContent,
  parseTags,
  readDist,
  resolveToDist,
  urlPathOf,
} from "./helpers.js";

const { PNG } = pngjs;

function readPng(relative) {
  return PNG.sync.read(readDist(relative, null));
}

function pngSize(relative) {
  const { width, height } = readPng(relative);
  return `${width}x${height}`;
}

/** Return the sizes an .ico holds, as "WxH" (a 0 byte means 256). */
function icoSizes(relative) {
  const ico = readDist(relative, null);
  assert.equal(ico.readUInt16LE(2), 1, "not an icon file");
  return Array.from({ length: ico.readUInt16LE(4) }, (_, i) => {
    const entry = 6 + 16 * i;
    return `${ico[entry] || 256}x${ico[entry + 1] || 256}`;
  });
}

function iconLinks(rel) {
  return linksByRel(indexTags, rel).map(({ attributes }) => ({
    sizes: attributes.sizes,
    file: resolveToDist(attributes.href, BASE),
  }));
}

const ICON_DIR = path.dirname(manifestPath);
const pngIcons = readdirSync(distPath(ICON_DIR)).filter((f) =>
  f.endsWith(".png"),
);

describe("icon links", () => {
  for (const { sizes, file } of [
    ...iconLinks("icon"),
    ...iconLinks("apple-touch-icon"),
  ]) {
    if (file.endsWith(".png")) {
      it(`${file} is ${sizes}`, () => {
        assert.equal(pngSize(file), sizes);
      });
    }
  }

  it("the apple-touch-icon is 180x180", () => {
    const [touchIcon] = iconLinks("apple-touch-icon");

    assert.equal(pngSize(touchIcon.file), "180x180");
  });

  it("the .ico holds 16, 32 and 48 px and the size its link names", () => {
    const icos = iconLinks("icon").filter(({ file }) => file.endsWith(".ico"));

    assert.equal(icos.length, 1);
    const held = icoSizes(icos[0].file);
    for (const size of ["16x16", "32x32", "48x48", icos[0].sizes]) {
      assert.ok(held.includes(size), `${size} not in ${held.join(", ")}`);
    }
  });

  it("the SVG has a viewBox matching its size, so it scales", () => {
    const svgs = iconLinks("icon").filter(({ file }) => file.endsWith(".svg"));

    assert.equal(svgs.length, 1);
    const svg = parseTags(readDist(svgs[0].file)).find((t) => t.name === "svg");
    const { width, height, viewbox } = svg.attributes;
    assert.equal(viewbox, `0 0 ${width} ${height}`);
  });
});

describe("manifest icons", () => {
  for (const icon of manifest.icons) {
    it(`${icon.src} (${icon.purpose}) is ${icon.sizes}`, () => {
      assert.equal(
        pngSize(resolveToDist(icon.src, urlPathOf(manifestPath))),
        icon.sizes,
      );
    });
  }
});

describe("PNG icons", () => {
  // iOS shows transparent pixels of the apple-touch-icon as black, and a
  // maskable icon must fill its whole square
  for (const name of pngIcons) {
    it(`${name} is opaque`, () => {
      const { data } = readPng(path.join(ICON_DIR, name));
      // pngjs decodes to RGBA
      const transparent = data.filter((_, i) => i % 4 === 3 && data[i] !== 255);

      assert.equal(transparent.length, 0);
    });
  }
});

describe("link preview image", () => {
  it("og:image's width and height match the image", () => {
    const [image] = metaContent(indexTags, "property", "og:image");
    const [width] = metaContent(indexTags, "property", "og:image:width");
    const [height] = metaContent(indexTags, "property", "og:image:height");

    assert.equal(
      pngSize(resolveToDist(new URL(image).pathname, BASE)),
      `${width}x${height}`,
    );
  });
});
