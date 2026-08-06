import { openChatTab, closeTab, getTabElementById } from './tabs.js';
import { api } from './api.js';
import { loadRooms } from './rooms.js';
import { state } from './state.js';

export async function handleGroupSubmission(e, contentNode) {
    e.preventDefault();
    if (!contentNode) return;

    const roomNameInput = contentNode.querySelector('[data-role="room-name-input"]') || contentNode.querySelector('#id_room_name');
    const roomTypeSelect = contentNode.querySelector('[data-role="room-type-select"]') || contentNode.querySelector('#id_room_type');
    const errorsDiv = contentNode.querySelector('[data-role="room-creation-errors"]') || contentNode.querySelector('#room-creation-errors');

    if (!roomNameInput || !roomTypeSelect) return;

    const roomName = roomNameInput.value.trim();

    // 1. Define the allowed characters regex (Matches Django Channels requirements)
    // Only allows ASCII alphanumerics, hyphens (-), underscores (_), and periods (.)
    const validRoomNameRegex = /^[a-zA-Z0-9._-]+$/;

    // 2. Validate the room name before sending it to the server
    if (!validRoomNameRegex.test(roomName)) {
        if (errorsDiv) {
            errorsDiv.textContent = 'Room name can only contain letters, numbers, hyphens, underscores, or periods. Spaces and special characters are not allowed.';
            errorsDiv.classList.remove('hidden');
        }
        return; // Stop the execution here so no fetch request is sent
    }
    
    const roomData = {
        'room_name': roomName,
        'room_type': roomTypeSelect.value,
    };

    try {
        const response = await api.rooms.create(roomData);
        const data = response.data

        if (response.ok) {
            roomNameInput.value = '';
            if (errorsDiv) {
                errorsDiv.classList.add('hidden');
                errorsDiv.textContent = '';
            }

            loadRooms((name) => { void openChatTab(name); });

            // remove any temporary "room-creation" tabs via central registry
            Object.keys(state.tabsById).forEach(id => {
                const t = state.tabsById[id];
                if (t && t.type === 'room-creation') {
                    const el = getTabElementById(id);
                    if (el) el.remove();
                    delete state.tabsById[id];
                }
            });

            setTimeout(() => { void openChatTab(roomName); }, 100);
        } else if (errorsDiv) {
            errorsDiv.textContent = 'An error occurred. Make sure the room name is unique and between 1-20 characters.';
            errorsDiv.classList.remove('hidden');
        }
    } catch (err) {
        console.error(err);
        if (errorsDiv) {
            errorsDiv.textContent = 'Network error. Please try again.';
            errorsDiv.classList.remove('hidden');
        }
    }
}

export function cancelGroupCreation(contentNode = null) {
    // close any room-creation tabs using the registry to ensure consistent cleanup
    Object.keys(state.tabsById).forEach(id => {
        const t = state.tabsById[id];
        if (t && t.type === 'room-creation') {
            const el = getTabElementById(id);
            if (el) closeTab(el);
        }
    });
}
