import { state } from './state.js';
import { api } from './api.js';

export function renderSettingsTab(contentNode) {
    const usernameEl = contentNode.querySelector('[data-role="settings-username"]');
    const usernameInput = contentNode.querySelector('[data-role="settings-username-input"]');

    if (usernameEl) {
        usernameEl.textContent = state.username || '';
        if (usernameInput) {
            usernameInput.value = state.username || '';
        }
    }

    if (usernameEl && usernameInput) {
        usernameEl.addEventListener('click', () => {
            usernameEl.classList.add('hidden');
            usernameInput.classList.remove('hidden');
            usernameInput.focus();
            usernameInput.select();
        });

        usernameInput.addEventListener('blur', () => {
            if (usernameInput.value.trim() !== "") {
                usernameEl.textContent = usernameInput.value.trim();
            }
            usernameInput.classList.add('hidden');
            usernameEl.classList.remove('hidden');
        });

        usernameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                usernameInput.blur();
            }
        });
    }

    const form = contentNode.querySelector('[data-role="settings-form"]');
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();

        const successEl = contentNode.querySelector('[data-role="settings-success"]');
        const errorsEl = contentNode.querySelector('[data-role="settings-errors"]');
        const submitBtn = contentNode.querySelector('.btn-save');

        if (successEl) successEl.classList.add('hidden');
        if (errorsEl) errorsEl.classList.add('hidden');

        const fileInput = contentNode.querySelector('[data-role="avatar-input"]');
        
        const hasNewAvatar = fileInput && fileInput.files[0];
        const hasNewUsername = usernameInput && usernameInput.value.trim() !== "" && usernameInput.value.trim() !== (state.username || '');

        if (!hasNewAvatar && !hasNewUsername) {
            if (errorsEl) {
                errorsEl.textContent = "Please change your username or select an avatar image first.";
                errorsEl.classList.remove('hidden');
            }
            return;
        }

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "Saving...";
        }

        const formData = new FormData();
        if (hasNewAvatar) {
            formData.append('avatar', fileInput.files[0]);
        }
        if (hasNewUsername) {
            formData.append('username', usernameInput.value.trim());
        }

        try {
            const response = await api.settings.edit(formData);

            const result = await response.data;
            if (response.ok && result.success) {
                if (successEl) {
                    successEl.textContent = "Settings updated successfully!";
                    successEl.classList.remove('hidden');
                }
                
                if (hasNewUsername) {
                    state.username = usernameInput.value.trim();
                }

                const navAvatar = document.getElementById('user-icon');
                if (navAvatar && result.avatar_url) {
                    navAvatar.src = result.avatar_url;
                }
                
                if (fileInput) fileInput.value = '';
            } else {
                if (errorsEl) {
                    errorsEl.textContent = result.error || "An error occurred while saving.";
                    errorsEl.classList.remove('hidden');
                }
            }
        } catch (err) {
            console.error("Settings save error:", err);
            if (errorsEl) {
                errorsEl.textContent = "Network error. Please try again.";
                errorsEl.classList.remove('hidden');
            }
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = "Save Changes";
            }
        }
    });
}
