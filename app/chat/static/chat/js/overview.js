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

    view.innerHTML = `
        <div class="overview-header"><h2>${escapeHtml(targetRoom || 'Rooms')}</h2></div>
        <div id="overview-list" class="overview-list">Loading…</div>
    `;

    if (!targetRoom) {
        const list = view.querySelector('#overview-list');
        if (list) {
            list.textContent = 'No room selected.';
        }
        return;
    }

    try {
        const res = await fetch(`/rooms/${encodeURIComponent(targetRoom)}/`);
        const list = view.querySelector('#overview-list');
        if (!list) return;

        if (!res.ok) {
            list.innerHTML = '';
            list.textContent = 'Room not found or you are not a member.';
            return;
        }

        const room = await res.json();
        list.innerHTML = '';

        const card = document.createElement('div');
        card.className = 'overview-room-card';
        card.innerHTML = `
            <div class="overview-room-card__name">${escapeHtml(room.name)}</div>
            <div class="overview-room-card__meta">Type: ${escapeHtml(room.room_type || '')}</div>
            <div class="overview-room-card__actions">
                <button class="btn-open">Open</button>
            </div>
        `;
        card.querySelector('.btn-open')?.addEventListener('click', async () => {
            await openChatTab(room.name);
        });
        list.appendChild(card);
    } catch (err) {
        const list = view.querySelector('#overview-list');
        if (list) list.textContent = 'Failed to load room details.';
        console.error('renderRoomOverview error:', err);
    }
}