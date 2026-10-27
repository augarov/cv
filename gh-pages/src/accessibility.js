/**
 * Check if the accessibility mode is enabled
 * @param {string} search the query string, e.g. "?accessibility=true"
 * @returns {boolean}
 */
function isAccessibilityMode(search = window.location.search) {
  // Check if the URL contains the accessibility mode parameter
  const urlParams = new URLSearchParams(search);
  const affirmativeValues = ["true", "1", "yes", "on"];
  return (
    affirmativeValues.includes(urlParams.get("accessibility")) ||
    affirmativeValues.includes(urlParams.get("a11y"))
  );
}

export { isAccessibilityMode };
