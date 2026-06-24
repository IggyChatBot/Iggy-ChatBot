"""
chat_routes.py – Chat API Routes
"""
from flask import Blueprint, request, jsonify, current_app, g
import logging
import os
from google import genai

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)

# ── Configure Gemini ────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
gemini_model = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        gemini_model = gemini_client
        logger.info("Gemini AI configured successfully.")
    except Exception as e:
        logger.error(f"Gemini setup failed: {e}")
        gemini_model = None
else:
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
                f'Using this information, give a helpful and friendly response as Iggy, '
                f'the official AI chatbot of ICCT Colleges in Cainta, Rizal, Philippines.'
            )
        else:
            prompt = (
                f'You are Iggy, the friendly AI chatbot of ICCT Colleges in Cainta, Rizal, Philippines. '
                f'Answer this question helpfully and concisely: {user_message}'
            )
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
    session_id = data.get('session_id') or g.get('session_id', 'anonymous')

    nlp = current_app.nlp_engine
    db = current_app.db_manager

    try:
        db_context = None
        faq_match = db.search_faq(user_message)
        if faq_match:
            db_context = {"answer": faq_match["answer"]}

        gemini_reply = ask_gemini(user_message, db_context)

        if gemini_reply:
            reply = gemini_reply
            intent = "ai_response"
            source = "gemini"
            entities = {}
        else:
            result = nlp.generate_response(user_message, db_context=db_context)
            reply = result["reply"]
            intent = result["intent"]
            source = result["source"]
            entities = result["entities"]

        db.log_interaction(
            session_id=session_id,
            user_message=user_message,
            bot_reply=reply,
            intent=intent,
            entities=str(entities)
        )

        return jsonify({
            "reply": reply,
            "intent": intent,
            "entities": entities,
            "source": source,
            "session_id": session_id
        }), 200

    except Exception as e:
        logger.error(f"[chat] Unhandled error: {e}")
        return jsonify({
            "reply": "I'm having trouble processing your request right now. Please try again.",
            "intent": "error",
            "error": str(e)
        }), 500


@chat_bp.route('/stats', methods=['GET'])
def stats():
    try:
        data = current_app.db_manager.get_interaction_stats()
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"[stats] Error: {e}")
        return jsonify({"error": "Could not retrieve stats."}), 500
