import { state } from './state.js';
import { switchView } from './views.js';
import { createChatSocket } from './socket.js';
import { joinRoom, showJoinError, getJoinErrorMessage } from './rooms.js';

export function activateTab(tabElement) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    const tabs = tabsContainer.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
    });

    tabElement.classList.add('active');
    tabElement.setAttribute('aria-selected', 'true');

    const tabId = tabElement.getAttribute('data-tab-id');
    const tabInfo = tabId ? state.tabsById[tabId] : null;
    const room = tabInfo && tabInfo.type === 'room' ? (tabInfo.metadata?.room || tabInfo.title) : null;
    const isGroupCreation = tabInfo?.type === 'room-creation';
    const isNewTab = tabInfo?.type === 'new-tab';
    const isRoomOverview = tabInfo?.type === 'room-overview';
    const isApplications = tabInfo?.type === 'review-applications';

    if (state.chatSocket) {
        state.chatSocket.close();
        state.chatSocket = null;
    }

    if (isNewTab) {
        state.currentRoom = null;
        switchView('new-tab');
    } else if (isGroupCreation) {
        state.currentRoom = null;
        switchView('room-creation');
    } else if (isRoomOverview) {
        const related = tabInfo?.metadata?.relatedRoom || null;
        state.currentRoom = related ? related : null;
        switchView('room-overview');
    } else if (isApplications) {
        state.currentRoom = null;
        switchView('review-applications');
    } else if (room) {
        state.currentRoom = room;
        switchView('chat');
        state.chatSocket = createChatSocket(state.currentRoom);
    }
}

export async function openChatTab(roomName) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return false;

    const trimmed = (roomName || '').trim();
    if (!trimmed) return false;

    const joinResult = await joinRoom(trimmed);
    if (!joinResult.ok) {
        showJoinError(getJoinErrorMessage(joinResult.error));
        return false;
    }
    showJoinError('');

    // prefer registry lookup to find existing room tab
    const existingId = Object.keys(state.tabsById).find(id => {
        const t = state.tabsById[id];
        return t && t.type === 'room' && ((t.metadata && t.metadata.room === joinResult.name) || t.title === joinResult.name);
    });
    if (existingId) {
        const existingTab = document.querySelector(`#tabs .tab[data-tab-id="${existingId}"]`);
        if (existingTab) {
            activateTab(existingTab);
            return true;
        }
    }

    const newTab = createTabElement(joinResult.name, 'room');
    tabsContainer.appendChild(newTab);
    activateTab(newTab);
    newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
    return true;
}

export function openNewTab() {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    const newTab = createTabElement('New Tab', 'new-tab');
    tabsContainer.appendChild(newTab);
    activateTab(newTab);
    newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
}

function createTabElement(titleText, typeAttr, metadata = {}) {
    const tabDiv = document.createElement('div');
    tabDiv.className = 'tab';
    tabDiv.setAttribute('role', 'tab');
    tabDiv.setAttribute('aria-selected', 'false');

    // generate a simple unique id for the tab and register metadata centrally
    const tabId = `t-${Date.now().toString(36)}-${Math.floor(Math.random()*10000).toString(36)}`;
    tabDiv.setAttribute('data-tab-id', tabId);

    // make a shallow copy of metadata we can augment
    const metaCopy = Object.assign({}, metadata || {});
    if (typeAttr === 'room') {
        tabDiv.setAttribute('data-room', titleText);
        // store canonical room identifier in metadata for registry lookups
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

    // store a structured representation in the central registry
    state.tabsById[tabId] = {
        id: tabId,
        title: String(titleText),
        type: typeAttr,
        metadata: metaCopy
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
    tabElement.remove();

    // clean up central registry
    if (tabId && state.tabsById[tabId]) delete state.tabsById[tabId];

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
            switchView('placeholder');
        }
    }
}

// Helper utilities for safer tab edits and metadata handling
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
        // if special/type changed, keep the typed field in sync
        if (meta.special) state.tabsById[tabId].type = String(meta.special);
        if (meta.type) state.tabsById[tabId].type = String(meta.type);
    }
    return true;
}

export function getTabMetadata(tabId) {
    return state.tabsById[tabId] ? state.tabsById[tabId].metadata : null;
}

export function openOverviewTab(roomName = null) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;
    // try registry-first lookup for overview tab
    let existingId = null;
    if (roomName) {
        existingId = Object.keys(state.tabsById).find(id => {
            const t = state.tabsById[id];
            return t && t.type === 'room-overview' && t.metadata && t.metadata.relatedRoom === roomName;
        });
    } else {
        existingId = Object.keys(state.tabsById).find(id => {
            const t = state.tabsById[id];
            return t && t.type === 'room-overview' && !(t.metadata && t.metadata.relatedRoom);
        });
    }

    if (existingId) {
        const existing = document.querySelector(`#tabs .tab[data-tab-id="${existingId}"]`);
        if (existing) { activateTab(existing); return; }
    }

    const title = roomName ? `Overview - ${roomName}` : 'Rooms';
    const metadata = roomName ? { relatedRoom: roomName } : {};
    const newTab = createTabElement(title, 'room-overview', metadata);
    tabsContainer.appendChild(newTab);
    activateTab(newTab);
    newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
}

export function openApplicationsTab() {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;
    const existingId = Object.keys(state.tabsById).find(id => {
        const t = state.tabsById[id];
        return t && t.type === 'review-applications';
    });
    if (existingId) {
        const existing = document.querySelector(`#tabs .tab[data-tab-id="${existingId}"]`);
        if (existing) { activateTab(existing); return; }
    }

    const newTab = createTabElement('Applications', 'review-applications', {});
    tabsContainer.appendChild(newTab);
    activateTab(newTab);
    newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
}