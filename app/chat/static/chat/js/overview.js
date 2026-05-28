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

        const memberTemplate = view.querySelector('.member-card');

        room.members_data.forEach(member => {
            const memberEl = memberTemplate.cloneNode(true);
            memberEl.classList.remove('hidden');
            console.log(member)
            memberEl.querySelector('.member-card__name').textContent = member.user__username;
            memberEl.querySelector('.member-card__meta').textContent = member.role;
            view.getElementsByClassName('overview-members-list')?.[0]?.appendChild(memberEl);
        });
    } catch (err) {
        const list = view.getElementsByClassName('overview-members-list');
        if (list) list[0].textContent = 'Failed to load room details.';
        console.error('renderRoomOverview error:', err);
    }
}