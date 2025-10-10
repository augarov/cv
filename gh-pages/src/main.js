import { detectPDFjsCapabilities } from "./fallback-detection.js";
import { isAccessibilityMode } from "./accessibility.js";

function resolvePDFViewer(base, cvUrl) {
  let iframeSrc = `${base}pdfjs/web/viewer.html?file=${encodeURIComponent(cvUrl)}`;

  const accessibilityModeUrl = encodeURIComponent(`${base}?accessibility=true`);
  iframeSrc += `&accessibilityModeUrl=${accessibilityModeUrl}`;

  const sourceUrl = encodeURIComponent("https://github.com/augarov/cv");
  iframeSrc += `&sourceUrl=${sourceUrl}`;

  const locale = encodeURIComponent("en-GB");
  iframeSrc += `&locale=${locale}`;

  document.getElementById("pdfViewerIframe").src = iframeSrc;
}

function resolveDownloadButtonLinks(cvUrl) {
  document.getElementById("cvDownloadButton").href = cvUrl;
  document.getElementById("cvOpenInNewTabButton").href = cvUrl;
}

function resolveElements() {
  const base = import.meta.env.BASE_URL;
  const cvUrl = base + "cv.pdf";
  resolvePDFViewer(base, cvUrl);
  resolveDownloadButtonLinks(cvUrl);
}

function testAndShowPDFViewer() {
  const accessibilityModeEnabled = isAccessibilityMode();
  const isPdfjsCapable = detectPDFjsCapabilities();

  if (isPdfjsCapable && !accessibilityModeEnabled) {
    // Hide fallback, show PDF viewer
    document.getElementById("accessibleContainer").style.display = "none";
    document.getElementById("pdfViewerContainer").style.display = "block";
    return true;
  }

  // If not capable, fallback remains visible (default state)
  return false;
}

function main() {
  resolveElements();

  document.addEventListener("DOMContentLoaded", testAndShowPDFViewer);
}

main();
