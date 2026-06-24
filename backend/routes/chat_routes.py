"""
chat_routes.py – Chat API Routes
Component 2: Back-End Server → Routes
POST /api/chat  — receives a user message, runs NLP, queries DB, returns reply
GET  /api/stats — returns interaction analytics
"""
from flask import Blueprint, request, jsonify, current_app, g
import logging
import os
from google import genai

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)

# ── Configure Gemini ────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    gemini_model = gemini_client
    logger.info("Gemini AI configured successfully.")
else:
    gemini_model = None
    logger.warning("GEMINI_API_KEY not set — falling back to NLP engine only.")


def ask_gemini(user_message, faq_context=None):
    """Send message to Gemini and get a response."""
    if not gemini_model:
        return None
    try:
        if faq_context:
            prompt = (
                f'The user asked: "{user_message}"\n\n'
                f'Here is relevant information from the ICCT database:\n'
                f'{faq_context["answer"]}\n\n'
                f'Using this information, give a helpful and friendly response as Iggy.'
            )
        else:
            prompt = user_message
        response = gemini_model.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        logger.error(f"[Gemini] Error: {e}")
        return None


@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True)

    if not data or not data.get('message', '').strip():
        return jsonify({"error": "Message is required."}), 400

    user_message = data['message'].strip()[:500]
    session_id   = data.get('session_id') or g.get('session_id', 'anonymous')

    nlp = current_app.nlp_engine
    db  = current_app.db_manager

    try:
        # Step 1: Search database for a matching FAQ
        db_context = None
        faq_match = db.search_faq(user_message)
        if faq_match:
            db_context = {"answer": faq_match["answer"]}

        # Step 2: Try Gemini AI first
        gemini_reply = ask_gemini(user_message, db_context)

        if gemini_reply:
            reply  = gemini_reply
            intent = "ai_response"
            source = "gemini"
            entities = {}
        else:
            # Fallback to NLP engine if Gemini fails
            result   = nlp.generate_response(user_message, db_context=db_context)
            reply    = result["reply"]
            intent   = result["intent"]
            source   = result["source"]
            entities = result["entities"]

        # Step 3: Log interaction
        db.log_interaction(
            session_id   = session_id,
            user_message = user_message,
            bot_reply    = reply,
            intent       = intent,
            entities     = str(entities)
        )

        return jsonify({
            "reply":      reply,
            "intent":     intent,
            "entities":   entities,
            "source":     source,
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
    try:
        data = current_app.db_manager.get_interaction_stats()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"[stats] Error: {e}")
        return jsonify({"error": "Could not retrieve stats."}), 500
