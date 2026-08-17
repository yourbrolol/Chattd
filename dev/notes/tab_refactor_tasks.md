# Tab System Refactor — Agent Task List

## Context

The current system uses a single shared DOM node per view type. `switchView()` just toggles
`hidden`. Render scripts overwrite that shared node on every tab activation. This means
content is never preserved between tab switches.

**Goal:** each tab owns its own detached DOM subtree (`contentNode`). Switching tabs detaches
the old node and reattaches the new one. Render scripts are scoped to the tab's node, not to
the document. Static views always render fresh; live views (chat, overview) preserve or
intelligently refresh their content.

---

## Phase 1 — Extend State

### Task 1 — Extend `state.js` tab registry shape

Add two new fields to the registry entry shape (comment-documented):
- `contentNode` — `HTMLElement | null` — the tab's detached DOM subtree; `null` until first activation
- `dirty` — `boolean` — when `true`, the view must re-fetch/re-render data on next activation even if `contentNode` already exists

No runtime logic changes yet — this is just a schema extension and a comment block.

---

## Phase 2 — View Mount Layer

### Task 2 — Replace `views.js` with a mount/unmount module

Remove the `switchView()` function entirely. Implement two new exported functions in its place:

- `attachTabContent(node)` — appends `node` as the sole visible child of `#view-main`
- `detachCurrentContent()` — removes and returns whatever node is currently inside `#view-main`

`#view-main` should always contain at most one child at a time. No `hidden` toggling.

---

## Phase 3 — Simplify HTML Template

### Task 3 — Strip static view divs from `index.html`

Remove the following static `<div>` blocks from `index.html` (they will be created per-tab in JS):
- `#new-tab-view`
- `#room-overview-view`
- `#apply-room-view`
- `#review-applications-view`
- `#room-creation-view`
- `#settings-view`
- `#chat` (the chat view including `#chat-log`, `#chat-input`, etc.)
- `#chat-placeholder`

Leave `#view-main` as an empty container. Leave the nav, sidebar (`#chats`), and `#tabs-container` untouched.

> **Note:** All CSS for these views remains in place — it will still work because factory functions
> produce nodes with the same classes.

---

## Phase 4 — Per-Tab View Factories

### Task 4 — Create `factories.js`

Create a new file `static/chat/js/factories.js`. It exports one factory function per tab type.
Each factory creates and returns a **fresh, fully-structured DOM subtree** for that view — equivalent
to what the old static HTML contained. No data is fetched or rendered at this stage; factories
only build structure.

Factories to implement:

| Export | Builds |
|---|---|
| `createNewTabContent()` | Dashboard with join-room input and create-room button |
| `createChatContent()` | Chat log, message input row, hamburger button |
| `createRoomCreationContent()` | Room name + type form with submit/cancel |
| `createRoomOverviewContent()` | Overview header, member list, action buttons |
| `createApplyRoomContent()` | Private-room apply form |
| `createReviewApplicationsContent()` | Applications list container |
| `createSettingsContent()` | Settings form (avatar upload, etc.) |
| `createPlaceholderContent()` | Welcome/empty state placeholder |

**Important:** factory functions must **not** use `id` attributes on inner elements — use
`data-*` attributes or classes instead, because multiple instances could theoretically exist.
Any code that currently uses `document.getElementById` to find elements inside a view must
instead use `contentNode.querySelector(...)`.

---

## Phase 5 — Rewrite `tabs.js` Core

### Task 5 — Define a `TAB_HANDLERS` dispatch table

At the top of `tabs.js`, define a `TAB_HANDLERS` object keyed by tab type string. Each entry
contains:
- `factory` — reference to the corresponding factory function from `factories.js`
- `onActivate(contentNode, tabInfo)` — async function called when the tab is activated;
  receives the tab's `contentNode` and its registry entry
- `dirty` — `boolean` — if `true`, `onActivate` is always called even if `contentNode` already
  exists (forces data refresh on every re-activation)
- `noCache` — `boolean` — if `true`, `contentNode` is discarded on deactivation and recreated
  fresh next time (used for static forms that need clean state)

Tab types and their flags:

| Type | `dirty` | `noCache` |
|---|---|---|
| `new-tab` | false | true |
| `room-creation` | false | true |
| `room` | false | false |
| `room-overview` | true | false |
| `apply-room` | false | true |
| `review-applications` | true | false |
| `settings` | false | true |
| `placeholder` | false | true |

### Task 6 — Update `createTabElement` to initialise new registry fields

When registering a tab in `state.tabsById`, include `contentNode: null` and `dirty: false`
alongside the existing `id`, `title`, `type`, `metadata` fields.

### Task 7 — Rewrite `activateTab`

Replace the current `if/else` type chain with the following logic:

1. Remove `.active` / `aria-selected` from all tabs; set them on the new tab
2. Look up the **previously active** tab from `state.tabsById`; if it has `noCache: true`,
   set its `contentNode = null`
3. Call `detachCurrentContent()` to unmount whatever is currently in `#view-main`
4. Look up the new tab's `tabInfo` from `state.tabsById`
5. Look up its handler from `TAB_HANDLERS`
6. If `tabInfo.contentNode` is `null`, call `handler.factory()` and assign the result to
   `tabInfo.contentNode`
7. Call `attachTabContent(tabInfo.contentNode)`
8. If `tabInfo.contentNode` was just created **or** `handler.dirty` is `true`,
   call `handler.onActivate(tabInfo.contentNode, tabInfo)`
9. Close any open WebSocket if the new tab type is not `room`; open one if it is

### Task 8 — Update `closeTab` to release `contentNode`

Before deleting the `state.tabsById[tabId]` entry, set `tabInfo.contentNode = null`
to allow GC of the detached subtree.

---

## Phase 6 — Unified Tab Opener

### Task 9 — Implement `openTab(type, opts)` in `tabs.js`

A single generic exported function that:
1. Accepts `type` (string) and `opts`:
   - `title` — display string
   - `metadata` — object (e.g. `{ room: 'general' }`)
   - `unique` — if `true`, find and reuse any existing tab of the same type instead of creating a new one
   - `uniqueKey` — if set, de-duplicate by `metadata[uniqueKey]` instead of just type
     (used for room tabs: one tab per room name, not one per type)
2. Performs de-duplication via `state.tabsById` lookup
3. If an existing tab is found, activates it and returns
4. Otherwise creates a new tab element via `createTabElement`, appends it, activates it,
   and scrolls it into view

### Task 10 — Replace all individual open functions with `openTab` calls

Replace these exported functions with thin wrappers around `openTab`:
- `openNewTab()` → `openTab('new-tab', { title: 'New Tab' })`
- `openOverviewTab(roomName)` → `openTab('room-overview', { title: ..., metadata: { relatedRoom: roomName }, unique: true, uniqueKey: 'relatedRoom' })`
- `openSettingsTab()` → `openTab('settings', { title: 'Settings', unique: true })`
- `openApplicationsTab()` → `openTab('review-applications', { title: 'Applications', unique: true })`
- `openChatTab(roomName)` → keep existing join-room logic, then call `openTab('room', { ... })`

Keep the function names as exported wrappers so call sites in other modules don't need to change.

---

## Phase 7 — Adapt Render Scripts

### Task 11 — Adapt `overview.js`

`renderRoomOverview` currently queries by global ID. Update it to:
- Accept a `contentNode` parameter (the tab's DOM subtree)
- Use `contentNode.querySelector(...)` for all element lookups instead of `document.getElementById`
- This function becomes the `onActivate` handler for the `room-overview` entry in `TAB_HANDLERS`

### Task 12 — Adapt `socket.js`

`appendMessage` and the `onmessage` handler currently write to the global `#chat-log`.
Update them to:
- Accept the chat `contentNode` (or resolve it from `state`) to find the log element via
  `contentNode.querySelector('[data-role="chat-log"]')`
- Do NOT wipe and re-render the log on `init` if the tab already has an existing `contentNode`
  with messages — only wipe and repopulate if this is a genuinely fresh connection.
  Use a flag on `tabInfo` (e.g. `tabInfo.roomLoaded`) to distinguish first-connect from reconnect.

### Task 13 — Adapt `init.js`

Several `bind*` functions attach event listeners to elements found by global ID. These must
now be set up inside each view's `onActivate` handler (or factory), not once at app init.
Move the following:

- `bindJoinRoom()` listener setup → into the `new-tab` `onActivate` handler
- `bindGroupCreation()` form and cancel listeners → into `room-creation` `onActivate`
- `bindApplyRoomView()` → into `apply-room` `onActivate`
- `bindReviewApplicationsView()` → into `review-applications` `onActivate`
- Hamburger button listener (currently in `openRoomOverview()`) → into `room` `onActivate`

Keep the following in `initApp()` as they are global:
- `bindMessageInput()` → move into `room` `onActivate` (scoped to contentNode)
- `bindSlashFocus()` → keep global (keyboard shortcut)
- `bindTabKeyboard()` → keep global
- `bindSettings()` (`#user` nav element) → keep global
- `loadRooms(...)` → keep in `initApp`
- `updateReviewBadge()` → keep in `initApp`

### Task 14 — Adapt `room.js`

`handleGroupSubmission` and `cancelGroupCreation` query global form elements.
Update them to receive the `contentNode` for the room-creation view and scope queries to it.
Thread the `contentNode` through from the `room-creation` `onActivate` handler.

---

## Phase 8 — Cleanup & Verification

### Task 15 — Audit for remaining global ID queries on view elements

Search all `static/chat/js/` files for `getElementById` and `querySelector` calls that
reference IDs of elements that no longer exist as globals (e.g. `chat-log`, `room-name`,
`overview-members-list`, `room-creation-form`, `chat-message-input`, etc.).
Each must be replaced with a scoped `contentNode.querySelector('[data-role="..."]')` call.

### Task 16 — Rename or repurpose `views.js`

If `views.js` now only exports `attachTabContent` and `detachCurrentContent`, rename it to
`mount.js` for clarity. Update all import paths in `tabs.js` and `init.js` accordingly.

### Task 17 — Manual verification checklist

Test each tab type end-to-end:

- [ ] Open a new tab → dashboard renders
- [ ] Type in join-room input, submit → chat tab opens, WS connects, messages appear
- [ ] Open a second chat tab for a different room → both tabs are independent
- [ ] Switch between two chat tabs → each shows its own message log, scroll position preserved
- [ ] Switch to a room-overview tab → member list fetched and rendered
- [ ] Switch away and back → member list re-fetched (dirty), shows updated data
- [ ] Open settings → form renders with correct username
- [ ] Close a tab → adjacent tab activates correctly
- [ ] Close all tabs → placeholder view shown
- [ ] Keyboard shortcuts (Alt+1/2/4/5) still work
