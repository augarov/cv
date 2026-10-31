/**
 * Minifies and prunes the pdf.js viewer in the build output. Vite copies
 * public/ as is, so without this the viewer of the pdf.js release
 * (public/pdfjs/) ships unminified, with files it never loads.
 */
import { readdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";

import { minify as minifyHtml } from "html-minifier-terser";
import { transform as transformCss } from "lightningcss";
import { minify as minifyJs } from "terser";

import { getTemplateParams } from "../src/template_params.js";

// Never loaded: source maps, the unminified library and worker (viewer.html
// and custom.js load the .min.mjs ones), the scripting sandbox (custom.js
// turns scripting off), the debugger (pdfBugEnabled is off) and the types
const UNUSED = [
  /\.map$/,
  /^build\/pdf(\.worker)?\.mjs$/,
  /^build\/pdf\.sandbox\./,
  /^build\/pdf\.d\.mts$/,
  /^web\/debugger\./,
];

// pdf.js's own options for its minified builds: some code relies on names.
// The license header and the version comment stay.
const TERSER_OPTIONS = {
  keep_classnames: true,
  keep_fnames: true,
  format: { comments: /@licstart|@licend|pdfjsVersion|pdfjsBuild/ },
};

async function minifyScript(file, module) {
  const { code } = await minifyJs(await readFile(file, "utf8"), {
    ...TERSER_OPTIONS,
    module,
  });
  await writeFile(file, code);
}

// No targets: lightningcss then keeps light-dark(), which the theme switch
// needs (its lowered form ignores color-scheme set from JavaScript)
async function minifyStylesheet(file) {
  const { code } = transformCss({
    filename: file,
    code: await readFile(file),
    minify: true,
  });
  await writeFile(file, code);
}

async function minifyPage(file) {
  const html = await minifyHtml(await readFile(file, "utf8"), {
    removeComments: true,
    collapseWhitespace: true,
  });
  await writeFile(file, html);
}

// Keep en-US (pdf.js's fallback) and the languages pdf.js tries for the
// site's locale (custom.js's ?locale=): the full tag and its language
async function pruneLocales(localeDir) {
  const indexFile = path.join(localeDir, "locale.json");
  const locales = JSON.parse(await readFile(indexFile, "utf8"));
  const lang = getTemplateParams().locale?.toLowerCase();
  const wanted = new Set(["en-us", lang, lang?.split("-")[0]]);

  const kept = Object.fromEntries(
    Object.entries(locales).filter(([key]) => wanted.has(key)),
  );
  const keptDirs = new Set(Object.values(kept).map((p) => path.dirname(p)));
  for (const entry of await readdir(localeDir, { withFileTypes: true })) {
    if (entry.isDirectory() && !keptDirs.has(entry.name)) {
      await rm(path.join(localeDir, entry.name), { recursive: true });
    }
  }
  await writeFile(indexFile, JSON.stringify(kept));
}

export default function pdfjsViewer() {
  let viewerDir;

  return {
    name: "pdfjs-viewer",
    apply: "build",
    configResolved(config) {
      viewerDir = path.resolve(config.root, config.build.outDir, "pdfjs");
    },
    async closeBundle() {
      const files = await readdir(viewerDir, { recursive: true });
      for (const file of files.filter((f) => UNUSED.some((r) => r.test(f)))) {
        await rm(path.join(viewerDir, file));
      }

      const web = (file) => path.join(viewerDir, "web", file);
      await minifyScript(web("viewer.mjs"), true);
      await minifyScript(web("custom.js"), false);
      await minifyStylesheet(web("viewer.css"));
      await minifyStylesheet(web("custom.css"));
      await minifyPage(web("viewer.html"));
      await pruneLocales(web("locale"));
    },
  };
}
