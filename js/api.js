/**
 * api.js – Handles all communication with the Python back-end server
 * Component 1: Web-Based Chat Interface (Front-End)
 * Connects to: Component 2 (Back-End Server)
 */

const API = (() => {

  const BASE_URL = 'https://iggy-chatbot-1-oic6.onrender.com/api';   // Change to production URL when deploying

  /** Send a chat message and receive the bot response */
  async function sendMessage(message, sessionId) {
    const response = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Session-ID': sessionId
      },
      body: JSON.stringify({ message, session_id: sessionId })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `Server error ${response.status}`);
    }

    return await response.json();
    /*
      Expected response shape:
      {
        "reply":    "Here is the answer...",
        "intent":   "enrollment_inquiry",
        "entities": { "course": "BSIT" },
        "source":   "database" | "nlp_model",
        "session_id": "..."
      }
    */
  }

  /** Retrieve FAQ entries from the database */
  async function getFAQs(category = null) {
    const url = category
      ? `${BASE_URL}/faqs?category=${encodeURIComponent(category)}`
      : `${BASE_URL}/faqs`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to load FAQs');
    return await response.json();
  }

  /** Submit user feedback for a specific message */
  async function submitFeedback(sessionId, messageId, rating, comment = '') {
    const response = await fetch(`${BASE_URL}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message_id: messageId, rating, comment })
    });
    return await response.json();
  }

  /** Health check – verify back-end is reachable */
  async function healthCheck() {
    try {
      const response = await fetch(`${BASE_URL}/health`, { signal: AbortSignal.timeout(4000) });
      return response.ok;
    } catch {
      return false;
    }
  }

  return { sendMessage, getFAQs, submitFeedback, healthCheck };
})();
