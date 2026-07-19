const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const messagesDiv = document.getElementById('messages');
const languageSelect = document.getElementById('language');
const welcomeMessage = document.querySelector('.welcome-message');

function addMessage(text, isUser = false) {
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    msgDiv.classList.add(isUser ? 'user-message' : 'bot-message');
    
    if (isUser) {
        msgDiv.textContent = text;
    } else {
        msgDiv.innerHTML = marked.parse(text);
    }
    
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return msgDiv;
}

function sendQuickMessage(text) {
    userInput.value = text;
    chatForm.dispatchEvent(new Event('submit'));
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;
    
    addMessage(text, true);
    userInput.value = '';
    const lang = languageSelect.value;
    
    const botMsgDiv = addMessage('...', false);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, language: lang })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let fullText = "";
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6);
                    if (dataStr === '[DONE]') {
                        break;
                    }
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.text) {
                            // adk run_async usually emits diffs or full text, we'll just append it for now.
                            // If it emits full text on each step, this might duplicate, but we'll try to just accumulate.
                            // The stream from server.py is str(event).
                            fullText += data.text;
                            botMsgDiv.innerHTML = marked.parse(fullText);
                            messagesDiv.scrollTop = messagesDiv.scrollHeight;
                        } else if (data.error) {
                            fullText += "\n\n**Error:** " + data.error;
                            botMsgDiv.innerHTML = marked.parse(fullText);
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        botMsgDiv.innerHTML = "An error occurred connecting to the server.";
    }
});
