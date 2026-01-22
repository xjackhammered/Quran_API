"""
Speech-to-Text Web GUI - Simplified Version
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/stt-gui", tags=["STT GUI"])


@router.get("/", response_class=HTMLResponse)
async def get_stt_interface():
    """Main STT interface"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎤 Arabic Speech-to-Text</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            
            body {
                font-family: 'Segoe UI', Tahoma, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #f0f0f0;
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            
            .header {
                background: #16213e;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            .header h1 {
                color: #e94560;
                font-size: 24px;
                margin-bottom: 10px;
            }
            
            .header p {
                color: #95a5a6;
                font-size: 14px;
            }
            
            .status-panel {
                background: #16213e;
                border-radius: 15px;
                padding: 25px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            #status {
                font-size: 18px;
                font-weight: bold;
                padding: 15px 30px;
                border-radius: 10px;
                background: #0f3460;
                display: inline-block;
                margin-bottom: 15px;
                color: #95a5a6;
            }
            
            #status.listening { color: #27ae60; }
            #status.processing { color: #f39c12; }
            #status.error { color: #e74c3c; }
            
            .controls {
                display: flex;
                justify-content: center;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            button {
                padding: 15px 35px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            #startBtn {
                background: #27ae60;
                color: white;
            }
            
            #startBtn:hover:not(:disabled) {
                background: #229954;
            }
            
            #stopBtn {
                background: #e74c3c;
                color: white;
            }
            
            #stopBtn:hover:not(:disabled) {
                background: #c0392b;
            }
            
            #clearBtn {
                background: #3498db;
                color: white;
            }
            
            .output-panel {
                background: #16213e;
                border-radius: 15px;
                padding: 20px;
            }
            
            .output-panel h3 {
                color: #e94560;
                margin-bottom: 15px;
                font-size: 14px;
                text-transform: uppercase;
            }
            
            #output {
                background: #0f3460;
                border-radius: 10px;
                padding: 20px;
                min-height: 300px;
                max-height: 500px;
                overflow-y: auto;
            }
            
            .transcription {
                margin-bottom: 15px;
                padding: 15px;
                background: #16213e;
                border-radius: 8px;
                border-right: 4px solid #e94560;
                animation: slideIn 0.3s ease;
            }
            
            @keyframes slideIn {
                from { opacity: 0; transform: translateX(-20px); }
                to { opacity: 1; transform: translateX(0); }
            }
            
            .transcription .timestamp {
                color: #95a5a6;
                font-size: 12px;
                margin-bottom: 5px;
            }
            
            .transcription .text {
                color: #f0f0f0;
                font-size: 18px;
                font-family: 'Traditional Arabic', serif;
                line-height: 1.8;
            }
            
            .tips {
                text-align: center;
                color: #95a5a6;
                font-size: 13px;
                margin-top: 20px;
                padding: 15px;
                background: rgba(255,255,255,0.05);
                border-radius: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎤 Arabic Speech Recognition</h1>
                <p>Optimized for Quranic Arabic | Powered by OpenAI Whisper</p>
            </div>
            
            <div class="status-panel">
                <div id="status">● Ready to Listen</div>
            </div>
            
            <div class="controls">
                <button id="startBtn">▶ START LISTENING</button>
                <button id="stopBtn" disabled>⏹ STOP</button>
                <button id="clearBtn">🗑 CLEAR</button>
            </div>
            
            <div class="output-panel">
                <h3>📝 Transcription Output</h3>
                <div id="output"></div>
            </div>
            
            <div class="tips">
                💡 <strong>Tips:</strong> Speak clearly | Wait 5 seconds after speaking | Minimize background noise
            </div>
        </div>

        <script>
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const clearBtn = document.getElementById('clearBtn');
            const status = document.getElementById('status');
            const output = document.getElementById('output');
            
            let ws = null;
            
            function updateStatus(message, className) {
                status.textContent = '● ' + message;
                status.className = className || '';
            }
            
            startBtn.onclick = () => {
                ws = new WebSocket(`ws://${window.location.host}/stt/ws/realtime`);
                
                ws.onopen = () => {
                    updateStatus('Connected - Initializing...', 'listening');
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'transcription') {
                        const div = document.createElement('div');
                        div.className = 'transcription';
                        div.innerHTML = `
                            <div class="timestamp">${new Date().toLocaleTimeString()}</div>
                            <div class="text">${data.text}</div>
                        `;
                        output.insertBefore(div, output.firstChild);
                        updateStatus('Success! Listening...', 'listening');
                    } 
                    else if (data.type === 'status') {
                        let cls = 'listening';
                        if (data.message.includes('Processing')) cls = 'processing';
                        if (data.message.includes('Error')) cls = 'error';
                        updateStatus(data.message, cls);
                    }
                    else if (data.type === 'error') {
                        updateStatus('Error: ' + data.message, 'error');
                    }
                };
                
                ws.onclose = () => {
                    updateStatus('Disconnected', '');
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                };
                
                ws.onerror = () => {
                    updateStatus('Connection error', 'error');
                };
            };
            
            stopBtn.onclick = () => {
                if (ws) {
                    ws.send('stop');
                    ws.close();
                }
            };
            
            clearBtn.onclick = () => {
                output.innerHTML = '';
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/test", response_class=HTMLResponse)
async def get_test_interface():
    """File upload test interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Audio Upload</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #1a1a2e;
                color: white;
                padding: 40px;
                max-width: 600px;
                margin: 0 auto;
            }
            h1 { color: #e94560; }
            .upload-area {
                background: #16213e;
                padding: 30px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }
            input[type="file"] { margin: 15px 0; }
            button {
                padding: 15px 30px;
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover { background: #229954; }
            #result {
                background: #0f3460;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
                min-height: 100px;
                direction: rtl;
                font-size: 18px;
            }
            .success { color: #27ae60; }
            .error { color: #e74c3c; }
            .loading { color: #f39c12; }
        </style>
    </head>
    <body>
        <h1>🎤 Test Audio Transcription</h1>
        
        <div class="upload-area">
            <h3>Upload a WAV file</h3>
            <input type="file" id="audioFile" accept=".wav">
            <br><br>
            <button onclick="transcribe()">Transcribe</button>
        </div>
        
        <div id="result">Results will appear here...</div>

        <script>
            async function transcribe() {
                const fileInput = document.getElementById('audioFile');
                const result = document.getElementById('result');
                
                if (!fileInput.files[0]) {
                    result.innerHTML = '<span class="error">Please select a file</span>';
                    return;
                }
                
                result.innerHTML = '<span class="loading">Processing...</span>';
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {
                    const response = await fetch('/stt/transcribe-file', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        result.innerHTML = `<span class="success">✓ Success!</span><br><br>${data.text}`;
                    } else {
                        result.innerHTML = `<span class="error">✗ ${data.error || 'Failed'}</span>`;
                    }
                } catch (error) {
                    result.innerHTML = `<span class="error">✗ ${error.message}</span>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
