console.log("JS loaded!")
const roomName = "general";
// const chatSocket = new WebSocket(
//     'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
// )
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/general/'
);

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOMContentLoaded");
});

function appendMessage(message) {
    console.log("Appending to DOM:", message);
    const log = document.getElementById('chat-log');
    const li = document.createElement('li');
    li.className = "message";
    li.textContent = message;
    log.appendChild(li);
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

document.getElementById('chat-message-submit').onclick = function() {
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