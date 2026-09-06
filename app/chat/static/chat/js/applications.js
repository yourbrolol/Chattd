import { api } from './api.js';
import { AppError, toUserMessage } from './errors.js';
import {
    activateTab,
    updateTabTitle,
    setTabMetadata,
    getTabElementById
} from './tabs.js';

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

/**
 * Submit a room application.
 * Returns { ok, status, app } on success or { ok: false, error } on failure.
 *   status: 'ok' | 'already_pending' | 'already_approved' | 'PENDING' | ...
 * Backend returns 201 for new, 200 {status} for idempotent re-apply.
 */
export async function applyToRoom(roomName) {
    const trimmed = (roomName || '').trim();
    if (!trimmed) return { ok: false, error: 'empty' };

    try {
        const data = await api.applications.apply(trimmed);
        // data: { id, room, status: 'PENDING', result: 'created'|'already_pending'|'already_approved' }
        return { ok: true, status: data?.result || 'ok', app: data };
    } catch (err) {
        console.error('applyToRoom failed:', err instanceof AppError ? err.toLogString() : err);
        return { ok: false, error: err instanceof AppError ? err.code : 'network' };
    }
}

/**
 * Approve or reject a room application (owner only).
 * action: 'approve' | 'reject'
 * Returns { ok, app } or { ok: false, error }.
 */
export async function reviewApplication(applicationId, action) {
    try {
        const data = await api.applications.review(applicationId, action);
        return { ok: true, error: null, app: data };
    } catch (err) {
        console.error('reviewApplication failed:', err instanceof AppError ? err.toLogString() : err);
        return { ok: false, error: err instanceof AppError ? err.code : 'network' };
    }
}

/**
 * Fetch pending applications for a room the current user owns.
 * Returns an array of { id, room, applicant, status } objects, or [].
 */
export async function loadRoomPendingApplications(roomName) {
    try {
        if (roomName) return await api.applications.list(roomName);
        return await api.applications.pending();
    } catch (err) {
        console.error('loadRoomPendingApplications failed:', err instanceof AppError ? err.toLogString() : err);
        return [];
    }
}

// SCRAPPED
export async function loadPendingApplications() {
    try {
        return await api.applications.pending();
    } catch (err) {
        console.error('loadPendingApplications failed:', err instanceof AppError ? err.toLogString() : err);
        return [];
    }
}

export function bindApplyRoomView(contentNode, roomName) {
    const nameEl = contentNode.querySelector('[data-role="apply-room-name"]');
    if (nameEl) nameEl.textContent = roomName || '';

    const errEl = contentNode.querySelector('[data-role="apply-room-errors"]');
    const okEl = contentNode.querySelector('[data-role="apply-room-success"]');
    const submitBtn = contentNode.querySelector('[data-role="apply-room-submit-btn"]');
    if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }
    if (okEl) { okEl.textContent = ''; okEl.classList.add('hidden'); }
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Send Request'; }

    submitBtn?.addEventListener('click', async () => {
        if (!roomName) return;

        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Sending\u2026'; }
        if (errEl) { errEl.classList.add('hidden'); errEl.textContent = ''; }
        if (okEl) { okEl.classList.add('hidden'); okEl.textContent = ''; }

        const result = await applyToRoom(roomName);

        if (!result.ok) {
            if (errEl) {
                errEl.textContent = toUserMessage({ code: result.error });
                errEl.classList.remove('hidden');
            }
            if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Send Request'; }
            return;
        }

        const successMsgs = {
            already_pending: 'Your request is already pending.',
            already_approved: 'You have already been approved. Try joining the room.',
        };
        const msg = successMsgs[result.status] || 'Request sent! Wait for the owner to review it.';
        if (okEl) { okEl.textContent = msg; okEl.classList.remove('hidden'); }
        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Request Sent'; }
    });

    contentNode.querySelector('[data-role="apply-room-cancel-btn"]')?.addEventListener('click', () => {
        const activeTab = document.querySelector('#tabs .tab.active');
        const tabId = activeTab?.getAttribute('data-tab-id');
        if (tabId) {
            setTabMetadata(tabId, { special: 'new-tab' });
            updateTabTitle(tabId, 'New Tab');
            const el = getTabElementById(tabId);
            if (el) activateTab(el);
        }
    });
}

export async function renderApplicationsList(contentNode, roomName) {
    const listEl = contentNode.querySelector('[data-role="applications-list"]');
    const emptyEl = contentNode.querySelector('[data-role="applications-empty"]');
    if (!listEl) return;

    listEl.innerHTML = '';

    const apps = await loadRoomPendingApplications(roomName);

    if (apps.length === 0) {
        emptyEl?.classList.remove('hidden');
        return;
    }
    emptyEl?.classList.add('hidden');

    apps.forEach(app => {
        const card = document.createElement('div');
        card.className = 'application-card';
        card.setAttribute('data-id', app.id);
        card.innerHTML = `
            <div class="application-card__info">
                <span class="application-card__user">${escapeHtml(app.applicant ?? '(deleted)')}</span>
                <span class="application-card__room">wants to join <strong>${escapeHtml(app.room)}</strong></span>
            </div>
            <div class="application-card__actions">
                <button class="btn-approve" data-id="${app.id}">Approve</button>
                <button class="btn-reject" data-id="${app.id}">Reject</button>
            </div>
        `;
        listEl.appendChild(card);
    });

    listEl.querySelectorAll('.btn-approve').forEach(btn => {
        btn.addEventListener('click', () => handleReview(Number(btn.dataset.id), 'approve', contentNode, roomName));
    });
    listEl.querySelectorAll('.btn-reject').forEach(btn => {
        btn.addEventListener('click', () => handleReview(Number(btn.dataset.id), 'reject', contentNode, roomName));
    });
}

async function handleReview(applicationId, action, contentNode, roomName) {
    const cardEl = contentNode.querySelector(`.application-card[data-id="${applicationId}"]`);
    if (cardEl) {
        cardEl.classList.add('application-card--loading');
        cardEl.querySelectorAll('button').forEach(btn => btn.disabled = true);
    }

    const result = await reviewApplication(applicationId, action);

    if (result.ok) {
        await renderApplicationsList(contentNode, roomName);
    } else {
        alert(toUserMessage({ code: result.error }));
        if (cardEl) {
            cardEl.classList.remove('application-card--loading');
            cardEl.querySelectorAll('button').forEach(btn => btn.disabled = false);
        }
    }
}

export async function updateReviewBadge() {
    const apps = await loadRoomPendingApplications();
    const badge = document.getElementById('review-apps-badge');
    if (!badge) return;
    if (apps.length > 0) {
        badge.textContent = apps.length > 9 ? '9+' : String(apps.length);
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
}
