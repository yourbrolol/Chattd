console.log("JS loaded!")
const roomName = "general";
// const chatSocket = new WebSocket(
//     'ws://' + window.location.host + '/ws/chat/' + roomName + '/'
// )
const chatSocket = new WebSocket(
    'ws://' + window.location.host + '/ws/chat/general/'
);

chatSocket.onmessage = function(e) {
    console.log("Recieved data!")
    const data = JSON.parse(e.data);
    if(data.type === 'init') {
        console.log("Initial message history received!")
        const messageHistory = data.message_history;
        const log = document.getElementById('chat-log');
        messageHistory.forEach(message => {
            const li = document.createElement('li');
            li.id = "message"
            li.textContent = message;
            log.appendChild(li);
        });
    }
    else if(data.type === 'chat_message') {
        console.log("Chat message received!")
        const message = data.message;
        const log = document.getElementById('chat-log');
        const li = document.createElement('li');
        li.id = "message"
        li.textContent = message;
        log.appendChild(li);
    }
}

document.getElementById('chat-message-submit').onclick = function() {
    const input = document.getElementById('chat-message-input');
    if(input.value === "") {
        console.log("Empty message revieved!")
        return;
    }
    chatSocket.send(JSON.stringify({'message': input.value}));
    console.log("Sent a message!")
    input.value = '';
}