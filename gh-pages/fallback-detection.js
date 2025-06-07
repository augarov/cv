/**
 * Enhanced PDF.js Capability Detection
 * Checks for basic APIs, browser versions, and known compatibility issues
 */
function detectPDFjsCapabilities() {
    // Basic feature detection (from original)
    if (!window.Worker ||
        !window.ArrayBuffer ||
        !window.Uint8Array ||
        !window.Promise ||
        !window.fetch ||
        !window.URL) {
        return false;
    }

    // Enhanced browser and version detection
    const browserInfo = getBrowserInfo();

    // Check against known minimum requirements
    if (!isVersionSupported(browserInfo)) {
        return false;
    }

    // Test Web Workers functionality (more reliable than just existence check)
    if (!testWebWorkerCapability()) {
        return false;
    }

    return true;
}

/**
 * Get browser information with version detection
 * Simplified to detect the three main rendering engines
 */
function getBrowserInfo() {
    const ua = navigator.userAgent;
    const browser = {
        name: 'unknown',
        version: 0
    };

    // Firefox detection (Gecko engine)
    const firefoxMatch = ua.match(/Firefox\/(\d+)/);
    if (firefoxMatch) {
        browser.name = 'firefox';
        browser.version = parseInt(firefoxMatch[1]);
        return browser;
    }

    // Safari detection (WebKit engine, but not Chromium-based)
    const safariMatch = ua.match(/Version\/(\d+).*Safari/);
    if (safariMatch && !ua.includes('Chrome')) {
        browser.name = 'safari';
        browser.version = parseInt(safariMatch[1]);
        return browser;
    }

    // Chromium-based browsers (Chrome, Edge, Opera, Brave, etc.)
    // This catches Chrome, modern Edge, Opera, and other Chromium-based browsers
    const chromeMatch = ua.match(/Chrome\/(\d+)/);
    if (chromeMatch) {
        browser.name = 'chromium';
        browser.version = parseInt(chromeMatch[1]);
        return browser;
    }

    return browser;
}

/**
 * Check if browser version meets minimum requirements
 * Based on official PDF.js compatibility requirements
 */
function isVersionSupported(browser) {
    const minVersions = {
        // Based on PDF.js official documentation (legacy build requirements)
        'chromium': 110, // Chrome 110+ covers Chrome, Edge, Opera, and other Chromium-based browsers
        'firefox': 78,   // Firefox ESR+
        'safari': 16,    // Safari 16.4+ (using 16 as safe minimum)
    };

    const minVersion = minVersions[browser.name] || 999;
    return browser.version >= minVersion;
}

/**
 * Test Web Worker capability more thoroughly
 */
function testWebWorkerCapability() {
    try {
        // Test if we can create a simple web worker
        const testScript = 'self.postMessage("test");';
        const blob = new Blob([testScript], { type: 'application/javascript' });
        const worker = new Worker(URL.createObjectURL(blob));

        // Clean up immediately
        worker.terminate();
        URL.revokeObjectURL(worker);

        return true;
    } catch (e) {
        return false;
    }
}

// Run the detection when the page loads
document.addEventListener('DOMContentLoaded', function () {
    const isCapable = detectPDFjsCapabilities();

    if (isCapable) {
        // Hide fallback, show PDF viewer
        document.getElementById('fallback-container').style.display = 'none';
        document.getElementById('pdf-viewer-container').style.display = 'block';
    }
    // If not capable, fallback remains visible (default state)
});