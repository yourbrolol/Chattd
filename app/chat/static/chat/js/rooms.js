import { state } from './state.js';
import { api } from './api.js';

const JOIN_ERROR_MESSAGES = {
    not_found: 'Room not found. Check the name and try again.',
    forbidden: 'You cannot join this room.',
    auth_required: 'You must be logged in to join a room.',
    network: 'Network error. Please try again.',
    empty: 'Enter a room name.',
    app_required: 'This is a private room. You need to apply for membership.',
    app_pending: 'Your application is pending. Please wait for the owner to review it.',
};

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

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

    const formData = {
        'room_name': trimmed,
    }

    try {
        const response = await api.rooms.join(formData);
        console.log(response)

        if (response.status === 401) {
            return { ok: false, error: 'auth_required' };
        }
        else if (response.status === 404) {
            return { ok: false, error: 'not_found' };
        }
        else if (response.status === 403) {
            const data403 = response.error;
            // app_required / app_pending arrive as { warning: '...' }
            const warning = data403.warning;
            if (warning === 'app_required') return { ok: false, error: 'app_required', roomName: trimmed };
            if (warning === 'app_pending') return { ok: false, error: 'app_pending' };
            return { ok: false, error: 'forbidden' };
        }
        else if (!response.ok) {
            return { ok: false, error: 'network' };
        }

        const data = response.data;
        return { ok: true, name: data.name, roomType: data.room_type };
    } catch {
        return { ok: false, error: 'network' };
    }
}

export function getJoinErrorMessage(error) {
    return JOIN_ERROR_MESSAGES[error] || JOIN_ERROR_MESSAGES.network;
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
        .catch(err => console.error('Failed to load rooms:', err));
}
