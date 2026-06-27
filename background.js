// 1. Dynamic Canvas Generator for the Psi (Ψ) Icon
chrome.runtime.onInstalled.addListener(() => {
    createDynamicPsiIcon();
});

chrome.runtime.onStartup.addListener(() => {
    createDynamicPsiIcon();
});

function createDynamicPsiIcon() {
    const canvas16 = new OffscreenCanvas(16, 16);
    const ctx16 = canvas16.getContext('2d');
    ctx16.fillStyle = '#3B82F6';
    ctx16.font = 'bold 14px "Segoe UI", Arial';
    ctx16.textAlign = 'center';
    ctx16.textBaseline = 'middle';
    ctx16.fillText('Ψ', 8, 8);

    const canvas48 = new OffscreenCanvas(48, 48);
    const ctx48 = canvas48.getContext('2d');
    ctx48.fillStyle = '#8B5CF6';
    ctx48.font = 'bold 42px "Segoe UI", Arial';
    ctx48.textAlign = 'center';
    ctx48.textBaseline = 'middle';
    ctx48.fillText('Ψ', 24, 24);

    chrome.action.setIcon({
        imageData: {
            "16": ctx16.getImageData(0, 0, 16, 16),
            "48": ctx48.getImageData(0, 0, 48, 48)
        }
    });
}

// 2. Centralized Listener for Handling Secure Tab Closure Commands
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "closeCurrentTab" && message.tabId) {
        chrome.tabs.remove(message.tabId, () => {
            if (chrome.runtime.lastError) {
                // Emergency fail-safe fallback using sender context if native tabId removal is restricted
                if (sender.tab && sender.tab.id) {
                    chrome.tabs.remove(sender.tab.id);
                }
            }
        });
        sendResponse({ status: "success", detail: "Tab extraction completed" });
    }
    return true; // Keeps the messaging channel open for asynchronous responses
});