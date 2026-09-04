import { api } from './api.js';
import { AppError } from './errors.js';

/**
 * Submit a room application.
 * Returns { ok, status, app } on success or { ok: false, error } on failure.
 *   status: 'ok' | 'already_pending' | 'already_approved' | 'PENDING' | ...
 * Backend returns 201 for new, 200 {status} for idempotent re-apply.
 */
export async function applyToRoom(roomName) {
    const trimmed = (roomName || '').trim();
    if (!trimmed) return { ok: false, error: 'empty' };

    try {
        const data = await api.applications.apply(trimmed);
        // data: { id, room, status: 'PENDING', result: 'created'|'already_pending'|'already_approved' }
        return { ok: true, status: data?.result || 'ok', app: data };
    } catch (err) {
        console.error('applyToRoom failed:', err instanceof AppError ? err.toLogString() : err);
        return { ok: false, error: err instanceof AppError ? err.code : 'network' };
    }
}

/**
 * Approve or reject a room application (owner only).
 * action: 'approve' | 'reject'
 * Returns { ok, app } or { ok: false, error }.
 */
export async function reviewApplication(applicationId, action) {
    try {
        const data = await api.applications.review(applicationId, action);
        return { ok: true, error: null, app: data };
    } catch (err) {
        console.error('reviewApplication failed:', err instanceof AppError ? err.toLogString() : err);
        return { ok: false, error: err instanceof AppError ? err.code : 'network' };
    }
}

/**
 * Fetch pending applications for a room the current user owns.
 * Returns an array of { id, room, applicant, status } objects, or [].
 */
export async function loadRoomPendingApplications(roomName) {
    try {
        if (roomName) return await api.applications.list(roomName);
        return await api.applications.pending();
    } catch (err) {
        console.error('loadRoomPendingApplications failed:', err instanceof AppError ? err.toLogString() : err);
        return [];
    }
}

// SCRAPPED
export async function loadPendingApplications() {
    try {
        return await api.applications.pending();
    } catch (err) {
        console.error('loadPendingApplications failed:', err instanceof AppError ? err.toLogString() : err);
        return [];
    }
}
