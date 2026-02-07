/**
 * IC-UFMT Smart Agent - Frontend Application
 * 
 * Features:
 * - SSE streaming for real-time responses
 * - Markdown rendering
 * - Conversation history
 * - Auto-resize textarea
 */

const API_BASE_URL = 'http://localhost:8000';

// State
let conversationHistory = [];
let isStreaming = false;

// DOM Elements
const welcomeScreen = document.getElementById('welcome-screen');
const messagesContainer = document.getElementById('messages-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const refreshDocsBtn = document.getElementById('refresh-docs-btn');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.querySelector('.sidebar');
const connectionStatus = document.getElementById('connection-status');
const suggestionBtns = document.querySelectorAll('.suggestion-btn');

// Provider info elements
const llmProviderEl = document.getElementById('llm-provider');
const llmModelEl = document.getElementById('llm-model');
const docCountEl = document.getElementById('doc-count');

// Configure marked for markdown
marked.setOptions({
    breaks: true,
    gfm: true,
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkConnection();
    setupEventListeners();
    autoResizeTextarea();
});

// Setup event listeners
function setupEventListeners() {
    // Send message
    sendBtn.addEventListener('click', sendMessage);
    
    // Enter to send, Shift+Enter for new line
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Enable/disable send button based on input
    messageInput.addEventListener('input', () => {
        sendBtn.disabled = !messageInput.value.trim() || isStreaming;
        autoResizeTextarea();
    });
    
    // New chat
    newChatBtn.addEventListener('click', () => {
        startNewChat();
    });
    
    // Refresh documents
    refreshDocsBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        await refreshDocuments();
    });
    
    // Sidebar toggle (mobile)
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('visible');
    });
    
    // Suggestion buttons
    suggestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.dataset.question;
            messageInput.value = question;
            sendMessage();
        });
    });
}

// Auto-resize textarea
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 200) + 'px';
}

// Check API connection
async function checkConnection() {
    const statusText = connectionStatus.querySelector('.status-text');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        const data = await response.json();
        
        if (response.ok) {
            connectionStatus.className = 'connection-status connected';
            statusText.textContent = 'Conectado';
            
            // Update provider info
            if (data.provider) {
                llmProviderEl.textContent = capitalizeFirst(data.provider.llm_provider);
                llmModelEl.textContent = data.provider.llm_model;
                docCountEl.textContent = `${data.provider.document_count} chunks`;
            }
        } else {
            throw new Error('API unhealthy');
        }
    } catch (error) {
        connectionStatus.className = 'connection-status error';
        statusText.textContent = 'Desconectado';
        llmProviderEl.textContent = 'Erro';
        llmModelEl.textContent = '-';
        docCountEl.textContent = '-';
        
        // Retry in 5 seconds
        setTimeout(checkConnection, 5000);
    }
}

// Start new chat
function startNewChat() {
    conversationHistory = [];
    messagesContainer.innerHTML = '';
    welcomeScreen.classList.remove('hidden');
    messageInput.value = '';
    messageInput.focus();
    sidebar.classList.remove('visible');
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    
    if (!message || isStreaming) return;
    
    // Hide welcome screen
    welcomeScreen.classList.add('hidden');
    
    // Add user message
    addMessage('user', message);
    conversationHistory.push({ role: 'user', content: message });
    
    // Clear input
    messageInput.value = '';
    autoResizeTextarea();
    sendBtn.disabled = true;
    isStreaming = true;
    
    // Create assistant message placeholder
    const assistantMessage = createMessageElement('assistant', '');
    messagesContainer.appendChild(assistantMessage);
    
    const contentEl = assistantMessage.querySelector('.message-content');
    const sourcesEl = assistantMessage.querySelector('.message-sources');
    
    // Add typing indicator
    contentEl.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    
    scrollToBottom();
    
    try {
        // Use streaming endpoint
        await streamResponse(message, contentEl, sourcesEl);
    } catch (error) {
        console.error('Error:', error);
        contentEl.innerHTML = `<div class="error-content">Erro ao conectar com o servidor. Verifique se o backend esta rodando.</div>`;
    }
    
    isStreaming = false;
    sendBtn.disabled = !messageInput.value.trim();
    messageInput.focus();
}

// Stream response using SSE
async function streamResponse(message, contentEl, sourcesEl) {
    return new Promise((resolve, reject) => {
        let fullResponse = '';
        let sources = [];
        
        // Prepare request body
        const body = JSON.stringify({
            message: message,
            conversation_history: conversationHistory.slice(-10), // Last 10 messages
        });
        
        // Create EventSource with POST (using fetch + ReadableStream)
        fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: body,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            function processStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        // Save to history
                        if (fullResponse) {
                            conversationHistory.push({ role: 'assistant', content: fullResponse });
                        }
                        resolve();
                        return;
                    }
                    
                    buffer += decoder.decode(value, { stream: true });
                    
                    // Process SSE events
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (line.startsWith('event: ')) {
                            const eventType = line.substring(7);
                            continue;
                        }
                        
                        if (line.startsWith('data: ')) {
                            const data = line.substring(6);
                            
                            // Determine event type from previous line or data content
                            try {
                                // Check if it's sources (JSON array)
                                const parsed = JSON.parse(data);
                                if (Array.isArray(parsed)) {
                                    sources = parsed;
                                    if (sources.length > 0) {
                                        sourcesEl.innerHTML = `<strong>Fontes:</strong> ${sources.join(', ')}`;
                                        sourcesEl.style.display = 'block';
                                    }
                                }
                            } catch {
                                // It's a token
                                if (data && data !== '[DONE]') {
                                    fullResponse += data;
                                    // Render markdown
                                    contentEl.innerHTML = marked.parse(fullResponse);
                                    scrollToBottom();
                                }
                            }
                        }
                    }
                    
                    processStream();
                }).catch(reject);
            }
            
            processStream();
        })
        .catch(error => {
            // Fallback to non-streaming endpoint
            console.warn('Streaming failed, falling back to sync:', error);
            fallbackToSync(message, contentEl, sourcesEl)
                .then(resolve)
                .catch(reject);
        });
    });
}

// Fallback to synchronous endpoint
async function fallbackToSync(message, contentEl, sourcesEl) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            conversation_history: conversationHistory.slice(-10),
        }),
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }
    
    const data = await response.json();
    
    // Render response
    contentEl.innerHTML = marked.parse(data.response);
    
    // Show sources
    if (data.sources && data.sources.length > 0) {
        sourcesEl.innerHTML = `<strong>Fontes:</strong> ${data.sources.join(', ')}`;
        sourcesEl.style.display = 'block';
    }
    
    // Save to history
    conversationHistory.push({ role: 'assistant', content: data.response });
    
    scrollToBottom();
}

// Add message to chat
function addMessage(role, content) {
    const messageEl = createMessageElement(role, content);
    messagesContainer.appendChild(messageEl);
    scrollToBottom();
}

// Create message element
function createMessageElement(role, content) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    
    const avatar = role === 'user' ? 'U' : 'IC';
    const roleName = role === 'user' ? 'Voce' : 'IC-UFMT';
    
    messageEl.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">${avatar}</div>
            <div class="message-role">${roleName}</div>
        </div>
        <div class="message-content">${role === 'user' ? escapeHtml(content) : marked.parse(content)}</div>
        <div class="message-sources" style="display: none;"></div>
    `;
    
    return messageEl;
}

// Refresh documents
async function refreshDocuments() {
    refreshDocsBtn.innerHTML = `
        <svg class="spinning" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
        </svg>
        Atualizando...
    `;
    
    try {
        const response = await fetch(`${API_BASE_URL}/documents/refresh`, {
            method: 'POST',
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`Documentos atualizados! ${data.chunks_count} chunks processados.`);
            checkConnection(); // Refresh info
        } else {
            alert(`Erro: ${data.detail}`);
        }
    } catch (error) {
        alert('Erro ao atualizar documentos. Verifique o console.');
        console.error(error);
    }
    
    refreshDocsBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
        </svg>
        Atualizar Documentos
    `;
}

// Scroll to bottom of chat
function scrollToBottom() {
    const chatArea = document.getElementById('chat-area');
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility: Capitalize first letter
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Add spinning animation style
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .spinning {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);
