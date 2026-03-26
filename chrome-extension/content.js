// JARVIS Premium Content Script
// Built Linkjob AI style for stability and premium UX

console.log("[JARVIS] Linkjob AI Style Content Script Loaded");

let mediaRecorder;
let audioChunks = [];

// 1. Create the Premium Panel
const panel = document.createElement('div');
panel.id = 'jarvis-panel';
panel.innerHTML = `
    <div id="jarvis-header">
        <div style="display: flex; align-items: center; gap: 8px;">
            <div id="jarvis-min-icon" style="display: none;">🤖</div> <!-- Icon for minimized state -->
            <h1>JARVIS AI</h1>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div id="jarvis-status-badge" class="status-ready">Ready</div>
            <button id="jarvis-minimize-btn" style="background: none; border: none; color: #8b949e; cursor: pointer; font-size: 18px; line-height: 1;">&minus;</button>
        </div>
    </div>
    <div id="jarvis-main">
        <div class="jarvis-section-title">Secret Assistant Tips</div>
        <div id="jarvis-suggestion-box">
            <div id="jarvis-ai-text">Waiting for interview to start... Click 'Activate Jarvis' to begin stealth assistance.</div>
        </div>

        <div class="jarvis-section-title">Quick Helpers</div>
        <div class="jarvis-pill-row">
            <div class="jarvis-pill">Suggest Answer</div>
            <div class="jarvis-pill">Explain Term</div>
            <div class="jarvis-pill">Smart Follow-up</div>
        </div>

        <div class="jarvis-section-title">Conversation Feed</div>
        <div id="jarvis-transcript">
            <!-- Transcripts will appear here -->
        </div>
    </div>
    <div id="jarvis-footer">
        <div style="display: flex; gap: 8px; margin-bottom: 8px;">
            <button id="jarvis-summary-btn" style="flex: 1; padding: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; color: #00d2ff; font-weight: 600; cursor: pointer;">✨ QUICK SUMMARY</button>
        </div>
        <button id="jarvis-activate-btn">ACTIVATE JARVIS (STEALTH)</button>
    </div>
`;
document.body.appendChild(panel);

// --- DRAG & MINIMIZE LOGIC ---
const header = document.getElementById('jarvis-header');
const minBtn = document.getElementById('jarvis-minimize-btn');
const minIcon = document.getElementById('jarvis-min-icon');

// Minimize Toggle
minBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    panel.classList.toggle('minimized');
    if (panel.classList.contains('minimized')) {
        minBtn.innerHTML = "+"; // Change to plus
        minIcon.style.display = 'block';
    } else {
        minBtn.innerHTML = "&minus;"; // Change to minus
        minIcon.style.display = 'none';
        // Restore dimensions if needed or let CSS handle it
        panel.style.width = '380px';
        panel.style.height = 'auto';
    }
});

// Restore from click on minimized
panel.addEventListener('click', (e) => {
    if (panel.classList.contains('minimized')) {
        panel.classList.remove('minimized');
        minBtn.innerHTML = "&minus;";
        minIcon.style.display = 'none';
        panel.style.width = '380px';
        panel.style.height = 'auto';
    }
});

// Draggable Logic
let isDragging = false;
let currentX;
let currentY;
let initialX;
let initialY;
let xOffset = 0;
let yOffset = 0;

header.addEventListener("mousedown", dragStart);
document.addEventListener("mouseup", dragEnd);
document.addEventListener("mousemove", drag);

function dragStart(e) {
    // Don't drag if clicking buttons
    if (e.target.tagName === 'BUTTON') return;

    initialX = e.clientX - xOffset;
    initialY = e.clientY - yOffset;

    if (e.target === header || header.contains(e.target)) {
        isDragging = true;
    }
}

function dragEnd(e) {
    initialX = currentX;
    initialY = currentY;
    isDragging = false;
}

function drag(e) {
    if (isDragging) {
        e.preventDefault();
        currentX = e.clientX - initialX;
        currentY = e.clientY - initialY;

        xOffset = currentX;
        yOffset = currentY;

        setTranslate(currentX, currentY, panel);
    }
}

function setTranslate(xPos, yPos, el) {
    el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
}
// --- END DRAG LOGIC ---

const activateBtn = document.getElementById('jarvis-activate-btn');
const statusBadge = document.getElementById('jarvis-status-badge');
const aiText = document.getElementById('jarvis-ai-text');
const transcriptBox = document.getElementById('jarvis-transcript');

// 2. Direct Capture Logic (The Linkjob AI Way)
activateBtn.addEventListener('click', async () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        stopStealthMode();
        return;
    }

    try {
        aiText.innerHTML = `
            <div style="text-align: left; font-size: 13px;">
                <strong>REQUIRED STEPS:</strong><br>
                1. Select <strong>"Chrome Tab"</strong> (Onglet Chrome) at the top.<br>
                2. Click <strong>this Google Meet tab</strong>.<br>
                3. <span style="color: #ff4757; font-weight: bold;">ENABLE "Share tab audio"</span> (Bottom Toggle).<br>
                4. Click Share.
            </div>
        `;

        // Use standard getDisplayMedia (Bulletproof)
        // We add specific hints to FORCE the current tab to show up
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: {
                displaySurface: "browser", // Helper to default to tabs
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                suppressLocalAudioPlayback: false // Important for sharing
            },
            selfBrowserSurface: "include",   // <--- CRITICAL: Allows capturing the tab we are on!
            preferCurrentTab: true,          // <--- CRITICAL: Highlights this tab!
            surfaceSwitching: "include",
            monitorTypeSurfaces: "include"
        });

        const audioTrack = stream.getAudioTracks()[0];
        if (!audioTrack) {
            alert("⚠️ WRONG SELECTION / MAUVAISE SÉLECTION!\n\nYou selected 'Entire Screen' or 'Window'?\nAudio only works with 'Chrome Tab' (Onglet Chrome)!\n\n1. Click 'Chrome Tab' (Onglet Chrome)\n2. Select this meeting\n3. Check 'Share tab audio'");
            stream.getTracks().forEach(t => t.stop());
            aiText.textContent = "Capture failed: User picked Screen/Window instead of Tab.";
            return;
        }

        startRecording(stream);

    } catch (err) {
        console.error("[JARVIS] Capture Failed:", err);
        aiText.textContent = `Error: ${err.message}. Make sure to allow tab sharing.`;
    }
});

function startRecording(stream) {
    // Stop video track - we only want audio
    stream.getVideoTracks().forEach(track => track.stop());

    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            console.log(`[JARVIS] Audio chunk available: ${event.data.size} bytes`);
            // Convert to base64 or blob and send to background
            const reader = new FileReader();
            reader.onloadend = () => {
                console.log("[JARVIS] Sending chunk to background script...");
                chrome.runtime.sendMessage({
                    type: 'audio-chunk',
                    data: reader.result
                });
            };
            reader.readAsDataURL(event.data);
        }
    };

    mediaRecorder.onstart = () => {
        statusBadge.textContent = "Listening";
        statusBadge.className = "status-active";
        statusBadge.innerHTML = `<span class="pulse-red"></span>Listening`;
        activateBtn.textContent = "STOP ASSISTANT";
        activateBtn.style.background = "#ff4757";
        aiText.textContent = "JARVIS is now analyzing the interview. Tips will appear here shortly...";
    };

    mediaRecorder.onstop = () => {
        statusBadge.textContent = "Ready";
        statusBadge.className = "status-ready";
        statusBadge.innerHTML = "Ready";
        activateBtn.textContent = "ACTIVATE JARVIS (STEALTH)";
        activateBtn.style.background = "linear-gradient(90deg, #00d2ff, #3a7bd5)";
    };

    mediaRecorder.start(1000); // 1-second chunks for faster real-time processing
}

function stopStealthMode() {
    if (mediaRecorder) mediaRecorder.stop();
    aiText.textContent = "Assistant stopped. Logs saved.";
}

// 4. Handle Summary Request
const summaryBtn = document.getElementById('jarvis-summary-btn');
summaryBtn.addEventListener('click', () => {
    aiText.textContent = "Generating real-time summary...";
    chrome.runtime.sendMessage({ type: 'get-summary' });
});

chrome.runtime.onMessage.addListener((message) => {
    if (message.action === "displaySummary") {
        aiText.innerHTML = `<div style="color: #00ff88;"><strong>Summary:</strong><br>${message.text}</div>`;
    }
    // ... rest of the existing listeners
        const text = message.text;

        if (text.includes("JARVIS:") || text.includes("Interviewer:")) {
            // New Suggestion/Transcription
            const entry = document.createElement('div');
            entry.className = 'transcript-entry';

            if (text.startsWith("JARVIS:")) {
                aiText.innerHTML = `<strong>${text}</strong>`;
            } else {
                entry.textContent = text;
                transcriptBox.prepend(entry);
            }
        }
    }
});
