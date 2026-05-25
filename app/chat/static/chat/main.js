// Initial Check
console.log("JS loaded!")

// Rooms
let currentRoom = null;

// UI
const input = document.getElementById('chat-message-input');
const chatLog = document.getElementById('chat-log');

// Connection
let chatSocket = null;

function appendMessage(data) {
    console.log("Appending to DOM:", data);
    const div = document.createElement('div');
    div.className = "message";

    div.textContent = `${data.user}: ${data.content}`;

    chatLog.appendChild(div);

    chatLog.scrollTop = chatLog.scrollHeight;
}

function createChatSocket(room) {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(protocol + '://' + window.location.host + '/ws/chat/' + room + '/');

    socket.onmessage = async function (e) {
        let text;
        if (e.data instanceof Blob) {
            text = await e.data.text();
        } else {
            text = e.data;
        }

        let data;
        try { data = JSON.parse(text); } catch (err) {
            console.error("Not JSON:", text);
            return;
        }

        console.log(data.user, data.message)

        if (data.type === "init") {
            console.log("Clearing DOM");
            chatLog.innerHTML = '';
            data.message_history.forEach(appendMessage);
            console.log("Appended history:", data.message_history);
        } else if (data.type === "chat_message") {
            console.log(data)
            appendMessage({"user": data.user, "content": data.content});
            console.log("Recieved data!");
        }
    };

    socket.onclose = function() {
        console.log("Socket closed for room:", room);
    };

    return socket;
}

function reconnectChatSocket(arg) {
    if (chatSocket) {
        chatSocket.close();
    }
    console.log(arg)
    chatSocket = createChatSocket(currentRoom)
}

function sendMessage() {
    if (!chatSocket) {
        console.log("No websocket connected yet.");
        return;
    }

    const input = document.getElementById('chat-message-input');
    if(input.value === "") {
        console.log("Empty message revieved!")
        return;
    }
    chatSocket.send(JSON.stringify({
        'type': 'chat_message',
        'message': input.value
    }));
    console.log("Sent a message!")
    input.value = '';
}

function loadRooms() {
    const roomsDiv = document.getElementById('chats');
    if (!roomsDiv) return;
    
    // Clear everything except the header
    const header = document.getElementById('chats-text');
    roomsDiv.innerHTML = '';
    if (header) {
        roomsDiv.appendChild(header);
    } else {
        const chatsText = document.createElement('div');
        chatsText.id = 'chats-text';
        chatsText.className = 'chats-text';
        chatsText.textContent = 'Chats';
        roomsDiv.appendChild(chatsText);
    }
    
    fetch("/rooms/")
        .then(r => r.json())
        .then(rooms => {
            rooms.forEach(r => {
                const btn = document.createElement('div');
                btn.className = "room";
                btn.textContent = r.name;
                roomsDiv.appendChild(btn);
                btn.addEventListener('pointerup', function() {
                    openChatTab(r.name);
                });
            });
        })
}

// View switching logic
function switchView(viewName) {
    const chatView = document.getElementById('chat');
    const placeholderView = document.getElementById('chat-placeholder');
    const groupCreationView = document.getElementById('group-creation-view');
    const newTabView = document.getElementById('new-tab-view');
    
    chatView.classList.add('hidden');
    placeholderView.classList.add('hidden');
    if (groupCreationView) groupCreationView.classList.add('hidden');
    if (newTabView) newTabView.classList.add('hidden');
    
    if (viewName === 'chat') {
        chatView.classList.remove('hidden');
    } else if (viewName === 'placeholder') {
        placeholderView.classList.remove('hidden');
    } else if (viewName === 'group-creation') {
        if (groupCreationView) groupCreationView.classList.remove('hidden');
    } else if (viewName === 'new-tab') {
        if (newTabView) newTabView.classList.remove('hidden');
    }
}

// Tab Management
function openChatTab(roomName) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;
    
    // Check if tab already exists
    let existingTab = null;
    const tabs = tabsContainer.querySelectorAll('.tab');
    tabs.forEach(tab => {
        if (tab.getAttribute('data-room') === roomName) {
            existingTab = tab;
        }
    });
    
    if (existingTab) {
        activateTab(existingTab);
    } else {
        const newTab = document.createElement('div');
        newTab.className = 'tab';
        newTab.setAttribute('role', 'tab');
        newTab.setAttribute('aria-selected', 'false');
        newTab.setAttribute('data-room', roomName);
        
        const title = document.createElement('span');
        title.className = 'tab-title';
        title.textContent = roomName;
        
        const closeBtn = document.createElement('span');
        closeBtn.className = 'tab-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            closeTab(newTab);
        });
        
        newTab.appendChild(title);
        newTab.appendChild(closeBtn);
        tabsContainer.appendChild(newTab);
        
        activateTab(newTab);
        newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
    }
}

function openNewTab() {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;
    
    const newTab = document.createElement('div');
    newTab.className = 'tab';
    newTab.setAttribute('role', 'tab');
    newTab.setAttribute('aria-selected', 'false');
    newTab.setAttribute('data-special', 'new-tab');
    
    const title = document.createElement('span');
    title.className = 'tab-title';
    title.textContent = 'New Tab';
    
    const closeBtn = document.createElement('span');
    closeBtn.className = 'tab-close';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        closeTab(newTab);
    });
    
    newTab.appendChild(title);
    newTab.appendChild(closeBtn);
    tabsContainer.appendChild(newTab);
    
    activateTab(newTab);
    newTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'end' });
}

function activateTab(tabElement) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;
    
    const tabs = tabsContainer.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
    });
    
    tabElement.classList.add('active');
    tabElement.setAttribute('aria-selected', 'true');
    
    const room = tabElement.getAttribute('data-room');
    const isGroupCreation = tabElement.getAttribute('data-special') === 'group-creation';
    const isNewTab = tabElement.getAttribute('data-special') === 'new-tab';
    
    if (isNewTab) {
        currentRoom = null;
        if (chatSocket) {
            chatSocket.close();
            chatSocket = null;
        }
        switchView('new-tab');
    } else if (isGroupCreation) {
        currentRoom = null;
        if (chatSocket) {
            chatSocket.close();
            chatSocket = null;
        }
        switchView('group-creation');
    } else if (room) {
        currentRoom = room;
        switchView('chat');
        
        if (chatSocket) {
            chatSocket.close();
        }
        chatSocket = createChatSocket(currentRoom);
    }
}

function closeTab(tabElement) {
    const tabsContainer = document.getElementById('tabs');
    if (!tabsContainer) return;
    
    const isActive = tabElement.classList.contains('active');
    tabElement.remove();
    
    if (isActive) {
        const remainingTabs = tabsContainer.querySelectorAll('.tab');
        if (remainingTabs.length > 0) {
            activateTab(remainingTabs[remainingTabs.length - 1]);
        } else {
            currentRoom = null;
            if (chatSocket) {
                chatSocket.close();
                chatSocket = null;
            }
            switchView('placeholder');
        }
    }
}

// Event Listeners
if (input) {
    input.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            sendMessage()
        }
    });
}

const submitBtn = document.getElementById('chat-message-submit');
if (submitBtn) {
    submitBtn.onclick = function() {
        sendMessage()
    }
}

// Add tab button (opens an empty New Tab dashboard)
const addTabBtn = document.getElementById('add-tab-btn');
if (addTabBtn) {
    addTabBtn.addEventListener('click', function() {
        openNewTab();
    });
}

// Dashboard "Create Group" action handler
const dashboardCreateGroupBtn = document.getElementById('dashboard-create-group-btn');
if (dashboardCreateGroupBtn) {
    dashboardCreateGroupBtn.addEventListener('click', function() {
        // Find the currently active tab
        const activeTab = document.querySelector('#tabs .tab.active');
        if (activeTab && activeTab.getAttribute('data-special') === 'new-tab') {
            // Update this tab's state/special type
            activeTab.setAttribute('data-special', 'group-creation');
            
            // Update the tab title to "Create Group"
            const titleSpan = activeTab.querySelector('.tab-title');
            if (titleSpan) {
                titleSpan.textContent = 'Create Group';
            }
            
            // Activate the updated tab to transition views
            activateTab(activeTab);
        }
    });
}

// Tab Switching logic (Event delegation for existing and dynamic tabs)
const tabsContainer = document.getElementById('tabs');
if (tabsContainer) {
    tabsContainer.addEventListener('click', function(e) {
        const clickedTab = e.target.closest('.tab');
        if (!clickedTab) return;
        activateTab(clickedTab);
    });
}

// Group creation form submit handler
const groupCreationForm = document.getElementById('group-creation-form');
if (groupCreationForm) {
    groupCreationForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const roomNameInput = document.getElementById('id_room_name');
        const roomTypeSelect = document.getElementById('id_room_type');
        const errorsDiv = document.getElementById('group-creation-errors');
        
        if (!roomNameInput || !roomTypeSelect) return;
        
        const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';
        
        const formData = new URLSearchParams();
        formData.append('csrfmiddlewaretoken', csrfToken);
        formData.append('room_name', roomNameInput.value);
        formData.append('room_type', roomTypeSelect.value);
        
        try {
            const response = await fetch('/rooms/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });
            
            // Since Django redirects on success or returns status 200 with the form on error,
            // we check if the response URL redirected away from '/rooms/create' to indicate success.
            const isSuccess = response.redirected || !response.url.endsWith('/rooms/create');
            
            if (response.ok && isSuccess) {
                const newRoomName = roomNameInput.value.trim();
                
                // Clear any form inputs and errors
                roomNameInput.value = '';
                if (errorsDiv) {
                    errorsDiv.classList.add('hidden');
                    errorsDiv.textContent = '';
                }
                
                // Reload rooms list in sidebar
                loadRooms();
                
                // Close the Group Creation tab
                const tabsContainer = document.getElementById('tabs');
                if (tabsContainer) {
                    const tabs = tabsContainer.querySelectorAll('.tab');
                    tabs.forEach(tab => {
                        if (tab.getAttribute('data-special') === 'group-creation') {
                            tab.remove();
                        }
                    });
                }
                
                // Open the new room as active tab
                setTimeout(() => {
                    openChatTab(newRoomName);
                }, 100);
            } else {
                if (errorsDiv) {
                    errorsDiv.textContent = "An error occurred. Make sure the room name is unique, between 1-20 characters, and contains no special characters.";
                    errorsDiv.classList.remove('hidden');
                }
            }
        } catch (err) {
            console.error(err);
            if (errorsDiv) {
                errorsDiv.textContent = "Network error. Please try again.";
                errorsDiv.classList.remove('hidden');
            }
        }
    });
}

// Cancel group creation button handler
const cancelGroupBtn = document.getElementById('cancel-group-btn');
if (cancelGroupBtn) {
    cancelGroupBtn.addEventListener('click', function() {
        const tabsContainer = document.getElementById('tabs');
        if (tabsContainer) {
            const tabs = tabsContainer.querySelectorAll('.tab');
            tabs.forEach(tab => {
                if (tab.getAttribute('data-special') === 'group-creation') {
                    closeTab(tab);
                }
            });
        }
    });
}

// Initialize rooms list
loadRooms();