import {
    cycleTabLeft,
    cycleTabRight,
    closeActiveTab,
    openNewTab,
    openOverviewTab
} from './tabs.js';
import { state } from './state.js';

function isTypingTarget(target) {
    return target instanceof HTMLInputElement
        || target instanceof HTMLTextAreaElement
        || target instanceof HTMLSelectElement
        || target.isContentEditable;
}

export function bindSlashFocus() {
    document.addEventListener('keydown', (e) => {
        if (e.key !== '/' || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
        if (isTypingTarget(e.target)) return;

        const activeTab = document.querySelector('#tabs .tab.active');
        const tabId = activeTab?.getAttribute('data-tab-id');
        const tabInfo = tabId ? state.tabsById[tabId] : null;
        if (tabInfo && tabInfo.type === 'room') {
            const input = tabInfo.contentNode?.querySelector('[data-role="chat-message-input"]');
            if (input) {
                e.preventDefault();
                input.focus();
            }
        }
    }, true);
}

export function bindTabKeyboard() {
    document.addEventListener('keydown', (e) => {
        if (!e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;

        if (e.key === '1') {
            e.preventDefault();
            cycleTabLeft();
        } else if (e.key === '2') {
            e.preventDefault();
            cycleTabRight();
        } else if (e.key === '3') {
            e.preventDefault();
            openNewTab();
        } else if (e.key === '4') {
            e.preventDefault();
            closeActiveTab();
        } else if (e.key === '5') {
            e.preventDefault();
            const activeTab = document.querySelector('#tabs .tab.active');
            const tabId = activeTab?.getAttribute('data-tab-id');
            const tabInstance = tabId ? state.tabsById[tabId] : null;
            if (tabInstance && tabInstance.type === 'room-overview') {
                tabInstance.dirty = true;
                tabInstance.activate();
            } else if (state.currentRoom) {
                openOverviewTab(state.currentRoom);
            }
        }
    });
}
