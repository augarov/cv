document.addEventListener('DOMContentLoaded', () => {
    const userAgent = navigator.userAgent;

    const isUnsupported =
        userAgent.includes('Safari') && // Safari is unsupported
        !userAgent.includes('Chrome') &&
        !userAgent.includes('Chromium') &&
        !userAgent.includes('Edg');

    if (isUnsupported) {
        // Redirect directly to pdf
        window.location.href = './cv.pdf';
    }
});