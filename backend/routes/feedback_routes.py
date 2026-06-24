"""
feedback_routes.py – Feedback API Routes
Component 2: Back-End Server → Routes

POST /api/feedback  — submit a rating and optional comment for a bot response
GET  /api/feedback  — retrieve all feedback (admin use)
"""

from flask import Blueprint, request, jsonify, current_app, g
import logging

logger = logging.getLogger(__name__)
feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit feedback for a bot response.
    Accepts: {
        "session_id":  "...",
        "message_id":  "...",   (optional — a reference ID for the message)
        "rating":      1–5,     (1 = poor, 5 = excellent)
        "comment":     "..."    (optional)
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body is required."}), 400

    # ── Validate rating ─────────────────────────────────────────
    rating = data.get('rating')
    if rating is None:
        return jsonify({"error": "'rating' field is required."}), 400

    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return jsonify({"error": "'rating' must be an integer."}), 400

    if not (1 <= rating <= 5):
        return jsonify({"error": "'rating' must be between 1 and 5."}), 400

    session_id = data.get('session_id') or g.get('session_id', 'anonymous')
    message_id = data.get('message_id', '')
    comment    = str(data.get('comment', '')).strip()[:500]

    try:
        success = current_app.db_manager.save_feedback(
            session_id = session_id,
            message_id = message_id,
            rating     = rating,
            comment    = comment
        )
        if success:
            return jsonify({
                "status":  "ok",
                "message": "Thank you for your feedback!",
                "rating":  rating
            }), 201
        else:
            return jsonify({"error": "Failed to save feedback."}), 500

    except Exception as e:
        logger.error(f"[feedback] Error: {e}")
        return jsonify({"error": "An error occurred while saving feedback."}), 500


@feedback_bp.route('/feedback', methods=['GET'])
def get_feedback():
    """
    Retrieve all feedback entries (for admin/analytics use).
    In production, protect this endpoint with authentication.
    """
    try:
        with current_app.db_manager._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM feedback ORDER BY timestamp DESC LIMIT 100")
            rows = [dict(row) for row in cur.fetchall()]

        avg_rating = (
            round(sum(r['rating'] for r in rows) / len(rows), 2) if rows else 0
        )

        return jsonify({
            "count":      len(rows),
            "avg_rating": avg_rating,
            "feedback":   rows
        }), 200

    except Exception as e:
        logger.error(f"[feedback GET] Error: {e}")
        return jsonify({"error": "Could not retrieve feedback."}), 500
