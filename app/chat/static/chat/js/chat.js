import { sendMessage } from './socket.js';
import {
    openChatTab,
    activateTab,
    updateTabTitle,
    setTabMetadata,
    getTabElementById
} from './tabs.js';
import { state } from './state.js';
import { joinRoom, showJoinError, getJoinErrorMessage } from './rooms.js';
import { loadRooms } from './rooms.js';
import { handleGroupSubmission, cancelGroupCreation } from './room.js';

export function bindMessageInput(contentNode) {
    const msgInput = contentNode.querySelector('[data-role="chat-message-input"]');
    msgInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendMessage(contentNode);
    });

    const submitBtn = contentNode.querySelector('[data-role="chat-message-submit"]');
    if (submitBtn) {
        submitBtn.onclick = () => sendMessage(contentNode);
    }
}

export async function joinRoomAndOpen(roomName) {
    const result = await joinRoom(roomName);
    console.log(result)
    if (!result.ok) {
        if (result.error === 'app_required') {
            console.warn("[WARN] chat.js/joinRoomAndOpen: Application Required.")

            showJoinError('');
            
            const activeTab = document.querySelector('#tabs .tab.active');
            const tabId = activeTab?.getAttribute('data-tab-id');
            if (tabId) {
                setTabMetadata(tabId, { special: 'apply-room', relatedRoom: result.roomName || roomName });
                updateTabTitle(tabId, `Apply - ${result.roomName || roomName}`);
                const el = getTabElementById(tabId);
                if (el) activateTab(el);
            }
            return false;
        }
        console.warn("[WARN] chat.js/joinRoomAndOpen: Forbidden.")
        showJoinError(getJoinErrorMessage(result.error));
        return false;
    }

    showJoinError('');
    loadRooms((name) => { void openChatTab(name); });

    console.log("[INFO] chat.js/joinRoomAndOpen: Success.")

    await openChatTab(result.name);
    return true;
}

export function bindJoinRoom(contentNode) {
    const joinBtn = contentNode.querySelector('[data-role="join-room-btn"]');
    const joinInput = contentNode.querySelector('[data-role="join-room-input"]');

    joinBtn?.addEventListener('click', async () => {
        if (!joinInput) return;
        await joinRoomAndOpen(joinInput.value);
    });

    joinInput?.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            await joinRoomAndOpen(joinInput.value);
        }
    });
}

export function bindGroupCreation(contentNode) {
    contentNode.querySelector('[data-role="create-room-btn"]')?.addEventListener('click', () => {
        const activeTab = document.querySelector('#tabs .tab.active');
        const tabId = activeTab?.getAttribute('data-tab-id');
        if (tabId) {
            const t = tabId ? state.tabsById[tabId] : null;
            if (t && t.type === 'new-tab') {
                setTabMetadata(tabId, { special: 'room-creation' });
                updateTabTitle(tabId, 'Create Room');
                const el = getTabElementById(tabId);
                if (el) activateTab(el);
            }
        }
    });
}

export function bindRoomCreationForm(contentNode) {
    contentNode.querySelector('[data-role="room-creation-form"]')?.addEventListener('submit', (e) => handleGroupSubmission(e, contentNode));
    contentNode.querySelector('[data-role="cancel-room-btn"]')?.addEventListener('click', () => cancelGroupCreation(contentNode));
}
