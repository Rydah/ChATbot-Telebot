document.addEventListener("DOMContentLoaded", function() {
    const sendButton = document.querySelector(".send-button")
    const messageInput = document.querySelector(".message-box")
    const chatBox = document.querySelector(".chat-box")

    // click send button to send message
    sendButton.addEventListener("click", function() {
        const message = messageInput.value;
        sendMessage(message)
        messageInput.value = ""
        messageInput.focus() // after sending, text cursor stays on messageBox
    })
    // or press enter when typing in message box
    messageInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            const message = messageInput.value;
            sendMessage(message)
            messageInput.value = ""
            messageInput.focus()
        } 
    })

    function updateChatLog() {
        fetch('/api/get-chat-log')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                chatBox.innerHTML = "" // reset chatbox to no messages
                data.chat_log.forEach(message => {
                    // if content as https, it is a image url from CatAPI
                    if (message.content.endsWith(".gif") || message.content.endsWith(".jpg") || message.content.endsWith(".png")) {
                        const container = document.createElement("div")
                        container.classList.add("chat-message")

                        const img = document.createElement("img")
                        img.src = message.content
                        img.classList.add("chat-image")

                        const p = document.createElement("p")
                        p.textContent = `assistant:`

                        container.appendChild(p)
                        container.appendChild(img);
                        chatBox.appendChild(container)
                    } else { // normal openAI chatbot
                        const p = document.createElement("p")
                        p.classList.add("chat-message")
                        p.textContent = `${message.role}: ${message.content}`
                        chatBox.appendChild(p)
                    }
                });
            })
            .catch(error => {
                console.error("Error", error);
            });
    }

    function sendMessage(message) { // send data over to python side
        fetch('/api/call-python', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        })
        .then(data => {
            updateChatLog() // update chat log to show new messages
        })
        .catch(error => {
            console.error("Error", error)
        })
    }

    updateChatLog()
})



