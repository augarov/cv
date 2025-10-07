import { detectPDFjsCapabilities } from "./fallback-detection.js";
import { isAccessibilityMode } from "./accessibility.js";

// Run the detection when the page loads
document.addEventListener("DOMContentLoaded", function () {
  const accessibilityModeEnabled = isAccessibilityMode();
  const isPdfjsCapable = detectPDFjsCapabilities();

  if (isPdfjsCapable && !accessibilityModeEnabled) {
    // Hide fallback, show PDF viewer
    document.getElementById("fallback-container").style.display = "none";
    document.getElementById("pdf-viewer-container").style.display = "block";
  }
  // If not capable, fallback remains visible (default state)
});
