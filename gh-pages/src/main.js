import { detectPDFjsCapabilities } from "./fallback_detection.js";
import { isAccessibilityMode } from "./accessibility.js";
import { getTemplateParams } from "./template_params.js";

function resolvePDFViewer(base, cvUrl) {
  const templateParams = getTemplateParams();

  let iframeSrc = `${base}pdfjs/web/viewer.html?file=${encodeURIComponent(cvUrl)}`;

  const accessibilityModeUrl = encodeURIComponent(`${base}?accessibility=true`);
  iframeSrc += `&accessibilityModeUrl=${accessibilityModeUrl}`;

  if (templateParams.sourceUrl) {
    const sourceUrl = encodeURIComponent(templateParams.sourceUrl);
    iframeSrc += `&sourceUrl=${sourceUrl}`;
  }

  if (templateParams.locale) {
    const locale = encodeURIComponent(templateParams.locale);
    iframeSrc += `&locale=${locale}`;
  }

  let pdfViewerIframe = document.getElementById("pdfViewerIframe");
  if (pdfViewerIframe) {
    pdfViewerIframe.src = iframeSrc;
  }
}

function resolveDownloadButtonLinks(cvUrl) {
  let cvDownloadButton = document.getElementById("cvDownloadButton");
  if (cvDownloadButton) {
    cvDownloadButton.href = cvUrl;
  }
  let cvOpenInNewTabButton = document.getElementById("cvOpenInNewTabButton");
  if (cvOpenInNewTabButton) {
    cvOpenInNewTabButton.href = cvUrl;
  }
}

function resolveElements() {
  const base = import.meta.env.BASE_URL;
  const cvUrl = base + "cv.pdf";
  resolvePDFViewer(base, cvUrl);
  resolveDownloadButtonLinks(cvUrl);
}

function testAndShowPDFViewer() {
  let pdfViewerContainer = document.getElementById("pdfViewerContainer");
  let accessibleContainer = document.getElementById("accessibleContainer");
  if (!pdfViewerContainer || !accessibleContainer) {
    return false;
  }

  const accessibilityModeEnabled = isAccessibilityMode();
  const isPdfjsCapable = detectPDFjsCapabilities();

  if (!isPdfjsCapable) {
    // If not capable, accessible container remains visible (default state)
    return false;
  }

  if (accessibilityModeEnabled) {
    // Show switch to pdf viewer button
    let cvOpenInPdfViewerButton = document.getElementById(
      "cvOpenInPdfViewerButton",
    );
    if (cvOpenInPdfViewerButton) {
      cvOpenInPdfViewerButton.style.display = "block";
    }
    // pdf viewer container remains hidden
    return false;
  }

  // Enable PDF viewer mode - add class for full-screen styling
  document.body.classList.add("pdf-viewer-mode");

  // Hide accessible container, show PDF viewer
  accessibleContainer.style.display = "none";
  pdfViewerContainer.style.display = "block";
  return true;
}

function main() {
  resolveElements();

  document.addEventListener("DOMContentLoaded", testAndShowPDFViewer);
}

main();
