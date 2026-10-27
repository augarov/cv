import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { isAccessibilityMode } from "../../src/accessibility.js";

describe("isAccessibilityMode", () => {
  for (const name of ["accessibility", "a11y"]) {
    for (const value of ["true", "1", "yes", "on"]) {
      it(`?${name}=${value}: on`, () => {
        assert.equal(isAccessibilityMode(`?${name}=${value}`), true);
      });
    }

    for (const value of ["false", "0", "no", "off", "", "TRUE", "maybe"]) {
      it(`?${name}=${value}: off`, () => {
        assert.equal(isAccessibilityMode(`?${name}=${value}`), false);
      });
    }

    it(`?${name} without a value: off`, () => {
      assert.equal(isAccessibilityMode(`?${name}`), false);
    });
  }

  it("no query string: off", () => {
    assert.equal(isAccessibilityMode(""), false);
  });

  it("other parameters only: off", () => {
    assert.equal(isAccessibilityMode("?utm_source=linkedin&lang=en"), false);
  });

  it("among other parameters: on", () => {
    assert.equal(isAccessibilityMode("?utm_source=linkedin&a11y=1"), true);
  });

  it("repeated parameter: the first value counts", () => {
    assert.equal(isAccessibilityMode("?accessibility=1&accessibility=0"), true);
    assert.equal(
      isAccessibilityMode("?accessibility=0&accessibility=1"),
      false,
    );
  });

  it("either parameter is enough", () => {
    assert.equal(isAccessibilityMode("?accessibility=0&a11y=1"), true);
  });

  it("percent-encoded value", () => {
    assert.equal(isAccessibilityMode("?a11y=%74rue"), true);
  });
});
