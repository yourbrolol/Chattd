import { api } from './api.js';
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
 *   status: 'ok' | 'already_pending' | 'already_approved' | 'already_member'
 */
export async function applyToRoom(roomName) {
    const trimmed = (roomName || '').trim();
    if (!trimmed) return { ok: false, error: 'empty' };

    try {
        const response = await api.applications.apply(trimmed);

        const data = await response.data;

        if (response.status === 401) return { ok: false, error: 'auth_required' };
        if (response.status === 404) return { ok: false, error: 'not_found' };
        if (response.status === 400) return { ok: false, error: data.error || 'unknown' };
        if (!response.ok && response.status !== 200) return { ok: false, error: 'network' };

        // 201 = new application, 200 = already_pending / already_approved
        return { ok: true, status: data.warning || 'ok', app: data };
    } catch {
        return { ok: false, error: 'network' };
    }
}

/**
 * Approve or reject a room application (owner only).
 * action: 'approve' | 'reject'
 * Returns { ok, app } or { ok: false, error }.
 */
export async function reviewApplication(applicationId, action) {
    try {
        const response = await api.applications.review(applicationId, action);

        if (response.status === 403) return { ok: false, error: 'forbidden' };
        if (response.status === 404) return { ok: false, error: 'not_found' };
        if (!response.ok) return { ok: false, error: 'network' };

        return { ok: true, error: null };
    } catch (e) {
        console.error(e)
        return { ok: false, error: 'network' };
    }
}

/**
 * Fetch pending applications for a room the current user owns.
 * Returns an array of { id, room, applicant, status } objects, or [].
 */
export async function loadRoomPendingApplications(roomName) {
    if (!roomName) return [];
    
    try {
        const response = await api.applications.list(roomName);
        if (!response.ok) return [];
        return await response.data;
    } catch {
        return [];
    }
}

// SCRAPPED
export async function loadPendingApplications() {
    try {
        const response = await api.applications.pending();
        if (!response.ok) return [];
        return await response.data;
    } catch {
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

        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Sending…'; }
        if (errEl) { errEl.classList.add('hidden'); errEl.textContent = ''; }
        if (okEl) { okEl.classList.add('hidden'); okEl.textContent = ''; }

        const result = await applyToRoom(roomName);

        if (!result.ok) {
            const msgs = {
                auth_required: 'You must be logged in.',
                not_found: 'Room not found.',
                already_member: 'You are already a member.',
                empty: 'No room specified.',
                network: 'Network error. Please try again.',
            };
            if (errEl) {
                errEl.textContent = msgs[result.error] || 'Something went wrong.';
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
        alert(`Failed to execute review: ${result.error}`);
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
