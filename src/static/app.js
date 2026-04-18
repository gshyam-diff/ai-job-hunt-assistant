// ===== DOM =====
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');
const suggestionsSection = document.getElementById('suggestions-section');
const suggestionsContainer = document.getElementById('suggestions-container');
const chatSection = document.getElementById('chat-section');
const messagesDiv = document.getElementById('messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');

const modeTabs = document.getElementById('mode-tabs');
const chatMode = document.getElementById('chat-mode');
const jobsMode = document.getElementById('jobs-mode');

const jobQueryInput = document.getElementById('job-query');
const jobLocationInput = document.getElementById('job-location');
const jobRemoteInput = document.getElementById('job-remote');
const searchJobsBtn = document.getElementById('search-jobs-btn');
const jobsStatus = document.getElementById('jobs-status');
const jobsList = document.getElementById('jobs-list');

const modalOverlay = document.getElementById('modal-overlay');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const modalClose = document.getElementById('modal-close');
const modalDismiss = document.getElementById('modal-dismiss');
const modalCopy = document.getElementById('modal-copy');

let isProcessing = false;
let currentJob = null; // Track current job for actions
const jobsMap = new Map(); // Store all job objects by ID — avoids JSON-in-HTML-attribute bugs

// ===== Upload =====
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
    if (isProcessing) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showStatus(uploadStatus, 'Only PDF files are accepted.', 'error');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        showStatus(uploadStatus, 'File too large. Maximum size is 10MB.', 'error');
        return;
    }

    isProcessing = true;
    showStatus(uploadStatus, 'Processing resume...', 'loading');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        const data = await res.json();

        if (!res.ok) {
            showStatus(uploadStatus, data.error || 'Upload failed', 'error');
            isProcessing = false;
            return;
        }

        showStatus(uploadStatus, `${data.message} (${data.chunks} chunks created)`, 'success');
        messagesDiv.innerHTML = '';
        chatSection.classList.remove('hidden');
        chatInput.disabled = false;
        sendBtn.disabled = false;
        modeTabs.classList.remove('hidden');

        if (data.suggestions && data.suggestions.length > 0) {
            showSuggestions(data.suggestions);
        }
    } catch (err) {
        showStatus(uploadStatus, 'Network error. Is the server running?', 'error');
    }
    isProcessing = false;
}

function showStatus(el, msg, type) {
    el.textContent = msg;
    el.className = `${el.id === 'upload-status' ? 'upload-status' : 'jobs-status'} ${type}`;
    el.classList.remove('hidden');
}

// ===== Mode Tabs =====
modeTabs.addEventListener('click', (e) => {
    if (!e.target.matches('.tab-btn')) return;
    const mode = e.target.dataset.mode;
    document.querySelectorAll('.tab-btn').forEach((b) => b.classList.toggle('active', b.dataset.mode === mode));
    chatMode.classList.toggle('hidden', mode !== 'chat');
    jobsMode.classList.toggle('hidden', mode !== 'jobs');
});

// ===== Suggestions =====
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

// ===== Chat =====
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
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

        if (!res.ok) addMessage(data.error || 'Something went wrong', 'error');
        else addMessage(data.answer, 'assistant');
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

// ===== Jobs =====
searchJobsBtn.addEventListener('click', searchJobs);
jobQueryInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') searchJobs(); });

async function searchJobs() {
    const query = jobQueryInput.value.trim();
    const location = jobLocationInput.value.trim();
    const isRemote = jobRemoteInput.checked;

    if (!query) {
        showStatus(jobsStatus, 'Enter a role or keyword to search.', 'error');
        return;
    }

    searchJobsBtn.disabled = true;
    showStatus(jobsStatus, 'Searching Indeed, LinkedIn, Google — and rating each match… this takes 20–60s.', 'loading');
    jobsList.innerHTML = '';

    try {
        const res = await fetch('/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, location, is_remote: isRemote }),
        });
        const data = await res.json();

        if (!res.ok) {
            showStatus(jobsStatus, data.error || 'Search failed', 'error');
            searchJobsBtn.disabled = false;
            return;
        }

        if (!data.jobs || data.jobs.length === 0) {
            showStatus(jobsStatus, data.message || 'No jobs found.', 'error');
            searchJobsBtn.disabled = false;
            return;
        }

        showStatus(jobsStatus, `Found ${data.count} jobs — sorted by match score.`, 'success');
        jobsMap.clear();
        data.jobs.forEach((job) => {
            jobsMap.set(job.id, job); // Store full job object safely
            jobsList.appendChild(renderJobCard(job));
        });
    } catch (err) {
        showStatus(jobsStatus, 'Network error searching jobs.', 'error');
    }
    searchJobsBtn.disabled = false;
}

function renderJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';

    const score = job.rating?.score ?? 5;
    const scoreClass = score >= 8 ? 'high' : score >= 6 ? 'mid' : 'low';

    const meta = [
        job.location,
        job.is_remote ? 'Remote' : null,
        job.salary_display,
        job.date_posted,
        job.site,
    ].filter(Boolean).join(' · ');

    const strengths = (job.rating?.strengths || []).map((s) => `<li>${esc(s)}</li>`).join('');
    const gaps = (job.rating?.gaps || []).map((s) => `<li>${esc(s)}</li>`).join('');

    card.innerHTML = `
        <div class="job-card-header">
            <div class="job-score ${scoreClass}">
                <span class="score-num">${score}</span>
                <span class="score-label">/10</span>
            </div>
            <div class="job-title-block">
                <h3>${esc(job.title)}</h3>
                <div class="job-company">${esc(job.company)}</div>
                <div class="job-meta">${esc(meta)}</div>
            </div>
        </div>
        <p class="job-rationale">${esc(job.rating?.rationale || '')}</p>
        ${strengths || gaps ? `
        <div class="job-assessment">
            ${strengths ? `<div><strong>Strengths</strong><ul>${strengths}</ul></div>` : ''}
            ${gaps ? `<div><strong>Gaps</strong><ul>${gaps}</ul></div>` : ''}
        </div>` : ''}
        <div class="job-actions">
            <button class="btn-action" data-action="view-desc" data-id="${job.id}">📄 View Description</button>
            ${job.job_url ? `<a class="btn-primary" href="${esc(job.job_url)}" target="_blank" rel="noopener">Apply →</a>` : ''}
            <button class="btn-action" data-action="tailor" data-id="${job.id}">Tailor Resume</button>
            <button class="btn-action" data-action="outreach" data-id="${job.id}">Draft Outreach Email</button>
            <button class="btn-action" data-action="gap" data-id="${job.id}">Skill Gap Analysis</button>
            <button class="btn-action" data-action="cover-letter" data-id="${job.id}">Cover Letter</button>
        </div>
    `;

    card.querySelectorAll('button.btn-action').forEach((btn) => {
        btn.addEventListener('click', () => {
            const job_data = jobsMap.get(btn.dataset.id) || job; // Always look up from Map
            runJobAction(btn.dataset.action, btn.dataset.id, job_data);
        });
    });

    return card;
}

function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function getFilename(job, action) {
    // Format: Role_CompanyName_Action.pdf
    const role = (job.title || 'Job').replace(/[^a-zA-Z0-9]/g, '_');
    const company = (job.company || 'Company').replace(/[^a-zA-Z0-9]/g, '_');
    
    const actionLabel = {
        'tailor': 'Tailored_Resume',
        'outreach': 'Outreach_Email',
        'gap': 'Skill_Gap_Analysis',
        'cover-letter': 'Cover_Letter',
    }[action] || action;
    
    return `${role}_${company}_${actionLabel}.pdf`;
}

async function runJobAction(action, jobId, job) {
    currentJob = job;
    
    if (action === 'view-desc') {
        openModal(`Job Description — ${job.title}`, job.description || 'No description available.');
        return;
    }

    const titles = {
        'tailor': `Tailored Resume — ${job.title}`,
        'outreach': `Outreach Email — ${job.company}`,
        'gap': `Skill Gap Analysis — ${job.title}`,
        'cover-letter': `Cover Letter — ${job.title}`,
    };
    openModal(titles[action] || 'Result', 'Generating… this takes a few seconds.');

    try {
        const res = await fetch(`/jobs/${jobId}/${action}`, { method: 'POST' });
        const data = await res.json();
        if (!res.ok) { setModalBody(data.error || 'Failed', 'text'); return; }

        if (action === 'outreach') {
            const recruiterLink = data.linkedin_recruiter_url
                ? `<p><a href="${esc(data.linkedin_recruiter_url)}" target="_blank" rel="noopener">🔍 Find recruiter on LinkedIn (Google search)</a></p>` : '';
            const hmLink = data.linkedin_hiring_manager_url
                ? `<a href="${esc(data.linkedin_hiring_manager_url)}" target="_blank" rel="noopener">🔍 Find hiring manager on LinkedIn</a></p>` : '';
            const emails = data.emails_found
                ? `<p><strong>Emails mentioned in listing:</strong> ${esc(data.emails_found)}</p>` : '';
            const html = `
                <p><strong>Subject:</strong> ${esc(data.subject)}</p>
                <pre class="modal-pre">${esc(data.body)}</pre>
                ${emails}
                ${recruiterLink}
                ${hmLink}
            `;
            modalBody.innerHTML = html;
            modalBody.dataset.copyText = `Subject: ${data.subject}\n\n${data.body}`;
        } else {
            setModalBody(data.content, data.format || 'markdown');
            modalBody.dataset.copyText = data.content;
        }
        
        // Show PDF download button
        updateModalWithPDF(action, data);
    } catch (err) {
        setModalBody('Network error.', 'text');
    }
}

function updateModalWithPDF(action, data) {
    const pdfBtn = document.createElement('button');
    pdfBtn.className = 'btn-primary';
    pdfBtn.textContent = '📥 Download PDF';
    pdfBtn.style.marginRight = '0.5rem';
    pdfBtn.addEventListener('click', () => downloadPDF(action, data));
    modalCopy.parentElement.insertBefore(pdfBtn, modalCopy);
}

async function downloadPDF(action, data) {
    try {
        const { jsPDF } = window.jspdf;
        if (!jsPDF) {
            alert('PDF library not loaded. Please refresh the page.');
            return;
        }

        const doc = new jsPDF();
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 15;
        const maxWidth = pageWidth - 2 * margin;

        // Title
        doc.setFontSize(16);
        doc.text(currentJob.title, margin, margin);
        
        // Company & meta
        doc.setFontSize(12);
        doc.setTextColor(100);
        doc.text(`${currentJob.company} | ${currentJob.location || 'Location N/A'}`, margin, margin + 10);
        
        // Content
        doc.setFontSize(11);
        doc.setTextColor(0);
        let yPos = margin + 25;
        
        const content = data.content || data.body || 'No content generated';
        const lines = doc.splitTextToSize(content, maxWidth);
        
        lines.forEach((line) => {
            if (yPos > pageHeight - margin) {
                doc.addPage();
                yPos = margin;
            }
            doc.text(line, margin, yPos);
            yPos += 7;
        });

        const filename = getFilename(currentJob, action);
        doc.save(filename);
    } catch (err) {
        console.error('PDF download error:', err);
        alert('Failed to download PDF. Make sure jsPDF is loaded.');
    }
}

// ===== Modal =====
modalClose.addEventListener('click', closeModal);
modalDismiss.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeModal(); });
modalCopy.addEventListener('click', () => {
    const text = modalBody.dataset.copyText || modalBody.innerText;
    navigator.clipboard.writeText(text).then(() => {
        modalCopy.textContent = 'Copied!';
        setTimeout(() => { modalCopy.textContent = 'Copy'; }, 1500);
    });
});

function openModal(title, body) {
    modalTitle.textContent = title;
    setModalBody(body, 'text');
    modalOverlay.classList.remove('hidden');
}
function closeModal() { 
    modalOverlay.classList.add('hidden'); 
    // Remove PDF button if it exists
    const pdfBtn = document.querySelector('[data-pdf-btn]');
    if (pdfBtn) pdfBtn.remove();
}

function setModalBody(content, format) {
    if (format === 'markdown') {
        modalBody.innerHTML = renderMarkdown(content);
    } else {
        modalBody.innerHTML = `<pre class="modal-pre">${esc(content)}</pre>`;
    }
    modalBody.dataset.copyText = content;
}

// Minimal markdown: headings, bullets, bold
function renderMarkdown(md) {
    const lines = md.split('\n');
    let html = '';
    let inList = false;
    for (const line of lines) {
        if (/^##\s+/.test(line)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<h3>${esc(line.replace(/^##\s+/, ''))}</h3>`;
        } else if (/^#\s+/.test(line)) {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<h2>${esc(line.replace(/^#\s+/, ''))}</h2>`;
        } else if (/^\s*[-*]\s+/.test(line)) {
            if (!inList) { html += '<ul>'; inList = true; }
            html += `<li>${inlineMd(line.replace(/^\s*[-*]\s+/, ''))}</li>`;
        } else if (line.trim() === '') {
            if (inList) { html += '</ul>'; inList = false; }
        } else {
            if (inList) { html += '</ul>'; inList = false; }
            html += `<p>${inlineMd(line)}</p>`;
        }
    }
    if (inList) html += '</ul>';
    return html;
}
function inlineMd(s) {
    return esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`(.+?)`/g, '<code>$1</code>');
}
