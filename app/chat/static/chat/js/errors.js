/**
 * Central error catalog: custom errors for users vs devs.
 *
 * - Users see only ERROR_CATALOG[code] (friendly sentence).
 * - Devs get the full AppError { code, status, requestId, cause } in console/server logs.
 * - Backend envelope: { error: { code, message }, request_id, detail (=code, legacy) }.
 */

export class AppError extends Error {
    constructor(code = 'unknown_error', message = '', { status = 0, requestId = null, cause = null } = {}) {
        super(message || code);
        this.name = 'AppError';
        this.code = code;
        this.status = status;
        this.requestId = requestId;
        if (cause !== null) this.cause = cause;
    }

    /** One-line dev-friendly summary (logs), never shown raw to users. */
    toLogString() {
        const ref = this.requestId ? ` ref:${this.requestId}` : '';
        return `[${this.status || '?'} ${this.code}]${ref} ${this.message}`;
    }
}

export class NetworkError extends AppError {
    constructor(message = ERROR_CATALOG.network, opts = {}) {
        super('network', message, opts);
        this.name = 'NetworkError';
    }
}

export class AuthError extends AppError {
    constructor(code = 'auth_required', message, opts = {}) {
        super(code, message || ERROR_CATALOG[code] || code, { status: 401, ...opts });
        this.name = 'AuthError';
    }
}

/** User-facing sentences. Single place to edit copy. */
export const ERROR_CATALOG = {
    auth_required: 'You must be logged in.',
    invalid_credentials: 'Invalid username or password.',
    username_taken: 'This username is already taken.',
    bad_request: 'Invalid characters in username or password.',
    not_found: 'Not found.',
    forbidden: 'You cannot do that.',
    not_member: 'You are not a member of this room.',
    user_not_member: 'That user is not a member of this room.',
    already_member: 'You are already a member.',
    empty: 'Enter a room name.',
    empty_name: 'Room name cannot be empty.',
    empty_username: 'Username cannot be empty.',
    name_taken: 'That name is already taken.',
    no_changes: 'No changes detected.',
    file_too_large: 'File size exceeds the limit of 2MB.',
    invalid_format: 'Invalid file format. Only PNG, JPG, JPEG, GIF, and WEBP are allowed.',
    invalid_action: 'Invalid action.',
    app_required: 'This is a private room. You need to apply for membership.',
    app_pending: 'Your application is pending. Please wait for the owner to review it.',
    already_pending: 'Your application is already pending.',
    already_approved: 'Your application was already approved.',
    unknown_error: 'Something went wrong. Please try again.',
    create_failed: 'Could not create. Please try again.',
    network: 'Network error. Please try again.',
    unknown: 'Something went wrong. Please try again.',
};

/** Map any thrown value to a user-safe sentence. */
export function toUserMessage(err) {
    if (err instanceof AppError) return ERROR_CATALOG[err.code] || ERROR_CATALOG.network;
    if (err && typeof err.code === 'string') return ERROR_CATALOG[err.code] || ERROR_CATALOG.network;
    return ERROR_CATALOG.network;
}

/**
 * Normalize a backend error body to { code, message, requestId }.
 * Supports new envelope { error: {code,message}, request_id }
 * and legacy shapes { detail: 'code' } / { warning: '...' }.
 */
export function normalizeBackendError(body, status = 0, requestId = null) {
    if (!body || typeof body !== 'object') return { code: 'unknown_error', message: '', requestId };
    if (body.error && typeof body.error === 'object') {
        return {
            code: body.error.code || body.detail || 'unknown_error',
            message: body.error.message || '',
            requestId: body.request_id || requestId,
        };
    }
    return {
        code: body.detail || body.warning || body.code || 'unknown_error',
        message: body.message || '',
        requestId: body.request_id || requestId,
    };
}
