import { state } from './state.js';

export function appendMessage(data) {
    const chatLog = document.getElementById('chat-log');
    if (!chatLog) return;

    const div = document.createElement('div');
    div.className = 'message';
    div.textContent = `${data.user}: ${data.content}`;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
}

export function createChatSocket(room) {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${room}/`);

    socket.onmessage = async function (e) {
        const text = e.data instanceof Blob ? await e.data.text() : e.data;

        let data;
        try {
            data = JSON.parse(text);
        } catch {
            console.error('Not JSON:', text);
            return;
        }

        if (data.type === 'init') {
            const chatLog = document.getElementById('chat-log');
            if (chatLog) chatLog.innerHTML = '';
            data.message_history.forEach(appendMessage);
        } else if (data.type === 'chat_message') {
            appendMessage({ user: data.user, content: data.content });
        }
    };

    socket.onclose = function () {
        console.log('Socket closed for room:', room);
    };

    return socket;
}

export function sendMessage() {
    const input = document.getElementById('chat-message-input');
    if (!input || input.value === '' || !state.chatSocket) return;

    state.chatSocket.send(JSON.stringify({
        type: 'chat_message',
        message: input.value
    }));
    input.value = '';
}
