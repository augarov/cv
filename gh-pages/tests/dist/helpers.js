// Reading the built site in dist/ (layer 3a): files from disk, no server.
// Expected values come from the built files, not from one person's CV.
import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

import viteConfig from "../../vite.config.js";

const DIST = path.resolve(import.meta.dirname, "../../dist");

if (!existsSync(path.join(DIST, "index.html"))) {
  throw new Error(`${DIST} has no build: run \`make build-website\` first`);
}

// The path the site is served under (Vite's base, "/cv/")
const BASE = viteConfig.base;

// Origin used to resolve site paths; never fetched
const ORIGIN = "https://site.invalid";

function distPath(relative) {
  return path.join(DIST, relative);
}

function readDist(relative, encoding = "utf-8") {
  return readFileSync(distPath(relative), encoding);
}

function isDistFile(relative) {
  return (
    existsSync(distPath(relative)) && statSync(distPath(relative)).isFile()
  );
}

const ENTITIES = {
  amp: "&",
  lt: "<",
  gt: ">",
  quot: '"',
  apos: "'",
  "#39": "'",
};

function decodeEntities(value) {
  return value.replace(
    /&(amp|lt|gt|quot|apos|#39);/g,
    (_, name) => ENTITIES[name],
  );
}

const TAG = /<([a-zA-Z][\w-]*)(\s[^>]*?)?\/?>/g;
const ATTRIBUTE =
  /([^\s"'=<>/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;

/**
 * Return the start tags of an HTML page as [{ name, attributes }].
 *
 * A regular expression is enough for our pages (Vite's minified output and
 * pdf.js's viewer.html); a "<tag" inside an inline script would be misread.
 */
function parseTags(html) {
  return [...html.replace(/<!--[\s\S]*?-->/g, "").matchAll(TAG)].map(
    ([, name, rest = ""]) => ({
      name: name.toLowerCase(),
      attributes: Object.fromEntries(
        [...rest.matchAll(ATTRIBUTE)].map(([, key, a, b, c]) => [
          key.toLowerCase(),
          decodeEntities(a ?? b ?? c ?? ""),
        ]),
      ),
    }),
  );
}

function metaContent(tags, key, value) {
  return tags
    .filter((t) => t.name === "meta" && t.attributes[key] === value)
    .map((t) => t.attributes.content);
}

function linksByRel(tags, rel) {
  return tags.filter(
    (t) =>
      t.name === "link" && (t.attributes.rel ?? "").split(/\s+/).includes(rel),
  );
}

/** Whether a reference points into the site (no scheme, not protocol-relative). */
function isLocalReference(reference) {
  return (
    reference !== "" &&
    !/^[a-z][a-z\d+.-]*:/i.test(reference) &&
    !reference.startsWith("//") &&
    !reference.startsWith("#") &&
    !reference.startsWith("?")
  );
}

/**
 * Return the file in dist/ that a reference from a page at `pageUrlPath`
 * (e.g. "/cv/pdfjs/web/viewer.html") loads, or null when it leaves the base.
 */
function resolveToDist(reference, pageUrlPath) {
  const url = new URL(reference, ORIGIN + pageUrlPath);
  if (url.origin !== ORIGIN || !url.pathname.startsWith(BASE)) {
    return null;
  }
  const relative = decodeURIComponent(url.pathname.slice(BASE.length));
  return relative === "" || relative.endsWith("/")
    ? relative + "index.html"
    : relative;
}

/** The URL path of a file in dist/, as the browser requests it. */
function urlPathOf(relative) {
  return BASE + relative;
}

const indexTags = parseTags(readDist("index.html"));

const manifestPath = resolveToDist(
  linksByRel(indexTags, "manifest")[0].attributes.href,
  BASE,
);
const manifest = JSON.parse(readDist(manifestPath));

// The site's own URL from the page: the canonical link
const siteUrl = linksByRel(indexTags, "canonical")[0].attributes.href;

export {
  BASE,
  DIST,
  distPath,
  indexTags,
  isDistFile,
  isLocalReference,
  linksByRel,
  manifest,
  manifestPath,
  metaContent,
  parseTags,
  readDist,
  resolveToDist,
  siteUrl,
  urlPathOf,
};
