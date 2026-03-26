// JARVIS Chrome Extension - Background Worker (Linkjob Style)

const BACKEND_URL = "http://localhost:8000/api/v1/meetings";
const WS_URL = "ws://localhost:8000/api/v1/streaming/ws/audio/0"; // 0 as temp meeting ID
let socket = null;
let chunkQueue = [];

// 1. WebSocket Management
function getSocket() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return socket;

    console.log("[JARVIS] Opening backend WebSocket...");
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
        console.log("[JARVIS] WebSocket connected successfully!");
        // Flush queue
        while (chunkQueue.length > 0) {
            const chunk = chunkQueue.shift();
            socket.send(chunk);
        }
        console.log("[JARVIS] Flushed pending chunks.");
    };
    socket.onerror = (err) => console.error("[JARVIS] WebSocket ERROR:", err);
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("[JARVIS] AI Message:", data);

        // Relay to all Meet tabs
        chrome.tabs.query({ url: "https://meet.google.com/*" }, (tabs) => {
            tabs.forEach(tab => {
                chrome.tabs.sendMessage(tab.id, {
                    action: "updateStatus",
                    text: data.text,
                    active: true
                }).catch(e => { });
            });
        });
    };
    socket.onclose = () => {
        console.log("[JARVIS] WebSocket closed, retrying in 3s...");
        setTimeout(getSocket, 3000);
    };
    return socket;
}

// 2. Listen for messages from Content Script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "audio-chunk") {
        const ws = getSocket();

        // Convert and handle
        fetch(request.data)
            .then(res => res.arrayBuffer())
            .then(buffer => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(buffer);
                } else {
                    console.log("[JARVIS] Socket not ready, queuing chunk...");
                    chunkQueue.push(buffer);
                    if (chunkQueue.length > 50) chunkQueue.shift(); // Max 50 chunks
                }
            });
    } else if (request.type === "get-summary") {
        console.log("[JARVIS] Summary requested...");
        // In a real scenario, this would call the backend
        // For now, we return a smart-looking mock summary
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: "displaySummary",
                text: "The discussion currently revolves around the Q3 roadmap. Key points: 1. Deploying the new API by Friday. 2. Finalizing the UI/UX design for the dashboard. 3. Addressing the latency issues in the transcription service."
            });
        });
    } else if (request.action === "userJoined") {
        console.log("[JARVIS] User joined meeting:", request.url);
        // We could still do auto-join for the bot here if needed
    }
});

// 3. Meet Detection (Keep only for status updates)
chrome.webNavigation.onCompleted.addListener((details) => {
    if (details.frameId === 0 && details.url.includes("meet.google.com/")) {
        console.log("[JARVIS] Meeting page loaded.");
    }
}, { url: [{ hostContains: "meet.google.com" }] });

function extractMeetingCode(urlStr) {
    try {
        const url = new URL(urlStr);
        return url.pathname.substring(1).split('?')[0];
    } catch (e) { return null; }
}
