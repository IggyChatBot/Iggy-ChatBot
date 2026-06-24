/**
 * app.js – Main application controller; wires together UI, API, and Chat modules
 * Component 1: Web-Based Chat Interface (Front-End)
 */

function init() {
  // Check if user is logged in
  const token = localStorage.getItem('icct_token');
  const isGuest = localStorage.getItem('icct_guest');
  if (!token && !isGuest) {
    window.location.href = 'login.html';
    return;
  }

  Utils.saveLocal('icct_session', sessionId);
  Chat.renderWelcome();
  _bindEvents();
  _checkBackendHealth();
}
const ChatApp = (() => {

  let sessionId = Utils.loadLocal('icct_session') || Utils.generateSessionId();
  let isLoading = false;
  let messageHistory = Utils.loadLocal('icct_history') || [];

  const input    = () => document.getElementById('user-input');
  const sendBtn  = () => document.getElementById('send-btn');
  const charCount = () => document.getElementById('char-count');
  const status   = () => document.getElementById('bot-status');

  // ── Init ──────────────────────────────────────────────────────
 function init() {
    Utils.saveLocal('icct_session', sessionId);
    Chat.renderWelcome();
    _bindEvents();
    _checkBackendHealth();
    _loadProfile();
  }

  function _loadProfile() {
    const user = Utils.loadLocal('icct_user');
    const token = Utils.loadLocal('icct_token');
    const isGuest = Utils.loadLocal('icct_guest');

    if (user) {
      const initials = (user.first_name?.[0] || '') + (user.last_name?.[0] || '');
      document.getElementById('profile-avatar').textContent    = initials || '👤';
      document.getElementById('profile-avatar-lg').textContent = initials || '👤';
      document.getElementById('profile-name').textContent      = user.first_name || 'User';
      document.getElementById('profile-fullname').textContent  = `${user.first_name} ${user.last_name}`;
      document.getElementById('profile-email').textContent     = user.email || '—';
      document.getElementById('profile-studentid').textContent = user.student_id ? `ID: ${user.student_id}` : '';
    } else if (isGuest) {
      document.getElementById('profile-name').textContent = 'Guest';
    }
  }

  function toggleProfile() {
    document.getElementById('profile-dropdown').classList.toggle('open');
  }

  function _bindEvents() {
    const inp = input();

    // Auto-resize + char counter
    inp.addEventListener('input', () => {
      Utils.autoResize(inp);
      charCount().textContent = `${inp.value.length}/500`;
    });

    // Enter to send (Shift+Enter = newline)
    inp.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Sidebar topic links
    document.querySelectorAll('.topic-item').forEach(item => {
      item.addEventListener('click', () => {
        inp.value = item.dataset.query;
        Utils.autoResize(inp);
        sendMessage();
      });
    });
  }

  async function _checkBackendHealth() {
    const online = await API.healthCheck();
    const el = status();
    if (!online) {
      el.innerHTML = `<span class="status-dot" style="background:#e74c3c"></span> Offline`;
      Utils.showToast('⚠️ Cannot connect to server. Responses may be limited.');
    }
  }

  // ── Send message ──────────────────────────────────────────────
  async function sendMessage() {
    const text = input().value.trim();
    if (!text || isLoading) return;

    // Clear input
    input().value = '';
    Utils.autoResize(input());
    charCount().textContent = '0/500';

    // Hide suggestions after first message
    document.getElementById('suggestions-bar').style.display = 'none';

    // Render user bubble
    Chat.appendUserMessage(text);
    Chat.addHistoryEntry(text);

    // Store in local history
    messageHistory.push({ role: 'user', content: text, time: Date.now() });

    // Show typing
    isLoading = true;
    sendBtn().disabled = true;
    Chat.showTyping();

    try {
      const data = await API.sendMessage(text, sessionId);
      Chat.hideTyping();
      Chat.appendBotMessage(data.reply, data.intent);

      messageHistory.push({ role: 'bot', content: data.reply, intent: data.intent, time: Date.now() });
      Utils.saveLocal('icct_history', messageHistory.slice(-50));

    } catch (err) {
      Chat.hideTyping();
      Chat.appendBotMessage(
        '⚠️ Sorry, I couldn\'t reach the server right now. Please try again in a moment.',
        null,
        true
      );
      console.error('[ChatApp] API error:', err.message);
    }

    isLoading = false;
    sendBtn().disabled = false;
    input().focus();
  }

  /** Called by suggestion chips */
  function sendSuggestion(btn) {
    input().value = btn.textContent;
    sendMessage();
  }

  /** Clear chat and reset session */
  function clearChat() {
    sessionId = Utils.generateSessionId();
    messageHistory = [];
    Utils.saveLocal('icct_session', sessionId);
    Utils.saveLocal('icct_history', []);
    Chat.clearMessages();
    input().focus();
    Utils.showToast('Chat cleared. New session started.');
  }

  /** Export chat as a plain-text file */
  function exportChat() {
    if (!messageHistory.length) { Utils.showToast('No messages to export.'); return; }
    const lines = messageHistory.map(m => {
      const time = new Date(m.time).toLocaleString('en-PH');
      const role = m.role === 'user' ? 'You' : 'ICCT Bot';
      return `[${time}] ${role}:\n${m.content}\n`;
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `ICCT_Chat_${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    Utils.showToast('Chat exported!');
  }

  // Auto-init when DOM is ready
  document.addEventListener('DOMContentLoaded', init);

  return { sendMessage, sendSuggestion, clearChat, exportChat, logout, toggleProfile };
  function logout() {
  localStorage.removeItem('icct_token');
  localStorage.removeItem('icct_guest');
  localStorage.removeItem('icct_session');
  localStorage.removeItem('icct_history');
  window.location.href = 'login.html';
}
})();
