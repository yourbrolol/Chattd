export function createNewTabContent() {
    const div = document.createElement('div');
    div.className = 'new-tab-view';
    div.innerHTML = `
        <div class="new-tab-dashboard">
            <h2>New Workspace Tab</h2>
            <p class="subtitle">Select an action to get started in this tab</p>
            <div class="actions-grid">
                <div class="action-bar join-room-card">
                    <div class="join-room-card__header">
                        <div class="join-room-card__icon" aria-hidden="true">🔗</div>
                        <div class="join-room-card__titles">
                            <h3>Join a Room</h3>
                            <p class="join-room-card__hint">Enter an existing room name to jump in instantly.</p>
                        </div>
                    </div>
                    <div class="join-room-card__form">
                        <label class="join-room-card__label">Room name</label>
                        <div class="join-room-card__input-row">
                            <input type="text" data-role="join-room-input" class="dashboard-join-room-input" name="room_name" maxlength="20" placeholder="e.g. gamers-club" required autocomplete="off">
                            <button type="button" class="btn-primary join-room-card__btn" data-role="join-room-btn">Join</button>
                        </div>
                        <div data-role="join-room-errors" class="form-errors hidden"></div>
                    </div>
                </div>
                <div class="action-card">
                    <div class="action-icon">👥</div>
                    <h3>Create Room</h3>
                    <p>Start a new public, private, or unlisted chat room with friends.</p>
                    <button type="button" class="btn-primary" data-role="create-room-btn">Create Room</button>
                </div>
            </div>
        </div>
    `;
    return div;
}

export function createChatContent() {
    const div = document.createElement('div');
    div.className = 'chat-view';
    div.innerHTML = `
        <button class="hamburger-btn" data-role="hamburger-btn">☰</button>
        <div class="chat-log" data-role="chat-log"></div>
        <div class="chat-input-row" data-role="chat-input">
            <div class="avatar" data-role="avatar"></div>
            <input class="chat-message-input" data-role="chat-message-input" type="text" placeholder="Type a message..." autofocus>
            <button class="chat-message-submit" data-role="chat-message-submit">Send</button>
        </div>
    `;
    return div;
}

export function createRoomCreationContent() {
    const div = document.createElement('div');
    div.className = 'room-creation-view';
    div.innerHTML = `
        <div class="form-container">
            <h2>Create New Room</h2>
            <form data-role="room-creation-form" method="POST">
                <div class="form-room">
                    <label>Room Name</label>
                    <input type="text" data-role="room-name-input" name="room_name" maxlength="20" placeholder="e.g. gamers-club" required autocomplete="off">
                </div>
                <div class="form-room">
                    <label>Room Type</label>
                    <select data-role="room-type-select" name="room_type" required>
                        <option value="PUBLIC">Public</option>
                        <option value="UNLISTED">Unlisted</option>
                        <option value="PRIVATE">Private</option>
                    </select>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn-primary">Create Room</button>
                    <button type="button" class="btn-secondary" data-role="cancel-room-btn">Cancel</button>
                </div>
                <div data-role="room-creation-errors" class="form-errors hidden"></div>
            </form>
        </div>
    `;
    return div;
}

export function createRoomOverviewContent() {
    const div = document.createElement('div');
    div.className = 'room-overview-view';
    div.innerHTML = `
        <div class="overview-container">
            <div class="overview-header">
                <div class="overview-header__titles">
                    <h2 data-role="room-name">Room_name</h2>
                    <div data-role="room-type" class="overview-meta">Type: Public</div>
                </div>
                <div class="overview-actions">
                    <button data-role="room-overview-join-btn" class="btn-primary">Open Room</button>
                    <button data-role="room-overview-delete-btn" class="btn-secondary btn-danger hidden">Delete Room</button>
                    <button data-role="room-overview-leave-btn" class="btn-secondary btn-danger hidden">Leave Room</button>
                </div>
            </div>

            <div class="overview-box" data-role="overview-members">
                <p class="overview-box-p">Members:</p>
                <div class="overview-box-list" data-role="overview-members-list">
                    <article class="member-card hidden" data-role="member-card-template">
                        <div class="member-card__avatar">P</div>
                        <div class="member-card__content">
                            <p class="member-card__name">Jane Doe</p>
                            <p class="member-card__meta">Member</p>
                        </div>
                        <button type="button" class="member-card__kick-btn hidden" data-role="member-kick-btn">Kick</button>
                    </article>
                </div>
                <p class="overview-box-p overview-members-total" data-role="overview-members-total">No members yet.</p>
            </div>
            
            <div class="overview-apps" data-role="overview-apps">
                <p class="overview-box-p">Applications:</p>
                <button type="button" class="overview-box-btn" data-role="overview-apps-btn">View All</button>
            </div>

            <div data-role="error-message" class="form-errors hidden"></div>
        </div>
    `;
    return div;
}

export function createApplyRoomContent() {
    const div = document.createElement('div');
    div.className = 'apply-room-view';
    div.innerHTML = `
        <div class="form-container">
            <div class="apply-room-icon">🔒</div>
            <h2>Private Room</h2>
            <p class="apply-room-desc">This room requires approval to join. Send a membership request to the room owner.</p>
            <p class="apply-room-name-label">Room: <strong data-role="apply-room-name"></strong></p>
            <div class="form-actions">
                <button type="button" class="btn-primary" data-role="apply-room-submit-btn">Send Request</button>
                <button type="button" class="btn-secondary" data-role="apply-room-cancel-btn">Cancel</button>
            </div>
            <div data-role="apply-room-errors" class="form-errors hidden"></div>
            <div data-role="apply-room-success" class="form-success hidden"></div>
        </div>
    `;
    return div;
}

export function createReviewApplicationsContent() {
    const div = document.createElement('div');
    div.className = 'review-applications-view';
    div.innerHTML = `
        <div class="review-applications-container">
            <div class="review-header">
                <h2>Pending Applications</h2>
                <p class="subtitle">People waiting to join your rooms</p>
            </div>
            <div class="applications-list" data-role="applications-list">
                <!-- Populated by JS -->
            </div>
            <div class="applications-empty hidden" data-role="applications-empty">
                <div class="applications-empty-icon">✅</div>
                <p>No pending applications.</p>
            </div>
        </div>
    `;
    return div;
}

export function createSettingsContent() {
    const div = document.createElement('div');
    div.className = 'settings-view';
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    div.innerHTML = `
        <form method="POST" action="/settings/edit" enctype="multipart/form-data" class="settings-container" data-role="settings-form">
            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">

            <h2>Settings</h2>
            <p class="subtitle">Manage your account and preferences</p>
            
            <div class="settings-section">
                <h3>Account</h3>
                <p><strong>Username:</strong> <span data-role="settings-username"></span></p>
                
                <div class="avatar-changer">
                    <label>Change Avatar:</label>
                    <input type="file" name="avatar" accept="image/*" data-role="avatar-input">
                </div>
            </div>

            <div class="form-actions">
                <button type="submit" class="btn-save">Save Changes</button>
            </div>
        </form>
    `;
    return div;
}

export function createPlaceholderContent() {
    const div = document.createElement('div');
    div.className = 'chat-placeholder-view';
    div.innerHTML = `
        <div class="placeholder-content">
            <div class="placeholder-icon">💬</div>
            <h2>Welcome to SpreadTalk</h2>
            <p>Select a room from the left sidebar to start chatting, or click the "+" button above to create a new room.</p>
        </div>
    `;
    return div;
}
