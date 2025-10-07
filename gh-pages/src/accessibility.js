/**
 * Check if the accessibility mode is enabled
 * @returns {boolean}
 */
function isAccessibilityMode() {
  // Check if the URL contains the accessibility mode parameter
  const urlParams = new URLSearchParams(window.location.search);
  const affirmativeValues = ["true", "1", "yes", "on"];
  return (
    affirmativeValues.includes(urlParams.get("accessibility")) ||
    affirmativeValues.includes(urlParams.get("a11y"))
  );
}

export { isAccessibilityMode };
