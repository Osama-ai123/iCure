from flask import Flask, request, jsonify 

app=Flask(__name__)

@app.route('/')
def home():
    return "Welcome to iCure"

@app.route('/about')
def about():
    return "This is a health care medical AI system "

@app.route('/user/<username>')
def show_user(username):
    return f'welcome {username}'

@app.route('/question/<int:question_id>')
def get_question(question_id):
    return f'get question number {question_id}'

@app.route('/hello',methods=['GET'])
def hello():
    return "this is GET request"

@app.route('/ask',methods=['POST'])
def ask_question():
    data=request.get_json()
    question=data['question']
    return f'we recieved the question {question}'

@app.route('/ask2',methods=['POST','GET'])
def ask2():
    if request.method=='POST':
        data = request.get_json()
        return f'your question:{data['question']}'
    else:
        return f'send your question by POST request'

#curl -X POST http://127.0.0.1:5000/ask2 \
#  -H "Content-Type: application/json" \
#  -d '{"question": "what is headache symptom?"}*/

@app.route('/ask3',methods=['POST'])
def ask3():
    data=request.get_json() #بيحول الـ JSON لـ dictionary
    question=data['question'] # بتاخذ قيمة المفتاح 'question'
    return question

@app.route('/login',methods=['POST'])
def login():
        username = request.form.get('username')
        age = request.form.get('age')
        return f'welcome {username}\nyour age= {age}'
# curl -X POST http://127.0.0.1:5000/login \ -d "username=osama&age=25"

@app.route('/login2', methods=['POST', 'GET'])
def login2():
    if request.method == 'POST':
        username = request.form.get('username')
        age = request.form.get('age')
        return f'welcome {username}<br>your age= {age}'
    else:
        return '''
            <form method="POST">
                <input type="text" name="username" placeholder="Username">
                <input type="text" name="age" placeholder="Age">
                <button type="submit">Login</button>
            </form>
        '''
#curl -X POST http://127.0.0.1:5000/login2 -d "username=osama&age=25"

@app.route('/login3', methods=['GET', 'POST'])
def login3():
    if request.method == 'POST':
        username = request.form.get('username')
        age = request.form.get('age')
        return f'welcome {username}<br>your age= {age}'
    
    return '''
        <form method="POST">
            <input type="text" name="username" placeholder="Username"><br>
            <input type="text" name="age" placeholder="Age"><br>
            <input type="submit">
        </form>
    '''

@app.route('/search')
def search():
    #localhost:5000/search?q=headache
    query=request.args.get('q')
    return f'you searched about {query}'
   


@app.route('/ask4',methods=['POST'])
def ask4():
    data=request.get_json()
    question = data['question']

    # iCure logic and work
    answer='this is a temp answer'

    return jsonify({
        'question': question,
        'answer':answer,
        'status':'success'
    })


if __name__ =='__main__':
    app.run(debug=True)
