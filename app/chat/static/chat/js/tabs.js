import { state } from './state.js';
import { detachCurrentContent, attachTabContent } from './mount.js';
import { createChatSocket } from './socket.js';
import { joinRoom, showJoinError, getJoinErrorMessage } from './rooms.js';
import { fetchTemplate } from './factories.js';
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
import { renderUserDetail } from './users.js';

// ─────────────────────────────────────────────────────────────────────────────
// Base Tab Class
// ─────────────────────────────────────────────────────────────────────────────

class Tab {
    constructor(id, title, metadata = {}, type = 'tab') {
        this.id = id;
        this.title = title;
        this.type = type;
        this.metadata = metadata;
        this.contentNode = null;
        this.dirty = false;
        this.noCache = true;
    }

    async render() {
        throw new Error('render() must be implemented by subclass');
    }

    async activate() {
        if (!this.contentNode) {
            this.contentNode = await this.render();
        } else if (this.dirty) {
            this.contentNode = await this.render();
            this.dirty = false;
        }
    }

    deactivate() {}

    destroy() {
        this.contentNode = null;
    }

    getRoomName() {
        return this.metadata?.room || this.metadata?.relatedRoom || null;
    }

    toJSON() {
        return {
            id: this.id,
            title: this.title,
            type: this.type,
            metadata: this.metadata,
            contentNode: this.contentNode,
            dirty: this.dirty,
            noCache: this.noCache
        };
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab Subclasses
// ─────────────────────────────────────────────────────────────────────────────

class NewTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.noCache = true;
    }

    async render() {
        return await fetchTemplate('new_tab');
    }

    async activate() {
        await super.activate();
        bindJoinRoom(this.contentNode);
        bindGroupCreation(this.contentNode);
    }
}

class RoomCreationTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.noCache = true;
    }

    async render() {
        return await fetchTemplate('room_creation');
    }

    async activate() {
        await super.activate();
        bindRoomCreationForm(this.contentNode);
    }
}

class RoomTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.noCache = false;
        this.roomLoaded = false;
    }

    async render() {
        return await fetchTemplate('chat_view');
    }

    async activate() {
        await super.activate();

        const roomName = this.metadata?.room || this.title;

        const hamburgerBtn = this.contentNode.querySelector('[data-role="hamburger-btn"]');
        hamburgerBtn?.addEventListener('click', () => {
            openOverviewTab(roomName);
        });

        bindMessageInput(this.contentNode);

        const navAvatar = document.getElementById('user-icon');
        const chatAvatar = this.contentNode.querySelector('[data-role="avatar"]');
        if (chatAvatar && navAvatar) {
            chatAvatar.innerHTML = `<img src="${navAvatar.src}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        }

        const chatLog = this.contentNode.querySelector('[data-role="chat-log"]');
        if (chatLog) chatLog.scrollTop = chatLog.scrollHeight;
    }

    deactivate() {}

    destroy() {
        this.roomLoaded = false;
        super.destroy();
    }
}

class RoomOverviewTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.dirty = true;
        this.noCache = true;
    }

    async render() {
        return await fetchTemplate('room_overview');
    }

    async activate() {
        await super.activate();
        const roomName = this.metadata?.relatedRoom || null;
        await renderRoomOverview(roomName, this.contentNode);
    }
}

class UserDetailTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.dirty = true;
        this.noCache = true;
    }

    async render() {
        return await fetchTemplate('user_detail');
    }

    async activate() {
        await super.activate();
        const username = this.metadata?.username || "Anonymous";
        const avatarUrl = null;
        await renderUserDetail(username, avatarUrl, this.contentNode);
    }
}

class ApplyRoomTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.noCache = true;
    }

    async render() {
        return await fetchTemplate('apply_room');
    }

    async activate() {
        await super.activate();
        const roomName = this.metadata?.relatedRoom || null;
        bindApplyRoomView(this.contentNode, roomName);
    }
}

class ReviewApplicationsTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.dirty = true;
        this.noCache = false;
    }

    async render() {
        return await fetchTemplate('review_applications');
    }

    async activate() {
        await super.activate();
        const roomName = this.metadata?.relatedRoom || null;
        await renderApplicationsList(this.contentNode, roomName);
    }
}

class SettingsTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.noCache = true;
    }

    async render() {
        const element = await fetchTemplate('settings_view');
        const form = element.querySelector('form') || element;
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        
        // Inject CSRF token hidden input dynamically
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = csrfToken;
        form.insertBefore(csrfInput, form.firstChild);

        return element;
    }

    async activate() {
        await super.activate();
        renderSettingsTab(this.contentNode);
    }
}

class SearchTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.noCache = true;
    }

    async render() {
        return await fetchTemplate('search_view');
    }

    async activate() {
        await super.activate();
        runSearchTab(this.contentNode);
    }
}

class PlaceholderTab extends Tab {
    constructor(id, title, metadata, type) {
        super(id, title, metadata, type);
        this.noCache = true;
    }

    async render() {
        return await fetchTemplate('placeholder_view');
    }

    async activate() {
        await super.activate();
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab Type Registry
// ─────────────────────────────────────────────────────────────────────────────

const TAB_TYPES = {
    'new-tab': NewTab,
    'room-creation': RoomCreationTab,
    'room': RoomTab,
    'room-overview': RoomOverviewTab,
    'user-detail': UserDetailTab,
    'apply-room': ApplyRoomTab,
    'review-applications': ReviewApplicationsTab,
    'settings': SettingsTab,
    'search': SearchTab,
    'placeholder': PlaceholderTab
};

function createTabInstance(type, id, title, metadata) {
    const TabClass = TAB_TYPES[type];
    if (!TabClass) {
        throw new Error(`Unknown tab type: ${type}`);
    }
    return new TabClass(id, title, metadata, type);
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab DOM Element Creation
// ─────────────────────────────────────────────────────────────────────────────

function createTabElement(titleText, typeAttr, metadata = {}) {
    const tabDiv = document.createElement('div');
    tabDiv.className = 'tab';
    tabDiv.setAttribute('role', 'tab');
    tabDiv.setAttribute('aria-selected', 'false');

    const tabId = `t-${Date.now().toString(36)}-${Math.floor(Math.random() * 10000).toString(36)}`;
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

    const tabInstance = createTabInstance(typeAttr, tabId, String(titleText), metaCopy);
    state.tabsById[tabId] = tabInstance;

    return tabDiv;
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab Lifecycle
// ─────────────────────────────────────────────────────────────────────────────

export async function activateTab(tabElement) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    const activeTabEl = tabsContainer.querySelector('.tab.active');
    const activeTabId = activeTabEl?.getAttribute('data-tab-id');
    const prevTab = activeTabId ? state.tabsById[activeTabId] : null;

    const tabs = tabsContainer.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
    });

    tabElement.classList.add('active');
    tabElement.setAttribute('aria-selected', 'true');

    if (prevTab && prevTab.noCache) {
        prevTab.destroy();
    }

    detachCurrentContent();

    const tabId = tabElement.getAttribute('data-tab-id');
    const currentTab = tabId ? state.tabsById[tabId] : null;
    if (!currentTab) return;

    await currentTab.activate();

    attachTabContent(currentTab.contentNode);

    if (currentTab instanceof RoomTab) {
        state.currentRoom = currentTab.metadata?.room || currentTab.title;
    } else if (currentTab instanceof RoomOverviewTab) {
        state.currentRoom = currentTab.metadata?.relatedRoom || null;
    } else {
        state.currentRoom = null;
    }

    if (!(currentTab instanceof RoomTab)) {
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

export function closeTab(tabElement) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    const isActive = tabElement.classList.contains('active');
    const tabId = tabElement.getAttribute('data-tab-id');

    if (tabId && state.tabsById[tabId]) {
        state.tabsById[tabId].destroy();
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
            openTab('placeholder', { title: 'Welcome!', unique: true });
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Convenience Openers
// ─────────────────────────────────────────────────────────────────────────────

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

export function openUserDetailTab(username = null) {
    openTab('user-detail', {
        title: username || 'User',
        metadata: { username: username }
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
        uniqueKey: 'relatedRoom'
    });
}

export function openSearchTab() {
    openTab('search', { title: 'Find Rooms', unique: true });
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab Navigation & Utilities
// ─────────────────────────────────────────────────────────────────────────────

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
        const tab = state.tabsById[tabId];
        tab.metadata = Object.assign({}, tab.metadata, meta);

        const oldType = tab.type;
        if (meta.special && String(meta.special) !== oldType) {
            tab.type = String(meta.special);
            tab.destroy();
            if (tab instanceof RoomTab) tab.roomLoaded = false;
        }
        if (meta.type && String(meta.type) !== oldType) {
            tab.type = String(meta.type);
            tab.destroy();
            if (tab instanceof RoomTab) tab.roomLoaded = false;
        }
    }
    return true;
}

export function getTabMetadata(tabId) {
    return state.tabsById[tabId] ? state.tabsById[tabId].metadata : null;
}

export { Tab, TAB_TYPES };
