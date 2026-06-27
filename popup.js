document.addEventListener('DOMContentLoaded', function() {
    const archiveBtn = document.getElementById('archiveBtn');
    const popupSearch = document.getElementById('recallInput'); // Matches recallInput ID
    const resultsContainer = document.getElementById('popupResults');

    // 1. Core Logic: Archive and Close current tab
    if (archiveBtn) {
        archiveBtn.addEventListener('click', async () => {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab) return;

            const tabId = tab.id;
            const tabUrl = tab.url;
            const tabTitle = tab.title || "Untitled Tab";

            archiveBtn.innerText = "Saving...";
            archiveBtn.disabled = true;

            try {
                // Send payload data directly to backend FastAPI
                const response = await fetch('http://127.0.0.1:8000/archive-tab', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: tabUrl, title: tabTitle })
                });
                await response.json();

                // Order structural closure execution
                chrome.runtime.sendMessage({ action: "closeCurrentTab", tabId: tabId });
            } catch (error) {
                console.error("Pipeline isolation failure. Triggering fallback kill:", error);
                chrome.runtime.sendMessage({ action: "closeCurrentTab", tabId: tabId });
            }
        });
    }

    // 2. Core Fix: Added Missing Recall & Retrieval Filter Implementation
    if (popupSearch && resultsContainer) {
        popupSearch.addEventListener('input', async () => {
            const query = popupSearch.value.trim();
            
            if (!query) {
                resultsContainer.innerHTML = '';
                return;
            }

            try {
                const response = await fetch(`http://127.0.0.1:8000/search-tabs?query=${encodeURIComponent(query)}`);
                const result = await response.json();
                resultsContainer.innerHTML = '';

                if (result.data && result.data.length > 0) {
                    result.data.slice().reverse().forEach(item => {
                        const itemDiv = document.createElement('div');
                        itemDiv.className = 'result-item';

                        const link = document.createElement('a');
                        link.href = item.url;
                        link.target = '_blank';
                        link.className = 'result-title';
                        link.innerText = item.title;

                        const summary = document.createElement('p');
                        summary.className = 'result-summary';
                        summary.innerHTML = `<b>AI Summary:</b> ${item.summary}`;

                        itemDiv.appendChild(link);
                        itemDiv.appendChild(summary);
                        resultsContainer.appendChild(itemDiv);
                    });
                } else {
                    resultsContainer.innerHTML = '<div class="no-data">No matching contexts found.</div>';
                }
            } catch (e) {
                resultsContainer.innerHTML = '<div class="no-data" style="color:#F87171;">Backend offline (Port 8000)</div>';
            }
        });
    }
});