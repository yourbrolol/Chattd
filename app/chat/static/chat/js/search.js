import { openChatTab, openSearchTab } from "./tabs.js";
import { api } from './api.js';

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export async function renderSearchTab(contentNode) {
    const inputEl = contentNode.querySelector('[data-role="search-input"]');
    const joinedSection = contentNode.querySelector('[data-role="joined-section"]');
    const joinedList = contentNode.querySelector('[data-role="joined-list"]');
    const publicSection = contentNode.querySelector('[data-role="public-section"]');
    const publicList = contentNode.querySelector('[data-role="public-list"]');
    const emptyEl = contentNode.querySelector('[data-role="search-empty"]');

    let debounceTimeout = null;

    inputEl?.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        const query = inputEl.value.trim();

        if (!query) {
            joinedSection?.classList.add('hidden');
            publicSection?.classList.add('hidden');
            emptyEl?.classList.add('hidden');
            return;
        }

        // Debounce backend hits by 250ms to keep it performant
        debounceTimeout = setTimeout(async () => {
            try {
                const response = await api.rooms.search(query);
                const data = response.data

                // Clear previous cycles
                if (joinedList) joinedList.innerHTML = '';
                if (publicList) publicList.innerHTML = '';

                console.log(data);

                const hasJoined = data.joined_rooms.length > 0;
                const hasPublic = data.public_rooms.length > 0;

                // Render Rooms User is Already In
                if (hasJoined) {
                    data.joined_rooms.forEach(room => {
                        const row = document.createElement('div');
                        row.className = 'search-result-row';
                        row.innerHTML = `
                            <span class="room-name"># ${escapeHtml(room.name)} ${room.is_public ? '' : '🔒'}</span>
                            <button class="btn-search-action" data-room="${escapeHtml(room.name)}">Enter</button>
                        `;
                        joinedList.appendChild(row);
                    });
                    joinedSection?.classList.remove('hidden');
                } else {
                    joinedSection?.classList.add('hidden');
                }

                // Render Global Discoverable Public Rooms
                if (hasPublic) {
                    data.public_rooms.forEach(room => {
                        const row = document.createElement('div');
                        row.className = 'search-result-row';
                        row.innerHTML = `
                            <span class="room-name"># ${escapeHtml(room.name)}</span>
                            <button class="btn-search-action btn-join-style" data-room="${escapeHtml(room.name)}">Join Room</button>
                        `;
                        publicList.appendChild(row);
                    });
                    publicSection?.classList.remove('hidden');
                } else {
                    publicSection?.classList.add('hidden');
                }

                // Handle Empty States
                if (!hasJoined && !hasPublic) {
                    emptyEl?.classList.remove('hidden');
                } else {
                    emptyEl?.classList.add('hidden');
                }

                // Bind Row Buttons to Open/Join the room
                contentNode.querySelectorAll('.btn-search-action').forEach(btn => {
                    btn.addEventListener('click', () => {
                        openChatTab(btn.dataset.room);
                    });
                });

            } catch (err) {
                console.error("Search fetch failure:", err);
            }
        }, 250);
    });
}

export function runSearchTab(contentNode) {
    if (!contentNode) return;
    renderSearchTab(contentNode);
}

export function bindSearchTab() {
    document.getElementById('search-tab-btn')?.addEventListener('click', () => {
        openSearchTab();
    });
}
