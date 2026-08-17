# Tab system changes and diffs

Date: 2026-05-29

This document lists every unstaged edit in the working tree (git diff) related to the tab system work I performed, followed by a concise explanation of each change and an overall description of the tab system mechanics I implemented.

---

## Full unstaged diff (raw)

```
<!-- begin raw git diff -->

diff --git a/app/chat/static/chat/js/init.js b/app/chat/static/chat/js/init.js
index 5cc9d30..ccbca52 100644
--- a/app/chat/static/chat/js/init.js
+++ b/app/chat/static/chat/js/init.js
@@ -1,8 +1,8 @@
 import { sendMessage } from './socket.js';
-import { openNewTab, activateTab, cycleTabLeft, cycleTabRight, closeActiveTab }
 from './tabs.js';
+import { openNewTab, activateTab, cycleTabLeft, cycleTabRight, closeActiveTab, 
updateTabTitle, setTabMetadata, getTabElementById, openChatTab, openOverviewTab 
} from './tabs.js';
+import { state } from './state.js';
 import { handleGroupSubmission, cancelGroupCreation } from './room.js';
 import { loadRooms, joinRoom, showJoinError, getJoinErrorMessage } from './room
s.js';
-import { openChatTab, openOverviewTab } from './tabs.js';
 import { applyToRoom, reviewApplication, loadPendingApplications } from './appl
ications.js';
 import { renderRoomOverview } from './overview.js';
 import { switchView } from './views.js';
@@ -264,11 +264,15 @@ function bindGroupCreation() {
 
     document.getElementById('dashboard-create-room-btn')?.addEventListener('cli
ck', () => {
         const activeTab = document.querySelector('#tabs .tab.active');
-        if (activeTab && activeTab.getAttribute('data-special') === 'new-tab') 
{
-            activeTab.setAttribute('data-special', 'room-creation');
-            const titleSpan = activeTab.querySelector('.tab-title');
-            if (titleSpan) titleSpan.textContent = 'Create Room';
-            activateTab(activeTab);
+        const tabId = activeTab?.getAttribute('data-tab-id');
+        if (tabId) {
+            const t = tabId ? state.tabsById[tabId] : null;
+            if (t && t.type === 'new-tab') {
+                setTabMetadata(tabId, { special: 'room-creation' });
+                updateTabTitle(tabId, 'Create Room');
+                const el = getTabElementById(tabId);
+                if (el) activateTab(el);
+            }
         }
     });
 }

diff --git a/app/chat/static/chat/js/room.js b/app/chat/static/chat/js/room.js
index c3c3d8c..90c78ab 100644
--- a/app/chat/static/chat/js/room.js
+++ b/app/chat/static/chat/js/room.js
@@ -1,5 +1,6 @@
-import { openChatTab, closeTab } from './tabs.js';
+import { openChatTab, closeTab, getTabElementById } from './tabs.js';
 import { loadRooms } from './rooms.js';
+import { state } from './state.js';
 
 export async function handleGroupSubmission(e) {
     e.preventDefault();
@@ -36,13 +37,15 @@ export async function handleGroupSubmission(e) {
             loadRooms((name) => { void openChatTab(name); });
 
             const tabsContainer = document.getElementById('tabs');
-            if (tabsContainer) {
-                tabsContainer.querySelectorAll('.tab').forEach(tab => {
-                    if (tab.getAttribute('data-special') === 'room-creation') {
-                        tab.remove();
-                    }
-                });
-            }
+            // remove any temporary "room-creation" tabs via central registry
+            Object.keys(state.tabsById).forEach(id => {
+                const t = state.tabsById[id];
+                if (t && t.type === 'room-creation') {
+                    const el = getTabElementById(id);
+                    if (el) el.remove();
+                    delete state.tabsById[id];
+                }
+            });
 
             setTimeout(() => { void openChatTab(newRoomName); }, 100);
         } else if (errorsDiv) {
@@ -59,12 +62,12 @@ export async function handleGroupSubmission(e) {
 }
 
 export function cancelGroupCreation() {
-    const tabsContainer = document.getElementById('tabs');
-    if (!tabsContainer) return;
-
-    tabsContainer.querySelectorAll('.tab').forEach(tab => {
-        if (tab.getAttribute('data-special') === 'room-creation') {
-            closeTab(tab);
-        }
-    });
+    // close any room-creation tabs using the registry to ensure consistent cle
anup
+    Object.keys(state.tabsById).forEach(id => {
+        const t = state.tabsById[id];
+        if (t && t.type === 'room-creation') {
+            const el = getTabElementById(id);
+            if (el) closeTab(el);
+        }
+    });
 }

diff --git a/app/chat/static/chat/js/state.js b/app/chat/static/chat/js/state.js
index 1bc19a6..f0cc9f4 100644
--- a/app/chat/static/chat/js/state.js
+++ b/app/chat/static/chat/js/state.js
@@ -1,4 +1,6 @@
 export const state = {
     currentRoom: null,
-    chatSocket: null
+    chatSocket: null,
+    // Registry for tab metadata keyed by internal tab id
+    tabsById: {}
 };

diff --git a/app/chat/static/chat/js/tabs.js b/app/chat/static/chat/js/tabs.js
index cb79bc7..1e86b3a 100644
--- a/app/chat/static/chat/js/tabs.js
+++ b/app/chat/static/chat/js/tabs.js
@@ -16,11 +16,13 @@ export function activateTab(tabElement) {
     tabElement.classList.add('active');
     tabElement.setAttribute('aria-selected', 'true');
 
-    const room = tabElement.getAttribute('data-room');
-    const isGroupCreation = tabElement.getAttribute('data-special') === 'room-c
reation';
-    const isNewTab = tabElement.getAttribute('data-special') === 'new-tab';
-    const isRoomOverview = tabElement.getAttribute('data-special') === 'room-ov
erview';
-    const isApplications = tabElement.getAttribute('data-special') === 'review-
applications';
+    const tabId = tabElement.getAttribute('data-tab-id');
+    const tabInfo = tabId ? state.tabsById[tabId] : null;
+    const room = tabInfo && tabInfo.type === 'room' ? (tabInfo.metadata?.room |
| tabInfo.title) : null;
+    const isGroupCreation = tabInfo?.type === 'room-creation';
+    const isNewTab = tabInfo?.type === 'new-tab';
+    const isRoomOverview = tabInfo?.type === 'room-overview';
+    const isApplications = tabInfo?.type === 'review-applications';
@@ -34,7 +36,7 @@ export function activateTab(tabElement) {
         state.currentRoom = null;
         switchView('room-creation');
     } else if (isRoomOverview) {
-        const related = tabElement.getAttribute('data-related-room');
+        const related = tabInfo?.metadata?.relatedRoom || null;
         state.currentRoom = related ? related : null;
         switchView('room-overview');
     } else if (isApplications) {
@@ -61,12 +63,17 @@ export async function openChatTab(roomName) {
     }
     showJoinError('');
 
-    const existingTab = [...tabsContainer.querySelectorAll('.tab')]
-        .find(tab => tab.getAttribute('data-room') === joinResult.name);
-
-    if (existingTab) {
-        activateTab(existingTab);
-        return true;
+    // prefer registry lookup to find existing room tab
+    const existingId = Object.keys(state.tabsById).find(id => {
+        const t = state.tabsById[id];
+        return t && t.type === 'room' && ((t.metadata && t.metadata.room === jo
inResult.name) || t.title === joinResult.name);
+    });
+    if (existingId) {
+        const existingTab = document.querySelector(`#tabs .tab[data-tab-id="${e
xistingId}"]`);
+        if (existingTab) {
+            activateTab(existingTab);
+            return true;
+        }
+    }
@@ -92,17 +99,24 @@ function createTabElement(titleText, typeAttr, metadata = {}
) {
     tabDiv.setAttribute('role', 'tab');
     tabDiv.setAttribute('aria-selected', 'false');
 
+    // generate a simple unique id for the tab and register metadata centrally
+    const tabId = `t-${Date.now().toString(36)}-${Math.floor(Math.random()*1000
0).toString(36)}`;
+    tabDiv.setAttribute('data-tab-id', tabId);
+
+    // make a shallow copy of metadata we can augment
+    const metaCopy = Object.assign({}, metadata || {});
     if (typeAttr === 'room') {
         tabDiv.setAttribute('data-room', titleText);
+        // store canonical room identifier in metadata for registry lookups
+        metaCopy.room = titleText;
     } else {
         tabDiv.setAttribute('data-special', typeAttr);
     }
 
-    Object.keys(metadata || {}).forEach(k => {
-        const attrName = 'data-' + k.replace(/([A-Z])/g, '-$1').toLowerCase();
-        const value = metadata[k];
-        if (value === undefined || value === null) return;
-        // store primitives directly; objects/arrays JSON-stringified
-        tabDiv.setAttribute(attrName, (typeof value === 'object') ? JSON.string
ify(value) : String(value));
-    });
+    Object.keys(metaCopy).forEach(k => {
+        const attrName = 'data-' + k.replace(/([A-Z])/g, '-$1').toLowerCase();
+        const value = metaCopy[k];
+        if (value === undefined || value === null) return;
+        tabDiv.setAttribute(attrName, (typeof value === 'object') ? JSON.string
ify(value) : String(value));
+    });
@@ -120,6 +134,14 @@ function createTabElement(titleText, typeAttr, metadata = {
}) {
 
     tabDiv.appendChild(span);
     tabDiv.appendChild(closeBtn);
+
+    // store a structured representation in the central registry
+    state.tabsById[tabId] = {
+        id: tabId,
+        title: String(titleText),
+        type: typeAttr,
+        metadata: metaCopy
+    };
     return tabDiv;
 }
 
@@ -159,8 +181,12 @@ export function closeTab(tabElement) {
     if (!tabsContainer) return;
 
     const isActive = tabElement.classList.contains('active');
-    tabElement.remove();
+    const tabId = tabElement.getAttribute('data-tab-id');
+    tabElement.remove();
+
+    // clean up central registry
+    if (tabId && state.tabsById[tabId]) delete state.tabsById[tabId];
 
     if (isActive) {
         const remainingTabs = tabsContainer.querySelectorAll('.tab');
         if (remainingTabs.length > 0) {
             activateTab(remainingTabs[remainingTabs.length - 1]);
         } else {
             state.currentRoom = null;
             if (state.chatSocket) {
                 state.chatSocket.close();
                 state.chatSocket = null;
             }
             switchView('placeholder');
         }
     }
 }
@@ -176,20 +202,67 @@ export function closeTab(tabElement) {
     }
 }
 
+// Helper utilities for safer tab edits and metadata handling
+export function getTabElementById(tabId) {
+    if (!tabId) return null;
+    return document.querySelector(`#tabs .tab[data-tab-id="${tabId}"]`);
+}
+
+export function updateTabTitle(tabId, newTitle) {
+    const el = getTabElementById(tabId);
+    if (!el) return false;
+    const span = el.querySelector('.tab-title');
+    if (span) span.textContent = String(newTitle);
+    if (state.tabsById[tabId]) state.tabsById[tabId].title = String(newTitle);
+    return true;
+}
+
+export function setTabMetadata(tabId, metadata) {
+    const el = getTabElementById(tabId);
+    if (!el) return false;
+    const meta = metadata || {};
+    Object.keys(meta).forEach(k => {
+        const attrName = 'data-' + k.replace(/([A-Z])/g, '-$1').toLowerCase();
+        const value = meta[k];
+        if (value === undefined || value === null) {
+            el.removeAttribute(attrName);
+        } else {
+            el.setAttribute(attrName, (typeof value === 'object') ? JSON.string
ify(value) : String(value));
+        }
+    });
+    if (state.tabsById[tabId]) {
+        state.tabsById[tabId].metadata = Object.assign({}, state.tabsById[tabId
].metadata, meta);
+        // if special/type changed, keep the typed field in sync
+        if (meta.special) state.tabsById[tabId].type = String(meta.special);
+        if (meta.type) state.tabsById[tabId].type = String(meta.type);
+    }
+    return true;
+}
+
+export function getTabMetadata(tabId) {
+    return state.tabsById[tabId] ? state.tabsById[tabId].metadata : null;
+}
+
 export function openOverviewTab(roomName = null) {
     const tabsContainer = document.getElementById('tabs');
     if (!tabsContainer) return;
-
-    let existing = null;
+    // try registry-first lookup for overview tab
+    let existingId = null;
     if (roomName) {
-        existing = [...tabsContainer.querySelectorAll('.tab')]
-            .find(tab => tab.getAttribute('data-special') === 'room-overview'
-                && tab.getAttribute('data-related-room') === roomName);
+        existingId = Object.keys(state.tabsById).find(id => {
+            const t = state.tabsById[id];
+            return t && t.type === 'room-overview' && t.metadata && t.metadata.
relatedRoom === roomName;
+        });
+    } else {
+        existingId = Object.keys(state.tabsById).find(id => {
+            const t = state.tabsById[id];
+            return t && t.type === 'room-overview' && !(t.metadata && t.metadat
a.relatedRoom);
+        });
     }
-    
-    if (existing) {
-        activateTab(existing);
-        return;
+
+    if (existingId) {
+        const existing = document.querySelector(`#tabs .tab[data-tab-id="${exis
tingId}"]`);
+        if (existing) { activateTab(existing); return; }
     }
@@ -203,13 +276,13 @@ export function openOverviewTab(roomName = null) {
 export function openApplicationsTab() {
     const tabsContainer = document.getElementById('tabs');
     if (!tabsContainer) return;
-
-    let existing = [...tabsContainer.querySelectorAll('.tab')]
-        .find(tab => tab.getAttribute('data-special') === 'review-applications'
-);
-    
-    if (existing) {
-        activateTab(existing);
-        return;
+    const existingId = Object.keys(state.tabsById).find(id => {
+        const t = state.tabsById[id];
+        return t && t.type === 'review-applications';
+    });
+    if (existingId) {
+        const existing = document.querySelector(`#tabs .tab[data-tab-id="${exis
tingId}"]`);
+        if (existing) { activateTab(existing); return; }
     }
 
     const newTab = createTabElement('Applications', 'review-applications', {});
@@
diff --git a/app/db.sqlite3 b/app/db.sqlite3
index 081be52..d1b2307 100644
Binary files a/app/db.sqlite3 and b/app/db.sqlite3 differ

(Projects/WebDev/messenger) 
yourbrolol $

<!-- end raw git diff -->
```


---

## Per-file explanations (each change I made)

> Note: all edits below were made to move ad-hoc DOM tab manipulation toward a small, centralized tab API and registry so future changes are safer and easier to reason about.

### 1) `app/chat/static/chat/js/state.js`

- Added a `tabsById` registry to `state` to hold structured tab metadata keyed by an internal `data-tab-id`.

Why: previously tab identity and metadata were only in DOM attributes. The registry provides a single source of truth for per-tab data (title, type, metadata), enabling safer updates and lookups.

Patch (excerpt):

```diff
 export const state = {
     currentRoom: null,
-    chatSocket: null
+    chatSocket: null,
+    // Registry for tab metadata keyed by internal tab id
+    tabsById: {}
 };
```


### 2) `app/chat/static/chat/js/tabs.js`

I made several focused changes in `tabs.js`:

- generate and attach a `data-tab-id` to every new tab element in `createTabElement`;
- store a structured object for each tab in `state.tabsById` (id, title, type, metadata);
- when creating `room` tabs, copy the room name into `metadata.room` to provide a canonical identifier;
- add helper APIs: `getTabElementById`, `updateTabTitle`, `setTabMetadata`, `getTabMetadata` for all future tab edits;
- change existing DOM-based searches to registry-first lookups (for openChatTab, openOverviewTab, openApplicationsTab);
- update `activateTab` to consult the registry for the tab's type and metadata (instead of reading `data-special`/`data-room` directly) and to read `relatedRoom` from the registry metadata;
- clean registry entry on tab close.

Why: these changes replace brittle string comparisons across the codebase and consolidate tab state editing to stable helper functions.

Key patch excerpts (high level):

- Creation and registry:
```diff
+    const tabId = `t-${Date.now().toString(36)}-${Math.floor(Math.random()*10000).toString(36)}`;
+    tabDiv.setAttribute('data-tab-id', tabId);
+    // metaCopy ensures room field is available
+    metaCopy.room = titleText; // for room tabs
+    state.tabsById[tabId] = { id: tabId, title: String(titleText), type: typeAttr, metadata: metaCopy };
```

- Helper API additions:
```js
export function getTabElementById(tabId) { ... }
export function updateTabTitle(tabId, newTitle) { ... }
export function setTabMetadata(tabId, metadata) { ... }
export function getTabMetadata(tabId) { ... }
```

- Registry-based lookups (example):
```diff
-    const existingTab = [...tabsContainer.querySelectorAll('.tab')].find(tab => tab.getAttribute('data-room') === joinResult.name);
+    const existingId = Object.keys(state.tabsById).find(id => { const t = state.tabsById[id]; return t && t.type === 'room' && ((t.metadata && t.metadata.room === joinResult.name) || t.title === joinResult.name); });
```

- Use registry metadata in `activateTab` for overview related-room:
```diff
-    const related = tabElement.getAttribute('data-related-room');
+    const related = tabInfo?.metadata?.relatedRoom || null;
```

- Remove registry entry on `closeTab`.


### 3) `app/chat/static/chat/js/init.js`

- Replaced direct checks and mutation of `data-special`/title on the active tab in `bindGroupCreation` with registry-based checks and helper calls.

Before: code directly called `activeTab.setAttribute('data-special', 'room-creation')` and updated the `.tab-title` textContent.

After: obtain `tabId` from active element, verify the registry entry's `type`, then call `setTabMetadata(tabId, { special: 'room-creation' })` and `updateTabTitle(tabId, 'Create Room')`, and activate via `getTabElementById(tabId)`.

Also imported `state` and consolidated `tabs` imports.

Why: this makes the active-tab transition use the same API surface as the rest of edits.

Patch excerpt (concept):

```diff
-        if (activeTab && activeTab.getAttribute('data-special') === 'new-tab') {
-            activeTab.setAttribute('data-special', 'room-creation');
-            const titleSpan = activeTab.querySelector('.tab-title');
-            if (titleSpan) titleSpan.textContent = 'Create Room';
-            activateTab(activeTab);
+        const tabId = activeTab?.getAttribute('data-tab-id');
+        if (tabId) {
+            const t = state.tabsById[tabId];
+            if (t && t.type === 'new-tab') {
+                setTabMetadata(tabId, { special: 'room-creation' });
+                updateTabTitle(tabId, 'Create Room');
+                const el = getTabElementById(tabId);
+                if (el) activateTab(el);
+            }
+        }
```


### 4) `app/chat/static/chat/js/room.js`

- Replaced DOM scans that removed/closed temporary `room-creation` tabs with registry-driven cleanup.
- Imported `state` and `getTabElementById`.

Before: `tabsContainer.querySelectorAll('.tab').forEach(tab => if (tab.getAttribute('data-special') === 'room-creation') tab.remove())`.
After: iterate `Object.keys(state.tabsById)`, find entries where `t.type === 'room-creation'`, remove the element via `getTabElementById(id)`, and delete the registry entry.

Why: ensures we only remove tabs we created and cleans the central state consistently.


### 5) `app/db.sqlite3`

- The diff shows the SQLite DB file is changed (binary). I did not intentionally modify the database; it likely changed as a side-effect of running the app or tests. I included the raw diff header above for completeness.


---

## Overall tab system mechanics (design & how to use the new API)

This section summarizes the tab model and how code should interact with tabs going forward.

- Tab identity
  - Each tab now has an internal immutable identifier `data-tab-id` generated on creation (string like `t-...`). Use this id as the stable handle for all programmatic operations.

- Central registry (`state.tabsById`)
  - Shape: `{ [tabId]: { id, title, type, metadata } }`
  - `title`: display title
  - `type`: a small string describing role, e.g. `room`, `new-tab`, `room-creation`, `room-overview`, `review-applications`
  - `metadata`: freeform key/value bag for additional fields, e.g. `room` (canonical room name), `relatedRoom` (overview target)

- DOM surface
  - Tabs still exist as DOM elements with class `.tab`. They also include `data-tab-id` and mirrored `data-*` attributes for simple observation and initial CSS/markup.
  - Prefer using API helpers rather than manually setting attributes/text.

- Public helper API (in `tabs.js`)
  - `getTabElementById(tabId)` → DOM element or `null`.
  - `updateTabTitle(tabId, newTitle)` → updates DOM and registry title.
  - `setTabMetadata(tabId, metadata)` → updates DOM attributes and registry metadata; keeps `type` in sync when `special`/`type` is provided.
  - `getTabMetadata(tabId)` → returns metadata object from registry.
  - `openChatTab(roomName)`, `openOverviewTab(roomName)`, `openApplicationsTab()` → these functions now prefer registry lookups to avoid duplicates.

- Lifecycle
  - Creation: `createTabElement(title, type, metadata)` attached a `data-tab-id` and registers the tab object in `state.tabsById`.
  - Closing: `closeTab(el)` removes the DOM element and deletes the registry entry.

- Migration guidance (what to change in other modules)
  - Replace any direct `element.getAttribute('data-...')` or `element.setAttribute(...)` usages with registry helper functions when performing programmatic updates.
  - When searching for existing tabs, prefer `Object.keys(state.tabsById).find(...)` using the registry fields (e.g. `.type === 'room'` and `.metadata.room === name`) instead of scanning DOM attributes.
  - Use `updateTabTitle` and `setTabMetadata` for any title/metadata changes so UI and registry stay consistent.