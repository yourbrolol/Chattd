# Frontend

- Page routes: `app/chat/routers/fe/` (`register.py`, `login.py`, composed in `fe_router.py`).
- Templates: `app/chat/templates/` (Jinja2).
- Assets: `app/chat/static/` (`*.html`, `*.css`, `*.js`) served at `/static`
  when `SERVE_FE=True` (see `app/main.py`).
- Uploads: `media/` served at `/media`; message `avatar` URLs are `/media/{avatar}`.

JavaScript is required in the browser. Client WS logic per room follows
[Websockets](API-WEBSOCKETS.md): handle `init` history, append `chat_message`
frames, back off on `rate_limited` using `retry_after`.

When adding a page: add a route in `routers/fe/`, a template in `templates/`,
assets in `static/`, and document the route + WS frames here.
