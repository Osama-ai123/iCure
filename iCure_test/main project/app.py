from flask import Flask, request, jsonify
from rag_pipeline import ask
from flask_cors import CORS
from db.database import SessionLocal
from db.models import User, Conversation, Message

##1
GUEST_EMAIL = "guest@icure.local"


def get_guest_user_id(db):
    """مؤقت حتى تصل المصادقة — يُستبدل بـ g.current_user_id"""
    return db.query(User).filter_by(email=GUEST_EMAIL).first().id

##2
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

##3
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

##

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'iCure API is running',
        'version': '1.0'
    })

@app.route('/ask', methods=['POST'])
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
        usr_id=get_guest_user_id(db)
        chat=get_or_create_conversation(db,usr_id,conversation_id)
        if chat is None:
            return jsonify({
                'error':'there is no chat or conversation'
            }),404
            

        history=build_history(db,chat.id)

        answer=ask(question,history)

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

 

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)