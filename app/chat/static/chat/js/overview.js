import { openChatTab } from './tabs.js';
import { state } from './state.js';
import { openOverviewTab, openApplicationsTab, closeActiveTab } from './tabs.js';

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

async function deleteRoom(roomName) {
    if (!confirm('Are you sure you want to delete this room? This action cannot be undone.')) return;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const delRes = await fetch(`/rooms/${encodeURIComponent(roomName)}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
        });
        if (!delRes.ok) {
            alert('Failed to delete room. You might not have permission to do this.');
            return;
        }
        alert('Room deleted successfully.');
        closeActiveTab();
    } catch (err) {
        alert('An error occurred while trying to delete the room.');
        console.error('Delete room error:', err);
    }
}

async function leaveRoom(roomName) {
    if (!confirm('Are you sure you want to leave this room?')) return;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const leaveRes = await fetch(`/rooms/${encodeURIComponent(roomName)}/leave/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
        });
        if (!leaveRes.ok) {
            alert('Failed to leave room. You might not have permission to do this.');
            return;
        }
        alert('You have left the room.');
        closeActiveTab();
    } catch (err) {
        alert('An error occurred while trying to leave the room.');
        console.error('Leave room error:', err);
    }
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

        const isOwner = room.owner.username === state.username;

        const joinBtn = view.querySelector('#room-overview-join-btn');
        if (joinBtn) {
            joinBtn.onclick = async () => {
                await openChatTab(room.name);
            };
        }

        const appsBtn = view.querySelector('#overview-apps-btn');
        if (appsBtn) {
            appsBtn.onclick = () => {
                openApplicationsTab();
            };
        }

        const deleteBtn = view.querySelector('#room-overview-delete-btn');
        if (deleteBtn) {
            if (isOwner) deleteBtn.classList.remove('hidden');
            else deleteBtn.classList.add('hidden');
            deleteBtn.onclick = async () => {
                await deleteRoom(room.name);
            };
        }

        const leaveBtn = view.querySelector('#room-overview-leave-btn');
        if (leaveBtn) {
            if (!isOwner) leaveBtn.classList.remove('hidden');
            else leaveBtn.classList.add('hidden');
            leaveBtn.onclick = async () => {
                await leaveRoom(room.name);
            };
        }

        const memberTemplate = view.querySelector('.member-card');
        const membersList = view.querySelector('#overview-members-list');

        if (membersList) {
            membersList.querySelectorAll('.member-card:not(.hidden)').forEach(el => el.remove());
        }

        let total = 0;

        room.members_data.forEach(member => {
            const memberEl = memberTemplate.cloneNode(true);
            memberEl.classList.remove('hidden');
            console.log(member)
            memberEl.querySelector('.member-card__name').textContent = member.user__username;
            memberEl.querySelector('.member-card__meta').textContent = member.role;
            membersList?.appendChild(memberEl);
            total++;
        });

        view.querySelector('#overview-members-total').textContent = `Total members: ${total}`;
    } catch (err) {
        const list = view.querySelector('#overview-members-list');
        if (list) list.textContent = 'Failed to load room details.';
        console.error('renderRoomOverview error:', err);
    }
}