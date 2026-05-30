Solution 3: Hybrid Approach (My suggestion) ⭐⭐⭐⭐⭐ BEST LONG-TERM
Combine cloning + state management strategically:

Clone the view containers (use Solution 1)
But share expensive resources – e.g., keep WebSocket data in a shared store, not per-DOM instance
Use a state store pattern – Central registry that maps tabId → {viewData, websocket, formState, ...}
Benefits:

Memory-efficient for heavy data (shared room cache, WebSocket pool)
Clean DOM management (cloned containers)
Scales to 100+ tabs without issues
Clear separation of concerns