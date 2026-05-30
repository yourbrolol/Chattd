import { sendMessage } from './socket.js';
import { openNewTab, activateTab, cycleTabLeft, cycleTabRight, closeActiveTab, updateTabTitle, setTabMetadata, getTabElementById, openChatTab, openOverviewTab } from './tabs.js';
import { state } from './state.js';
import { handleGroupSubmission, cancelGroupCreation } from './room.js';
import { loadRooms, joinRoom, showJoinError, getJoinErrorMessage } from './rooms.js';
import { applyToRoom, reviewApplication, loadPendingApplications } from './applications.js';
import { renderRoomOverview } from './overview.js';
import { switchView } from './views.js';
import { openSettings } from './settings.js';

function setUsername() {
    const userEl = document.getElementById('username-p');
    if (userEl) state.username = userEl.textContent || null;
}

function bindMessageInput() {
    const msgInput = document.getElementById('chat-message-input');
    msgInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    const submitBtn = document.getElementById('chat-message-submit');
    if (submitBtn) submitBtn.onclick = sendMessage;
}

function bindTabs() {
    document.getElementById('add-tab-btn')?.addEventListener('click', openNewTab);

    document.getElementById('tabs')?.addEventListener('click', (e) => {
        const clickedTab = e.target.closest('.tab');
        if (clickedTab) activateTab(clickedTab);
    });
}

function isTypingTarget(target) {
    return target instanceof HTMLInputElement
        || target instanceof HTMLTextAreaElement
        || target instanceof HTMLSelectElement
        || target.isContentEditable;
}

function bindSlashFocus() {
    document.addEventListener('keydown', (e) => {
        if (e.key !== '/' || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
        if (isTypingTarget(e.target)) return;

        const chatView = document.getElementById('chat');
        const input = document.getElementById('chat-message-input');
        if (!input || chatView?.classList.contains('hidden')) return;

        e.preventDefault();
        input.focus();
    }, true);
}

function bindTabKeyboard() {
    document.addEventListener('keydown', (e) => {
        if (!e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;

        if (e.key === '1') {
            e.preventDefault();
            cycleTabLeft();
        } else if (e.key === '2') {
            e.preventDefault();
            cycleTabRight();
        } else if (e.key === '4') {
            e.preventDefault();
            closeActiveTab();
        } else if (e.key === '5') {
            e.preventDefault();
            renderRoomOverview();
        }
    });
}

// ---------- Apply-to-room view ----------

let _pendingApplyRoomName = null;

function showApplyRoomView(roomName) {
    _pendingApplyRoomName = roomName;
    const nameEl = document.getElementById('apply-room-name');
    if (nameEl) nameEl.textContent = roomName;

    const errEl = document.getElementById('apply-room-errors');
    const okEl = document.getElementById('apply-room-success');
    const submitBtn = document.getElementById('apply-room-submit-btn');
    if (errEl) { errEl.textContent = ''; errEl.classList.add('hidden'); }
    if (okEl) { okEl.textContent = ''; okEl.classList.add('hidden'); }
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Send Request'; }

    switchView('apply-room');
}

function bindApplyRoomView() {
    document.getElementById('apply-room-submit-btn')?.addEventListener('click', async () => {
        if (!_pendingApplyRoomName) return;

        const submitBtn = document.getElementById('apply-room-submit-btn');
        const errEl = document.getElementById('apply-room-errors');
        const okEl = document.getElementById('apply-room-success');

        if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Sending…'; }
        if (errEl) { errEl.classList.add('hidden'); errEl.textContent = ''; }
        if (okEl) { okEl.classList.add('hidden'); okEl.textContent = ''; }

        const result = await applyToRoom(_pendingApplyRoomName);

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

    document.getElementById('apply-room-cancel-btn')?.addEventListener('click', () => {
        _pendingApplyRoomName = null;
        switchView('new-tab');
    });
}

// ---------- Review-applications view ----------

async function renderApplicationsList() {
    const listEl = document.getElementById('applications-list');
    const emptyEl = document.getElementById('applications-empty');
    if (!listEl) return;

    listEl.innerHTML = '';
    const apps = await loadPendingApplications();

    if (apps.length === 0) {
        emptyEl?.classList.remove('hidden');
        return;
    }
    emptyEl?.classList.add('hidden');

    apps.forEach(app => {
        const card = document.createElement('div');
        card.className = 'application-card';
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
        btn.addEventListener('click', () => handleReview(Number(btn.dataset.id), 'approve'));
    });
    listEl.querySelectorAll('.btn-reject').forEach(btn => {
        btn.addEventListener('click', () => handleReview(Number(btn.dataset.id), 'reject'));
    });
}

async function handleReview(appId, action) {
    const card = document.querySelector(`[data-id="${appId}"]`)?.closest('.application-card');
    if (card) {
        card.classList.add('application-card--loading');
        card.querySelectorAll('button').forEach(b => { b.disabled = true; });
    }

    const result = await reviewApplication(appId, action);
    if (result.ok) {
        card?.remove();
        const listEl = document.getElementById('applications-list');
        if (listEl && listEl.children.length === 0) {
            document.getElementById('applications-empty')?.classList.remove('hidden');
        }
        updateReviewBadge();
    } else {
        if (card) {
            card.classList.remove('application-card--loading');
            card.querySelectorAll('button').forEach(b => { b.disabled = false; });
        }
    }
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

async function updateReviewBadge() {
    const apps = await loadPendingApplications();
    const badge = document.getElementById('review-apps-badge');
    if (!badge) return;
    if (apps.length > 0) {
        badge.textContent = apps.length > 9 ? '9+' : String(apps.length);
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
}

function bindReviewApplicationsView() {
    document.getElementById('review-apps-btn')?.addEventListener('click', async () => {
        await renderApplicationsList();
        switchView('review-applications');
    });
}

// ---------- Join flow ----------

async function joinRoomAndOpen(roomName) {
    const result = await joinRoom(roomName);
    if (!result.ok) {
        if (result.error === 'app_required') {
            showJoinError('');
            showApplyRoomView(result.roomName || roomName);
            return false;
        }
        showJoinError(getJoinErrorMessage(result.error));
        return false;
    }

    showJoinError('');
    loadRooms((name) => { void openChatTab(name); });
    await openChatTab(result.name);
    return true;
}

function bindJoinRoom() {
    const joinBtn = document.getElementById('dashboard-join-room-btn');
    const joinInput = document.getElementById('dashboard-join-room-input');

    joinBtn?.addEventListener('click', async () => {
        if (!joinInput) return;
        await joinRoomAndOpen(joinInput.value);
    });

    joinInput?.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            await joinRoomAndOpen(joinInput.value);
        }
    });
}

function bindGroupCreation() {
    document.getElementById('room-creation-form')?.addEventListener('submit', handleGroupSubmission);
    document.getElementById('cancel-room-btn')?.addEventListener('click', cancelGroupCreation);

    document.getElementById('dashboard-create-room-btn')?.addEventListener('click', () => {
        const activeTab = document.querySelector('#tabs .tab.active');
        const tabId = activeTab?.getAttribute('data-tab-id');
        if (tabId) {
            const t = tabId ? state.tabsById[tabId] : null;
            if (t && t.type === 'new-tab') {
                setTabMetadata(tabId, { special: 'room-creation' });
                updateTabTitle(tabId, 'Create Room');
                const el = getTabElementById(tabId);
                if (el) activateTab(el);
            }
        }
    });
}

// Room overview flow

function openRoomOverview() {
    const btn = document.getElementById('hamburger-btn');
    btn?.addEventListener('click', () => {
        renderRoomOverview();
    });
}

// Settings flow

function bindSettings() {
    const settingsBtn = document.getElementById('user');
    settingsBtn?.addEventListener('click', () => {
        openSettings();
    });
}

export function initApp() {
    setUsername();
    bindMessageInput();
    bindTabs();
    bindTabKeyboard();
    bindSlashFocus();
    bindJoinRoom();
    bindGroupCreation();
    bindApplyRoomView();
    bindReviewApplicationsView();
    openRoomOverview();
    bindSettings();
    loadRooms((name) => { void openChatTab(name); });
    updateReviewBadge();
}