# Websockets

Endpoint (see `app/core/websockets.py`): `/ws/chat/{room_name}/`

## Connect sequence

1. Client opens WS with authenticated session (JWT cookie, `websocket.user`).
2. Unauthenticated → server closes with `WS_CLOSE_AUTH_REQUIRED`.
3. Per-user connect limiter (`ws-connect:{username}`, `WS_CONNECT_*`) is checked;
   over limit → close code `4029`, reason `rate_limited`.
4. Server loads the room (`chat/services/rooms.py:get_room`):
   missing → `WS_CLOSE_NOT_FOUND`; non-member → `WS_CLOSE_FORBIDDEN`.
5. Server sends history frame, then enters the receive loop.

## Frames

Server → client, history:

```json
{"type": "init", "message_history": [{"user": "ada", "content": "hi", "avatar": "/media/ada.png"}]}
```

Client → server, chat:

```json
{"type": "chat_message", "message": "hello room"}
```

Server → client, broadcast:

```json
{"type": "chat_message", "user": "ada", "content": "hello room", "avatar": "/media/ada.png"}
```

Server → client, rate feedback (`WS_MESSAGE_*` limiter, key `ws-msg:{username}`):

```json
{"type": "rate_limited", "detail": "rate_limit_exceeded", "limit": 1, "remaining": 0, "retry_after": 1.0}
{"type": "quota_left", "limit": 1, "remaining": 0, "retry_after": 1.0}
```

Malformed JSON from the client is ignored (`continue`), the socket stays open.

## Tuning

See [Configuration](CONFIGURATION.md). Defaults are strict
(1 message / second) — raise `WS_MESSAGE_MAX_EVENTS` for load tests.

## Client sketch

```js
const ws = new WebSocket(`ws://${location.host}/ws/chat/general/`);
ws.onmessage = (ev) => {
  const frame = JSON.parse(ev.data);
  if (frame.type === "init") renderHistory(frame.message_history);
  if (frame.type === "chat_message") appendMessage(frame);
  if (frame.type === "rate_limited") showCooldown(frame.retry_after);
};
ws.onopen = () => ws.send(JSON.stringify({type: "chat_message", message: "hi"}));
```
