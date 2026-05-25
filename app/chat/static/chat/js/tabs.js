import { state } from './state.js';
import { switchView } from './views.js';
import { createChatSocket } from './socket.js';

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

    const room = tabElement.getAttribute('data-room');
    const isGroupCreation = tabElement.getAttribute('data-special') === 'group-creation';
    const isNewTab = tabElement.getAttribute('data-special') === 'new-tab';

    if (state.chatSocket) {
        state.chatSocket.close();
        state.chatSocket = null;
    }

    if (isNewTab) {
        state.currentRoom = null;
        switchView('new-tab');
    } else if (isGroupCreation) {
        state.currentRoom = null;
        switchView('group-creation');
    } else if (room) {
        state.currentRoom = room;
        switchView('chat');
        state.chatSocket = createChatSocket(state.currentRoom);
    }
}

export function openChatTab(roomName) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    const existingTab = [...tabsContainer.querySelectorAll('.tab')]
        .find(tab => tab.getAttribute('data-room') === roomName);

    if (existingTab) {
        activateTab(existingTab);
        return;
    }

    const newTab = createTabElement(roomName, 'room');
    tabsContainer.appendChild(newTab);
    activateTab(newTab);
    newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
}

export function openNewTab() {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    const newTab = createTabElement('New Tab', 'new-tab');
    tabsContainer.appendChild(newTab);
    activateTab(newTab);
    newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
}

function createTabElement(titleText, typeAttr) {
    const tabDiv = document.createElement('div');
    tabDiv.className = 'tab';
    tabDiv.setAttribute('role', 'tab');
    tabDiv.setAttribute('aria-selected', 'false');

    if (typeAttr === 'room') {
        tabDiv.setAttribute('data-room', titleText);
    } else {
        tabDiv.setAttribute('data-special', typeAttr);
    }

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
    return tabDiv;
}

export function closeTab(tabElement) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;

    const isActive = tabElement.classList.contains('active');
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
            switchView('placeholder');
        }
    }
}
