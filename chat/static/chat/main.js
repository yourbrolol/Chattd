console.log("JS loaded!")
const roomName = "general";
const input = document.getElementById('chat-message-input');
const chatLog = document.getElementById('chat-log')
let currentRoom = "general"

let chatSocket = null

function clearDOM() {
    console.log("Clearing DOM");
    chatLog.innerHTML = '';
}

function appendMessage(data) {
    console.log("Appending to DOM:", data);
    const log = document.getElementById('chat-log');
    const div = document.createElement('div');
    div.className = "message";

    // data could be an object with {user, content} or a string
    if (typeof data === "object" && data.user && data.content) {
        div.textContent = `${data.user}: ${data.content}`;
    } else {
        div.textContent = data;  // fallback for plain strings
    }

    log.appendChild(div);

    log.scrollTop = log.scrollHeight;
}

function createChatSocket(room) {
    const socket = new WebSocket('ws://' + window.location.host + '/ws/chat/' + room + '/');

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
            clearDOM();
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
    chatSocket.close()
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

input.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        sendMessage()
    }
});

document.getElementById('chat-message-submit').onclick = function() {
    sendMessage()
}

function loadRooms() {
    const roomsDiv = document.getElementById('chats')
    fetch("/chat/rooms/")
        .then(r => r.json())
        .then(rooms => {
            rooms.forEach(r => {
                console.log(r.name);
                const btn = document.createElement('btn');
                btn.className = "room";
                btn.textContent = r.name;
                roomsDiv.appendChild(btn);
                btn.addEventListener('pointerup', function() {
                    currentRoom = btn.textContent;
                    reconnectChatSocket(currentRoom)
                });
            });
        })
}

chatSocket = createChatSocket(roomName);

loadRooms();