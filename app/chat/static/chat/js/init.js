import { state } from './state.js';
import { openTab, activateTab } from './tabs.js';
import { bindTabKeyboard, bindSlashFocus } from './keyboard.js';
import { bindJoinRoom, bindGroupCreation } from './chat.js';
import { bindSettings } from './settings.js';
import { bindSearchTab } from './search.js';
import { loadRooms } from './rooms.js';
import { openChatTab } from './tabs.js';

function setUsername() {
    const userEl = document.getElementById('username-p');
    if (userEl) state.username = userEl.textContent || null;
}

function bindTabs() {
    document.getElementById('add-tab-btn')?.addEventListener('click', () => {
        import('./tabs.js').then(m => m.openNewTab());
    });

    document.getElementById('tabs')?.addEventListener('click', (e) => {
        const clickedTab = e.target.closest('.tab');
        if (clickedTab) activateTab(clickedTab);
    });
}

export function initApp() {
    setUsername();
    bindTabs();
    bindTabKeyboard();
    bindSlashFocus();
    bindSettings();
    bindSearchTab();
    loadRooms((name) => { void openChatTab(name); });

    const tabsContainer = document.getElementById('tabs');
    if (tabsContainer && tabsContainer.children.length === 0) {
        openTab('placeholder', { title: 'Welcome!', unique: true });
    }
}
