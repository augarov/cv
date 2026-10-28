import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { HtmlValidate } from "html-validate";

import { distPath } from "./helpers.js";

describe("index.html", () => {
  // The page is generated from a template (stage 1) and minified by Vite;
  // this is the only check of what gets deployed. Rules: .htmlvalidate.json
  it("is valid HTML", async () => {
    const report = await new HtmlValidate().validateFile(
      distPath("index.html"),
    );
    const messages = report.results.flatMap((result) =>
      result.messages.map(
        (m) => `${m.line}:${m.column} ${m.ruleId}: ${m.message}`,
      ),
    );

    assert.deepEqual(messages, []);
  });
});
