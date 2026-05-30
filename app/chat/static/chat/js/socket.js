import { state } from './state.js';

export function appendMessage(data, contentNode) {
    if (!contentNode) return;
    const chatLog = contentNode.querySelector('[data-role="chat-log"]') || contentNode.querySelector('#chat-log');
    if (!chatLog) return;

    const div = document.createElement('div');
    div.className = 'message';
    
    // Add own styling if it is our own message
    if (data.user === state.username) {
        div.classList.add('own');
    }
    
    div.textContent = `${data.user}: ${data.content}`;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
}

export function createChatSocket(room) {
    const tabInfo = Object.values(state.tabsById).find(t => t.type === 'room' && t.metadata?.room === room);
    if (!tabInfo) return null;
    const contentNode = tabInfo.contentNode;

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
            const chatLog = contentNode?.querySelector('[data-role="chat-log"]') || contentNode?.querySelector('#chat-log');
            if (chatLog) {
                if (!tabInfo.roomLoaded) {
                    chatLog.querySelectorAll(".message").forEach(el => el.remove());
                    data.message_history.forEach(msg => appendMessage(msg, contentNode));
                    tabInfo.roomLoaded = true;
                }
            }
        } else if (data.type === 'chat_message') {
            appendMessage({ user: data.user, content: data.content }, contentNode);
        }
    };

    socket.onclose = function (e) {
        console.log('Socket closed for room:', room, 'code:', e.code);
        if (e.code === 4003) {
            const chatLog = contentNode?.querySelector('[data-role="chat-log"]') || contentNode?.querySelector('#chat-log');
            if (chatLog) {
                const notice = document.createElement('div');
                notice.className = 'message message--error';
                notice.textContent = 'You must join this room before you can chat.';
                chatLog.appendChild(notice);
            }
        }
    };

    return socket;
}

export function sendMessage(contentNode = null) {
    if (!contentNode) {
        // Fallback to active tab's contentNode
        const activeTab = document.querySelector('#tabs .tab.active');
        const tabId = activeTab?.getAttribute('data-tab-id');
        const tabInfo = tabId ? state.tabsById[tabId] : null;
        if (tabInfo && tabInfo.type === 'room') {
            contentNode = tabInfo.contentNode;
        }
    }
    if (!contentNode) return;

    const input = contentNode.querySelector('[data-role="chat-message-input"]') || contentNode.querySelector('#chat-message-input');
    if (!input || input.value === '' || !state.chatSocket) return;

    state.chatSocket.send(JSON.stringify({
        type: 'chat_message',
        message: input.value
    }));
    input.value = '';
}
