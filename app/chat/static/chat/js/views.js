export function switchView(viewName) {
    const views = {
        chat: document.getElementById('chat'),
        placeholder: document.getElementById('chat-placeholder'),
        'group-creation': document.getElementById('group-creation-view'),
        'new-tab': document.getElementById('new-tab-view')
    };

    Object.values(views).forEach(v => v?.classList.add('hidden'));

    const activeView = views[viewName];
    if (activeView) {
        activeView.classList.remove('hidden');
    }
}
