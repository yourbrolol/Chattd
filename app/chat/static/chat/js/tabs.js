import { state } from './state.js';
import { detachCurrentContent, attachTabContent } from './mount.js';
import { createChatSocket } from './socket.js';
import { joinRoom, showJoinError, getJoinErrorMessage } from './rooms.js';
import {
    createNewTabContent,
    createChatContent,
    createRoomCreationContent,
    createRoomOverviewContent,
    createApplyRoomContent,
    createReviewApplicationsContent,
    createSettingsContent,
    createPlaceholderContent,
    createSearchContent
} from './factories.js';
import {
    bindJoinRoom,
    bindGroupCreation,
    bindRoomCreationForm,
    bindApplyRoomView,
    renderApplicationsList,
    bindMessageInput,
    updateReviewBadge,
    bindSearchTab,
    runSearchTab
} from './init.js';
import { renderRoomOverview } from './overview.js';
import { renderSettingsTab } from './settings.js';

export const TAB_HANDLERS = {
    'new-tab': {
        factory: createNewTabContent,
        dirty: false,
        noCache: true,
        onActivate: async (contentNode, tabInfo) => {
            bindJoinRoom(contentNode);
            bindGroupCreation(contentNode);
        }
    },
    'room-creation': {
        factory: createRoomCreationContent,
        dirty: false,
        noCache: true,
        onActivate: async (contentNode, tabInfo) => {
            bindRoomCreationForm(contentNode);
        }
    },
    'room': {
        factory: createChatContent,
        dirty: false,
        noCache: false,
        onActivate: async (contentNode, tabInfo) => {
            const roomName = tabInfo.metadata?.room || tabInfo.title;
            
            // Bind hamburger button
            const hamburgerBtn = contentNode.querySelector('[data-role="hamburger-btn"]');
            hamburgerBtn?.addEventListener('click', () => {
                openOverviewTab(roomName);
            });

            // Bind message input
            bindMessageInput(contentNode);

            // Bind dynamic avatar in input row
            const navAvatar = document.getElementById('user-icon');
            const chatAvatar = contentNode.querySelector('[data-role="avatar"]');
            if (chatAvatar && navAvatar) {
                chatAvatar.innerHTML = `<img src="${navAvatar.src}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
            }
        }
    },
    'room-overview': {
        factory: createRoomOverviewContent,
        dirty: true,
        noCache: false,
        onActivate: async (contentNode, tabInfo) => {
            const roomName = tabInfo.metadata?.relatedRoom || null;
            await renderRoomOverview(roomName, contentNode);
        }
    },
    'apply-room': {
        factory: createApplyRoomContent,
        dirty: false,
        noCache: true,
        onActivate: async (contentNode, tabInfo) => {
            const roomName = tabInfo.metadata?.relatedRoom || null;
            bindApplyRoomView(contentNode, roomName);
        }
    },
    'review-applications': {
        factory: createReviewApplicationsContent,
        dirty: true,
        noCache: false,
        onActivate: async (contentNode, tabInfo) => {
            const roomName = tabInfo.metadata?.relatedRoom || null;
            await renderApplicationsList(contentNode, roomName);
        }
    },
    'settings': {
        factory: createSettingsContent,
        dirty: false,
        noCache: true,
        onActivate: async (contentNode, tabInfo) => {
            renderSettingsTab(contentNode);
        }
    },
    'search': {
        factory: createSearchContent,
        dirty: false,
        noCache: true,
        onActivate: async (contentNode, tabInfo) => {
            runSearchTab(contentNode);
        }
    },
    'placeholder': {
        factory: createPlaceholderContent,
        dirty: false,
        noCache: true,
        onActivate: async (contentNode, tabInfo) => {
            // Placeholder has no actions
        }
    }
};

export async function activateTab(tabElement) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    // 1. Get previously active tab info
    const activeTabEl = tabsContainer.querySelector('.tab.active');
    const activeTabId = activeTabEl?.getAttribute('data-tab-id');
    const prevTabInfo = activeTabId ? state.tabsById[activeTabId] : null;

    // 2. Remove active state from all tabs
    const tabs = tabsContainer.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
    });

    // 3. Mark the new tab as active
    tabElement.classList.add('active');
    tabElement.setAttribute('aria-selected', 'true');

    // 4. Clean up previous tab if it has noCache
    if (prevTabInfo) {
        const prevHandler = TAB_HANDLERS[prevTabInfo.type];
        if (prevHandler?.noCache) {
            prevTabInfo.contentNode = null;
            prevTabInfo.roomLoaded = false;
        }
    }

    // 5. Detach current view content
    detachCurrentContent();

    // 6. Look up the new tab's info and handler
    const tabId = tabElement.getAttribute('data-tab-id');
    const tabInfo = tabId ? state.tabsById[tabId] : null;
    if (!tabInfo) return;

    const type = tabInfo.type;
    const handler = TAB_HANDLERS[type];
    if (!handler) {
        console.error('No handler found for tab type:', type);
        return;
    }

    // 7. Create contentNode if null
    let justCreated = false;
    if (!tabInfo.contentNode) {
        tabInfo.contentNode = await handler.factory();
        justCreated = true;
    }

    // 8. Attach new contentNode to DOM
    attachTabContent(tabInfo.contentNode);

    // 9. Sync state.currentRoom
    if (type === 'room') {
        state.currentRoom = tabInfo.metadata?.room || tabInfo.title;
    } else if (type === 'room-overview') {
        state.currentRoom = tabInfo.metadata?.relatedRoom || null;
    } else {
        state.currentRoom = null;
    }

    // 10. Run onActivate handler if justCreated or dirty
    if (justCreated || handler.dirty || tabInfo.dirty) {
        tabInfo.dirty = false;
        if (handler.onActivate) {
            await handler.onActivate(tabInfo.contentNode, tabInfo);
        }
    }

    // 11. Manage WebSocket connections
    if (type !== 'room') {
        if (state.chatSocket) {
            state.chatSocket.close();
            state.chatSocket = null;
        }
    } else {
        if (state.chatSocket) {
            state.chatSocket.close();
            state.chatSocket = null;
        }
        state.chatSocket = createChatSocket(state.currentRoom);
    }
}

export function openTab(type, opts = {}) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return null;

    // If opening any tab that is not a placeholder, close any open placeholder tabs first!
    if (type !== 'placeholder') {
        Object.keys(state.tabsById).forEach(id => {
            const t = state.tabsById[id];
            if (t && t.type === 'placeholder') {
                const el = getTabElementById(id);
                if (el) el.remove();
                delete state.tabsById[id];
            }
        });
    }

    const {
        title = 'New Tab',
        metadata = {},
        unique = false,
        uniqueKey = null
    } = opts;

    let existingId = null;

    if (uniqueKey) {
        existingId = Object.keys(state.tabsById).find(id => {
            const t = state.tabsById[id];
            return t && t.type === type && t.metadata && t.metadata[uniqueKey] === metadata[uniqueKey];
        });
    } else if (unique) {
        existingId = Object.keys(state.tabsById).find(id => {
            const t = state.tabsById[id];
            return t && t.type === type;
        });
    }

    if (existingId) {
        const existingTab = document.querySelector(`#tabs .tab[data-tab-id="${existingId}"]`);
        if (existingTab) {
            activateTab(existingTab);
            return existingTab;
        }
    }

    // If opening placeholder, ensure we close any existing placeholders first to avoid duplicates
    if (type === 'placeholder') {
        Object.keys(state.tabsById).forEach(id => {
            const t = state.tabsById[id];
            if (t && t.type === 'placeholder') {
                const el = getTabElementById(id);
                if (el) el.remove();
                delete state.tabsById[id];
            }
        });
    }

    const newTab = createTabElement(title, type, metadata);
    tabsContainer.appendChild(newTab);
    activateTab(newTab);
    newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
    return newTab;
}

export async function openChatTab(roomName) {
    const trimmed = (roomName || '').trim();
    if (!trimmed) return false;

    const joinResult = await joinRoom(trimmed);
    if (!joinResult.ok) {
        showJoinError(getJoinErrorMessage(joinResult.error));
        return false;
    }
    showJoinError('');

    openTab('room', {
        title: joinResult.name,
        metadata: { room: joinResult.name },
        unique: true,
        uniqueKey: 'room'
    });
    return true;
}

export function openNewTab() {
    openTab('new-tab', { title: 'New Tab' });
}

export function openOverviewTab(roomName = null) {
    const title = roomName ? `Overview - ${roomName}` : 'Rooms';
    openTab('room-overview', {
        title: title,
        metadata: roomName ? { relatedRoom: roomName } : {},
        unique: true,
        uniqueKey: 'relatedRoom'
    });
}

export function openSettingsTab() {
    openTab('settings', { title: 'Settings', unique: true });
}

export function openApplicationsTab(roomName) {
    if (!roomName) return;

    const title = `Applications - ${roomName}`;
    
    openTab('review-applications', {
        title: title,
        metadata: { relatedRoom: roomName },
        unique: true,
        uniqueKey: 'relatedRoom' // Scopes the tab uniquely to this specific room name field
    });
}

export function openSearchTab() {
    openTab('search', { title: 'Find Rooms', unique: true });
}

function createTabElement(titleText, typeAttr, metadata = {}) {
    const tabDiv = document.createElement('div');
    tabDiv.className = 'tab';
    tabDiv.setAttribute('role', 'tab');
    tabDiv.setAttribute('aria-selected', 'false');

    const tabId = `t-${Date.now().toString(36)}-${Math.floor(Math.random()*10000).toString(36)}`;
    tabDiv.setAttribute('data-tab-id', tabId);

    const metaCopy = Object.assign({}, metadata || {});
    if (typeAttr === 'room') {
        tabDiv.setAttribute('data-room', titleText);
        metaCopy.room = titleText;
    } else {
        tabDiv.setAttribute('data-special', typeAttr);
    }

    Object.keys(metaCopy).forEach(k => {
        const attrName = 'data-' + k.replace(/([A-Z])/g, '-$1').toLowerCase();
        const value = metaCopy[k];
        if (value === undefined || value === null) return;
        tabDiv.setAttribute(attrName, (typeof value === 'object') ? JSON.stringify(value) : String(value));
    });

    const span = document.createElement('span');
    span.className = 'tab-title';
    span.textContent = titleText;

    const closeBtn = document.createElement('span');
    closeBtn.className = 'tab-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeTab(tabDiv);
    });

    tabDiv.appendChild(span);
    tabDiv.appendChild(closeBtn);

    state.tabsById[tabId] = {
        id: tabId,
        title: String(titleText),
        type: typeAttr,
        metadata: metaCopy,
        contentNode: null,
        dirty: false
    };
    return tabDiv;
}

function getTabs() {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return [];
    return [...tabsContainer.querySelectorAll('.tab')];
}

export function cycleTabLeft() {
    const tabs = getTabs();
    if (tabs.length < 2) return;

    const activeIndex = tabs.findIndex(tab => tab.classList.contains('active'));
    const currentIndex = activeIndex >= 0 ? activeIndex : 0;
    const nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    activateTab(tabs[nextIndex]);
}

export function cycleTabRight() {
    const tabs = getTabs();
    if (tabs.length < 2) return;

    const activeIndex = tabs.findIndex(tab => tab.classList.contains('active'));
    const currentIndex = activeIndex >= 0 ? activeIndex : 0;
    const nextIndex = (currentIndex + 1) % tabs.length;
    activateTab(tabs[nextIndex]);
}

export function closeActiveTab() {
    const activeTab = document.querySelector('#tabs .tab.active');
    if (activeTab) closeTab(activeTab);
}

export function closeTab(tabElement) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    const isActive = tabElement.classList.contains('active');
    const tabId = tabElement.getAttribute('data-tab-id');
    
    // clean up central registry
    if (tabId && state.tabsById[tabId]) {
        state.tabsById[tabId].contentNode = null;
        delete state.tabsById[tabId];
    }
    
    tabElement.remove();

    if (isActive) {
        const remainingTabs = tabsContainer.querySelectorAll('.tab');
        if (remainingTabs.length > 0) {
            activateTab(remainingTabs[remainingTabs.length - 1]);
        } else {
            state.currentRoom = null;
            if (state.chatSocket) {
                state.chatSocket.close();
                state.chatSocket = null;
            }
            // Mount the placeholder tab
            openTab('placeholder', { title: 'Welcome!', unique: true });
        }
    }
}

export function getTabElementById(tabId) {
    if (!tabId) return null;
    return document.querySelector(`#tabs .tab[data-tab-id="${tabId}"]`);
}

export function updateTabTitle(tabId, newTitle) {
    const el = getTabElementById(tabId);
    if (!el) return false;
    const span = el.querySelector('.tab-title');
    if (span) span.textContent = String(newTitle);
    if (state.tabsById[tabId]) state.tabsById[tabId].title = String(newTitle);
    return true;
}

export function setTabMetadata(tabId, metadata) {
    const el = getTabElementById(tabId);
    if (!el) return false;
    const meta = metadata || {};
    Object.keys(meta).forEach(k => {
        const attrName = 'data-' + k.replace(/([A-Z])/g, '-$1').toLowerCase();
        const value = meta[k];
        if (value === undefined || value === null) {
            el.removeAttribute(attrName);
        } else {
            el.setAttribute(attrName, (typeof value === 'object') ? JSON.stringify(value) : String(value));
        }
    });
    if (state.tabsById[tabId]) {
        state.tabsById[tabId].metadata = Object.assign({}, state.tabsById[tabId].metadata, meta);
        
        const oldType = state.tabsById[tabId].type;
        // if special/type changed, keep the typed field in sync and discard old DOM contentNode
        if (meta.special && String(meta.special) !== oldType) {
            state.tabsById[tabId].type = String(meta.special);
            state.tabsById[tabId].contentNode = null;
            state.tabsById[tabId].roomLoaded = false;
        }
        if (meta.type && String(meta.type) !== oldType) {
            state.tabsById[tabId].type = String(meta.type);
            state.tabsById[tabId].contentNode = null;
            state.tabsById[tabId].roomLoaded = false;
        }
    }
    return true;
}

export function getTabMetadata(tabId) {
    return state.tabsById[tabId] ? state.tabsById[tabId].metadata : null;
}