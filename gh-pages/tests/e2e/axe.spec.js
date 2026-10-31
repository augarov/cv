import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// WCAG 2.2 A and AA, with the rules of the earlier versions; wcag22aa has
// target-size (2.5.8: 24 px, or spaced so a 24 px circle around each target
// touches no other)
const WCAG_TAGS = [
  "wcag2a",
  "wcag2aa",
  "wcag21a",
  "wcag21aa",
  "wcag22a",
  "wcag22aa",
];

for (const colorScheme of ["light", "dark"]) {
  test(`the accessible page has no WCAG violations (${colorScheme})`, async ({
    page,
  }) => {
    await page.emulateMedia({ colorScheme });
    await page.goto("?accessibility=true");
    await expect(page.locator("#accessibleContainer")).toBeVisible();

    const { violations } = await new AxeBuilder({ page })
      .withTags(WCAG_TAGS)
      .analyze();
    expect(
      violations.map(({ id, nodes }) => ({
        id,
        targets: nodes.map((node) => node.target.join(" ")),
      })),
    ).toEqual([]);
  });
}
