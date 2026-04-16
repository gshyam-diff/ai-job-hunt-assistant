const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');
const uploadSection = document.getElementById('upload-section');
const suggestionsSection = document.getElementById('suggestions-section');
const suggestionsContainer = document.getElementById('suggestions-container');
const chatSection = document.getElementById('chat-section');
const messagesDiv = document.getElementById('messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

let isProcessing = false;

// --- Upload ---

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) uploadFile(files[0]);
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
    if (isProcessing) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showStatus('Only PDF files are accepted.', 'error');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showStatus('File too large. Maximum size is 10MB.', 'error');
        return;
    }

    isProcessing = true;
    showStatus('Processing resume...', 'loading');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();

        if (!res.ok) {
            showStatus(data.error || 'Upload failed', 'error');
            isProcessing = false;
            return;
        }

        showStatus(`${data.message} (${data.chunks} chunks created)`, 'success');
        messagesDiv.innerHTML = '';
        chatSection.classList.remove('hidden');
        chatInput.disabled = false;
        sendBtn.disabled = false;

        if (data.suggestions && data.suggestions.length > 0) {
            showSuggestions(data.suggestions);
        }
    } catch (err) {
        showStatus('Network error. Is the server running?', 'error');
    }

    isProcessing = false;
}

function showStatus(msg, type) {
    uploadStatus.textContent = msg;
    uploadStatus.className = `upload-status ${type}`;
    uploadStatus.classList.remove('hidden');
}

// --- Suggestions ---

function showSuggestions(suggestions) {
    suggestionsContainer.innerHTML = '';
    suggestions.forEach((q) => {
        const chip = document.createElement('button');
        chip.className = 'suggestion-chip';
        chip.textContent = q;
        chip.addEventListener('click', () => {
            chatInput.value = q;
            sendMessage();
            suggestionsSection.classList.add('hidden');
        });
        suggestionsContainer.appendChild(chip);
    });
    suggestionsSection.classList.remove('hidden');
}

// --- Chat ---

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);

async function sendMessage() {
    const msg = chatInput.value.trim();
    if (!msg || isProcessing) return;

    isProcessing = true;
    chatInput.value = '';
    sendBtn.disabled = true;

    addMessage(msg, 'user');
    const typing = addTypingIndicator();

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg }),
        });
        const data = await res.json();

        typing.remove();

        if (!res.ok) {
            addMessage(data.error || 'Something went wrong', 'error');
        } else {
            addMessage(data.answer, 'assistant');
        }
    } catch (err) {
        typing.remove();
        addMessage('Network error. Is the server running?', 'error');
    }

    isProcessing = false;
    sendBtn.disabled = false;
    chatInput.focus();
}

function addMessage(content, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = content;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return div;
}

function addTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return div;
}
