async function sendMessage(){

    let input = document.getElementById("userInput")

    let message = input.value

    if(message.trim() === ""){
        return
    }

    let chatBox = document.getElementById("chat-box")

    chatBox.innerHTML += `
        <div class="user-msg">
            <b>You:</b><br>${message}
        </div>
    `

    input.value = ""

    chatBox.innerHTML += `
        <div class="ai-msg" id="typing">
            AI is typing...
        </div>
    `

    chatBox.scrollTop = chatBox.scrollHeight

    let response = await fetch("/chat", {

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body: JSON.stringify({
            message: message
        })

    })

    let data = await response.json()

    document.getElementById("typing").remove()

    chatBox.innerHTML += `
        <div class="ai-msg">
            <b>AI Tutor:</b><br>${data.reply}
        </div>
    `

    chatBox.scrollTop = chatBox.scrollHeight
}