// Exam Workspace Controller
let currentQuestionId = null;
let webcamStream = null;
let monitorInterval = null;
let timerInterval = null;

// Audio Context & Analyser Variables
let audioContext = null;
let audioAnalyser = null;
let audioDataArray = null;
let audioMeterInterval = null;
let sustainedSpeechCounter = 0;
let lastAudioReportTime = 0;

// Initialize Workspace
document.addEventListener('DOMContentLoaded', () => {
    // 1. Pick first question
    const questionIds = Object.keys(QUESTIONS_DATA);
    if (questionIds.length > 0) {
        selectQuestion(parseInt(questionIds[0]));
    }

    // 2. Setup textarea tab handling
    setupCodeEditorTabHandling();

    // 3. Initialize Countdown Timer
    initCountdownTimer();

    // 4. Initialize Multimodal Monitoring (Webcam + Audio)
    initMultimodalMonitoring();
});

// Select & Load Question into Editor
function selectQuestion(qid) {
    currentQuestionId = qid;
    const qData = QUESTIONS_DATA[qid];
    if (!qData) return;

    // Update title & language
    document.getElementById('currentQuestionTitle').innerText = qData.title;
    document.getElementById('editorLanguage').innerText = qData.language || 'python';

    const editor = document.getElementById('codeEditor');
    const consoleOutput = document.getElementById('consoleOutput');
    const statusBadge = document.getElementById('outputStatusBadge');

    // Load existing submission or starter code
    if (SUBMISSIONS_DATA[qid] && SUBMISSIONS_DATA[qid].code) {
        editor.value = SUBMISSIONS_DATA[qid].code;
        consoleOutput.innerText = SUBMISSIONS_DATA[qid].output || 'Previously submitted solution loaded.';
        statusBadge.innerText = `Score: ${SUBMISSIONS_DATA[qid].score}/100`;
        statusBadge.className = 'badge bg-success-subtle text-success border small';
    } else {
        editor.value = qData.starter_code || '# Write your solution here\n';
        consoleOutput.innerText = 'Execution console ready. Click "Run Test Cases" to evaluate your solution.';
        statusBadge.innerText = 'Ready';
        statusBadge.className = 'badge bg-light text-dark border small';
    }
}

// Reset to original starter code
function resetStarterCode() {
    if (!currentQuestionId) return;
    if (confirm('Reset code to initial template? Any unsubmitted changes will be lost.')) {
        const qData = QUESTIONS_DATA[currentQuestionId];
        document.getElementById('codeEditor').value = qData.starter_code || '';
    }
}

// Intercept Tab key in Code Editor for standard 4-space indentation
function setupCodeEditorTabHandling() {
    const editor = document.getElementById('codeEditor');
    editor.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;
            this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = start + 4;
        }
    });
}

// Countdown Timer
function initCountdownTimer() {
    const timerElem = document.getElementById('countdownTimer');
    const durationMins = parseInt(timerElem.getAttribute('data-duration')) || 30;
    let totalSeconds = durationMins * 60;

    function updateDisplay() {
        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        timerElem.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

        if (totalSeconds <= 300) { // 5 mins left
            timerElem.classList.add('text-danger', 'fw-bold');
        }

        if (totalSeconds <= 0) {
            clearInterval(timerInterval);
            alert('Time has expired! Submitting your exam session.');
            document.querySelector('#finishModal form').submit();
        } else {
            totalSeconds--;
        }
    }

    updateDisplay();
    timerInterval = setInterval(updateDisplay, 1000);
}

// Run Test Cases (Mock Sandbox Execution)
async function runTestCases() {
    if (!currentQuestionId) return;

    const editor = document.getElementById('codeEditor');
    const code = editor ? editor.value : '';
    const consoleOutput = document.getElementById('consoleOutput');
    const statusBadge = document.getElementById('outputStatusBadge');
    const btnRun = document.getElementById('btnRunCode') || document.querySelector('button[onclick*="run"]') || document.querySelector('button[onclick*="Run"]');

    if (btnRun) {
        btnRun.disabled = true;
        btnRun.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Running...';
    }
    if (statusBadge) {
        statusBadge.innerText = 'Evaluating Sandbox...';
        statusBadge.className = 'badge bg-warning-subtle text-warning border small';
    }

    try {
        const response = await fetch('/student/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: currentQuestionId,
                code: code
            })
        });

        const data = await response.json();
        if (consoleOutput) {
            consoleOutput.innerText = data.output || 'Execution completed with no output.';
        }

        if (statusBadge) {
            if (data.status === 'PASSED' || data.status === 'Accepted') {
                statusBadge.innerText = `All Tests Passed (Score: ${data.score}/100)`;
                statusBadge.className = 'badge bg-success-subtle text-success border small';
            } else {
                statusBadge.innerText = `Tests Failed (Score: ${data.score}/100)`;
                statusBadge.className = 'badge bg-danger-subtle text-danger border small';
            }
        }
    } catch (err) {
        if (consoleOutput) {
            consoleOutput.innerText = 'Error connecting to code execution sandbox:\n' + err.message;
        }
        if (statusBadge) {
            statusBadge.innerText = 'Execution Error';
            statusBadge.className = 'badge bg-danger-subtle text-danger border small';
        }
    } finally {
        if (btnRun) {
            btnRun.disabled = false;
            btnRun.innerHTML = '<i class="bi bi-play-fill me-1"></i> Run Test Cases';
        }
    }
}

// Submit Solution for Current Question
async function submitSolution() {
    if (!currentQuestionId) return;

    const editor = document.getElementById('codeEditor');
    const code = editor ? editor.value : '';
    const btnSubmit = document.getElementById('btnSubmitCode') || document.querySelector('button[onclick*="submit"]') || document.querySelector('button[onclick*="Submit"]');

    if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Submitting...';
    }

    try {
        const response = await fetch('/student/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                question_id: currentQuestionId,
                code: code
            })
        });

        const data = await response.json();
        if (data.success) {
            SUBMISSIONS_DATA[currentQuestionId] = data.submission;
            selectQuestion(currentQuestionId); // Refresh UI
            alert('Solution submitted and recorded successfully!');
        } else {
            alert('Submission error: ' + (data.error || 'Unknown error'));
        }
    } catch (err) {
        alert('Failed to transmit code submission: ' + err.message);
    } finally {
        if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<i class="bi bi-cloud-upload-fill me-1"></i> Submit Solution';
        }
    }
}

// Global aliases for template buttons
window.runCurrentCode = runTestCases;
window.runTestCases = runTestCases;
window.submitCurrentCode = submitSolution;
window.submitSolution = submitSolution;

// Multimodal Proctoring Setup (Webcam + Web Audio API)
async function initMultimodalMonitoring() {
    const video = document.getElementById('webcamVideo');
    const cameraStatusPill = document.getElementById('cameraStatusPill');
    const micStatusPill = document.getElementById('micStatusPill');

    // 1. Initialize Media Stream (Video + Audio)
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 320 }, height: { ideal: 240 } },
            audio: true
        });

        video.srcObject = webcamStream;
        if (cameraStatusPill) {
            cameraStatusPill.className = 'badge bg-success';
            cameraStatusPill.innerText = 'Camera: ACTIVE';
        }

        // Set up Web Audio API real-time analyser
        initAudioAnalyser(webcamStream);

        // Start visual frame capture loop (every 5 seconds)
        monitorInterval = setInterval(captureAndAnalyzeFrame, 5000);
        setTimeout(captureAndAnalyzeFrame, 1500);

    } catch (err) {
        console.warn('Webcam or Microphone not directly accessible, attempting video only:', err.message);

        // Try video only fallback if mic was denied
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 320 }, height: { ideal: 240 } },
                audio: false
            });
            video.srcObject = webcamStream;
            if (cameraStatusPill) {
                cameraStatusPill.className = 'badge bg-success';
                cameraStatusPill.innerText = 'Camera: ACTIVE';
            }
            if (micStatusPill) {
                micStatusPill.className = 'badge bg-warning text-dark';
                micStatusPill.innerText = 'Mic: SIMULATED';
            }
            monitorInterval = setInterval(captureAndAnalyzeFrame, 5000);
            setTimeout(captureAndAnalyzeFrame, 1500);
        } catch (vErr) {
            console.warn('Media fully offline/simulated:', vErr.message);
            if (cameraStatusPill) {
                cameraStatusPill.className = 'badge bg-warning text-dark';
                cameraStatusPill.innerText = 'Camera: SIMULATED';
            }
            if (micStatusPill) {
                micStatusPill.className = 'badge bg-warning text-dark';
                micStatusPill.innerText = 'Mic: SIMULATED';
            }
            document.getElementById('overlayStatus').innerText = 'STANDBY';
            document.getElementById('overlayStatus').className = 'camera-status-pill bg-warning text-dark';
            document.getElementById('cvStatusText').innerText = 'Using Simulation Mode';
            document.getElementById('cvStatusText').className = 'fw-bold text-warning';
        }
    }
}

// Web Audio API Real-Time Acoustic & Speech Monitoring
function initAudioAnalyser(stream) {
    const micStatusPill = document.getElementById('micStatusPill');
    try {
        const audioTracks = stream.getAudioTracks();
        if (audioTracks.length === 0) {
            if (micStatusPill) {
                micStatusPill.className = 'badge bg-warning text-dark';
                micStatusPill.innerText = 'Mic: SIMULATED';
            }
            return;
        }

        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!window.AudioContext) return;

        audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        audioAnalyser = audioContext.createAnalyser();
        audioAnalyser.fftSize = 256;
        source.connect(audioAnalyser);
        audioDataArray = new Uint8Array(audioAnalyser.frequencyBinCount);

        if (micStatusPill) {
            micStatusPill.className = 'badge bg-success';
            micStatusPill.innerText = 'Mic: ACTIVE';
        }

        // Sample audio every 250ms for live decibel meter
        audioMeterInterval = setInterval(sampleLiveAudioMeter, 250);
    } catch (e) {
        console.warn('AudioContext setup error:', e);
        if (micStatusPill) {
            micStatusPill.className = 'badge bg-warning text-dark';
            micStatusPill.innerText = 'Mic: SIMULATED';
        }
    }
}

// Live Audio Sampling & Anomaly Detection
function sampleLiveAudioMeter() {
    if (!audioAnalyser || !audioDataArray) return;

    audioAnalyser.getByteFrequencyData(audioDataArray);
    let sum = 0;
    for (let i = 0; i < audioDataArray.length; i++) {
        sum += audioDataArray[i];
    }
    const avg = sum / audioDataArray.length; // 0 to 255
    const normalizedVol = Math.min(1.0, avg / 128.0);
    const dbApprox = normalizedVol > 0.001 ? Math.round(20 * Math.log10(normalizedVol) * 2) : -60;

    // Update UI Decibel meter bar
    const bar = document.getElementById('micVolumeBar');
    const text = document.getElementById('micVolumeText');
    if (bar && text) {
        const pct = Math.max(5, Math.min(100, Math.round(normalizedVol * 100)));
        bar.style.width = pct + '%';

        if (normalizedVol > 0.55 || dbApprox > -18) {
            bar.className = 'progress-bar bg-danger';
            text.innerText = `Speaking / Voice! (${pct}%)`;
            text.className = 'fw-bold small text-danger';
            sustainedSpeechCounter++;
        } else if (normalizedVol > 0.3 || dbApprox > -32) {
            bar.className = 'progress-bar bg-warning';
            text.innerText = `Whisper / Noise (${pct}%)`;
            text.className = 'fw-bold small text-warning';
            sustainedSpeechCounter++;
        } else {
            bar.className = 'progress-bar bg-success';
            text.innerText = `Quiet (${pct}%)`;
            text.className = 'fw-bold small text-success';
            sustainedSpeechCounter = Math.max(0, sustainedSpeechCounter - 1);
        }
    }

    // If sustained speech or loud voice detected (> 2.5 seconds = 10 intervals)
    const now = Date.now();
    if (sustainedSpeechCounter >= 10 && (now - lastAudioReportTime > 8000)) {
        lastAudioReportTime = now;
        sustainedSpeechCounter = 0;

        fetch('/api/monitor/audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                volume: normalizedVol,
                speech_detected: true,
                db_level: dbApprox,
                continuous_count: 2
            })
        }).then(r => r.json()).then(res => {
            updateProctoringUI({
                face_count: 1,
                status: res.status,
                incident_type: res.incident_type,
                severity: res.severity,
                details: res.details
            });
        }).catch(err => console.warn('Audio telemetry report error:', err));
    }
}

let simulationHoldTimer = null;

// Capture current webcam frame to canvas and send to /api/monitor/analyze
async function captureAndAnalyzeFrame() {
    if (simulationHoldTimer) return; // Hold simulated anomaly during demonstration

    const video = document.getElementById('webcamVideo');
    const canvas = document.getElementById('analysisCanvas');
    if (!video || !webcamStream || video.videoWidth === 0) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL('image/jpeg', 0.6);

    try {
        const response = await fetch('/api/monitor/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                image: dataUrl
            })
        });

        if (response.ok) {
            const result = await response.json();
            if (!simulationHoldTimer) {
                updateProctoringUI(result);
            }
        }
    } catch (err) {
        console.warn('Proctoring ping error:', err.message);
    }
}

// Update proctoring widgets with analysis result
function updateProctoringUI(result) {
    const faceCountElem = document.getElementById('cvFaceCount');
    const statusTextElem = document.getElementById('cvStatusText');
    const overlayCount = document.getElementById('overlayFaceCount');
    const overlayStatus = document.getElementById('overlayStatus');
    const lastPing = document.getElementById('cvLastPing');
    const gazeStatus = document.getElementById('gazeStatusText');
    const deviceStatus = document.getElementById('deviceStatusText');

    if (faceCountElem && result.face_count !== undefined) {
        faceCountElem.innerText = `${result.face_count} detected`;
    }
    if (overlayCount && result.face_count !== undefined) {
        overlayCount.innerText = `Faces: ${result.face_count}`;
    }

    const now = new Date();
    if (lastPing) lastPing.innerText = now.toLocaleTimeString();

    // Update Gaze Status
    if (gazeStatus) {
        if (result.incident_type === 'GAZE_SHIFT') {
            gazeStatus.innerText = 'Gaze Shift / Looking Away!';
            gazeStatus.className = 'fw-bold text-warning';
        } else {
            gazeStatus.innerText = 'Centered on Screen';
            gazeStatus.className = 'fw-bold text-success';
        }
    }

    // Update Device Status
    if (deviceStatus) {
        // A frame can carry several infractions at once; fall back to the primary one.
        const types = (result.violations && result.violations.length)
            ? result.violations.map(v => v.incident_type)
            : [result.incident_type];
        const labels = [];
        if (types.includes('PHONE_DETECTED')) labels.push('Mobile Phone');
        if (types.includes('PROHIBITED_DEVICE_DETECTED')) labels.push('Prohibited Device');
        if (types.includes('PROHIBITED_MATERIAL_DETECTED')) labels.push('Prohibited Material');
        if (labels.length) {
            deviceStatus.innerText = labels.join(' + ') + ' Detected!';
            deviceStatus.className = 'fw-bold text-danger';
        } else {
            deviceStatus.innerText = 'None Detected';
            deviceStatus.className = 'fw-bold text-success';
        }
    }

    // Update Overall Proctoring Status
    if (result.status === 'NORMAL') {
        if (overlayStatus) {
            overlayStatus.innerText = 'NORMAL';
            overlayStatus.className = 'camera-status-pill bg-success';
        }
        if (statusTextElem) {
            statusTextElem.innerText = 'NORMAL';
            statusTextElem.className = 'fw-bold text-success';
        }
    } else if (result.status === 'INCIDENT') {
        const isHigh = (result.severity === 'HIGH');
        if (overlayStatus) {
            overlayStatus.innerText = result.incident_type || 'ANOMALY';
            overlayStatus.className = isHigh ? 'camera-status-pill bg-danger text-white' : 'camera-status-pill bg-warning text-dark';
        }
        if (statusTextElem) {
            const extra = (result.violations && result.violations.length > 1)
                ? ` +${result.violations.length - 1} more` : '';
            statusTextElem.innerText = `${result.incident_type} (${result.severity || 'REVIEW'})${extra}`;
            statusTextElem.className = isHigh ? 'fw-bold text-danger' : 'fw-bold text-warning';
        }
    }
}

// Simulate Visual / App Anomaly
async function simulateAnomaly(type) {
    if (type !== 'normal') {
        if (simulationHoldTimer) clearTimeout(simulationHoldTimer);
        simulationHoldTimer = setTimeout(() => { simulationHoldTimer = null; }, 10000);
    } else {
        if (simulationHoldTimer) clearTimeout(simulationHoldTimer);
        simulationHoldTimer = null;
    }

    try {
        const response = await fetch('/api/monitor/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                simulation: type
            })
        });

        if (response.ok) {
            const result = await response.json();
            updateProctoringUI(result);
        }
    } catch (err) {
        console.error('Simulation error:', err);
    }
}

// Simulate Audio Anomaly
async function simulateAudioAnomaly(audioType) {
    if (audioType !== 'normal') {
        if (simulationHoldTimer) clearTimeout(simulationHoldTimer);
        simulationHoldTimer = setTimeout(() => { simulationHoldTimer = null; }, 10000);
    } else {
        if (simulationHoldTimer) clearTimeout(simulationHoldTimer);
        simulationHoldTimer = null;
    }

    try {
        const response = await fetch('/api/monitor/audio', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                simulation: audioType
            })
        });

        if (response.ok) {
            const result = await response.json();
            updateProctoringUI({
                face_count: 1,
                status: result.status,
                incident_type: result.incident_type,
                severity: result.severity,
                details: result.details
            });
        }
    } catch (err) {
        console.error('Audio simulation error:', err);
    }
}

window.simulateAnomaly = simulateAnomaly;
window.simulateAudioAnomaly = simulateAudioAnomaly;

// Automatic Unauthorized Application & Window Blur Detection
(function initAppFocusMonitoring() {
    let lastBlurReportTime = 0;

    function reportWindowBlur(reason) {
        const now = Date.now();
        // Debounce reports to at most once per 10 seconds
        if (now - lastBlurReportTime < 10000) return;
        lastBlurReportTime = now;

        fetch('/api/monitor/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: SESSION_ID,
                simulation: 'unauthorized_application',
                details: `Candidate switched away from active exam window (${reason}). Potential unauthorized application in foreground.`
            })
        }).then(r => r.json()).then(res => {
            updateProctoringUI(res);
        }).catch(e => console.warn('Focus monitoring ping failed:', e));
    }

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            reportWindowBlur('Browser Tab Hidden / Switched');
        }
    });

    window.addEventListener('blur', () => {
        reportWindowBlur('Window Focus Lost to Another Application');
    });
})();
