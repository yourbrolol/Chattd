const API_PREFIX = "/api";

function hasBody(body) {
    return body !== undefined && body !== null;
}

function shouldStringify(body) {
    return hasBody(body)
        && typeof body === "object"
        && !(body instanceof FormData)
        && !(body instanceof URLSearchParams)
        && !(body instanceof Blob)
        && !(body instanceof ArrayBuffer);
}

async function request(path, options = {}) {
    const { body, headers = {}, ...rest } = options;
    const finalHeaders = { ...headers };
    let finalBody = body;

    if (!Object.prototype.hasOwnProperty.call(finalHeaders, "X-CSRFToken")) {
        finalHeaders["X-CSRFToken"] = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    if (shouldStringify(body)) {
        finalBody = JSON.stringify(body);
        if (!Object.prototype.hasOwnProperty.call(finalHeaders, "Content-Type")) {
            finalHeaders["Content-Type"] = "application/json";
        }
    }

    const response = await fetch(API_PREFIX + path, {
        headers: finalHeaders,
        credentials: "include",
        ...rest,
        body: finalBody,
    });

    // if (!response.ok) {
    //     const text = await response.text();
    //     throw new Error(text || response.statusText);
    // }

    // if (response.status === 204) {
    //     return;
    // }

    const rawData = await response.json()

    const target = {
        status: response.status,
        ok: response.ok,
        data: response.ok ? rawData : null,
        error: !response.ok ? rawData : null,
        
        toString() {
            return JSON.stringify(this.ok ? this.data : this.error, null, 2);
        }
    };

    return new Proxy(target, {
        get(obj, prop) {
            if (prop in obj) {
                return obj[prop];
            }
            
            if (obj.data && typeof obj.data === 'object') {
                const value = obj.data[prop];
                if (typeof value === 'function') {
                    return value.bind(obj.data);
                }
                return value;
            }
            
            if (obj.error && typeof obj.error === 'object') {
                const value = obj.error[prop];
                if (typeof value === 'function') {
                    return value.bind(obj.error);
                }
                return value;
            }
            
            return undefined;
        }
    });
}

export const http = {
    get: (path, options = {}) => request(path, options),

    post: (path, body, options = {}) =>
        request(path, {
            ...options,
            method: "POST",
            body,
        }),

    put: (path, body, options = {}) =>
        request(path, {
            ...options,
            method: "PUT",
            body,
        }),

    patch: (path, body, options = {}) =>
        request(path, {
            ...options,
            method: "PATCH",
            body,
        }),

    delete: (path, options = {}) =>
        request(path, {
            ...options,
            method: "DELETE",
        }),
};

export const api = {
    rooms: {
        list: () => http.get("/rooms"),
        create: (body, options = {}) => http.post("/rooms", body, options),
        join: (body, options = {}) => http.post("/rooms/join", body, options),
        get: (roomName, options = {}) => http.get(`/rooms/${encodeURIComponent(roomName)}`, options),
        delete: (roomName, options = {}) => http.delete(`/rooms/${encodeURIComponent(roomName)}/delete`, options),
        leave: (roomName, options = {}) => http.post(`/rooms/${encodeURIComponent(roomName)}/leave`, undefined, options),
        update: (roomName, body, options = {}) => http.patch(`/rooms/${encodeURIComponent(roomName)}`, body, options),
        kick: (roomName, username, options = {}) => http.post(`/rooms/${encodeURIComponent(roomName)}/kick`, { username }, options),
        search: (query, options = {}) => http.get(`/rooms/search?q=${encodeURIComponent(query)}`, options),
    },

    applications: {
        apply: (roomName, options = {}) => http.post("/applications", { room_name: roomName }, options),
        review: (applicationId, action, options = {}) => http.post(`/applications/${applicationId}/review`, { action }, options),
        list: (roomName, options = {}) => http.get(`/applications/pending/${encodeURIComponent(roomName)}`, options),
        pending: (options = {}) => http.get("/applications/pending", options),
    },

    settings: {
        edit: (body, options = {}) => http.post("/settings/edit", body, options),
    },

    users: {
        me: () => http.get("/users/me"),
        get: (userId, options = {}) => http.get(`/users/${encodeURIComponent(userId)}`, options),
        getByUsername: (username, options = {}) => http.get(`/users/by-username/${encodeURIComponent(username)}`, options),
    },
};
