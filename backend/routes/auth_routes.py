from flask import Blueprint, request, jsonify, current_app
import hashlib
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    first_name = data.get('first_name', '').strip()
    last_name  = data.get('last_name', '').strip()
    email      = data.get('email', '').strip()
    student_id = data.get('student_id', '').strip()
    password   = data.get('password', '')

    if not all([first_name, last_name, email, password]):
        return jsonify({"message": "All fields are required."}), 400

    db = current_app.db_manager
    existing = db.get_user_by_email(email)
    if existing:
        return jsonify({"message": "Email already registered."}), 409

    hashed = hashlib.sha256(password.encode()).hexdigest()
    db.create_user({
        "id":         str(uuid.uuid4()),
        "first_name": first_name,
        "last_name":  last_name,
        "email":      email,
        "student_id": student_id,
        "password":   hashed
    })
    return jsonify({"message": "Account created successfully."}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email    = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400

    db = current_app.db_manager
    user = db.get_user_by_email(email)

    if not user:
        return jsonify({"message": "Invalid email or password."}), 401

    hashed = hashlib.sha256(password.encode()).hexdigest()
    if user['password'] != hashed:
        return jsonify({"message": "Invalid email or password."}), 401

    return jsonify({
        "message": "Login successful.",
        "token": user['id'],
        "user": {
            "first_name": user['first_name'],
            "last_name":  user['last_name'],
            "email":      user['email']
        }
    }), 200
