import { api } from './api.js';

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

/**
 * Submit a room application.
 * Returns { ok, status, app } on success or { ok: false, error } on failure.
 *   status: 'ok' | 'already_pending' | 'already_approved' | 'already_member'
 */
export async function applyToRoom(roomName) {
    const trimmed = (roomName || '').trim();
    if (!trimmed) return { ok: false, error: 'empty' };

    const body = new URLSearchParams();
    body.append('csrfmiddlewaretoken', getCsrfToken());
    body.append('room_name', trimmed);

    try {
        const response = await api.applications.apply(trimmed);

        const data = await response.data;

        if (response.status === 401) return { ok: false, error: 'auth_required' };
        if (response.status === 404) return { ok: false, error: 'not_found' };
        if (response.status === 400) return { ok: false, error: data.error || 'unknown' };
        if (!response.ok && response.status !== 200) return { ok: false, error: 'network' };

        // 201 = new application, 200 = already_pending / already_approved
        return { ok: true, status: data.warning || 'ok', app: data };
    } catch {
        return { ok: false, error: 'network' };
    }
}

/**
 * Approve or reject a room application (owner only).
 * action: 'approve' | 'reject'
 * Returns { ok, app } or { ok: false, error }.
 */
export async function reviewApplication(applicationId, action) {
    try {
        const response = await api.applications.review(applicationId, action);

        if (response.status === 403) return { ok: false, error: 'forbidden' };
        if (response.status === 404) return { ok: false, error: 'not_found' };
        if (!response.ok) return { ok: false, error: 'network' };

        return { ok: true, app: data };
    } catch (e) {
        console.error(e)
        return { ok: false, error: 'network' };
    }
}

/**
 * Fetch pending applications for a room the current user owns.
 * Returns an array of { id, room, applicant, status } objects, or [].
 */
export async function loadRoomPendingApplications(roomName) {
    if (!roomName) return [];
    
    try {
        const response = await api.applications.list(roomName);
        if (!response.ok) return [];
        return await response.data;
    } catch {
        return [];
    }
}

// SCRAPPED
export async function loadPendingApplications() {
    try {
        const response = await api.applications.pending();
        if (!response.ok) return [];
        return await response.data;
    } catch {
        return [];
    }
}
