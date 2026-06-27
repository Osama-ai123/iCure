from flask import Flask 
app=Flask(__name__)

#localhost:5000
@app.route("/")
def hello():
    return "HELLO WORLDDDDD 2"

if __name__=="__main__":
    app.run()


