import { useEffect, useRef } from 'react';

/**
 * ChatWindow — Collapsible bottom chat panel with auto-scroll,
 * typing indicator, and keyboard-send support.
 */
const ChatWindow = ({
  messages = [],
  chatInput = '',
  onChatInputChange,
  chatLoading = false,
  onSendChat,
  chatView = 'split',
  onToggleMinimize,
  onToggleFullscreen,
}) => {
  const chatEndRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);

  /* ── IntersectionObserver: track whether the sentinel is visible ── */
  useEffect(() => {
    const sentinel = chatEndRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        shouldAutoScrollRef.current = entry.isIntersecting;
      },
      { threshold: 0.1 }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, []);

  /* ── Auto-scroll on new messages ───────────────────────────────── */
  useEffect(() => {
    if (shouldAutoScrollRef.current && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  /* ── Send on Enter key ─────────────────────────────────────────── */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (chatInput.trim() && !chatLoading) {
        onSendChat();
      }
    }
  };

  const handleSendClick = () => {
    if (chatInput.trim() && !chatLoading) {
      onSendChat();
    }
  };

  return (
    <div className={`chat-window chat-window-${chatView}`}>
      {/* Header bar */}
      <div className="chat-header">
        <div className="chat-header-left">
          <span className="chat-status-dot" />
          <span>CIVION AI Assistant</span>
        </div>

        <div className="chat-header-actions">
          <button className="chat-toggle-btn" onClick={onToggleFullscreen} title="Toggle Fullscreen">
            {chatView === 'fullscreen' ? '🗗' : '⛶'}
          </button>
          <button className="chat-toggle-btn" onClick={onToggleMinimize} title="Minimize/Expand">
            {chatView === 'minimized' ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {/* Message list (visible only when not minimized) */}
      {chatView !== 'minimized' && (
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`chat-message ${
                msg.role === 'user' ? 'msg-user' : 'msg-assistant'
              }`}
            >
              {msg.content}
            </div>
          ))}

          {/* Typing indicator */}
          {chatLoading && (
            <div className="chat-message msg-assistant">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          {/* Scroll sentinel */}
          <div ref={chatEndRef} />
        </div>
      )}

      {/* Input area (visible only when not minimized) */}
      {chatView !== 'minimized' && (
        <div className="chat-input-area">
          <input
            className="chat-input"
            type="text"
            value={chatInput}
            onChange={(e) => onChatInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask CIVION AI..."
          />
          <button
            className="chat-send"
            disabled={chatLoading || !chatInput.trim()}
            onClick={handleSendClick}
          >
            ➤
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatWindow;
