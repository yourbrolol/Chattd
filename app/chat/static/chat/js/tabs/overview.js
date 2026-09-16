import { openChatTab, closeTab, getTabElementById, openOverviewTab, openApplicationsTab, closeActiveTab } from './tabs.js';
import { api } from '../core/api.js';
import { AppError, toUserMessage } from '../core/errors.js';
import { state } from '../core/state.js';

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

const DELETE_CONFIRM_TIMEOUT_MS = 1000;

function resetDeleteButton(deleteBtn) {
    if (deleteBtn._disarmTimeout) {
        clearTimeout(deleteBtn._disarmTimeout);
        deleteBtn._disarmTimeout = null;
    }
    delete deleteBtn.dataset.armed;
    if (deleteBtn.dataset.originalText !== undefined) {
        deleteBtn.textContent = deleteBtn.dataset.originalText;
        delete deleteBtn.dataset.originalText;
    }
    deleteBtn.classList.remove('danger-armed');
    deleteBtn.disabled = false;
}

// Two-step inline confirm: first click arms ("Are you sure?"),
// second click within the timeout confirms. Returns true if confirmed.
function requestDeleteConfirmation(deleteBtn, timeoutMs = DELETE_CONFIRM_TIMEOUT_MS) {
    if (deleteBtn.dataset.armed === 'true') {
        return true;
    }
    if (deleteBtn.dataset.originalText === undefined) {
        deleteBtn.dataset.originalText = deleteBtn.textContent;
    }
    deleteBtn.dataset.armed = 'true';
    deleteBtn.textContent = 'Are you sure?';
    deleteBtn.classList.add('danger-armed');

    if (deleteBtn._disarmTimeout) clearTimeout(deleteBtn._disarmTimeout);
    deleteBtn._disarmTimeout = setTimeout(() => {
        resetDeleteButton(deleteBtn);
    }, timeoutMs);

    return false;
}

async function deleteRoom(roomName, deleteBtn) {
    if (deleteBtn && !requestDeleteConfirmation(deleteBtn)) return;
    try {
        if (deleteBtn) deleteBtn.disabled = true;
        await api.rooms.delete(roomName);
        if (deleteBtn) resetDeleteButton(deleteBtn);
        alert('Room deleted successfully.');
        closeRoomTabs(roomName);
    } catch (err) {
        if (deleteBtn) {
            resetDeleteButton(deleteBtn);
        }
        alert(toUserMessage(err));
        console.error('Delete room error:', err instanceof AppError ? err.toLogString() : err);
    }
}

async function leaveRoom(roomName) {
    if (!confirm('Are you sure you want to leave this room?')) return;
    try {
        await api.rooms.leave(roomName);
        alert('You have left the room.');
        closeRoomTabs(roomName);
    } catch (err) {
        alert(toUserMessage(err));
        console.error('Leave room error:', err instanceof AppError ? err.toLogString() : err);
    }
}

async function updateRoomName(oldName, newName, contentNode) {
    if (!newName || newName.trim() === "" || oldName === newName) return oldName;

    try {
        await api.rooms.update(oldName, { name: newName.trim() });

        alert('Room renamed successfully.');

        return newName.trim();
    } catch (err) {
        alert(toUserMessage(err));
        console.error('Update room name error:', err instanceof AppError ? err.toLogString() : err);
        return oldName;
    }
}

async function kickMember(member, contentNode) {
    if (member.username === state.username) {
        alert('You cannot kick yourself. To leave the room, use the Leave button.');
        return false;
    }
    if (!confirm(`Are you sure you want to kick ${member.username}?`)) return false;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        await api.rooms.kick(state.currentRoom, member.username, { headers: { 'X-CSRFToken': csrfToken } });
        alert(`${member.username} has been kicked from the room.`);
        contentNode.querySelector(`[data-member="${member.username}"]`)?.remove();
        return true;
    }
    catch (err) {
        alert(toUserMessage(err));
        console.error('Kick member error:', err instanceof AppError ? err.toLogString() : err);
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

function createMemberCard(member, memberTemplate, membersList, isOwner = false, contentNode, roomName = null) {
    if (!memberTemplate) return;
    const memberEl = memberTemplate.cloneNode(true);
    memberEl.classList.remove('hidden');
    memberEl.removeAttribute('data-role');

    const nameSpan = memberEl.querySelector('.member-card__name');
    const metaSpan = memberEl.querySelector('.member-card__meta');
    if (nameSpan) nameSpan.textContent = member.username;
    if (metaSpan) metaSpan.textContent = member.role;
    const isSelf = member.username === state.username;
    if (isSelf) memberEl.dataset.self = 'true';
    const kickBtn = memberEl.querySelector('.member-card__kick-btn');
    if (kickBtn) {
        if (isSelf) {
            kickBtn.textContent = 'Leave';
            kickBtn.classList.remove('hidden');
            kickBtn.onclick = async () => {
                await leaveRoom(roomName || state.currentRoom);
            };
        } else if (isOwner) {
            kickBtn.textContent = 'Kick';
            kickBtn.classList.remove('hidden');
            kickBtn.onclick = async () => {
                await kickMember(member, contentNode);
            };
        }
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
        resetDeleteButton(deleteBtn);
        deleteBtn.onclick = async (e) => {
            e.preventDefault();
            await deleteRoom(room.name, deleteBtn);
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
        const room = await api.rooms.get(targetRoom);
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
        console.log(room.members_data)

        room.members_data.sort((a, b) => {
            if (a.username === state.username) return -1;
            if (b.username === state.username) return 1;
            return 0;
        });

        room.members_data.forEach(member => {
            const memberEl = createMemberCard(member, memberTemplate, membersList, isOwner, contentNode, room.name);
            if (memberEl) membersList?.appendChild(memberEl);
            total++;
        });

        const totalEl = contentNode.querySelector('[data-role="overview-members-total"]') || contentNode.querySelector('#overview-members-total');
        if (totalEl) {
            totalEl.textContent = `Total members: ${total}`;
        }
    } catch (err) {
        const list = contentNode.querySelector('[data-role="overview-members-list"]') || contentNode.querySelector('#overview-members-list');
        if (errEl) {
            errEl.classList.remove('hidden');
            errEl.textContent = toUserMessage(err);
        } else if (list) list.textContent = toUserMessage(err);
        console.error('renderRoomOverview error:', err instanceof AppError ? err.toLogString() : err);
    }
}
