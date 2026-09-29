from flask import Flask, request, jsonify, g
from rag_pipeline import ask
from flask_cors import CORS
from db.database import SessionLocal
from datetime import datetime, timezone
from auth import (
    hash_password, check_password, create_access_token,
    generate_refresh_token, refresh_token_expiry, hash_refresh_token,
    require_auth, MAX_PASSWORD_BYTES, ACCESS_TOKEN_MINUTES,
)
from db.models import User, Conversation, Message, RefreshToken
from sqlalchemy.exc import IntegrityError
from auth import hash_password, MAX_PASSWORD_BYTES
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

MIN_PASSWORD_LENGTH = 8


def get_or_create_conversation(db, user_id, conversation_id):
    if conversation_id is None:
        conv = Conversation(user_id=user_id)
        db.add(conv)
        db.commit()
        return conv

    return db.query(Conversation).filter_by(
        id=conversation_id,
        user_id=user_id
    ).first()


def build_history(db, conversation_id, limit=6):
    messages = (
        db.query(Message)
        .filter_by(conversation_id=conversation_id)
        .order_by(Message.sent_time.desc())
        .limit(limit)
        .all()
    )

    messages.reverse()

    role_map = {'question': 'user', 'response': 'assistant'}
    return [
        {'role': role_map[m.role], 'content': m.content}
        for m in messages
    ]



app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'iCure API is running',
        'version': '1.0'
    })

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or '@' not in email:
        return jsonify({'error': 'A valid email is required'}), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({'error': f'Password must be at least {MIN_PASSWORD_LENGTH} characters'}), 400
    if len(password.encode('utf-8')) > MAX_PASSWORD_BYTES:
        return jsonify({'error': 'Password is too long'}), 400

    db = SessionLocal()
    try:
        if db.query(User).filter_by(email=email).first():
            return jsonify({'error': 'Email is already registered'}), 409

        user = User(email=email, pass_hash=hash_password(password))
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return jsonify({'error': 'Email is already registered'}), 409

        return jsonify({'id': user.id, 'email': user.email}), 201
    finally:
        db.close()


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        if user is None or not check_password(password, user.pass_hash):
            return jsonify({'error': 'Invalid email or password'}), 401

        refresh_token, token_hash = generate_refresh_token()
        db.add(RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=refresh_token_expiry(),
        ))
        db.commit()

        return jsonify({
            'access_token': create_access_token(user.id),
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_MINUTES * 60,
        }), 200
    finally:
        db.close()

@app.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json(silent=True) or {}
    token = data.get('refresh_token') or ''
    if not token:
        return jsonify({'error': 'refresh_token is required'}), 400

    db = SessionLocal()
    try:
        row = db.query(RefreshToken).filter_by(token_hash=hash_refresh_token(token)).first()
        if row is None:
            return jsonify({'error': 'Invalid refresh token'}), 401
        if row.expires_at < datetime.now(timezone.utc):
            db.delete(row)
            db.commit()
            return jsonify({'error': 'Refresh token expired'}), 401

        return jsonify({
            'access_token': create_access_token(row.user_id),
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_MINUTES * 60,
        }), 200
    finally:
        db.close()


@app.route('/logout', methods=['POST'])
def logout():
    data = request.get_json(silent=True) or {}
    token = data.get('refresh_token') or ''
    if not token:
        return jsonify({'error': 'refresh_token is required'}), 400

    db = SessionLocal()
    try:
        db.query(RefreshToken).filter_by(token_hash=hash_refresh_token(token)).delete()
        db.commit()
        return '', 204
    finally:
        db.close()


@app.route('/ask', methods=['POST'])
@require_auth
def ask_question():
    data = request.get_json()

    if not data or 'question' not in data:
        return jsonify({
            'error': 'Please provide a question',
            'example': {
                'question': 'ما هي أعراض فقر الدم؟',
                'conversation_id': 7
            }
        }), 400
    
   
    question = data['question'].strip()
    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400
    conversation_id = data.get('conversation_id')
    
    db = SessionLocal()
    try:
        usr_id = g.current_user_id
        is_new = conversation_id is None
        chat=get_or_create_conversation(db,usr_id,conversation_id)
        if chat is None:
            return jsonify({
                'error':'there is no chat or conversation'
            }),404
        if chat.title is None:
            chat.title = question[:60]

        history=build_history(db,chat.id)

        try:
            answer = ask(question, history)
        except Exception:
            logging.exception("RAG/LLM call failed")
            db.rollback()
            if is_new:
                db.delete(chat)
                db.commit()
            return jsonify({'error': 'The AI service is temporarily unavailable. Please try again later.'}), 503

        last_question=Message(conversation_id=chat.id,content=question,role="question")
        db.add(last_question)
        last_answer=Message(conversation_id=chat.id,content=answer,role="response")
        db.add(last_answer)
        db.commit()

        return jsonify({
                'question': question,
                'answer': answer,
                'conversation_id':chat.id,
                'status': 'success'
            }), 200
        
    finally:
         db.close()

@app.route('/conversations', methods=['GET'])
@require_auth
def list_conversations():
    db = SessionLocal()
    try:
        convs = (db.query(Conversation)
                 .filter_by(user_id=g.current_user_id)
                 .order_by(Conversation.created_at.desc())
                 .all())
        return jsonify([
            {
                'id': c.id,
                'title': c.title or 'New conversation',
                'created_at': c.created_at.isoformat() if c.created_at else None,
            }
            for c in convs
        ]), 200
    finally:
        db.close()


@app.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@require_auth
def get_conversation_messages(conversation_id):
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter_by(
            id=conversation_id, user_id=g.current_user_id).first()
        if conv is None:
            return jsonify({'error': 'Conversation not found'}), 404
        return jsonify([
            {'role': m.role, 'content': m.content}
            for m in conv.messages
        ]), 200
    finally:
        db.close()


@app.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@require_auth
def delete_conversation(conversation_id):
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter_by(
            id=conversation_id, user_id=g.current_user_id).first()
        if conv is None:
            return jsonify({'error': 'Conversation not found'}), 404
        db.delete(conv)
        db.commit()
        return '', 204
    finally:
        db.close()
 

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)