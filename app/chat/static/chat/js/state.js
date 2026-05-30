export const state = {
    currentRoom: null,
    chatSocket: null,
    username: null,
    // Registry for tab metadata keyed by internal tab id
    // tabsById entry shape:
    // {
    //   id, title, type, metadata,
    //   contentNode: HTMLElement | null,   // detached DOM subtree; null until first activation
    //   dirty: boolean,                    // true = re-fetch/re-render on next activation
    // }
    tabsById: {}
};

