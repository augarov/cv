import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import { describe, it } from "node:test";

import {
  BASE,
  distPath,
  indexTags,
  isDistFile,
  isLocalReference,
  manifest,
  manifestPath,
  metaContent,
  parseTags,
  readDist,
  resolveToDist,
  siteUrl,
  urlPathOf,
} from "./helpers.js";

/** Return the local references of a page or stylesheet that aren't files. */
function missingFiles(references, fromFile) {
  return references.filter(isLocalReference).filter((reference) => {
    const file = resolveToDist(reference, urlPathOf(fromFile));
    return file === null || !isDistFile(file);
  });
}

function pageReferences(tags) {
  return tags.flatMap((t) =>
    ["href", "src"]
      .filter((a) => a in t.attributes)
      .map((a) => t.attributes[a]),
  );
}

function cssReferences(css) {
  return [...css.matchAll(/url\(\s*(["']?)(.*?)\1\s*\)/g)].map(
    ([, , url]) => url,
  );
}

describe("site URL", () => {
  it("the canonical URL's path is Vite's base", () => {
    assert.equal(new URL(siteUrl).pathname, BASE);
  });
});

describe("pages", () => {
  // Vite rewrites a root-relative path to the base only when the file exists:
  // a link to a missing file stays without the base and fails here
  it("every local href / src in index.html is a file in dist/", () => {
    const references = pageReferences(indexTags).filter(isLocalReference);

    assert.ok(references.length > 0);
    assert.deepEqual(missingFiles(references, "index.html"), []);
  });

  it("every local href / src in the viewer is a file in dist/", () => {
    const page = "pdfjs/web/viewer.html";
    const references = pageReferences(parseTags(readDist(page)));

    assert.ok(references.filter(isLocalReference).length > 0);
    assert.deepEqual(missingFiles(references, page), []);
  });
});

describe("stylesheets", () => {
  const stylesheets = [
    ...readdirSync(distPath("assets"))
      .filter((f) => f.endsWith(".css"))
      .map((f) => `assets/${f}`),
    ...readdirSync(distPath("pdfjs/web"))
      .filter((f) => f.endsWith(".css"))
      .map((f) => `pdfjs/web/${f}`),
  ];

  for (const stylesheet of stylesheets) {
    it(`every url() in ${stylesheet} is a file in dist/`, () => {
      const references = cssReferences(readDist(stylesheet));

      assert.deepEqual(missingFiles(references, stylesheet), []);
    });
  }
});

describe("manifest", () => {
  it("every icon is a file in dist/", () => {
    const sources = manifest.icons.map((icon) => icon.src);

    assert.ok(sources.length > 0);
    assert.deepEqual(missingFiles(sources, manifestPath), []);
  });

  it("id, start_url and scope are the base, and start_url is the page", () => {
    for (const key of ["id", "start_url", "scope"]) {
      assert.equal(new URL(manifest[key], siteUrl).pathname, BASE, key);
    }
    assert.equal(
      resolveToDist(manifest.start_url, urlPathOf(manifestPath)),
      "index.html",
    );
  });
});

describe("link preview image", () => {
  it("og:image is an absolute URL to a file of the site", () => {
    const [image] = metaContent(indexTags, "property", "og:image");

    assert.ok(image.startsWith(siteUrl), image);
    assert.ok(isDistFile(resolveToDist(new URL(image).pathname, BASE)), image);
  });
});

describe("sitemap", () => {
  const sitemap = readDist("sitemap.xml");
  const locs = [...sitemap.matchAll(/<loc>\s*(.*?)\s*<\/loc>/g)].map(
    ([, loc]) => loc,
  );

  it("lists the page", () => {
    assert.ok(locs.includes(siteUrl), locs.join(", "));
  });

  it("every <loc> under the site is a file in dist/", () => {
    const missing = locs
      .filter((loc) => loc.startsWith(siteUrl))
      .filter((loc) => !isDistFile(resolveToDist(new URL(loc).pathname, BASE)));

    assert.ok(locs.length > 0);
    assert.deepEqual(missing, []);
  });
});
