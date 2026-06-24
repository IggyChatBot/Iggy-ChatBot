"""
faq_routes.py – FAQ API Routes
Component 2: Back-End Server → Routes

GET  /api/faqs              — list all FAQs (optional ?category=enrollment)
GET  /api/faqs/<int:faq_id> — get a single FAQ by ID
GET  /api/courses           — list all courses (optional ?college=computer)
GET  /api/courses/<code>    — get a course by its code (e.g. BSIT)
"""

from flask import Blueprint, request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)
faq_bp = Blueprint('faq', __name__)


# ── FAQs ──────────────────────────────────────────────────────────

@faq_bp.route('/faqs', methods=['GET'])
def get_faqs():
    """
    Return all FAQs. Optionally filter by category.
    Query param: ?category=enrollment
    """
    category = request.args.get('category', '').strip() or None
    try:
        faqs = current_app.db_manager.get_faqs(category=category)
        return jsonify({
            "count":    len(faqs),
            "category": category,
            "faqs":     faqs
        }), 200
    except Exception as e:
        logger.error(f"[faqs] Error: {e}")
        return jsonify({"error": "Could not retrieve FAQs."}), 500


@faq_bp.route('/faqs/search', methods=['GET'])
def search_faqs():
    """
    Search FAQs by keyword.
    Query param: ?q=enrollment requirements
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400

    try:
        result = current_app.db_manager.search_faq(query)
        if result:
            return jsonify({"found": True, "faq": result}), 200
        else:
            return jsonify({"found": False, "message": "No matching FAQ found."}), 200
    except Exception as e:
        logger.error(f"[faqs/search] Error: {e}")
        return jsonify({"error": "Search failed."}), 500


# ── Courses ───────────────────────────────────────────────────────

@faq_bp.route('/courses', methods=['GET'])
def get_courses():
    """
    Return all courses. Optionally filter by college.
    Query param: ?college=computer
    """
    college = request.args.get('college', '').strip() or None
    try:
        courses = current_app.db_manager.get_courses(college=college)
        return jsonify({
            "count":   len(courses),
            "courses": courses
        }), 200
    except Exception as e:
        logger.error(f"[courses] Error: {e}")
        return jsonify({"error": "Could not retrieve courses."}), 500


@faq_bp.route('/courses/<string:code>', methods=['GET'])
def get_course(code):
    """Return a single course by its code (e.g. /api/courses/BSIT)."""
    try:
        course = current_app.db_manager.get_course_by_code(code)
        if course:
            return jsonify(course), 200
        else:
            return jsonify({"error": f"Course '{code.upper()}' not found."}), 404
    except Exception as e:
        logger.error(f"[courses/{code}] Error: {e}")
        return jsonify({"error": "Could not retrieve course."}), 500
