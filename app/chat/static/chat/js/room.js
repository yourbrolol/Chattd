import { openChatTab, closeTab, getTabElementById } from './tabs.js';
import { loadRooms } from './rooms.js';
import { state } from './state.js';

export async function handleGroupSubmission(e) {
    e.preventDefault();

    const roomNameInput = document.getElementById('id_room_name');
    const roomTypeSelect = document.getElementById('id_room_type');
    const errorsDiv = document.getElementById('room-creation-errors');

    if (!roomNameInput || !roomTypeSelect) return;

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const formData = new URLSearchParams();
    formData.append('csrfmiddlewaretoken', csrfToken);
    formData.append('room_name', roomNameInput.value);
    formData.append('room_type', roomTypeSelect.value);

    try {
        const response = await fetch('/rooms/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        const isSuccess = response.redirected || !response.url.endsWith('/rooms/create');

        if (response.ok && isSuccess) {
            const newRoomName = roomNameInput.value.trim();
            roomNameInput.value = '';
            if (errorsDiv) {
                errorsDiv.classList.add('hidden');
                errorsDiv.textContent = '';
            }

            loadRooms((name) => { void openChatTab(name); });

            const tabsContainer = document.getElementById('tabs');
            // remove any temporary "room-creation" tabs via central registry
            Object.keys(state.tabsById).forEach(id => {
                const t = state.tabsById[id];
                if (t && t.type === 'room-creation') {
                    const el = getTabElementById(id);
                    if (el) el.remove();
                    delete state.tabsById[id];
                }
            });

            setTimeout(() => { void openChatTab(newRoomName); }, 100);
        } else if (errorsDiv) {
            errorsDiv.textContent = 'An error occurred. Make sure the room name is unique, between 1-20 characters, and contains no special characters.';
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

export function cancelGroupCreation() {
    // close any room-creation tabs using the registry to ensure consistent cleanup
    Object.keys(state.tabsById).forEach(id => {
        const t = state.tabsById[id];
        if (t && t.type === 'room-creation') {
            const el = getTabElementById(id);
            if (el) closeTab(el);
        }
    });
}
