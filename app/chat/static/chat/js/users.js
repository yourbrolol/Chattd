import { api } from './api.js';
import { AppError, toUserMessage } from './errors.js';

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export async function renderUserDetail(username = "Anonymous", avatarUrl = null, contentNode = null) {
    if (!contentNode) return;

    const avatarEl = contentNode.querySelector('[data-role="user-avatar"]');
    const displayNameEl = contentNode.querySelector('[data-role="user-display-name"]');
    const usernameEl = contentNode.querySelector('[data-role="user-username"]');
    const bioEl = contentNode.querySelector('[data-role="user-bio"]');
    const statusBadgeEl = contentNode.querySelector('[data-role="user-status-badge"]');
    const errEl = contentNode.querySelector('[data-role="user-detail-errors"]');

    if (errEl) {
        errEl.classList.add('hidden');
        errEl.textContent = '';
    }

    const setAvatar = (url) => {
        if (!avatarEl) return;
        if (url) {
            avatarEl.innerHTML = `<img src="${escapeHtml(url)}" alt="${escapeHtml(username)}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        } else {
            avatarEl.textContent = (username || '?').substring(0, 1).toUpperCase();
        }
    };

    if (displayNameEl) displayNameEl.textContent = username || "Anonymous";
    if (usernameEl) usernameEl.textContent = username ? `@${username}` : "@Anonymous";
    if (bioEl) bioEl.textContent = "No bio yet.";
    if (statusBadgeEl) statusBadgeEl.textContent = "Online";

    setAvatar(avatarUrl);

    if (!username || username === "Anonymous") return;

    try {
        const user = await api.users.getByUsername(username);
        if (!user) return;

        if (displayNameEl) displayNameEl.textContent = user.username || username;
        if (usernameEl) usernameEl.textContent = user.username ? `@${user.username}` : `@${username}`;
        if (user.avatar_url) setAvatar(user.avatar_url);
    } catch (err) {
        if (errEl) {
            errEl.classList.remove('hidden');
            errEl.textContent = toUserMessage(err);
        }
        console.error('renderUserDetail error:', err instanceof AppError ? err.toLogString() : err);
    }
}
