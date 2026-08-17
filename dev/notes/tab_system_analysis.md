# Tab System — Architecture Analysis & Refactor Design

## Current Problems (Root Cause)

There is a **single shared DOM node per view type**. `switchView()` only toggles CSS `hidden`.
When a tab is activated, its render script **overwrites the shared node** unconditionally.

This causes:

| Scenario | What breaks |
|---|---|
| Two `room-overview` tabs for different rooms | Switching back always re-fetches; no history preserved |
| Two `room` (chat) tabs | Only one `#chat-log` exists; switching kills the other WS and wipes messages |
| `new-tab` → type mutates to `room-creation` | Works by accident; there's only ever one of each |
| Re-opening the same tab type | De-duplication in registry prevents a second tab, but it's fragile |

Additionally, in `tabs.js` every open function (`openNewTab`, `openOverviewTab`, `openSettingsTab`, `openApplicationsTab`) is a near-identical copy. `activateTab` has a long hardcoded `if/else` chain matching type strings.

---

## Evaluating the User's Idea

> "Keep tab content for most renders and render either from zero or from the content."

**Good parts:**
- Caching rendered content per tab avoids redundant fetches
- Makes the tab model actually match what the user sees (content is preserved on re-visit)
- Chat rooms in particular benefit enormously — you don't want to re-fetch 50 messages every tab switch

**Risk/nuance:**
- Static views (`new-tab`, `room-creation`, `settings`) have no state worth caching — always render fresh
- Live views (`chat room`) can't truly cache because the WebSocket is real-time; you can cache the message log DOM but must reconnect the WS
- `room-overview` can cache the rendered member list but should re-fetch on re-activation (data could be stale)
- `review-applications` should always re-fetch (highly mutable, badge count already polls it)

The idea is correct in principle. The key insight is: **cache the rendered DOM fragment per tab, not a single shared node**.

---

## Recommended Design: Per-Tab Detached DOM

### Core concept

Each tab gets its own **detached DOM subtree** stored in `state.tabsById[id].contentNode`.

When a tab is activated:
1. Detach the current view's subtree from `#view-main` (save it back to the old tab's `contentNode`)
2. Attach the new tab's `contentNode` into `#view-main`
3. If `contentNode` is null (first visit), call the view's init/render function

This means:
- The HTML template no longer needs static view divs — they're created dynamically per tab
- `switchView()` becomes `attachTabContent(node)`
- No more singleton view nodes

### Per-view strategy

| Type | Cache behaviour | Re-render on re-activation? |
|---|---|---|
| `new-tab` | No cache needed; it's a static form | Always fresh (reset input values) |
| `room-creation` | No cache needed; ephemeral tab | Always fresh |
| `room` (chat) | **Cache the message log DOM** | Re-open WS, don't re-fetch history (append from WS `init`) |
| `room-overview` | Cache the rendered HTML | **Re-fetch** on re-activation (mark stale) |
| `review-applications` | No cache | Always re-fetch |
| `settings` | No cache needed | Always fresh |

### `state.js` additions

```js
export const state = {
    currentRoom: null,
    chatSocket: null,
    username: null,
    tabsById: {},
    // tabsById entry shape:
    // {
    //   id, title, type, metadata,
    //   contentNode: HTMLElement | null,   // detached DOM subtree
    //   dirty: boolean,                    // true = re-fetch on next activation
    // }
};
```

### Unified `tabs.js` API

Instead of one `openXxxTab()` function per type, a single generic opener:

```js
// Generic opener — handles de-dup, creation, activation
export function openTab(type, { title, metadata = {}, unique = false } = {}) {
    // if unique=true, find existing tab of same type (like settings)
    // if metadata.room set, de-dup by room name
    // create tab, register in state, activate
}
```

`activateTab` becomes data-driven instead of an if/else chain:

```js
const TAB_HANDLERS = {
    'new-tab':              { onActivate: initNewTabView },
    'room-creation':        { onActivate: initRoomCreationView },
    'room':                 { onActivate: activateChatRoom, preserveContent: true },
    'room-overview':        { onActivate: renderRoomOverview, dirty: true },
    'review-applications':  { onActivate: renderApplicationsList },
    'settings':             { onActivate: initSettingsView },
};

export function activateTab(tabElement) {
    // 1. deactivate current tab, detach its contentNode
    // 2. look up handler by tabInfo.type
    // 3. attach contentNode if exists, else create and call onActivate
    // 4. if dirty=true, always call onActivate regardless
}
```

---

## What to Keep vs Change

| Current code | Verdict |
|---|---|
| `state.tabsById` registry | ✅ Keep, extend with `contentNode` + `dirty` |
| `createTabElement` | ✅ Keep, minor cleanup |
| `closeTab` | ✅ Keep, add contentNode cleanup |
| `cycleTabLeft/Right`, `closeActiveTab` | ✅ Keep as-is |
| `updateTabTitle`, `setTabMetadata` | ✅ Keep as-is |
| `openNewTab`, `openOverviewTab`, `openSettingsTab`, `openApplicationsTab` | ⚠️ Consolidate into `openTab(type, opts)` |
| `activateTab` if/else chain | ❌ Replace with `TAB_HANDLERS` dispatch table |
| `switchView()` (views.js) | ❌ Replace with `attachTabContent(node)` |
| Singleton view divs in HTML | ❌ Remove; create per-tab via JS |
| `renderRoomOverview` (always re-renders) | ⚠️ Add dirty-flag guard |
| `socket.js` wiping `#chat-log` on `init` | ⚠️ Must write to per-tab node, not global `#chat-log` |

---

## What Makes Chat Rooms Special

The chat view is the hardest because:
- The WebSocket pushes messages in real-time to `#chat-log`
- If you cache the DOM but close the WS (on tab switch), you miss messages
- Options:
  1. **Keep WS alive** on tab switch (background tabs still receive messages, appended to cached node) — best UX, highest resource use
  2. **Close WS, reconnect on re-activation** — WS `init` event re-sends history, so you get messages you missed; simplest
  3. **Hybrid**: keep WS alive for a short TTL after tab switch, then close

Option 2 is the most practical given the current WS design (server sends `init` with full history on connect).

---

## Summary

Your instinct is right. The fix is:
1. **Per-tab detached DOM subtrees** stored in `state.tabsById`
2. **Dirty flag** for views that must re-fetch on re-activation
3. **Unified `openTab()` + dispatch table** in tabs.js to eliminate the hardcoded boilerplate
4. The HTML template becomes much simpler — no static view divs, just `#view-main` as the mount point
