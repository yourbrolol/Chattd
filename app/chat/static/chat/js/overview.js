import { openChatTab } from './tabs.js';
import { state } from './state.js';
import { openOverviewTab } from './tabs.js';

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// renderRoomOverview: render details only for a specific room.
// If no roomName is provided, it falls back to state.currentRoom.
export async function renderRoomOverview(roomName = null) {
    const view = document.getElementById('room-overview-view');
    if (!view) return;

    const targetRoom = roomName || state.currentRoom;
    openOverviewTab(targetRoom);

    const errEl = view.querySelector('#error-message');
    if (errEl) errEl.classList.add('hidden');
    const nameEl = view.querySelector('#room-name');
    if (nameEl) nameEl.textContent = targetRoom || 'No room selected';
    const typeEl = view.querySelector('#room-type');
    if (typeEl) typeEl.textContent = '';

    try {
        const res = await fetch(`/rooms/${encodeURIComponent(targetRoom)}/`);

        if (!res.ok) {
            if (errEl) {
                errEl.classList.remove('hidden');
                errEl.textContent = 'Room not found or you are not a member.';
            }
            return;
        }

        const room = await res.json();
        view.querySelector('#room-type').textContent = `Type: ${escapeHtml(room.room_type)}`;

        const joinBtn = view.querySelector('#room-overview-join-btn');

        joinBtn?.addEventListener('click', async () => {
            await openChatTab(room.name);
        });
    } catch (err) {
        const list = view.querySelector('#overview-list');
        if (list) list.textContent = 'Failed to load room details.';
        console.error('renderRoomOverview error:', err);
    }
}