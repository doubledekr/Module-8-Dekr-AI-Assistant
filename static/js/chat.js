/**
 * Dekr AI Assistant Chat Interface
 * Handles all frontend chat functionality including messaging, UI updates, and API interactions
 */

class ChatInterface {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.messageForm = document.getElementById('messageForm');
        this.chatMessages = document.getElementById('chatMessages');
        this.sendButton = document.getElementById('sendButton');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.charCount = document.getElementById('charCount');
        this.messageCount = document.getElementById('messageCount');
        this.usageProgress = document.getElementById('usageProgress');
        this.userTierDisplay = document.getElementById('userTierDisplay');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.alertContainer = document.getElementById('alertContainer');
        this.recentTopics = document.getElementById('recentTopics');
        
        this.currentSessionId = null;
        this.userTier = 1;
        this.messagesUsedToday = 0;
        this.dailyLimit = 10;
        this.isProcessing = false;
        this.conversationHistory = [];
        
        this.initializeChat();
        this.setupEventListeners();
        this.updateUI();
    }

    /**
     * Initialize chat interface
     */
    initializeChat() {
        // Set up textarea auto-resize
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateCharCount();
        });

        // Load session data
        this.loadSessionData();
        
        // Check chat status
        this.checkChatStatus();
        
        // Auto-focus on input
        this.messageInput.focus();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Form submission
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Enter key handling
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-save input
        this.messageInput.addEventListener('input', () => {
            this.debounce(() => {
                localStorage.setItem('dekr_draft_message', this.messageInput.value);
            }, 500)();
        });

        // Load draft message
        const draftMessage = localStorage.getItem('dekr_draft_message');
        if (draftMessage) {
            this.messageInput.value = draftMessage;
            this.updateCharCount();
        }
    }

    /**
     * Auto-resize textarea based on content
     */
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    /**
     * Update character count display
     */
    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = count;
        
        // Update styling based on count
        if (count > 4500) {
            this.charCount.className = 'char-count danger';
        } else if (count > 4000) {
            this.charCount.className = 'char-count warning';
        } else {
            this.charCount.className = 'char-count';
        }
    }

    /**
     * Send message to AI assistant
     */
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isProcessing) {
            return;
        }

        // Check message length
        if (message.length > 5000) {
            this.showAlert('Message too long. Please keep it under 5000 characters.', 'warning');
            return;
        }

        this.isProcessing = true;
        this.updateSendButton(true);
        this.showLoadingIndicator(true);

        try {
            // Add user message to chat
            this.addMessage(message, 'user');
            
            // Clear input and draft
            this.messageInput.value = '';
            this.updateCharCount();
            this.autoResizeTextarea();
            localStorage.removeItem('dekr_draft_message');

            // Show typing indicator
            this.showTypingIndicator();

            // Send request to API
            const response = await axios.post('/api/v1/chat/message', {
                message: message
            });

            // Remove typing indicator
            this.hideTypingIndicator();

            if (response.data.error) {
                throw new Error(response.data.error);
            }

            // Add AI response to chat
            this.addMessage(response.data.response, 'ai', {
                responseTime: response.data.response_time_ms,
                intent: response.data.intent,
                contextUsed: response.data.context_used,
                cached: response.data.cached
            });

            // Update usage statistics
            this.updateUsageStats();

        } catch (error) {
            this.hideTypingIndicator();
            this.handleError(error);
        } finally {
            this.isProcessing = false;
            this.updateSendButton(false);
            this.showLoadingIndicator(false);
            this.messageInput.focus();
        }
    }

    /**
     * Add message to chat interface
     */
    addMessage(content, type, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message fade-in`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.innerHTML = this.formatMessage(content);

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.innerHTML = `<small class="text-muted">${this.formatTimestamp(new Date())}</small>`;

        // Add metadata for AI messages
        if (type === 'ai' && metadata.responseTime) {
            const metadataDiv = document.createElement('div');
            metadataDiv.className = 'message-metadata';
            metadataDiv.innerHTML = `
                <small class="text-muted">
                    ${metadata.responseTime}ms
                    ${metadata.cached ? ' • Cached' : ''}
                    ${metadata.intent ? ' • ' + metadata.intent : ''}
                </small>
            `;
            messageTime.appendChild(metadataDiv);
        }

        // Add message actions
        const actions = document.createElement('div');
        actions.className = 'message-actions';
        actions.innerHTML = `
            <button onclick="copyMessage(this)" title="Copy message">
                <i class="fas fa-copy"></i>
            </button>
            ${type === 'ai' ? `
                <button onclick="regenerateResponse(this)" title="Regenerate response">
                    <i class="fas fa-redo"></i>
                </button>
            ` : ''}
        `;

        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);
        messageContent.appendChild(actions);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Update conversation history
        this.conversationHistory.push({
            content: content,
            type: type,
            timestamp: new Date(),
            metadata: metadata
        });

        // Update recent topics
        this.updateRecentTopics();
    }

    /**
     * Format message content with proper HTML
     */
    formatMessage(content) {
        // Basic markdown-style formatting
        let formatted = content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');

        // Convert URLs to links
        formatted = formatted.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );

        // Convert numbered lists
        formatted = formatted.replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ol>$1</ol>');

        // Convert bullet lists
        formatted = formatted.replace(/^[•-]\s+(.+)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

        return formatted;
    }

    /**
     * Format timestamp for display
     */
    formatTimestamp(date) {
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;

        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    /**
     * Update send button state
     */
    updateSendButton(disabled) {
        this.sendButton.disabled = disabled;
        this.sendButton.innerHTML = disabled ? 
            '<i class="fas fa-spinner fa-spin"></i>' : 
            '<i class="fas fa-paper-plane"></i>';
    }

    /**
     * Show/hide loading indicator
     */
    showLoadingIndicator(show) {
        this.loadingIndicator.style.display = show ? 'block' : 'none';
    }

    /**
     * Handle API errors
     */
    handleError(error) {
        console.error('Chat error:', error);
        
        let errorMessage = 'An error occurred while processing your message.';
        
        if (error.response) {
            if (error.response.status === 429) {
                errorMessage = error.response.data.error || 'Rate limit exceeded. Please try again later.';
            } else if (error.response.status === 401) {
                errorMessage = 'Session expired. Please refresh the page.';
            } else if (error.response.data && error.response.data.error) {
                errorMessage = error.response.data.error;
            }
        } else if (error.message) {
            errorMessage = error.message;
        }

        this.showAlert(errorMessage, 'danger');
        
        // Add error message to chat
        this.addMessage(
            `I'm sorry, but I encountered an error: ${errorMessage}. Please try again.`,
            'ai'
        );
    }

    /**
     * Show alert message
     */
    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        this.alertContainer.appendChild(alertDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    /**
     * Load session data
     */
    loadSessionData() {
        // This would typically load from session storage or API
        // For now, we'll use defaults
        this.userTier = 1;
        this.messagesUsedToday = 0;
        this.dailyLimit = 10;
    }

    /**
     * Update UI elements
     */
    updateUI() {
        this.updateTierDisplay();
        this.updateUsageDisplay();
        this.updateStatusIndicator();
    }

    /**
     * Update tier display
     */
    updateTierDisplay() {
        const tierNames = {
            1: 'Freemium',
            2: 'Market Hours Pro',
            3: 'Premium',
            4: 'Premium Plus',
            5: 'Professional',
            6: 'Enterprise',
            7: 'Elite'
        };
        
        this.userTierDisplay.textContent = tierNames[this.userTier] || 'Unknown';
    }

    /**
     * Update usage display
     */
    updateUsageDisplay() {
        const limitText = this.dailyLimit === -1 ? '∞' : this.dailyLimit;
        this.messageCount.textContent = `${this.messagesUsedToday}/${limitText}`;
        
        const percentage = this.dailyLimit === -1 ? 0 : (this.messagesUsedToday / this.dailyLimit) * 100;
        this.usageProgress.style.width = `${Math.min(percentage, 100)}%`;
        
        // Update progress bar color
        if (percentage >= 90) {
            this.usageProgress.className = 'progress-bar bg-danger';
        } else if (percentage >= 70) {
            this.usageProgress.className = 'progress-bar bg-warning';
        } else {
            this.usageProgress.className = 'progress-bar bg-success';
        }
    }

    /**
     * Update status indicator
     */
    updateStatusIndicator() {
        this.statusIndicator.className = 'status-indicator online';
    }

    /**
     * Update usage statistics
     */
    async updateUsageStats() {
        try {
            const response = await axios.get('/api/v1/chat/status');
            if (response.data.usage_stats) {
                this.messagesUsedToday = response.data.usage_stats.daily_messages_used || 0;
                this.userTier = response.data.user_tier || 1;
                this.updateUsageDisplay();
            }
        } catch (error) {
            console.error('Error updating usage stats:', error);
        }
    }

    /**
     * Check chat status
     */
    async checkChatStatus() {
        try {
            const response = await axios.get('/api/v1/chat/status');
            if (response.data) {
                this.userTier = response.data.user_tier || 1;
                this.currentSessionId = response.data.session_id;
                this.updateUI();
            }
        } catch (error) {
            console.error('Error checking chat status:', error);
        }
    }

    /**
     * Update recent topics
     */
    updateRecentTopics() {
        const topics = this.conversationHistory
            .filter(msg => msg.type === 'user')
            .slice(-5)
            .map(msg => msg.content.substring(0, 50) + (msg.content.length > 50 ? '...' : ''));

        if (topics.length === 0) {
            this.recentTopics.innerHTML = '<small class="text-muted">No recent conversations</small>';
            return;
        }

        this.recentTopics.innerHTML = topics.map(topic => `
            <div class="topic-item" onclick="insertTopic('${topic.replace(/'/g, "\\'")}')">
                <small>${topic}</small>
            </div>
        `).join('');
    }

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Global functions for UI interactions
let chatInterface;

/**
 * Initialize chat when page loads
 */
document.addEventListener('DOMContentLoaded', () => {
    chatInterface = new ChatInterface();
});

/**
 * Show suggestions modal
 */
async function showSuggestions() {
    const modal = new bootstrap.Modal(document.getElementById('suggestionsModal'));
    const content = document.getElementById('suggestionsContent');
    
    modal.show();
    
    try {
        const response = await axios.get('/api/v1/chat/suggestions');
        
        if (response.data.suggestions) {
            content.innerHTML = response.data.suggestions.map(suggestion => `
                <div class="suggestion-item" onclick="useSuggestion('${suggestion.replace(/'/g, "\\'")}')">
                    <i class="fas fa-lightbulb text-primary me-2"></i>
                    ${suggestion}
                </div>
            `).join('');
        } else {
            content.innerHTML = '<p class="text-muted">No suggestions available.</p>';
        }
    } catch (error) {
        content.innerHTML = '<p class="text-danger">Error loading suggestions.</p>';
    }
}

/**
 * Use suggestion
 */
function useSuggestion(suggestion) {
    chatInterface.messageInput.value = suggestion;
    chatInterface.updateCharCount();
    chatInterface.autoResizeTextarea();
    chatInterface.messageInput.focus();
    
    // Close modal
    bootstrap.Modal.getInstance(document.getElementById('suggestionsModal')).hide();
}

/**
 * Show market overview
 */
async function showMarketOverview() {
    chatInterface.messageInput.value = "What's happening in the market today?";
    chatInterface.updateCharCount();
    chatInterface.sendMessage();
}

/**
 * Show usage statistics modal
 */
async function showUsageStats() {
    const modal = new bootstrap.Modal(document.getElementById('usageModal'));
    const content = document.getElementById('usageStatsContent');
    
    modal.show();
    
    try {
        const response = await axios.get('/api/v1/chat/status');
        
        if (response.data) {
            const stats = response.data.usage_stats || {};
            const tierLimits = {
                1: 10, 2: 50, 3: 100, 4: 200, 5: 500, 6: 1000, 7: -1
            };
            
            const dailyLimit = tierLimits[response.data.user_tier] || 10;
            const limitText = dailyLimit === -1 ? 'Unlimited' : dailyLimit;
            
            content.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Daily Messages</h5>
                                <div class="display-6">${stats.daily_messages_used || 0}</div>
                                <small class="text-muted">of ${limitText}</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <h5 class="card-title">Current Tier</h5>
                                <div class="display-6">${response.data.user_tier || 1}</div>
                                <small class="text-muted">User Tier</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-12">
                        <div class="card">
                            <div class="card-body">
                                <h6 class="card-title">Rate Limit Usage</h6>
                                <div class="progress">
                                    <div class="progress-bar" style="width: ${(stats.rate_limit_usage || 0) * 10}%"></div>
                                </div>
                                <small class="text-muted">${stats.rate_limit_usage || 0} requests in the last minute</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            content.innerHTML = '<p class="text-muted">No usage statistics available.</p>';
        }
    } catch (error) {
        content.innerHTML = '<p class="text-danger">Error loading usage statistics.</p>';
    }
}

/**
 * Clear chat history
 */
async function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    try {
        await axios.post('/api/v1/chat/clear');
        
        // Clear UI
        chatInterface.chatMessages.innerHTML = `
            <div class="message ai-message">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-text">
                        <p>Chat history cleared. How can I help you today?</p>
                    </div>
                    <div class="message-time">
                        <small class="text-muted">Just now</small>
                    </div>
                </div>
            </div>
        `;
        
        // Clear conversation history
        chatInterface.conversationHistory = [];
        chatInterface.updateRecentTopics();
        
        chatInterface.showAlert('Chat history cleared successfully.', 'success');
    } catch (error) {
        chatInterface.showAlert('Error clearing chat history.', 'danger');
    }
}

/**
 * Copy message content
 */
function copyMessage(button) {
    const messageText = button.closest('.message-content').querySelector('.message-text').textContent;
    navigator.clipboard.writeText(messageText).then(() => {
        chatInterface.showAlert('Message copied to clipboard.', 'success');
    });
}

/**
 * Regenerate AI response
 */
function regenerateResponse(button) {
    // This would trigger a regeneration of the last AI response
    chatInterface.showAlert('Regenerate feature coming soon!', 'info');
}

/**
 * Export chat history
 */
function exportChat() {
    const chatData = {
        session_id: chatInterface.currentSessionId,
        timestamp: new Date().toISOString(),
        messages: chatInterface.conversationHistory
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dekr-chat-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

/**
 * Insert topic into input
 */
function insertTopic(topic) {
    chatInterface.messageInput.value = topic;
    chatInterface.updateCharCount();
    chatInterface.autoResizeTextarea();
    chatInterface.messageInput.focus();
}

/**
 * Show input options
 */
function showInputOptions() {
    chatInterface.showAlert('Input options coming soon!', 'info');
}

// Handle connection issues
window.addEventListener('online', () => {
    chatInterface.updateStatusIndicator();
    chatInterface.showAlert('Connection restored.', 'success');
});

window.addEventListener('offline', () => {
    chatInterface.statusIndicator.className = 'status-indicator offline';
    chatInterface.showAlert('Connection lost. Please check your internet connection.', 'warning');
});
