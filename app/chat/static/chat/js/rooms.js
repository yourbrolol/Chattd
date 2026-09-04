import { state } from './state.js';
import { api } from './api.js';
import { AppError, toUserMessage } from './errors.js';

export function showJoinError(message) {
    const activeTab = document.querySelector('#tabs .tab.active');
    const tabId = activeTab?.getAttribute('data-tab-id');
    const tabInfo = tabId ? state.tabsById[tabId] : null;
    const contentNode = tabInfo?.contentNode;
    if (!contentNode) return;

    const errorsDiv = contentNode.querySelector('[data-role="join-room-errors"]') || contentNode.querySelector('#join-room-errors');
    if (!errorsDiv) return;
    if (!message) {
        errorsDiv.classList.add('hidden');
        errorsDiv.textContent = '';
        return;
    }
    errorsDiv.textContent = message;
    errorsDiv.classList.remove('hidden');
}

export async function joinRoom(roomName) {
    const trimmed = (roomName || '').trim();
    if (!trimmed) {
        return { ok: false, error: 'empty' };
    }

    try {
        const data = await api.rooms.join({ room_name: trimmed });
        return { ok: true, name: data.name, roomType: data.room_type };
    } catch (err) {
        // Dev: structured log with code/status/ref; user: code only.
        console.error('joinRoom failed:', err instanceof AppError ? err.toLogString() : err, err?.cause ?? '');
        const code = err instanceof AppError ? err.code : 'network';
        if (code === 'app_required') return { ok: false, error: 'app_required', roomName: trimmed };
        if (code === 'app_pending') return { ok: false, error: 'app_pending' };
        return { ok: false, error: code };
    }
}

/** Legacy alias — prefer toUserMessage(err) from errors.js in new code. */
export function getJoinErrorMessage(error) {
    return toUserMessage({ code: error });
}

export function loadRooms(onRoomClick) {
    const listDiv = document.getElementById('rooms-list');
    if (!listDiv) return;

    listDiv.innerHTML = '';

    api.rooms.list()
        .then(rooms => {
            rooms.forEach(r => {
                const btn = document.createElement('div');
                btn.className = 'room';
                btn.textContent = r.name;

                listDiv.appendChild(btn);

                btn.addEventListener('pointerup', () => onRoomClick?.(r.name));
            });
        })
        .catch(err => console.error('Failed to load rooms:', err instanceof AppError ? err.toLogString() : err));
}
