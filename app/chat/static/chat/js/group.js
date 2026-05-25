import { openChatTab, closeTab } from './tabs.js';
import { loadRooms } from './rooms.js';

export async function handleGroupSubmission(e) {
    e.preventDefault();

    const roomNameInput = document.getElementById('id_room_name');
    const roomTypeSelect = document.getElementById('id_room_type');
    const errorsDiv = document.getElementById('group-creation-errors');

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
            if (tabsContainer) {
                tabsContainer.querySelectorAll('.tab').forEach(tab => {
                    if (tab.getAttribute('data-special') === 'group-creation') {
                        tab.remove();
                    }
                });
            }

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
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    tabsContainer.querySelectorAll('.tab').forEach(tab => {
        if (tab.getAttribute('data-special') === 'group-creation') {
            closeTab(tab);
        }
    });
}
