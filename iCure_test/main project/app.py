from flask import Flask, request, jsonify
from rag_pipeline import ask
import os
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
# تخزين الـ sessions بالذاكرة
sessions = {}

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
                'session_id': 'any-unique-id'
            }
        }), 400

    question = data['question'].strip()
    session_id = data.get('session_id', 'default')

    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    # جيب الـ history تبع الـ session
    if session_id not in sessions:
        sessions[session_id] = []
    
    history = sessions[session_id]

    # اطلب الجواب
    answer = ask(question, history)

    # حدّث الـ history تلقائياً
    sessions[session_id].append({'role': 'user', 'content': question})
    sessions[session_id].append({'role': 'assistant', 'content': answer})

    # خلّي الـ history بآخر 6 رسائل بس (3 أسئلة وأجوبة)
    sessions[session_id] = sessions[session_id][-6:]

    return jsonify({
        'question': question,
        'answer': answer,
        'session_id': session_id,
        'status': 'success'
    }), 200

@app.route('/clear', methods=['POST'])
def clear_session():
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    if session_id in sessions:
        sessions.pop(session_id)
    return jsonify({'status': 'session cleared', 'session_id': session_id})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)