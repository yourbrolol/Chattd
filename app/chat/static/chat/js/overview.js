import { openChatTab, closeTab, getTabElementById, openOverviewTab, openApplicationsTab, closeActiveTab } from './tabs.js';
import { state } from './state.js';

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function closeRoomTabs(roomName) {
    Object.keys(state.tabsById).forEach(id => {
        const t = state.tabsById[id];
        if (t && (t.type === 'room-overview' && t.metadata?.relatedRoom === roomName)) {
            const el = getTabElementById(id);
            if (el) closeTab(el);
        }
        if (t && (t.type === 'room' && t.metadata?.room === roomName)) {
            const el = getTabElementById(id);
            if (el) closeTab(el);
        }
    });
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
        closeRoomTabs(roomName);
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
        closeRoomTabs(roomName);
    } catch (err) {
        alert('An error occurred while trying to leave the room.');
        console.error('Leave room error:', err);
    }
}

async function updateRoomName(oldName, newName, contentNode) {
    if (!newName || newName.trim() === "" || oldName === newName) return oldName;

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const response = await fetch(`/rooms/${encodeURIComponent(oldName)}/edit/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ name: newName.trim() })
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            alert(data.error || 'Failed to update room name.');
            return oldName;
        }

        alert('Room renamed successfully.');

        return newName.trim();
    } catch (err) {
        alert('An error occurred while updating the room name.');
        console.error('Update room name error:', err);
        return oldName;
    }
}

async function kickMember(member) {
    if (member.username === state.username) {
        alert('You cannot kick yourself. To leave the room, use the Leave button.');
        return false;
    }
    if (!confirm(`Are you sure you want to kick ${member.username}?`)) return false;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch(`/rooms/${encodeURIComponent(state.currentRoom)}/kick/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ username: member.username })
        });
        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            alert(data.error || 'Failed to kick member. You might not have permission to do this.');
            return;
        }
        alert(`${member.username} has been kicked from the room.`);
        return true;
    }
    catch (err) {
        alert('An error occurred while trying to kick the member.');
        console.error('Kick member error:', err);
        return false;
    }
}

function bindInlineNameEditing(nameEl, nameInput, targetRoom, isOwner, contentNode) {
    if (isOwner) {
        nameEl.classList.add('editable-name');
        nameEl.setAttribute('title', 'Click to rename');

        nameEl.onclick = () => {
            nameEl.classList.add('hidden');
            nameInput.classList.remove('hidden');
            nameInput.value = nameEl.textContent;
            nameInput.focus();
        };

        const saveEdit = async () => {
            if (nameInput.classList.contains('hidden')) return;

            const updatedValue = nameInput.value.trim();
            console.log('Attempting to save new room name:', updatedValue);
            if (updatedValue && updatedValue !== nameEl.textContent) {
                const savedName = await updateRoomName(targetRoom, updatedValue, contentNode);
                nameEl.textContent = savedName;

                if (savedName !== targetRoom) {
                    targetRoom = savedName;
                }
            }

            nameInput.classList.add('hidden');
            nameEl.classList.remove('hidden');
        };

        // Save on Enter, Cancel on Escape
        nameInput.onkeydown = async (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                await saveEdit();
            } else if (e.key === 'Escape') {
                nameInput.classList.add('hidden');
                nameEl.classList.remove('hidden');
            }
        };

        nameInput.onblur = async () => {
            await saveEdit();
        };
    } else {
        nameEl.classList.remove('editable-name');
        nameEl.removeAttribute('title');
        nameEl.onclick = null;
    }
}

function createMemberCard(member, memberTemplate, membersList, isOwner = false) {
    if (!memberTemplate) return;
    const memberEl = memberTemplate.cloneNode(true);
    memberEl.classList.remove('hidden');
    memberEl.removeAttribute('data-role');

    const nameSpan = memberEl.querySelector('.member-card__name');
    const metaSpan = memberEl.querySelector('.member-card__meta');
    if (nameSpan) nameSpan.textContent = member.username;
    if (metaSpan) metaSpan.textContent = member.role;
    if (isOwner) {
        const kickBtn = memberEl.querySelector('.member-card__kick-btn');
        if (kickBtn) kickBtn.classList.remove('hidden');
        kickBtn.onclick = async () => {
            kicked = await kickMember(member);
        };
    }

    const avatarDiv = memberEl.querySelector('.member-card__avatar');
    if (avatarDiv) {
        if (member.avatar) {
            console.log(member.avatar);
            avatarDiv.innerHTML = `<img src="${member.avatar}" alt="${escapeHtml(member.username)}" class="member-avatar-img" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        } else {
            avatarDiv.textContent = (member.username || '?').substring(0, 1).toUpperCase();
        }
    }

    return memberEl;
}

function bindActionButtons(contentNode, room, isOwner) {
    const joinBtn = contentNode.querySelector('[data-role="room-overview-join-btn"]') || contentNode.querySelector('#room-overview-join-btn');
    if (joinBtn) {
        joinBtn.onclick = async () => {
            await openChatTab(room.name);
        };
    }

    const appsBtn = contentNode.querySelector('[data-role="overview-apps-btn"]') || contentNode.querySelector('#overview-apps-btn');
    if (appsBtn) {
        appsBtn.onclick = () => {
            openApplicationsTab(room.name);
        };
    }

    const deleteBtn = contentNode.querySelector('[data-role="room-overview-delete-btn"]') || contentNode.querySelector('#room-overview-delete-btn');
    if (deleteBtn) {
        if (isOwner) deleteBtn.classList.remove('hidden');
        else deleteBtn.classList.add('hidden');
        deleteBtn.onclick = async () => {
            await deleteRoom(room.name);
        };
    }

    const leaveBtn = contentNode.querySelector('[data-role="room-overview-leave-btn"]') || contentNode.querySelector('#room-overview-leave-btn');
    if (leaveBtn) {
        if (!isOwner) leaveBtn.classList.remove('hidden');
        else leaveBtn.classList.add('hidden');
        leaveBtn.onclick = async () => {
            await leaveRoom(room.name);
        };
    }
}

export async function renderRoomOverview(roomName = null, contentNode = null) {
    let targetRoom = roomName || state.currentRoom;
    if (!targetRoom) return;

    if (!contentNode) {
        const tabInfo = Object.values(state.tabsById).find(t => t.type === 'room-overview' && t.metadata?.relatedRoom === targetRoom);
        contentNode = tabInfo?.contentNode;
    }
    if (!contentNode) return;

    const errEl = contentNode.querySelector('[data-role="error-message"]') || contentNode.querySelector('#error-message');
    if (errEl) errEl.classList.add('hidden');
    const nameEl = contentNode.querySelector('[data-role="room-name"]') || contentNode.querySelector('#room-name');
    if (nameEl) nameEl.textContent = targetRoom || 'No room selected';
    const typeEl = contentNode.querySelector('[data-role="room-type"]') || contentNode.querySelector('#room-type');
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
        if (typeEl) typeEl.textContent = `Type: ${escapeHtml(room.room_type)}`;

        const isOwner = room.owner === state.username;
        console.log('Room details:', room, 'Is owner:', isOwner);

        const nameInput = contentNode.querySelector('[data-role="room-name-input"]');

        if (nameEl && nameInput) bindInlineNameEditing(nameEl, nameInput, targetRoom, isOwner, contentNode);

        bindActionButtons(contentNode, room, isOwner);

        const memberTemplate = contentNode.querySelector('[data-role="member-card-template"]') || contentNode.querySelector('.member-card');
        const membersList = contentNode.querySelector('[data-role="overview-members-list"]') || contentNode.querySelector('#overview-members-list');

        if (membersList) {
            membersList.querySelectorAll('.member-card:not(.hidden), article:not(.hidden)').forEach(el => el.remove());
        }

        let total = 0;

        room.members_data.forEach(member => {
            const memberEl = createMemberCard(member, memberTemplate, membersList, isOwner);
            if (memberEl) membersList?.appendChild(memberEl);
            total++;
        });

        const totalEl = contentNode.querySelector('[data-role="overview-members-total"]') || contentNode.querySelector('#overview-members-total');
        if (totalEl) {
            totalEl.textContent = `Total members: ${total}`;
        }
    } catch (err) {
        const list = contentNode.querySelector('[data-role="overview-members-list"]') || contentNode.querySelector('#overview-members-list');
        if (list) list.textContent = 'Failed to load room details.';
        console.error('renderRoomOverview error:', err);
    }
}