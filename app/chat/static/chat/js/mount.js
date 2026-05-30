export function detachCurrentContent() {
    const viewMain = document.getElementById('view-main');
    if (!viewMain) return null;
    
    // The active tab's content node is the child of #view-main that is not #tabs-container
    const activeNode = Array.from(viewMain.children).find(child => child.id !== 'tabs-container');
    if (activeNode) {
        viewMain.removeChild(activeNode);
        return activeNode;
    }
    return null;
}

export function attachTabContent(node) {
    const viewMain = document.getElementById('view-main');
    if (!viewMain || !node) return;
    
    // Remove any existing active view node first
    detachCurrentContent();
    viewMain.appendChild(node);
}
