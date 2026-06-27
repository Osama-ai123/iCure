import os
from flask import Flask

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
instance_path = os.path.join(root_path, 'instance')

app = Flask(__name__, instance_path=instance_path)

print("instance_path:", app.instance_path)

app.config.from_object('config.default')
app.config.from_pyfile(os.path.join(instance_path, 'config.py'))  # مسار كامل
app.config.from_envvar('APP_SETTINGS')

@app.route("/")
def hello():
    return "lesson 2 : hello + config file"


if __name__=="__main__":
    app.run(port=app.config['PORT'],debug=app.config['DEBUG'])

