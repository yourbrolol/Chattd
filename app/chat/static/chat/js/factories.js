const templateCache = {};

async function fetchTemplate(name) {
    if (templateCache[name]) {
        return templateCache[name].cloneNode(true);
    }

    const response = await fetch(`/static/chat/templates/${name}.html`);
    if (!response.ok) {
        throw new Error(`Failed to load template: ${name}`);
    }
    const htmlText = await response.text();

    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, 'text/html');
    const element = doc.body.firstElementChild;
    if (!element) {
        throw new Error(`Invalid template content for: ${name}`);
    }

    templateCache[name] = element;
    return element.cloneNode(true);
}

export async function createNewTabContent() {
    return await fetchTemplate('new_tab');
}

export async function createChatContent() {
    return await fetchTemplate('chat_view');
}

export async function createRoomCreationContent() {
    return await fetchTemplate('room_creation');
}

export async function createRoomOverviewContent() {
    return await fetchTemplate('room_overview');
}

export async function createApplyRoomContent() {
    return await fetchTemplate('apply_room');
}

export async function createReviewApplicationsContent() {
    return await fetchTemplate('review_applications');
}

export async function createSettingsContent() {
    const element = await fetchTemplate('settings_view');
    const form = element.querySelector('form') || element;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    
    // Inject CSRF token hidden input dynamically!
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    form.insertBefore(csrfInput, form.firstChild);

    return element;
}

export async function createPlaceholderContent() {
    return await fetchTemplate('placeholder_view');
}

export async function createSearchContent() {
    return await fetchTemplate('search_view');
}