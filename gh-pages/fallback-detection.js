/**
 * PDF.js Capability Detection
 * Shows PDF viewer only if required capabilities are available
 * Otherwise keeps the default fallback interface visible
 */

function detectPDFJSSupport() {
    // Check essential features for PDF.js
    const hasWebWorkers = !!window.Worker;
    const hasArrayBuffer = !!window.ArrayBuffer;
    const hasTypedArrays = !!window.Uint8Array;
    const hasPromises = !!window.Promise;
    const hasFetch = !!window.fetch;

    const isSupported = hasWebWorkers && hasArrayBuffer && hasTypedArrays && hasPromises && hasFetch;

    if (isSupported) {
        // Hide fallback and show PDF viewer
        showPDFViewer();
    }
    // If not supported, fallback remains visible by default
}

function showPDFViewer() {
    // Hide the fallback interface
    const fallbackContainer = document.getElementById('fallback-container');
    if (fallbackContainer) {
        fallbackContainer.style.display = 'none';
    }

    // Show the PDF viewer
    const pdfContainer = document.getElementById('pdf-viewer-container');
    if (pdfContainer) {
        pdfContainer.style.display = 'block';
    }
}

// Run detection when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', detectPDFJSSupport);
} else {
    detectPDFJSSupport();
}