/**
 * utils.js – Shared helper utilities
 * Component 1: Web-Based Chat Interface (Front-End)
 */

const Utils = (() => {

  /** Format a timestamp to HH:MM */
  function formatTime(date = new Date()) {
    return date.toLocaleTimeString('en-PH', { hour: '2-digit', minute: '2-digit' });
  }

  /** Escape HTML to prevent XSS */
  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /** Auto-resize a textarea based on content */
  function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 110) + 'px';
  }

  /** Show a toast notification */
  function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
  }

  /** Debounce a function */
  function debounce(fn, delay) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
  }

  /** Scroll an element to the bottom */
  function scrollToBottom(el) {
    el.scrollTop = el.scrollHeight;
  }

  /** Generate a simple session ID */
  function generateSessionId() {
    return 'icct_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8);
  }

  /** Save data to localStorage safely */
  function saveLocal(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
  }

  /** Load data from localStorage safely */
  function loadLocal(key, fallback = null) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
  }

  return { formatTime, escapeHTML, autoResize, showToast, debounce, scrollToBottom, generateSessionId, saveLocal, loadLocal };
})();