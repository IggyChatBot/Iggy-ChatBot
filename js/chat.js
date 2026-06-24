/**
 * chat.js – Chat UI rendering and message management
 * Component 1: Web-Based Chat Interface (Front-End)
 */

const Chat = (() => {

  const messagesArea = () => document.getElementById('messages-area');

  /** Render the welcome card on first load */
  function renderWelcome() {
    const area = messagesArea();
    area.innerHTML = `
      <div class="welcome-card">
        <img src="Iggy.png" alt="Iggy" class="welcome-icon-img"/>
        <div class="welcome-title">Welcome to ICCT Bot!</div>
        <div class="welcome-sub">
          I can help you with enrollment, courses, schedules, tuition, scholarships, and school policies.
          <br/><br/>Select a topic on the left or type your question below.
        </div>
      </div>`;
  }

  /** Append a user message bubble */
  function appendUserMessage(text) {
    const area = messagesArea();
    const row = document.createElement('div');
    row.className = 'msg-row user';
    row.innerHTML = `
      <div>
        <div class="msg-bubble">${Utils.escapeHTML(text)}</div>
        <div class="msg-meta">${Utils.formatTime()}</div>
      </div>
      <div class="msg-avatar-sm" aria-hidden="true">👤</div>`;
    area.appendChild(row);
    Utils.scrollToBottom(area);
    return row;
  }

  /** Show animated typing indicator */
  function showTyping() {
    const area = messagesArea();
    const row = document.createElement('div');
    row.className = 'typing-row';
    row.id = 'typing-indicator';
    row.innerHTML = `
      <img src="Iggy.png" style="width:20px;height:20px;border-radius:50%;object-fit:cover;">
      <div class="typing-bubble">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>`;
    area.appendChild(row);
    Utils.scrollToBottom(area);
  }

  /** Remove typing indicator */
  function hideTyping() {
    document.getElementById('typing-indicator')?.remove();
  }

  /** Append a bot response bubble */
  function appendBotMessage(text, intent = null, isError = false) {
    const area = messagesArea();
    const row = document.createElement('div');
    row.className = 'msg-row bot';
    row.dataset.intent = intent || '';

    const bubbleClass = isError ? 'msg-bubble error-bubble' : 'msg-bubble';
    // Convert newlines to <br> and preserve simple markdown bold **text**
    const formatted = Utils.escapeHTML(text)
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    row.innerHTML = `
      <img src="Iggy.png" style="width:20px;height:20px;border-radius:50%;object-fit:cover;">
      <div>
        <div class="${bubbleClass}">${formatted}</div>
        <div class="msg-meta">
          ${Utils.formatTime()}
          ${intent ? `· <em>${intent.replace(/_/g, ' ')}</em>` : ''}
        </div>
      </div>`;
    area.appendChild(row);
    Utils.scrollToBottom(area);
    return row;
  }

  /** Add an entry to the sidebar history list */
  function addHistoryEntry(text) {
    const list = document.getElementById('history-list');
    const empty = list.querySelector('.history-empty');
    if (empty) empty.remove();

    const item = document.createElement('li');
    item.className = 'history-item';
    item.title = text;
    item.textContent = text.length > 30 ? text.slice(0, 30) + '…' : text;
    list.insertBefore(item, list.firstChild);

    // Keep only last 8 entries
    while (list.children.length > 8) list.removeChild(list.lastChild);
  }

  /** Clear all messages and re-render welcome */
  function clearMessages() {
    renderWelcome();
    document.getElementById('history-list').innerHTML =
      '<li class="history-empty">No previous sessions</li>';
    document.getElementById('suggestions-bar').style.display = 'flex';
  }

  return { renderWelcome, appendUserMessage, showTyping, hideTyping, appendBotMessage, addHistoryEntry, clearMessages };
})();