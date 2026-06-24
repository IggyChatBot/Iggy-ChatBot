"""
chat_routes.py – Chat API Routes
Component 2: Back-End Server → Routes

POST /api/chat  — receives a user message, runs NLP, queries DB, returns reply
GET  /api/stats — returns interaction analytics
"""

from flask import Blueprint, request, jsonify, current_app, g
import logging

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint.
    Accepts: { "message": "...", "session_id": "..." }
    Returns: { "reply": "...", "intent": "...", "entities": {...}, "source": "..." }
    """
    data = request.get_json(silent=True)

    # ── Validate input ──────────────────────────────────────────
    if not data or not data.get('message', '').strip():
        return jsonify({"error": "Message is required."}), 400

    user_message = data['message'].strip()[:500]   # Hard cap at 500 chars
    session_id   = data.get('session_id') or g.get('session_id', 'anonymous')

    if len(user_message) < 1:
        return jsonify({"error": "Message cannot be empty."}), 400

    # ── Get shared instances ────────────────────────────────────
    nlp = current_app.nlp_engine
    db  = current_app.db_manager

    try:
        # Step 1: Search database for a matching FAQ first
        db_context = None
        faq_match = db.search_faq(user_message)
        if faq_match:
            db_context = {"answer": faq_match["answer"]}

        # Step 2: Run NLP engine (intent + entity detection + response)
        result = nlp.generate_response(user_message, db_context=db_context)

        # Step 3: Log the interaction to the database
        db.log_interaction(
            session_id   = session_id,
            user_message = user_message,
            bot_reply    = result["reply"],
            intent       = result["intent"],
            entities     = result["entities"]
        )

        # Step 4: Return response to front-end
        return jsonify({
            "reply":      result["reply"],
            "intent":     result["intent"],
            "entities":   result["entities"],
            "source":     result["source"],
            "session_id": session_id
        }), 200

    except Exception as e:
        logger.error(f"[chat] Unhandled error: {e}")
        return jsonify({
            "reply":  "I'm having trouble processing your request right now. Please try again.",
            "intent": "error",
            "error":  str(e)
        }), 500


@chat_bp.route('/stats', methods=['GET'])
def stats():
    """Return basic analytics (admin use)."""
    try:
        data = current_app.db_manager.get_interaction_stats()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"[stats] Error: {e}")
        return jsonify({"error": "Could not retrieve stats."}), 500
