const JOIN_ERROR_MESSAGES = {
    not_found: 'Room not found. Check the name and try again.',
    forbidden: 'You cannot join this room.',
    auth_required: 'You must be logged in to join a room.',
    network: 'Network error. Please try again.',
    empty: 'Enter a room name.',
};

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

export function showJoinError(message) {
    const errorsDiv = document.getElementById('join-room-errors');
    if (!errorsDiv) return;
    if (!message) {
        errorsDiv.classList.add('hidden');
        errorsDiv.textContent = '';
        return;
    }
    errorsDiv.textContent = message;
    errorsDiv.classList.remove('hidden');
}

export async function joinRoom(roomName) {
    const trimmed = (roomName || '').trim();
    if (!trimmed) {
        return { ok: false, error: 'empty' };
    }

    const formData = new URLSearchParams();
    formData.append('csrfmiddlewaretoken', getCsrfToken());
    formData.append('room_name', trimmed);

    try {
        const response = await fetch('/rooms/join/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData,
        });

        if (response.status === 401) {
            return { ok: false, error: 'auth_required' };
        }
        if (response.status === 404) {
            return { ok: false, error: 'not_found' };
        }
        if (response.status === 403) {
            return { ok: false, error: 'forbidden' };
        }
        if (!response.ok) {
            return { ok: false, error: 'network' };
        }

        const data = await response.json();
        return { ok: true, name: data.name, roomType: data.room_type };
    } catch {
        return { ok: false, error: 'network' };
    }
}

export function getJoinErrorMessage(error) {
    return JOIN_ERROR_MESSAGES[error] || JOIN_ERROR_MESSAGES.network;
}

export function loadRooms(onRoomClick) {
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
        .then(r => {
            if (!r.ok) throw new Error('list failed');
            return r.json();
        })
        .then(rooms => {
            rooms.forEach(r => {
                const btn = document.createElement('div');
                btn.className = 'room';
                btn.textContent = r.name;
                roomsDiv.appendChild(btn);
                btn.addEventListener('pointerup', () => onRoomClick?.(r.name));
            });
        })
        .catch(err => console.error('Failed to load rooms:', err));
}
