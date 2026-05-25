import { openChatTab } from './tabs.js';

export function loadRooms() {
    const roomsDiv = document.getElementById('chats');
    if (!roomsDiv) return;

    const header = document.getElementById('chats-text');
    roomsDiv.innerHTML = '';
    if (header) {
        roomsDiv.appendChild(header);
    } else {
        const chatsText = document.createElement('div');
        chatsText.id = 'chats-text';
        chatsText.className = 'chats-text';
        chatsText.textContent = 'Chats';
        roomsDiv.appendChild(chatsText);
    }

    fetch('/rooms/')
        .then(r => r.json())
        .then(rooms => {
            rooms.forEach(r => {
                const btn = document.createElement('div');
                btn.className = 'room';
                btn.textContent = r.name;
                roomsDiv.appendChild(btn);
                btn.addEventListener('pointerup', () => openChatTab(r.name));
            });
        });
}
