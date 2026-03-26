// JARVIS Audio Capture - Offscreen Script
// This script runs in an offscreen document to capture audio in MV3

const BACKEND_WS_URL = "ws://localhost:8000/api/v1/streaming/ws/audio";

chrome.runtime.onMessage.addListener(async (message) => {
    if (message.target !== 'offscreen') return;

    if (message.type === 'start-capture') {
        startCapture(message.data);
    } else if (message.type === 'stop-capture') {
        stopCapture();
    }
});

let mediaRecorder;
let socket;

async function startCapture(streamId) {
    console.log("[JARVIS] Starting audio capture with stream ID:", streamId);

    try {
        // Report progress
        chrome.runtime.sendMessage({
            type: 'transcript-update',
            target: 'background',
            data: { text: "Getting Audio...", active: true }
        });

        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                mandatory: {
                    chromeMediaSource: 'desktop',
                    chromeMediaSourceId: streamId
                }
            },
            video: {
                mandatory: {
                    chromeMediaSource: 'desktop',
                    chromeMediaSourceId: streamId
                }
            }
        });

        // Report progress
        chrome.runtime.sendMessage({
            type: 'transcript-update',
            target: 'background',
            data: { text: "Audio Got. Connecting...", active: true }
        });

        // Continue to play the audio locally so the user can still hear it
        const audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(audioContext.destination);

        // Setup WebSocket
        socket = new WebSocket(`${BACKEND_WS_URL}/0`); // Use 0 as temporary meeting ID

        socket.onopen = () => {
            console.log("[JARVIS] WebSocket connected to backend");

            // Report success
            chrome.runtime.sendMessage({
                type: 'transcript-update',
                target: 'background',
                data: { text: "WS Connected!", active: true }
            });

            // Setup MediaRecorder
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                    socket.send(event.data);
                }
            };

            mediaRecorder.start(1000); // Send chunks every 1 second
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("[JARVIS] Received from backend:", data);

            // Relay to background script
            chrome.runtime.sendMessage({
                type: 'transcript-update',
                target: 'background',
                data: data
            });
        };

        socket.onclose = () => {
            console.log("[JARVIS] WebSocket closed");
            chrome.runtime.sendMessage({
                type: 'transcript-update',
                target: 'background',
                data: { text: "Stealth Disconnected", active: false }
            });
        };

        socket.onerror = (err) => {
            console.error("[JARVIS] WebSocket error:", err);
            chrome.runtime.sendMessage({
                type: 'transcript-update',
                target: 'background',
                data: { text: "Connection Error (Check Backend)", active: false }
            });
        };

    } catch (err) {
        console.error("[JARVIS] Failed to capture audio:", err);
        let errorMsg = "Capture Failed";

        if (err.name === 'NotAllowedError' || err.message.includes("permission")) {
            errorMsg = "Perms Denied (Allow Share)";
        } else if (err.name === 'NotFoundError') {
            errorMsg = "No Audio Found";
        } else {
            // Show more of the error message to debug
            const detailedMsg = err.message ? `${err.name}: ${err.message}` : err.name;
            errorMsg = detailedMsg.length < 50 ? detailedMsg : detailedMsg.substring(0, 45) + "...";
        }

        chrome.runtime.sendMessage({
            type: 'transcript-update',
            target: 'background',
            data: { text: `Err: ${errorMsg}`, active: false }
        });
    }
}

function stopCapture() {
    if (mediaRecorder) mediaRecorder.stop();
    if (socket) socket.close();
    console.log("[JARVIS] Audio capture stopped");
}
