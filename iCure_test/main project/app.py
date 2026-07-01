from flask import Flask, request, jsonify
from rag_pipeline import ask
import os

app = Flask(__name__)

# Route 1: Health check
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'iCure API is running',
        'version': '1.0'
    })

# Route 2: السؤال الطبي
@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()

    if not data or 'question' not in data:
        return jsonify({
            'error': 'Please provide a question',
            'example': {
                'question': 'What is the treatment?',
                'history': [
                    {'role': 'user', 'content': 'What are symptoms of diabetes?'},
                    {'role': 'assistant', 'content': 'Symptoms include frequent urination...'}
                ]
            }
        }), 400

    question = data['question'].strip()
    history = data.get('history', [])  # لو ما في history يرجع قائمة فاضية

    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400

    answer = ask(question, history)

    return jsonify({
        'question': question,
        'answer': answer,
        'status': 'success'
    }), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)