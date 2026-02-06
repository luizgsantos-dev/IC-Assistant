// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');
const loadingIndicator = document.getElementById('loading-indicator');
const connectionStatus = document.getElementById('connection-status');
const providerInfo = document.getElementById('provider-info');
const providerName = document.getElementById('provider-name');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    messageInput.focus();
    
    // Check API connection
    checkConnection();
    
    // Send message on Enter key
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Send message on button click
    sendButton.addEventListener('click', sendMessage);
});

// Check API connection and get provider info
async function checkConnection() {
    const statusText = connectionStatus.querySelector('.status-text');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        
        if (response.ok) {
            connectionStatus.classList.remove('disconnected');
            connectionStatus.classList.add('connected');
            statusText.textContent = 'Conectado';
            
            // Try to get provider info (if endpoint exists)
            // For now, just show connected status
            providerInfo.style.display = 'flex';
            providerName.textContent = 'Ativo';
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        connectionStatus.classList.remove('connected');
        connectionStatus.classList.add('disconnected');
        statusText.textContent = 'Desconectado';
        providerInfo.style.display = 'none';
        
        // Retry connection after 5 seconds
        setTimeout(checkConnection, 5000);
    }
}

// Add message to chat
function addMessage(content, role, sources = null) {
    // Remove welcome message if it's the first user message
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage && role === 'user') {
        welcomeMessage.style.display = 'none';
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format content with line breaks
    contentDiv.innerHTML = formatMessage(content);
    
    messageDiv.appendChild(contentDiv);
    
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        sourcesDiv.innerHTML = `<strong>Fontes:</strong> ${sources.join(', ')}`;
        messageDiv.appendChild(sourcesDiv);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message content
function formatMessage(content) {
    // Convert line breaks to <br>
    let formatted = content.replace(/\n/g, '<br>');
    
    // Bold text between ** **
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text between * *
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    return formatted;
}

// Add error message
function addErrorMessage(error) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content error-message';
    contentDiv.innerHTML = `<strong>Erro:</strong> ${error}`;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send message to API
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    messageInput.value = '';
    
    // Disable input and show loading
    messageInput.disabled = true;
    sendButton.disabled = true;
    loadingIndicator.style.display = 'flex';
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_history: null
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Erro ao processar mensagem');
        }
        
        const data = await response.json();
        
        // Add assistant response to chat
        addMessage(data.response, 'assistant', data.sources);
        
    } catch (error) {
        console.error('Error:', error);
        
        let errorMessage = 'Erro ao conectar com o servidor.';
        
        if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Nao foi possivel conectar ao servidor. Verifique se o backend esta rodando em ' + API_BASE_URL;
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        addErrorMessage(errorMessage);
        
        // Update connection status
        checkConnection();
    } finally {
        // Re-enable input and hide loading
        messageInput.disabled = false;
        sendButton.disabled = false;
        loadingIndicator.style.display = 'none';
        messageInput.focus();
    }
}
