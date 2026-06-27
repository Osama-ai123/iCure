from flask import Flask, jsonify, request

app=Flask(__name__)

# Route للتأكد ان الـ API شغالة
@app.route('/',methods=['GET'])
def check():
    return jsonify({'status':'iCure API is Running'})

# Route الرئيسي - يستقبل سؤال ويرجع جواب
@app.route('/ask',methods=['POST'])
def ask():
    data=request.get_json()

    if not data or 'question' not in data:
        return jsonify({'error':'Please, Send the Question'}),400
    
    question= data['question']
    # الخطوة 3: هون بتحط منطق RAG (بعدين)
    # answer = rag_search(question)

    answer=f'We Recieved your Question: {question}' #temp case

    # الخطوة 4: ارجع الجواب
    return jsonify({'question':question,'answer':answer}),250

if __name__ =='__main__':
    app.run(debug=True,host='0.0.0.0', port=5000)
    