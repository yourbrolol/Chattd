console.log("JS loaded!")
const roomName = "general";
const input = document.getElementById('chat-message-input');
// const chatSocket = new WebSocket(
//     'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
// )
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/general/'
);

function appendMessage(message) {
    console.log("Appending to DOM:", message);
    const log = document.getElementById('chat-log');
    const div = document.createElement('div');
    div.className = "message";
    div.textContent = message;
    log.appendChild(div);
}

function sendMessage() {
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

chatSocket.onmessage = async function (e) {
    let text;

    if (e.data instanceof Blob) {
        text = await e.data.text();
    } else {
        text = e.data;
    }

    let data;
    try {
        data = JSON.parse(text);
    } catch (err) {
        console.error("Not JSON:", text);
        return;
    }

    if (data.type === "init") {
        data.message_history.forEach(appendMessage);
        console.log("Appended history:", data.message_history);
    } else if (data.type === "chat_message") {
        appendMessage(data.message);
    }
};

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOMContentLoaded");
});

input.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        sendMessage()
    }
});

document.getElementById('chat-message-submit').onclick = function() {
    sendMessage()
}