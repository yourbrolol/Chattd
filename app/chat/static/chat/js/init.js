import { sendMessage } from './socket.js';
import { openNewTab, activateTab } from './tabs.js';
import { handleGroupSubmission, cancelGroupCreation } from './group.js';
import { loadRooms } from './rooms.js';

function bindMessageInput() {
    const msgInput = document.getElementById('chat-message-input');
    msgInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    const submitBtn = document.getElementById('chat-message-submit');
    if (submitBtn) submitBtn.onclick = sendMessage;
}

function bindTabs() {
    document.getElementById('add-tab-btn')?.addEventListener('click', openNewTab);

    document.getElementById('tabs')?.addEventListener('click', (e) => {
        const clickedTab = e.target.closest('.tab');
        if (clickedTab) activateTab(clickedTab);
    });
}

function bindGroupCreation() {
    document.getElementById('group-creation-form')?.addEventListener('submit', handleGroupSubmission);
    document.getElementById('cancel-group-btn')?.addEventListener('click', cancelGroupCreation);

    document.getElementById('dashboard-create-group-btn')?.addEventListener('click', () => {
        const activeTab = document.querySelector('#tabs .tab.active');
        if (activeTab && activeTab.getAttribute('data-special') === 'new-tab') {
            activeTab.setAttribute('data-special', 'group-creation');
            const titleSpan = activeTab.querySelector('.tab-title');
            if (titleSpan) titleSpan.textContent = 'Create Group';
            activateTab(activeTab);
        }
    });
}

export function initApp() {
    bindMessageInput();
    bindTabs();
    bindGroupCreation();
    loadRooms();
}
