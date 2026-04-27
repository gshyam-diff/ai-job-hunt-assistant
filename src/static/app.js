// ===== DOM =====
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');
const demoBtn = document.getElementById('demo-btn');

const hero = document.getElementById('hero');
const uploadSection = document.getElementById('upload-section');
const resumePill = document.getElementById('resume-pill');
const pillFilename = document.getElementById('pill-filename');
const pillRole = document.getElementById('pill-role');
const pillReupload = document.getElementById('pill-reupload');

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
let cachedResumeText = null;
let activeStream = null;
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

        collapseToPill(data.filename || file.name, data.inferred_role || '');
        jobsMode.classList.remove('hidden');

        // Auto-fill inferred role, location, remote preference, then auto-search
        if (data.inferred_role) {
            jobQueryInput.value = data.inferred_role;
            if (data.inferred_location) jobLocationInput.value = data.inferred_location;
            if (data.open_to_remote) jobRemoteInput.checked = true;
            searchJobs();
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

function collapseToPill(filename, role) {
    pillFilename.textContent = filename;
    pillRole.textContent = role;
    resumePill.classList.remove('hidden');
    hero.classList.add('hidden');
    uploadSection.classList.add('hidden');
}

function expandToHero() {
    resumePill.classList.add('hidden');
    hero.classList.remove('hidden');
    uploadSection.classList.remove('hidden');
    jobsMode.classList.add('hidden');
    uploadStatus.classList.add('hidden');
    fileInput.value = '';
    cachedResumeText = null;
}

pillReupload.addEventListener('click', expandToHero);

demoBtn.addEventListener('click', async () => {
    if (isProcessing) return;
    isProcessing = true;
    showStatus(uploadStatus, 'Loading sample resume...', 'loading');

    try {
        const res = await fetch('/demo', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) {
            showStatus(uploadStatus, data.error || 'Demo failed', 'error');
            isProcessing = false;
            return;
        }

        collapseToPill(data.filename || 'sample-resume.pdf', data.inferred_role || '');
        jobsMode.classList.remove('hidden');

        if (data.inferred_role) {
            jobQueryInput.value = data.inferred_role;
            if (data.inferred_location) jobLocationInput.value = data.inferred_location;
            if (data.open_to_remote) jobRemoteInput.checked = true;
            searchJobs();
        }
    } catch (err) {
        showStatus(uploadStatus, 'Network error loading demo.', 'error');
    }
    isProcessing = false;
});

// ===== Jobs =====
searchJobsBtn.addEventListener('click', searchJobs);
jobQueryInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') searchJobs(); });

async function searchJobs() {
    const query = jobQueryInput.value.trim();
    const location = jobLocationInput.value.trim();
    const isRemote = jobRemoteInput.checked;

    // Collect selected job sites
    const siteCheckboxes = document.querySelectorAll('.site-filter:checked');
    const sites = Array.from(siteCheckboxes).map(cb => cb.value);

    if (!query) {
        showStatus(jobsStatus, 'Enter a role or keyword to search.', 'error');
        return;
    }

    if (sites.length === 0) {
        showStatus(jobsStatus, 'Select at least one job site to search.', 'error');
        return;
    }

    searchJobsBtn.disabled = true;
    showStatus(jobsStatus, 'Searching ' + sites.join(', ') + ' — and rating each match… this takes 20–60s.', 'loading');
    jobsList.innerHTML = '';

    try {
        const res = await fetch('/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, location, is_remote: isRemote, sites }),
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

    const match = job.rating?.match ?? 0;
    const scoreClass = match >= 75 ? 'high' : match >= 50 ? 'mid' : 'low';

    const meta = [
        job.location,
        job.is_remote ? 'Remote' : null,
        job.salary_display,
        job.date_posted,
        job.site,
    ].filter(Boolean).join(' · ');

    card.innerHTML = `
        <div class="job-card-header">
            <div class="job-score ${scoreClass}">
                <span class="score-num">${match}</span>
                <span class="score-label">% match</span>
            </div>
            <div class="job-title-block">
                <h3>${esc(job.title)}</h3>
                <div class="job-company">${esc(job.company)}</div>
                <div class="job-meta">${esc(meta)}</div>
            </div>
        </div>
        <p class="job-rationale">${esc(job.rating?.verdict || '')}</p>
        <div class="job-actions">
            <button class="btn-action" data-action="view-desc" data-id="${job.id}">📄 View Description</button>
            ${job.job_url ? `<a class="btn-primary" href="${esc(job.job_url)}" target="_blank" rel="noopener">Apply →</a>` : ''}
            <button class="btn-action" data-action="ats" data-id="${job.id}">ATS Deep Dive</button>
            <button class="btn-action" data-action="tailor" data-id="${job.id}">Tailor Resume</button>
            <button class="btn-action" data-action="outreach" data-id="${job.id}">Draft Outreach Email</button>
            <button class="btn-action" data-action="cover-letter" data-id="${job.id}">Cover Letter</button>
        </div>
        <div class="ats-panel hidden" data-id="${job.id}"></div>
    `;

    card.querySelectorAll('button.btn-action').forEach((btn) => {
        btn.addEventListener('click', () => {
            const job_data = jobsMap.get(btn.dataset.id) || job; // Always look up from Map
            runJobAction(btn.dataset.action, btn.dataset.id, job_data);
        });
    });

    return card;
}

async function runATS(jobId, job) {
    const panel = document.querySelector(`.ats-panel[data-id="${jobId}"]`);
    if (!panel) return;

    if (!panel.classList.contains('hidden') && panel.dataset.loaded === 'true') {
        panel.classList.add('hidden');
        return;
    }

    panel.classList.remove('hidden');
    panel.innerHTML = '<div class="ats-loading">Analyzing job description against your resume…</div>';

    try {
        const res = await fetch(`/jobs/${jobId}/ats`, { method: 'POST' });
        const data = await res.json();
        if (!res.ok) {
            panel.innerHTML = `<div class="ats-error">${esc(data.error || 'Failed to score.')}</div>`;
            return;
        }
        renderATS(panel, data);
        panel.dataset.loaded = 'true';
    } catch (err) {
        panel.innerHTML = `<div class="ats-error">Network error scoring ATS.</div>`;
    }
}

function renderATS(panel, data) {
    const ats = data.ats || {};
    const jd = data.parsed_jd || {};
    const match = ats.overall_match ?? 0;
    const matchClass = match >= 75 ? 'high' : match >= 50 ? 'mid' : 'low';

    const chipList = (arr, type) => (arr || []).map((s) => `<span class="ats-chip ats-chip-${type}">${esc(s)}</span>`).join('');
    const bullets = (arr) => (arr || []).map((s) => `<li>${esc(s)}</li>`).join('');
    const redFlags = (jd.red_flags || []).map((s) => `<li>${esc(s)}</li>`).join('');

    panel.innerHTML = `
        <div class="ats-header">
            <div class="ats-score ${matchClass}">
                <span class="ats-score-num">${match}</span>
                <span class="ats-score-label">% match</span>
            </div>
            <div class="ats-verdict">${esc(ats.verdict || '')}</div>
        </div>
        <div class="ats-grid">
            <div class="ats-col">
                <h4>Must-have skills</h4>
                <div class="ats-chips">${chipList(ats.must_have_matched, 'match')}${chipList(ats.must_have_missing, 'miss')}</div>
            </div>
            <div class="ats-col">
                <h4>Nice-to-have skills</h4>
                <div class="ats-chips">${chipList(ats.nice_to_have_matched, 'match')}${chipList(ats.nice_to_have_missing, 'miss')}</div>
            </div>
        </div>
        ${(ats.keyword_gaps || []).length ? `
        <div class="ats-section">
            <h4>Keywords to add to your resume</h4>
            <ul>${bullets(ats.keyword_gaps)}</ul>
        </div>` : ''}
        ${redFlags ? `
        <div class="ats-section ats-redflags">
            <h4>Red flags</h4>
            <ul>${redFlags}</ul>
        </div>` : ''}
    `;
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
        'cover-letter': 'Cover_Letter',
    }[action] || action;
    
    return `${role}_${company}_${actionLabel}.pdf`;
}

async function runJobAction(action, jobId, job) {
    currentJob = job;

    if (action === 'ats') {
        await runATS(jobId, job);
        return;
    }

    if (action === 'tailor') {
        await runTailorStream(jobId, job);
        return;
    }

    if (action === 'view-desc') {
        if (job.description && job.description.trim().length > 10) {
            openModal(`Job Description — ${job.title}`, job.description, 'markdown');
        } else {
            // LinkedIn and some other sites block description scraping
            const site = (job.site || '').toLowerCase();
            const applyUrl = job.job_url || '';
            const siteNote = site === 'linkedin'
                ? 'LinkedIn blocks automated description fetching.'
                : site === 'glassdoor'
                ? 'Glassdoor requires login to fetch descriptions.'
                : 'This job board does not provide descriptions via scraping.';

            modalTitle.textContent = `Job Description — ${job.title}`;
            modalBody.innerHTML = `
                <div style="text-align:center; padding: 1.5rem 0;">
                    <p style="font-size:2rem; margin-bottom:0.75rem;">🔒</p>
                    <p style="color:var(--text-primary); font-weight:600; margin-bottom:0.5rem;">${siteNote}</p>
                    <p style="color:var(--text-secondary); margin-bottom:1.5rem;">
                        View the full description directly on <strong>${job.site || 'the job board'}</strong>.
                    </p>
                    ${applyUrl ? `<a href="${esc(applyUrl)}" target="_blank" rel="noopener" class="btn-primary" style="display:inline-flex; text-decoration:none;">
                        Open Job on ${job.site || 'Site'} →
                    </a>` : ''}
                </div>
            `;
            modalBody.dataset.copyText = '';
            modalOverlay.classList.remove('hidden');
        }
        return;
    }

    const titles = {
        'tailor': `Tailored Resume — ${job.title}`,
        'outreach': `Outreach Email — ${job.company}`,
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
    pdfBtn.dataset.pdfBtn = 'true';
    pdfBtn.addEventListener('click', () => {
        if (action === 'tailor') {
            downloadResumePDF(data.content || '', currentJob);
        } else {
            downloadPDF(action, data);
        }
    });
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

function openModal(title, body, format = 'text') {
    modalTitle.textContent = title;
    setModalBody(body, format);
    modalOverlay.classList.remove('hidden');
}
function closeModal() {
    if (activeStream) { activeStream.close(); activeStream = null; }
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

// ===== Professional Resume PDF =====
// jsPDF default unit is mm, format a4 (210 x 297). We render the tailored
// resume text into a structured, ATS-friendly PDF with clickable links.

function isSectionHeading(line) {
    const t = line.trim();
    if (t.length < 2 || t.length > 40) return false;
    // All uppercase letters + spaces/ampersands/slashes, at least one letter
    return /^[A-Z][A-Z0-9 &/\-]+$/.test(t) && /[A-Z]/.test(t);
}

function isRoleHeader(line) {
    // Detects "Title — Company (2022 - Present)" style role headers
    return /\s[—–-]\s/.test(line) && /\(.+\d{4}.+\)\s*$/.test(line);
}

// Regex for emails / URLs / bare domains like linkedin.com/in/x or github.com/x
const LINK_RE = /(https?:\/\/\S+|[\w.+-]+@[\w.-]+\.\w+|(?:www\.)?(?:linkedin\.com|github\.com|gitlab\.com)\/\S+)/gi;

function normalizeUrl(raw) {
    const v = raw.replace(/[).,;]+$/, ''); // strip trailing punctuation
    if (v.includes('@') && !v.startsWith('mailto:')) return 'mailto:' + v;
    if (/^https?:\/\//i.test(v)) return v;
    return 'https://' + v;
}

function drawTextWithLinks(doc, text, x, y, options = {}) {
    // Draws text then overlays clickable rects on any detected links.
    const align = options.align || 'left';
    doc.text(text, x, y, { align });

    const fontHeight = doc.getLineHeight() / doc.internal.scaleFactor;
    const textW = doc.getTextWidth(text);
    let startX = x;
    if (align === 'center') startX = x - textW / 2;
    else if (align === 'right') startX = x - textW;

    LINK_RE.lastIndex = 0;
    let m;
    while ((m = LINK_RE.exec(text)) !== null) {
        const pre = text.slice(0, m.index);
        const preW = doc.getTextWidth(pre);
        const linkW = doc.getTextWidth(m[0]);
        doc.link(startX + preW, y - fontHeight + 0.5, linkW, fontHeight, {
            url: normalizeUrl(m[0]),
        });
    }
}

function downloadResumePDF(content, job) {
    const { jsPDF } = window.jspdf;
    if (!jsPDF) { alert('PDF library not loaded.'); return; }
    if (!content || !content.trim()) { alert('No tailored content to download.'); return; }

    const doc = new jsPDF();
    const pageW = doc.internal.pageSize.getWidth();
    const pageH = doc.internal.pageSize.getHeight();
    const marginX = 18;
    const marginTop = 18;
    const marginBottom = 15;
    const usableW = pageW - 2 * marginX;

    // Set PDF metadata so it's professional when viewed
    doc.setProperties({
        title: `${job?.title || 'Tailored'} — Resume`,
        subject: 'Tailored Resume',
        creator: 'AI Job Hunt Assistant',
    });

    const lines = content.split('\n').map((l) => l.trimEnd());
    let y = marginTop;
    let i = 0;

    const ensureSpace = (needed) => {
        if (y + needed > pageH - marginBottom) {
            doc.addPage();
            y = marginTop;
        }
    };

    // --- Header: name (first non-empty line) ---
    while (i < lines.length && !lines[i].trim()) i++;
    const name = (lines[i] || 'Resume').trim();
    i++;

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(20);
    doc.setTextColor(25, 25, 50);
    doc.text(name, pageW / 2, y, { align: 'center' });
    y += 7;

    // --- Contact line (next non-empty line, if it's not a section heading) ---
    while (i < lines.length && !lines[i].trim()) i++;
    if (i < lines.length && !isSectionHeading(lines[i])) {
        const contact = lines[i].trim();
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(9.5);
        doc.setTextColor(70, 70, 90);
        drawTextWithLinks(doc, contact, pageW / 2, y, { align: 'center' });
        y += 5;
        i++;
    }

    // --- Separator ---
    doc.setDrawColor(180, 180, 200);
    doc.setLineWidth(0.3);
    doc.line(marginX, y, pageW - marginX, y);
    y += 5;

    const LINE_H = 4.8; // mm per line of body text

    // --- Body ---
    while (i < lines.length) {
        const raw = lines[i];
        const line = raw.trim();

        if (!line) { y += 2.2; i++; continue; }

        if (isSectionHeading(line)) {
            ensureSpace(10);
            y += 2;
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(11);
            doc.setTextColor(25, 25, 50);
            doc.text(line, marginX, y);
            y += 1.5;
            doc.setDrawColor(200, 200, 215);
            doc.setLineWidth(0.2);
            doc.line(marginX, y, pageW - marginX, y);
            y += 4;
            i++;
            continue;
        }

        const bulletMatch = line.match(/^[-•*·]\s+(.+)/);
        if (bulletMatch) {
            const text = bulletMatch[1];
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(10);
            doc.setTextColor(45, 45, 60);
            const wrapped = doc.splitTextToSize(text, usableW - 5);
            ensureSpace(wrapped.length * LINE_H);
            doc.text('•', marginX + 1, y);
            wrapped.forEach((w, idx) => {
                drawTextWithLinks(doc, w, marginX + 5, y + idx * LINE_H);
            });
            y += wrapped.length * LINE_H;
            i++;
            continue;
        }

        // Role header: "Title — Company (dates)"
        if (isRoleHeader(line)) {
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(10.5);
            doc.setTextColor(30, 30, 55);
            const wrapped = doc.splitTextToSize(line, usableW);
            ensureSpace(wrapped.length * LINE_H);
            wrapped.forEach((w, idx) => {
                doc.text(w, marginX, y + idx * LINE_H);
            });
            y += wrapped.length * LINE_H + 0.5;
            i++;
            continue;
        }

        // Paragraph / regular line
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(45, 45, 60);
        const wrapped = doc.splitTextToSize(line, usableW);
        ensureSpace(wrapped.length * LINE_H);
        wrapped.forEach((w, idx) => {
            drawTextWithLinks(doc, w, marginX, y + idx * LINE_H);
        });
        y += wrapped.length * LINE_H;
        i++;
    }

    const filename = getFilename(job, 'tailor');
    doc.save(filename);
}

// ===== Streaming Resume Tailor =====
async function getResumeText() {
    if (cachedResumeText) return cachedResumeText;
    const res = await fetch('/resume');
    if (!res.ok) return '';
    const data = await res.json();
    cachedResumeText = data.raw_text || '';
    return cachedResumeText;
}

async function runTailorStream(jobId, job) {
    const originalText = await getResumeText();
    if (!originalText) {
        openModal('Tailor Resume', 'No resume loaded.', 'text');
        return;
    }

    // Abort any previous stream
    if (activeStream) { activeStream.close(); activeStream = null; }

    modalTitle.textContent = `Tailoring Resume — ${job.title}`;
    modalBody.innerHTML = `
        <div class="tailor-stream">
            <div class="tailor-status">
                <span class="pulse-dot"></span>
                <span id="tailor-status-text">Connecting to Claude...</span>
            </div>
            <div class="tailor-diff" id="tailor-diff"></div>
        </div>
    `;
    modalBody.dataset.copyText = '';
    modalOverlay.classList.remove('hidden');

    const diffEl = document.getElementById('tailor-diff');
    const statusEl = document.getElementById('tailor-status-text');

    let accumulated = '';
    let tokenCount = 0;
    let renderScheduled = false;

    const renderDiff = () => {
        renderScheduled = false;
        if (!window.Diff) {
            diffEl.textContent = accumulated;
            return;
        }
        const parts = window.Diff.diffLines(originalText, accumulated, { newlineIsToken: false });
        const html = parts.map((p) => {
            const cls = p.added ? 'diff-add' : p.removed ? 'diff-del' : 'diff-same';
            return `<span class="${cls}">${esc(p.value)}</span>`;
        }).join('');
        diffEl.innerHTML = html;
        diffEl.scrollTop = diffEl.scrollHeight;
    };

    const scheduleRender = () => {
        if (renderScheduled) return;
        renderScheduled = true;
        setTimeout(renderDiff, 120);
    };

    const source = new EventSource(`/jobs/${jobId}/tailor-stream`);
    activeStream = source;

    source.onmessage = (e) => {
        let msg;
        try { msg = JSON.parse(e.data); } catch { return; }

        if (msg.error) {
            statusEl.textContent = `Error: ${msg.error}`;
            source.close();
            activeStream = null;
            return;
        }
        if (msg.done) {
            statusEl.textContent = `Done — ${tokenCount} chunks streamed.`;
            document.querySelector('.pulse-dot')?.classList.add('done');
            renderDiff();
            modalBody.dataset.copyText = accumulated;
            updateModalWithPDF('tailor', { content: accumulated });
            source.close();
            activeStream = null;
            return;
        }
        if (msg.token) {
            accumulated += msg.token;
            tokenCount += 1;
            statusEl.textContent = `Streaming... ${tokenCount} chunks · ${accumulated.length} chars`;
            scheduleRender();
        }
    };

    source.onerror = () => {
        if (source.readyState === EventSource.CLOSED) return;
        statusEl.textContent = 'Connection dropped.';
        source.close();
        activeStream = null;
    };
}

